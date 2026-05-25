"""Celery application factory for background training jobs.

The Celery worker is an optional component of the hosted platform. To avoid
breaking the open-source ``nightmarenet`` install, importing this module
without Celery present yields a ``celery_app`` of ``None``; the FastAPI
server can detect this and fall back to in-process execution via the
existing :class:`nightmarenet.pipeline_runner.PipelineRunner`.

Environment variables consulted:

* ``NIGHTMARENET_REDIS_URL`` — broker + result backend (default
  ``redis://redis:6379/0``).
* ``NIGHTMARENET_CELERY_QUEUE`` — name of the default queue.
* ``NIGHTMARENET_CELERY_INCLUDE`` — comma-separated additional task modules
  to autodiscover.
"""

import logging
import os
from typing import Any, List, Optional

logger = logging.getLogger(__name__)

try:
    from celery import Celery
except ImportError:
    Celery = None  # type: ignore[assignment,misc]


DEFAULT_REDIS_URL = "redis://redis:6379/0"
DEFAULT_QUEUE = "nightmarenet"


def _default_modules() -> List[str]:
    """Modules autodiscovered for Celery tasks."""
    base = ["nightmarenet_server.tasks.training"]
    extra = os.environ.get("NIGHTMARENET_CELERY_INCLUDE", "")
    base.extend(m.strip() for m in extra.split(",") if m.strip())
    return base


def build_celery_app() -> Optional[Any]:
    """Construct and return a configured :class:`Celery` instance.

    Returns ``None`` when Celery is not installed so callers can short-circuit
    cleanly and fall back to synchronous or threaded execution.
    """
    if Celery is None:
        logger.info("Celery not installed — background worker is disabled.")
        return None

    broker_url = os.environ.get("NIGHTMARENET_REDIS_URL", DEFAULT_REDIS_URL)
    result_backend = os.environ.get(
        "NIGHTMARENET_CELERY_RESULT_BACKEND",
        broker_url,
    )
    queue = os.environ.get("NIGHTMARENET_CELERY_QUEUE", DEFAULT_QUEUE)

    app = Celery(
        "nightmarenet",
        broker=broker_url,
        backend=result_backend,
        include=_default_modules(),
    )
    app.conf.update(
        task_default_queue=queue,
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        worker_prefetch_multiplier=1,
        broker_connection_retry_on_startup=True,
        result_expires=60 * 60 * 24 * 7,
    )
    app.autodiscover_tasks(packages=_default_modules(), force=True)
    return app


celery_app: Optional[Any] = build_celery_app()
