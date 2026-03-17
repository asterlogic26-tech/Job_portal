from celery.schedules import crontab

# Task names must match the `name=` argument in each @celery_app.task decorator
# and the module paths in celery_app.include
BEAT_SCHEDULE = {
    # Job discovery every 4 hours
    "job-discovery-run": {
        "task": "workers.tasks.discovery_tasks.run_discovery",
        "schedule": crontab(minute=0, hour="*/4"),
        "options": {"queue": "discovery"},
    },
    # Match refresh every 12 hours
    "match-refresh": {
        "task": "workers.tasks.matching_tasks.compute_all_matches",
        "schedule": crontab(minute=30, hour="*/12"),
        "options": {"queue": "matching"},
    },
    # Company radar scan daily at midnight
    "company-radar-scan": {
        "task": "workers.tasks.company_radar_tasks.scan_company_signals",
        "schedule": crontab(minute=0, hour=0),
        "options": {"queue": "radar"},
    },
    # Daily digest at 8 AM UTC
    "daily-digest": {
        "task": "workers.tasks.notification_tasks.send_digest",
        "schedule": crontab(minute=0, hour=8),
        "options": {"queue": "notifications"},
    },
    # Follow-up reminders at 9 AM UTC
    "followup-reminders": {
        "task": "workers.tasks.notification_tasks.send_followup_reminders",
        "schedule": crontab(minute=0, hour=9),
        "options": {"queue": "notifications"},
    },
    # Profile health check daily at 7 AM UTC
    "profile-health-check": {
        "task": "workers.tasks.profile_tasks.check_profile_health",
        "schedule": crontab(minute=0, hour=7),
        "options": {"queue": "default"},
    },
    # Cleanup stale jobs daily at 2 AM UTC
    "cleanup-stale-jobs": {
        "task": "workers.tasks.cleanup_tasks.remove_stale_jobs",
        "schedule": crontab(minute=0, hour=2),
        "options": {"queue": "default"},
    },
    # Content suggestion drafts daily at 7:30 AM UTC
    "content-suggestions": {
        "task": "workers.tasks.content_tasks.generate_daily_content_suggestions",
        "schedule": crontab(minute=30, hour=7),
        "options": {"queue": "content"},
    },
}
