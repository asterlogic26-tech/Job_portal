import logging
import hashlib
import asyncio
import os
from typing import Optional


from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="workers.tasks.normalization_tasks.normalize_job",
    bind=True,
    max_retries=2,
)
def normalize_job(self, raw_job_data: dict):
    """Normalize a raw job posting into structured schema."""
    try:
        result = asyncio.run(_normalize_async(raw_job_data))
        if result:
            # Trigger matching
            from workers.tasks.matching_tasks import compute_job_match
            compute_job_match.delay(str(result["job_id"]))
        return result
    except Exception as exc:
        logger.error(f"Normalization failed: {exc}")
        raise self.retry(exc=exc)


async def _normalize_async(raw: dict) -> Optional[dict]:
    """Async normalization pipeline."""
    from engines.normalization.extractor import JobEntityExtractor
    from engines.normalization.deduplicator import compute_content_hash
    from engines.normalization.title_normalizer import normalize_title
    from engines.embedding.embedder import embed_text
    from workers.db_utils import get_sync_session
    from sqlalchemy import text
    import uuid

    title = raw.get("title", "")
    company = raw.get("company_name", "")
    description = raw.get("description_raw", "")

    if not title or not description:
        return None

    # Compute content hash for deduplication
    content_hash = compute_content_hash(title, company, description)

    # Check for exact duplicate
    with get_sync_session() as session:
        existing = session.execute(
            text("SELECT id FROM jobs WHERE content_hash = :hash LIMIT 1"),
            {"hash": content_hash},
        ).fetchone()

        if existing:
            logger.debug(f"Duplicate job detected: {title}")
            return None

    # Extract entities
    extractor = JobEntityExtractor()
    extracted = await extractor.extract(description, fallback_data=raw)

    # Normalize title
    normalized_title = normalize_title(extracted.get("title", title))

    # Generate embedding for vector search
    embed_text_content = f"{normalized_title} {company} {description[:500]}"
    vector = embed_text(embed_text_content)

    # Store job in DB
    job_id = str(uuid.uuid4())
    # Generate a unique external_id for sources that don't provide one (e.g. RSS)
    external_id = raw.get("external_id") or f"hash_{content_hash[:24]}"
    with get_sync_session() as session:
        session.execute(
            text("""
            INSERT INTO jobs (
                id, external_id, source, url, company_name,
                title, normalized_title, description, description_html,
                required_skills, preferred_skills, seniority_level,
                remote_policy, location, salary_min, salary_max, salary_currency,
                apply_url, content_hash, posted_at,
                created_at, updated_at
            ) VALUES (
                :id, :external_id, :source, :url, :company_name,
                :title, :normalized_title, :description, :description_html,
                :required_skills::jsonb, :preferred_skills::jsonb, :seniority_level,
                :remote_policy, :location, :salary_min, :salary_max, 'USD',
                :apply_url, :content_hash, :posted_at,
                NOW(), NOW()
            )
            ON CONFLICT DO NOTHING
            """),
            {
                "id": job_id,
                "external_id": external_id,
                "source": raw.get("source", "unknown"),
                "url": raw.get("source_url") or raw.get("apply_url", ""),
                "company_name": extracted.get("company_name") or company,
                "title": title,
                "normalized_title": normalized_title,
                "description": description[:10000],
                "description_html": extracted.get("description_markdown", "")[:5000],
                "required_skills": str(extracted.get("skills_required", [])).replace("'", '"'),
                "preferred_skills": str(extracted.get("skills_preferred", [])).replace("'", '"'),
                "seniority_level": extracted.get("seniority_level") or "unknown",
                "remote_policy": extracted.get("remote_policy") or raw.get("remote_policy") or "unknown",
                "location": extracted.get("location") or raw.get("location", ""),
                "salary_min": extracted.get("salary_min"),
                "salary_max": extracted.get("salary_max"),
                "apply_url": raw.get("apply_url") or raw.get("source_url", ""),
                "content_hash": content_hash,
                "posted_at": raw.get("posted_at"),
            },
        )
        session.commit()

    # Store embedding in vector store
    try:
        from engines.embedding.vector_store import VectorStore
        import os
        store = VectorStore(
            url=os.environ.get("QDRANT_URL", "http://localhost:6333"),
            collection_name=os.environ.get("QDRANT_COLLECTION_JOBS", "job_embeddings"),
        )
        store.upsert(
            id=job_id,
            vector=vector,
            payload={
                "job_id": job_id,
                "title": normalized_title,
                "company": company,
                "source": raw.get("source"),
            },
        )
    except Exception as e:
        logger.warning(f"Vector store upsert failed (non-critical): {e}")

    logger.info(f"Normalized job: {normalized_title} at {company}")
    return {"job_id": job_id, "title": normalized_title}
