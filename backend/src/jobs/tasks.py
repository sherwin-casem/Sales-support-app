from src.jobs.celery_app import celery_app


@celery_app.task(name="health.ping")
def health_ping() -> str:
    """No-op task used to verify the Celery worker is connected."""
    return "pong"
