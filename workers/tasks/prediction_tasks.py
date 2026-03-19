import logging

from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="workers.tasks.prediction_tasks.predict_success")
def predict_success(job_id: str):
    """Trigger match re-computation which includes interview probability prediction."""
    from workers.tasks.matching_tasks import compute_job_match
    compute_job_match.delay(job_id)
    return {"message": f"Prediction queued for job {job_id}"}
