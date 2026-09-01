import os
import sys

# Ensure backend app package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from celery import Celery
from app.config import settings

celery_app = Celery(
    "email_automation",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "worker.imap_worker",
        "worker.cta_worker",
        "worker.reply_worker",
        "worker.workflow_worker"
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "worker.imap_worker.*": {"queue": "imap"},
        "worker.workflow_worker.*": {"queue": "email_processing"},
        "worker.cta_worker.*": {"queue": "cta"},
        "worker.reply_worker.*": {"queue": "reply"},
    },
    worker_concurrency=settings.MAX_CONCURRENT_WORKERS
)
