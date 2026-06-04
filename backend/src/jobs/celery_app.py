from celery import Celery

from src.common.config import get_settings

settings = get_settings()

celery_app = Celery(
    "sales_intelligence",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["src.jobs.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    beat_schedule={
        "refresh-stale-leads-daily": {
            "task": "discovery.refresh_stale_leads",
            "schedule": 86400.0,
        },
    },
)
