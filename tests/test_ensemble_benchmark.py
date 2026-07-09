"""Tests for ensemble benchmarking functionality."""

import os
import tempfile
from unittest import mock

import yaml

from nightmarenet.evaluation.degradation_curves import calculate_degradation_curves
from nightmarenet.evaluation.ensemble_benchmark import EnsembleOrchestrator
from nightmarenet.evaluation.format_results import to_latex_table
from nightmarenet.evaluation.pareto_analysis import get_pareto_frontier


def test_pareto_frontier_correctness():
    """Test that the Pareto frontier correctly identifies non-dominated models."""
    results = [
        {"model": "A", "robustness": 0.9, "latency": 10.0, "params": 100},  # dominated by B
        {"model": "B", "robustness": 0.95, "latency": 5.0, "params": 50},   # pareto optimal
        {"model": "C", "robustness": 0.8, "latency": 2.0, "params": 20},    # pareto optimal
        {"model": "D", "robustness": 0.7, "latency": 8.0, "params": 80},    # dominated by C
    ]

    pareto_front = get_pareto_frontier(results)
    assert len(pareto_front) == 2
    models_on_front = {m["model"] for m in pareto_front}
    assert "B" in models_on_front
    assert "C" in models_on_front
    assert "A" not in models_on_front
    assert "D" not in models_on_front


def test_degradation_curve_aggregation():
    """Test aggregation of robustness scores into degradation curves."""
    raw_results = {
        "model_A": {
            "dream": {
                "strengths": [0.1, 0.5, 0.9],
                "accuracies": [10.0, 50.0, 100.0]
            }
        },
        "model_B": {
            "dream": {
                "strengths": [0.1, 0.5],
                "accuracies": [5.0, 20.0]
            }
        }
    }

    curves = calculate_degradation_curves(raw_results)

    assert "model_A" in curves
    assert len(curves["model_A"]) == 3
    assert curves["model_A"][0]["strength"] == 0.1
    assert curves["model_A"][0]["robustness"] == 10.0

    assert "model_B" in curves
    assert len(curves["model_B"]) == 2
    assert curves["model_B"][1]["strength"] == 0.5
    assert curves["model_B"][1]["robustness"] == 20.0


def test_latex_table_generation():
    """Test output formatting for LaTeX table generation."""
    models_summary = [
        {"model": "test-model-1", "robustness": 0.85, "latency": 1.2, "params": 110_000_000},
        {"model": "test_model_2", "robustness": 0.92, "latency": 2.5, "params": 340_000_000},
    ]

    with tempfile.TemporaryDirectory() as temp_dir:
        latex_path = os.path.join(temp_dir, "table.tex")
        to_latex_table(models_summary, latex_path)

        with open(latex_path, encoding="utf-8") as f:
            content = f.read()

        assert "\\begin{tabular}" in content
        assert "test-model-1" in content
        assert "110.0M" in content
        # Note: test_model_2 should have underscores escaped
        assert "test\\_model\\_2" in content
        assert "340.0M" in content


@mock.patch("nightmarenet.evaluation.ensemble_benchmark.ProcessPoolExecutor")
def test_ensemble_orchestrator_logic(mock_executor_class):
    """Test EnsembleOrchestrator config parsing and orchestration logic."""
    mock_future = mock.MagicMock()
    mock_future.result.return_value = {
        "model": "dummy",
        "robustness": 0.99,
        "latency": 1.5,
        "params": 1000,
        "results_by_distortion": {
            "dream": {
                "strengths": [0.1, 0.5],
                "accuracies": [5.0, 10.0]
            }
        }
    }

    mock_executor = mock.MagicMock()
    mock_executor.submit.return_value = mock_future
    mock_executor.__enter__.return_value = mock_executor
    mock_executor_class.return_value = mock_executor

    config = {
        "models": ["dummy"],
        "dataset": {"name": "test", "split": "val"},
        "distortions": [{"type": "dream", "strengths": [0.1, 0.5]}]
    }

    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        yaml.dump(config, f)
        temp_config = f.name

    try:
        orchestrator = EnsembleOrchestrator(temp_config)
        assert orchestrator.config.models == ["dummy"]

        results = orchestrator.run()
        assert "models_summary" in results
        assert len(results["models_summary"]) == 1
        assert results["models_summary"][0]["robustness"] == 0.99

        assert "raw_results" in results
        assert "dummy" in results["raw_results"]
    finally:
        os.remove(temp_config)


@mock.patch("nightmarenet.evaluation.ensemble_benchmark.ProcessPoolExecutor")
def test_ensemble_orchestrator_timeout(mock_executor_class):
    """Test EnsembleOrchestrator timeout behavior."""
    from concurrent.futures import TimeoutError

    # Mock future that raises TimeoutError
    mock_future = mock.MagicMock()
    mock_future.result.side_effect = TimeoutError("Timed out")

    mock_executor = mock.MagicMock()
    mock_executor.submit.return_value = mock_future
    mock_executor.__enter__.return_value = mock_executor

    mock_executor_class.return_value = mock_executor

    config = {
        "models": ["slow_model"],
        "dataset": {"name": "test"}
    }

    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        yaml.dump(config, f)
        temp_config = f.name

    try:
        orchestrator = EnsembleOrchestrator(temp_config)
        results = orchestrator.run(timeout_seconds=1)

        # It should handle the timeout gracefully without crashing,
        # but the slow_model won't be in the results.
        assert len(results["models_summary"]) == 0
        assert "slow_model" not in results["raw_results"]
    finally:
        os.remove(temp_config)
