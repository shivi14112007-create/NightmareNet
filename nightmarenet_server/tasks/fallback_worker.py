"""In-process fallback worker for the NightmareNet hosted platform.

Activated by ``docker/worker-entrypoint.sh`` when Celery is not installed.
This loop polls the ``runs`` table for ``pending`` rows and executes them
synchronously via :func:`nightmarenet_server.tasks.training.execute_pipeline`.

It is intentionally minimal — production deployments should install Celery
to get retries, distributed scheduling, and observability. The fallback
exists so the worker container always has *some* useful behaviour.
"""

import json
import logging
import os
import signal
import sys
import time
from typing import Any, Dict

from nightmarenet_server.tasks.training import execute_pipeline

logger = logging.getLogger(__name__)

_POLL_INTERVAL = float(os.environ.get("NIGHTMARENET_FALLBACK_POLL_SECONDS", "5.0"))
_running = True


def _stop(signum: int, _frame: Any) -> None:
    """Signal handler — flip the run flag so the loop exits cleanly."""
    global _running
    logger.info("Received signal %s — shutting down fallback worker.", signum)
    _running = False


def _claim_next_run(session_factory: Any) -> Any:
    """Atomically claim the next pending run, or ``None`` if queue is empty."""
    try:
        from nightmarenet_server.models import Experiment, Run
    except ImportError:
        return None

    session = session_factory()
    try:
        run = (
            session.query(Run)
            .filter(Run.status == "pending")
            .order_by(Run.started_at.is_(None).desc(), Run.id)
            .with_for_update(skip_locked=True)
            .first()
        )
        if run is None:
            return None
        run.status = "running"
        experiment = session.get(Experiment, run.experiment_id)
        config: Dict[str, Any] = {}
        if experiment and experiment.config_json:
            try:
                config = json.loads(experiment.config_json)
            except json.JSONDecodeError:
                logger.warning("Run %s has invalid config_json; defaulting.", run.id)
        session.commit()
        return run.id, config
    except Exception:
        logger.exception("Failed to claim next run")
        session.rollback()
        return None
    finally:
        session.close()


def main() -> int:
    logging.basicConfig(
        level=os.environ.get("NIGHTMARENET_LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    try:
        from nightmarenet_server.models.base import (
            DEFAULT_DATABASE_URL,
            get_session_factory,
        )
    except ImportError:
        logger.error("nightmarenet_server.models is required for the fallback worker.")
        return 1

    db_url = os.environ.get("NIGHTMARENET_DATABASE_URL", DEFAULT_DATABASE_URL)
    session_factory = get_session_factory(db_url)

    logger.info(
        "NightmareNet fallback worker started (poll=%.1fs, db=%s).",
        _POLL_INTERVAL,
        db_url,
    )

    while _running:
        claim = _claim_next_run(session_factory)
        if claim is None:
            time.sleep(_POLL_INTERVAL)
            continue
        run_id, config = claim
        try:
            execute_pipeline(run_id, config)
        except Exception:
            logger.exception("Run %s failed in fallback worker", run_id)

    return 0


if __name__ == "__main__":
    sys.exit(main())
