"""Celery application and task definitions."""
from __future__ import annotations

from celery import Celery

from app.config import settings

celery_app = Celery(
    "noesis",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "cleanup-expired-tokens": {
            "task": "app.workers.tasks.cleanup_expired_tokens",
            "schedule": 3600.0,  # hourly
        },
        "rebuild-bm25-index": {
            "task": "app.workers.tasks.rebuild_bm25_index",
            "schedule": 1800.0,  # every 30 min
        },
    },
)
