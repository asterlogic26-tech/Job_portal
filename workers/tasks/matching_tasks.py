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
    from workers.db_utils import get_sync_session
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
    from workers.db_utils import get_sync_session
    from sqlalchemy import text
    from engines.matching.matcher import compute_match_score
    from engines.predictor.predictor import predict_interview_probability
    import uuid

    with get_sync_session() as session:
        # Load job
        # Column order: 0=id, 1=title, 2=seniority_level, 3=required_skills, 4=preferred_skills,
        #               5=salary_min, 6=salary_max, 7=remote_policy, 8=posted_at, 9=company_id, 10=company_name
        job_row = session.execute(
            text("""
            SELECT id, title, seniority_level, required_skills, preferred_skills,
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
            "salary_min": job_row[5],
            "salary_max": job_row[6],
            "posted_at": job_row[8],
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

        # Extract matched/missing skills from breakdown
        skill_breakdown = match_result["scoring_breakdown"].get("skill_overlap", {})
        matching_skills = skill_breakdown.get("matched_skills", [])
        missing_skills = skill_breakdown.get("missing_skills", [])

        # Upsert match record (scores stored as 0.0–1.0 to match frontend expectations)
        session.execute(
            text("""
            INSERT INTO job_matches (
                id, job_id, user_id,
                total_score, skill_score, seniority_score, salary_score,
                recency_score, culture_score, company_growth_score,
                interview_probability,
                matching_skills, missing_skills, score_breakdown,
                created_at, updated_at
            ) VALUES (
                :id, :job_id, :user_id,
                :total_score, :skill_score, :seniority_score, :salary_score,
                :recency_score, :culture_score, :company_growth_score,
                :interview_prob,
                :matching_skills::jsonb, :missing_skills::jsonb, :score_breakdown::jsonb,
                NOW(), NOW()
            )
            ON CONFLICT (job_id) DO UPDATE SET
                total_score = EXCLUDED.total_score,
                interview_probability = EXCLUDED.interview_probability,
                skill_score = EXCLUDED.skill_score,
                matching_skills = EXCLUDED.matching_skills,
                missing_skills = EXCLUDED.missing_skills,
                updated_at = NOW()
            """),
            {
                "id": str(uuid.uuid4()),
                "job_id": job_id,
                "user_id": SINGLE_USER_ID,
                "total_score": round(match_result["match_score"] / 100.0, 4),
                "skill_score": match_result["skill_overlap_score"],
                "seniority_score": match_result["seniority_fit_score"],
                "salary_score": match_result["salary_alignment_score"],
                "recency_score": match_result["recency_score"],
                "culture_score": 0.5,
                "company_growth_score": match_result["company_growth_score"],
                "interview_prob": round(predictor_result["interview_probability"] / 100.0, 4),
                "matching_skills": json.dumps(matching_skills),
                "missing_skills": json.dumps(missing_skills),
                "score_breakdown": json.dumps(match_result["scoring_breakdown"]),
            },
        )
        session.commit()

    # High match → create notification + queue auto-apply
    if match_result["match_score"] >= 75:
        _create_high_match_notification(job_id, job_row[1], job_row[10], match_result["match_score"])
        _trigger_auto_apply(job_id, match_result["match_score"])

    logger.debug(f"Match computed for job {job_id}: {match_result['match_score']}")


def _create_high_match_notification(job_id: str, title: str, company: str, score: float):
    """Create notification for high-match jobs."""
    from workers.db_utils import get_sync_session
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
    """Queue an auto-apply task for a high-match job — respects daily limit."""
    try:
        from workers.rate_limiter import check_apply_limit
        allowed, used, limit = check_apply_limit()
        if not allowed:
            logger.warning(
                "Daily apply limit reached (%d/%d) — NOT queuing auto-apply for job %s. "
                "Limit resets at midnight UTC.",
                used, limit, job_id,
            )
            # Still create a notification so the user can apply manually
            _create_limit_reached_notification(job_id, used, limit)
            return

        from workers.celery_app import celery_app
        celery_app.send_task(
            "workers.tasks.apply_tasks.auto_apply_job",
            args=[job_id, match_score],
            queue="default",
        )
        logger.info(
            "Auto-apply queued for job %s (score=%.0f%%, daily=%d/%d)",
            job_id, match_score, used, limit,
        )
    except Exception as e:
        logger.error(f"Failed to queue auto-apply for {job_id}: {e}")


def _create_limit_reached_notification(job_id: str, used: int, limit: int):
    """Notify the user that a high-match job was found but daily limit is reached."""
    from workers.db_utils import get_sync_session
    from sqlalchemy import text
    import uuid

    try:
        with get_sync_session() as session:
            session.execute(
                text("""
                INSERT INTO notifications (
                    id, type, title, body, channel, is_read, priority,
                    related_job_id, created_at, updated_at
                )
                VALUES (
                    :id, 'limit_reached',
                    'Daily Apply Limit Reached',
                    :body,
                    'in_app', false, 'medium', :job_id, NOW(), NOW()
                )
                """),
                {
                    "id": str(uuid.uuid4()),
                    "body": (
                        f"A high-match job was found but the daily limit of {limit} applies "
                        f"has been reached ({used}/{limit}). Check the job manually — "
                        "the limit resets at midnight UTC."
                    ),
                    "job_id": job_id,
                },
            )
            session.commit()
    except Exception as e:
        logger.error("Failed to create limit notification: %s", e)
