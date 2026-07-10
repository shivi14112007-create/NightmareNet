"""Tests for training callback event system."""

from nightmarenet.training.callbacks import CallbackManager, EventType, TrainingEvent


def test_event_progress_pct() -> None:
    event = TrainingEvent(
        event_type=EventType.STEP,
        phase="wake",
        step=25,
        total_steps=100,
    )
    assert event.progress_pct == 25.0


def test_callback_manager_emits_to_handlers() -> None:
    mgr = CallbackManager()
    received = []

    def handler(event: TrainingEvent) -> None:
        received.append(event.phase)

    mgr.on(EventType.STEP, handler)
    mgr.emit(
        TrainingEvent(event_type=EventType.STEP, phase="dream", step=1, total_steps=10)
    )
    assert received == ["dream"]


def test_callback_manager_global_handler() -> None:
    mgr = CallbackManager()
    phases = []
    mgr.on_all(lambda e: phases.append(e.phase))
    mgr.emit(TrainingEvent(event_type=EventType.PHASE_START, phase="nightmare"))
    assert phases == ["nightmare"]


def test_event_to_dict() -> None:
    event = TrainingEvent(
        event_type=EventType.METRIC,
        phase="compress",
        metrics={"loss": 0.5},
    )
    d = event.to_dict()
    assert d["event_type"] == "metric"
    assert d["phase"] == "compress"
    assert d["metrics"]["loss"] == 0.5

def test_callback_manager_phase_start_event() -> None:
    mgr = CallbackManager()
    received = []

    def handler(event: TrainingEvent) -> None:
        received.append(event.event_type)

    mgr.on(EventType.PHASE_START, handler)

    mgr.emit(
        TrainingEvent(
            event_type=EventType.PHASE_START,
            phase="wake",
        )
    )

    assert received == [EventType.PHASE_START]


def test_callback_manager_phase_end_event() -> None:
    mgr = CallbackManager()
    received = []

    def handler(event: TrainingEvent) -> None:
        received.append(event.event_type)

    mgr.on(EventType.PHASE_END, handler)

    mgr.emit(
        TrainingEvent(
            event_type=EventType.PHASE_END,
            phase="wake",
        )
    )

    assert received == [EventType.PHASE_END]