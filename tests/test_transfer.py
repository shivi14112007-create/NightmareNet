"""Tests for robustness transfer learning modules."""

from __future__ import annotations

from nightmarenet.transfer.measurement import calculate_transfer_ratio, evaluate_transfer_efficiency
from nightmarenet.transfer.registry import FoundationRegistry
from nightmarenet.transfer.report import generate_transfer_report


def test_calculate_transfer_ratio():
    assert calculate_transfer_ratio(0.8, 1.0) == 0.8
    assert calculate_transfer_ratio(0.5, 0.0) == 0.0  # Safe division by zero
    assert calculate_transfer_ratio(0.65, 0.8) == 0.8125


def test_evaluate_transfer_efficiency():
    assert evaluate_transfer_efficiency(0.8) == "Highly Efficient (Saves 70%+ of compute)"
    assert evaluate_transfer_efficiency(0.5) == "Moderately Efficient (Partial transfer)"
    assert evaluate_transfer_efficiency(0.2) == "Weak (Full cycle still needed)"


def test_generate_transfer_report():
    report = generate_transfer_report(0.7, 0.9, 0.85, 0.88, 120.0, 600.0)
    assert "Highly Efficient" in report
    assert "0.7778" in report  # ratio = 0.7/0.9
    assert "80.0%" in report  # savings = (600-120)/600
    assert "ratio exceeds 0.6" in report


def test_registry_initialization(tmp_path):
    registry = FoundationRegistry(cache_dir=tmp_path)
    assert registry.cache_dir == tmp_path
    assert tmp_path.exists()


# Integration test with HuggingFace models would be here, but we avoid downloading big models in CI.
# We can mock the AutoModel / AutoTokenizer for test_registry_registration or just skip it.
