"""Background runner for the NightmareNet pipeline.

Executes a ``Pipeline`` in a background thread with event streaming
for WebSocket / SSE integration.
"""

from __future__ import annotations

import logging
import os
import threading
import uuid
from typing import Any, Callable, Optional

from nightmarenet.pipeline import Pipeline

logger = logging.getLogger(__name__)


class PipelineRunner:
    """Runs a Pipeline in a daemon thread, streaming events via callback.

    Usage::

        runner = PipelineRunner(pipeline)
        runner.start(urls=["https://..."])
        runner.status()  # -> dict
        runner.cancel()

    Args:
        pipeline: Configured Pipeline instance.
        on_event: Optional event callback ``fn(event_dict)`` for WebSocket.
    """

    def __init__(
        self,
        pipeline: Pipeline,
        on_event: Optional[Callable[[dict], None]] = None,
    ) -> None:
        self.id = str(uuid.uuid4())
        self.pipeline = pipeline
        self.pipeline.run_id = self.id
        self.on_event = on_event
        self._thread: Optional[threading.Thread] = None
        self._cancel_event = threading.Event()

        # Wire event callback into the pipeline
        if on_event:
            self.pipeline.on_event = on_event

    def start(self, **ingest_kwargs: Any) -> str:
        """Launch the pipeline in a background thread.

        Accepts the same keyword arguments as ``Pipeline.ingest()``.

        Returns:
            The run ID.
        """
        if self._thread is not None and self._thread.is_alive():
            raise RuntimeError("Pipeline is already running.")

        self._cancel_event.clear()

        def _run() -> None:
            try:
                self.pipeline.ingest(**ingest_kwargs)
                if self._cancel_event.is_set():
                    return
                self.pipeline.prepare()
                if self._cancel_event.is_set():
                    return
                self.pipeline.train()
                if self._cancel_event.is_set():
                    return
                self.pipeline.evaluate()
            except Exception:
                logger.exception("Pipeline run %s failed", self.id)

        self._thread = threading.Thread(target=_run, daemon=True, name=f"pipeline-{self.id}")
        self._thread.start()
        logger.info("Pipeline %s started.", self.id)
        return self.id

    def cancel(self) -> None:
        """Request cancellation of a running pipeline."""
        self._cancel_event.set()
        self.pipeline.cancel()
        logger.info("Pipeline %s cancellation requested.", self.id)

    def status(self) -> dict:
        """Return the current pipeline metrics as a dict."""
        data = self.pipeline.metrics.to_dict()
        data["run_id"] = self.id
        data["is_running"] = self._thread is not None and self._thread.is_alive()
        return data

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()


# ------------------------------------------------------------------
# Global runner registry (for multi-pipeline API support)
# ------------------------------------------------------------------

_runners: dict[str, PipelineRunner] = {}
_MAX_RUNNERS = int(os.environ.get("NIGHTMARENET_MAX_PIPELINE_RUNNERS", "64"))


def register_runner(runner: PipelineRunner) -> str:
    """Register a runner and return its ID.

    Evicts completed (not running) entries when the registry would exceed
    :envvar:`NIGHTMARENET_MAX_PIPELINE_RUNNERS` (default 64). If the cap is
    reached and every registered run is still active, raises ``RuntimeError``.
    """
    while len(_runners) >= _MAX_RUNNERS:
        for rid, r in list(_runners.items()):
            if not r.is_running:
                del _runners[rid]
                logger.info("Evicted completed pipeline runner %s (registry cap).", rid)
                break
        else:
            msg = (
                f"Pipeline runner registry at capacity ({_MAX_RUNNERS}) and all "
                "registered runs are still active"
            )
            raise RuntimeError(msg) from None
    _runners[runner.id] = runner
    return runner.id


def get_runner(run_id: str) -> Optional[PipelineRunner]:
    """Retrieve a runner by ID."""
    return _runners.get(run_id)


def list_runners() -> list[dict]:
    """Return status of all registered runners."""
    return [r.status() for r in _runners.values()]
