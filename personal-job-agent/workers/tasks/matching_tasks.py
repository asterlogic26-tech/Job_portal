import logging
import asyncio
import os
import json


from workers.celery_app import celery_app

logger = logging.getLogger(__name__)

SINGLE_USER_ID = "00000000-0000-0000-0000-000000000001"


@celery_app.task(name="workers.tasks.matching_tasks.compute_job_match", bind=True)
def compute_job_match(self, job_id: str):
    """Compute match score for a single job."""
    try:
        asyncio.run(_compute_match_async(job_id))
    except Exception as exc:
        logger.error(f"Match computation failed for {job_id}: {exc}")
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(name="workers.tasks.matching_tasks.compute_all_matches")
def compute_all_matches():
    """Recompute match scores for all unmatched jobs."""
    from db_utils import get_sync_session
    from sqlalchemy import text

    logger.info("Computing match scores for all unanalyzed jobs...")

    with get_sync_session() as session:
        jobs = session.execute(
            text("SELECT id FROM jobs WHERE status = 'new' AND is_duplicate = false LIMIT 200")
        ).fetchall()

    count = 0
    for (job_id,) in jobs:
        compute_job_match.delay(str(job_id))
        count += 1

    logger.info(f"Queued {count} match computations")
    return {"queued": count}


async def _compute_match_async(job_id: str):
    """Async match computation."""
    from db_utils import get_sync_session
    from sqlalchemy import text
    from engines.matching.matcher import compute_match_score
    from engines.predictor.predictor import predict_interview_probability
    import uuid

    with get_sync_session() as session:
        # Load job
        job_row = session.execute(
            text("""
            SELECT id, title, seniority_level, skills_required, skills_preferred,
                   salary_min, salary_max, remote_policy, posted_at, company_id,
                   company_name
            FROM jobs WHERE id = :job_id
            """),
            {"job_id": job_id},
        ).fetchone()

        if not job_row:
            return

        # Load profile
        profile_row = session.execute(
            text("""
            SELECT skills, experience_years, target_salary_min, target_salary_max,
                   remote_preference, target_titles
            FROM user_profile WHERE id = :user_id
            """),
            {"user_id": SINGLE_USER_ID},
        ).fetchone()

        if not profile_row:
            return

        # Build dicts
        job = {
            "seniority_level": job_row[2],
            "skills_required": job_row[3] or [],
            "salary_min": job_row[6],
            "salary_max": job_row[7],
            "posted_at": job_row[9],
        }
        profile = {
            "skills": profile_row[0] or [],
            "experience_years": profile_row[1] or 0,
            "target_salary_min": profile_row[2],
            "target_salary_max": profile_row[3],
        }

        # Get company hiring score
        company_hiring_score = 0.0
        if job_row[10]:
            company_result = session.execute(
                text("SELECT hiring_score FROM companies WHERE name = :name"),
                {"name": job_row[10]},
            ).fetchone()
            if company_result:
                company_hiring_score = company_result[0] or 0.0

        # Compute match
        match_result = compute_match_score(job, profile, company_hiring_score)

        # Compute interview probability
        from datetime import datetime, timezone
        posted_at = job_row[9]
        posting_age = 0
        if posted_at:
            if hasattr(posted_at, 'replace'):
                if posted_at.tzinfo is None:
                    posted_at = posted_at.replace(tzinfo=timezone.utc)
            posting_age = (datetime.now(timezone.utc) - posted_at).days

        predictor_result = predict_interview_probability(
            match_score=match_result["match_score"],
            skill_coverage_pct=match_result["skill_coverage_pct"],
            experience_years=profile.get("experience_years", 0),
            required_years_min=0,
            posting_age_days=posting_age,
            company_hiring_score=company_hiring_score,
        )

        # Upsert match record
        session.execute(
            text("""
            INSERT INTO job_matches (
                id, job_id, match_score, interview_probability, confidence_score,
                skill_coverage_pct, skill_overlap_score, seniority_fit_score,
                salary_alignment_score, recency_score, company_growth_score,
                risk_factors, strength_factors, scoring_breakdown, computed_at,
                created_at, updated_at
            ) VALUES (
                :id, :job_id, :match_score, :interview_prob, :confidence,
                :skill_cov, :skill_ovlp, :seniority, :salary, :recency, :company,
                :risks::jsonb, :strengths::jsonb, :breakdown::jsonb, NOW(), NOW(), NOW()
            )
            ON CONFLICT (job_id) DO UPDATE SET
                match_score = EXCLUDED.match_score,
                interview_probability = EXCLUDED.interview_probability,
                skill_coverage_pct = EXCLUDED.skill_coverage_pct,
                risk_factors = EXCLUDED.risk_factors,
                strength_factors = EXCLUDED.strength_factors,
                computed_at = NOW(),
                updated_at = NOW()
            """),
            {
                "id": str(uuid.uuid4()),
                "job_id": job_id,
                "match_score": match_result["match_score"],
                "interview_prob": predictor_result["interview_probability"],
                "confidence": predictor_result["confidence_score"],
                "skill_cov": match_result["skill_coverage_pct"],
                "skill_ovlp": match_result["skill_overlap_score"],
                "seniority": match_result["seniority_fit_score"],
                "salary": match_result["salary_alignment_score"],
                "recency": match_result["recency_score"],
                "company": match_result["company_growth_score"],
                "risks": json.dumps(match_result["risk_factors"]),
                "strengths": json.dumps(match_result["strength_factors"]),
                "breakdown": json.dumps(match_result["scoring_breakdown"]),
            },
        )

        # Update job status
        session.execute(
            text("UPDATE jobs SET status = 'matched', updated_at = NOW() WHERE id = :id"),
            {"id": job_id},
        )
        session.commit()

    # High match → create notification + queue auto-apply
    if match_result["match_score"] >= 75:
        _create_high_match_notification(job_id, job_row[1], job_row[10], match_result["match_score"])
        _trigger_auto_apply(job_id, match_result["match_score"])

    logger.debug(f"Match computed for job {job_id}: {match_result['match_score']}")


def _create_high_match_notification(job_id: str, title: str, company: str, score: float):
    """Create notification for high-match jobs."""
    from db_utils import get_sync_session
    from sqlalchemy import text
    import uuid

    try:
        with get_sync_session() as session:
            session.execute(
                text("""
                INSERT INTO notifications (id, type, title, body, channel, is_read, priority, related_job_id, created_at, updated_at)
                VALUES (:id, :type, :title, :body, 'in_app', false, 'high', :job_id, NOW(), NOW())
                """),
                {
                    "id": str(uuid.uuid4()),
                    "type": "high_match_job",
                    "title": f"High Match: {title} at {company}",
                    "body": f"Match score: {score:.0f}%. This job is a strong fit!",
                    "job_id": job_id,
                },
            )
            session.commit()
    except Exception as e:
        logger.error(f"Notification creation failed: {e}")


def _trigger_auto_apply(job_id: str, match_score: float):
    """Queue an auto-apply task for a high-match job."""
    try:
        from workers.celery_app import celery_app
        celery_app.send_task(
            "workers.tasks.apply_tasks.auto_apply_job",
            args=[job_id, match_score],
            queue="default",
        )
        logger.info(f"Auto-apply queued for job {job_id} (score={match_score:.0f}%)")
    except Exception as e:
        logger.error(f"Failed to queue auto-apply for {job_id}: {e}")
