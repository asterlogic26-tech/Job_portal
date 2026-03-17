"""
Celery application entry point.

Run from project root with PYTHONPATH=/app:
  celery -A workers.celery_app worker --loglevel=info
  celery -A workers.celery_app beat   --loglevel=info
  celery -A workers.celery_app flower --port=5555
"""
import os

from celery import Celery

from workers.beat_schedule import BEAT_SCHEDULE

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

celery_app = Celery(
    "personal_job_agent",
    broker=REDIS_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "workers.tasks.discovery_tasks",
        "workers.tasks.normalization_tasks",
        "workers.tasks.matching_tasks",
        "workers.tasks.content_tasks",
        "workers.tasks.company_radar_tasks",
        "workers.tasks.notification_tasks",
        "workers.tasks.profile_tasks",
        "workers.tasks.cleanup_tasks",
        "workers.tasks.prediction_tasks",
        "workers.tasks.agent_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=300,
    task_time_limit=600,
    beat_schedule=BEAT_SCHEDULE,
    beat_scheduler="celery.beat:PersistentScheduler",
    beat_schedule_filename=os.environ.get("BEAT_SCHEDULE_FILE", "/tmp/celerybeat-schedule"),
    task_default_retry_delay=60,
    task_max_retries=3,
    result_expires=3600,
)

if __name__ == "__main__":
    celery_app.start()
