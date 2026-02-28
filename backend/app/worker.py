"""
Celery Application Configuration
==================================
Celery worker for PPSC Crack background tasks.

Start worker::

    celery -A app.worker.celery_app worker --loglevel=info --concurrency=2

Start beat (scheduled tasks)::

    celery -A app.worker.celery_app beat --loglevel=info
"""

from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "ppsc_crack",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    # Explicitly register all task modules so they appear in [tasks]
    include=[
        "app.tasks.paper_ingestion",
        "app.tasks.pattern_engine",
        "app.tasks.story_generation",
        "app.tasks.note_processing",
        "app.tasks.prediction_engine_task",
        "app.tasks.current_affairs_pipeline",
    ],
)

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    # Timezone — PKT is UTC+5
    timezone="Asia/Karachi",
    enable_utc=True,
    # Task defaults
    task_soft_time_limit=600,   # 10 min soft limit
    task_time_limit=900,        # 15 min hard limit
    task_acks_late=True,        # ack after completion (safer)
    worker_prefetch_multiplier=1,
    # Result backend
    result_expires=3600,        # results expire after 1 hour
    # Task routes
    task_routes={
        "app.tasks.paper_ingestion.*": {"queue": "ai_pipeline"},
        "app.tasks.pattern_engine.*": {"queue": "ai_pipeline"},
        "app.tasks.story_generation.*": {"queue": "ai_pipeline"},
        "app.tasks.note_processing.*": {"queue": "ai_pipeline"},
        "app.tasks.prediction_engine_task.*": {"queue": "ai_pipeline"},
        "app.tasks.current_affairs_pipeline.*": {"queue": "default"},
    },
    # Default queue
    task_default_queue="default",
    # ── Celery Beat Schedule ─────────────────────────────────
    beat_schedule={
        "daily-current-affairs-6am-pkt": {
            "task": "app.tasks.current_affairs_pipeline.run_daily_current_affairs",
            "schedule": crontab(hour=1, minute=0),  # 01:00 UTC = 06:00 PKT
            "options": {"queue": "default"},
        },
    },
)
