"""Tests for the Pipeline orchestrator and PipelineRunner."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from nightmarenet.pipeline import Pipeline, PipelineStatus


@pytest.fixture
def minimal_config():
    """Minimal config for pipeline tests."""
    return {
        "model": {
            "name": "gpt2",
            "type": "causal_lm",
            "max_length": 32,
            "device": "cpu",
        },
        "dataset": {
            "text_column": "text",
            "max_samples": 20,
        },
        "training": {
            "wake_epochs": 1,
            "dream_epochs": 1,
            "nightmare_epochs": 1,
            "num_cycles": 1,
            "batch_size": 2,
            "learning_rate": 5e-5,
            "weight_decay": 0.01,
            "max_grad_norm": 1.0,
            "gradient_accumulation_steps": 1,
            "save_every_phase": False,
            "checkpoint_dir": "checkpoints",
            "log_dir": "logs",
        },
        "distortion": {
            "dream_strength": 0.25,
            "nightmare_strength": 0.8,
        },
        "compression": {
            "pruning_ratio": 0.1,
            "pruning_method": "magnitude",
        },
        "evaluation": {
            "metrics": ["recall"],
        },
        "tracking": {"backend": "none"},
        "seed": 42,
    }


class TestPipelineStatus:
    """Tests for PipelineStatus enum."""

    def test_status_values(self):
        assert PipelineStatus.IDLE.value == "idle"
        assert PipelineStatus.TRAINING.value == "training"
        assert PipelineStatus.COMPLETE.value == "complete"
        assert PipelineStatus.FAILED.value == "failed"
        assert PipelineStatus.CANCELLED.value == "cancelled"


class TestPipelineInit:
    """Tests for Pipeline initialization."""

    def test_init(self, minimal_config):
        pipe = Pipeline(minimal_config)
        assert pipe.metrics.status == PipelineStatus.IDLE
        assert pipe._dataset is None
        assert pipe._trainer is None

    def test_init_with_callback(self, minimal_config):
        events = []
        pipe = Pipeline(minimal_config, on_event=lambda e: events.append(e))
        assert pipe.on_event is not None


class TestPipelineIngest:
    """Tests for the ingest stage."""

    def test_ingest_text_content(self, minimal_config):
        """Ingesting raw text should produce a Dataset."""
        pipe = Pipeline(minimal_config)
        content = "\n\n".join(
            [
                f"Paragraph {i}: This sentence is long enough to be valid training data."
                for i in range(30)
            ]
        )
        pipe.ingest(text_content=content)
        assert pipe._dataset is not None
        assert len(pipe._dataset) >= 10
        assert pipe.metrics.status == PipelineStatus.INGESTING

    def test_ingest_no_source_raises(self, minimal_config):
        """Calling ingest with no source should raise."""
        pipe = Pipeline(minimal_config)
        with pytest.raises(ValueError, match="Provide one of"):
            pipe.ingest()

    def test_ingest_insufficient_data(self, minimal_config):
        """Ingesting too little data should fail."""
        pipe = Pipeline(minimal_config)
        content = "Short text.\n\nAnother short one."
        with pytest.raises(ValueError, match="usable samples"):
            pipe.ingest(text_content=content)


class TestPipelineStageOrder:
    """Tests that stages must be called in order."""

    def test_prepare_before_ingest_raises(self, minimal_config):
        pipe = Pipeline(minimal_config)
        with pytest.raises(RuntimeError, match="Call .ingest"):
            pipe.prepare()

    def test_train_before_prepare_raises(self, minimal_config):
        pipe = Pipeline(minimal_config)
        with pytest.raises(RuntimeError, match="Call .prepare"):
            pipe.train()

    def test_evaluate_before_train_raises(self, minimal_config):
        pipe = Pipeline(minimal_config)
        with pytest.raises(RuntimeError, match="Call .train"):
            pipe.evaluate()


class TestPipelineCancel:
    """Tests for pipeline cancellation."""

    def test_cancel_sets_status(self, minimal_config):
        pipe = Pipeline(minimal_config)
        pipe.cancel()
        assert pipe.metrics.status == PipelineStatus.CANCELLED
        assert pipe._cancelled is True


class TestPipelineMetrics:
    """Tests for PipelineMetrics serialization."""

    def test_to_dict(self, minimal_config):
        pipe = Pipeline(minimal_config)
        d = pipe.metrics.to_dict()
        assert d["status"] == "idle"
        assert d["current_cycle"] == 0
        assert d["has_report"] is False
        assert isinstance(d["history"], list)


class TestPipelineEventCallback:
    """Tests that events are emitted at each stage."""

    def test_events_on_ingest(self, minimal_config):
        events = []
        pipe = Pipeline(minimal_config, on_event=lambda e: events.append(e))
        content = "\n\n".join(
            [
                f"Paragraph {i}: Long enough text for ingestion testing purposes here."
                for i in range(30)
            ]
        )
        pipe.ingest(text_content=content)
        assert len(events) >= 1
        assert events[0]["status"] == "ingesting"

    def test_event_callback_exception_doesnt_crash(self, minimal_config):
        """If callback raises, pipeline should not crash."""

        def bad_callback(e):
            raise RuntimeError("callback error")

        pipe = Pipeline(minimal_config, on_event=bad_callback)
        content = "\n\n".join(
            [f"Paragraph {i}: This is text number {i} with enough characters." for i in range(30)]
        )
        # Should not raise
        pipe.ingest(text_content=content)


class TestPipelineRunner:
    """Tests for the PipelineRunner class."""

    def test_runner_status(self, minimal_config):
        from nightmarenet.pipeline_runner import PipelineRunner

        pipe = Pipeline(minimal_config)
        runner = PipelineRunner(pipe)
        status = runner.status()
        assert "run_id" in status
        assert status["is_running"] is False

    def test_runner_cancel(self, minimal_config):
        from nightmarenet.pipeline_runner import PipelineRunner

        pipe = Pipeline(minimal_config)
        runner = PipelineRunner(pipe)
        runner.cancel()
        assert pipe._cancelled is True

    def test_runner_registry(self, minimal_config):
        from nightmarenet.pipeline_runner import (
            PipelineRunner,
            get_runner,
            register_runner,
        )

        pipe = Pipeline(minimal_config)
        runner = PipelineRunner(pipe)
        rid = register_runner(runner)
        assert get_runner(rid) is runner
        assert get_runner("nonexistent") is None


class TestAdaptiveTermination:
    """Tests adaptive cycle termination."""

    def test_auto_terminate_disabled(self, minimal_config):
        """Adaptive termination should do nothing when disabled."""

        pipe = Pipeline(minimal_config)

        pipe._trainer = MagicMock()
        pipe._dataset = MagicMock()

        minimal_config["training"]["auto_terminate"] = False

        event = {"cycle": 0}
        with patch("nightmarenet.pipeline.quick_robustness_score") as mock_score:
            pipe._handle_cycle_end(event)

            mock_score.assert_not_called()
            pipe._trainer.request_stop.assert_not_called()

    def test_convergence_patience_respected(self, minimal_config):
        """Training should stop only after patience consecutive small deltas."""

        minimal_config["training"]["auto_terminate"] = True
        minimal_config["training"]["convergence_threshold"] = 0.01
        minimal_config["training"]["convergence_patience"] = 2

        pipe = Pipeline(minimal_config)
        pipe._trainer = MagicMock()
        pipe._trainer.model = MagicMock()
        pipe._trainer.tokenizer = MagicMock()
        pipe._trainer.device = "cpu"
        pipe._dataset = MagicMock()

        with patch("nightmarenet.pipeline.quick_robustness_score") as mock_score:
            mock_score.side_effect = [
                0.80,
                0.805,
                0.809,
            ]

            pipe._handle_cycle_end({"cycle": 0})
            pipe._trainer.request_stop.assert_not_called()

            pipe._handle_cycle_end({"cycle": 1})
            pipe._trainer.request_stop.assert_not_called()

            pipe._handle_cycle_end({"cycle": 2})
            pipe._trainer.request_stop.assert_called_once()

    def test_hard_cap_configuration_preserved(self, minimal_config):
        """num_cycles remains configured when adaptive termination is disabled."""

        pipe = Pipeline(minimal_config)

        assert pipe.config["training"]["num_cycles"] == 1


class TestPerCycleMetrics:
    """Tests per-cycle evaluation via evaluate_cycle()."""

    def test_per_cycle_metrics_appended(self, minimal_config):
        pipe = Pipeline(minimal_config)
        pipe._trainer = MagicMock()
        pipe._trainer.model = MagicMock()
        pipe._trainer.tokenizer = MagicMock()
        pipe._trainer.device = "cpu"
        pipe._dataset = MagicMock()
        pipe._train_dl = MagicMock()

        minimal_config["training"]["auto_terminate"] = False

        with patch("nightmarenet.pipeline.evaluate_cycle") as mock_eval_cycle:
            mock_eval_cycle.return_value = {
                "accuracy": 0.85,
                "robustness": {0.3: 0.8, 0.5: 0.7, 0.7: 0.6},
            }
            pipe._handle_cycle_end({"cycle": 0})

            mock_eval_cycle.assert_called_once()
            assert len(pipe.metrics.per_cycle_metrics) == 1
            assert pipe.metrics.per_cycle_metrics[0]["cycle"] == 0
            assert pipe.metrics.per_cycle_metrics[0]["accuracy"] == 0.85

    def test_per_cycle_metrics_skipped_without_train_dl(self, minimal_config):
        """No train_dl means the lightweight probe is skipped, not crashed."""
        pipe = Pipeline(minimal_config)
        pipe._trainer = MagicMock()
        pipe._dataset = MagicMock()
        # pipe._train_dl left as None

        minimal_config["training"]["auto_terminate"] = False

        pipe._handle_cycle_end({"cycle": 0})
        assert pipe.metrics.per_cycle_metrics == []
