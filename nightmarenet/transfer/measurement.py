"""Measurement metrics for robustness transfer learning.

Calculates transfer ratios and related efficiency metrics.
"""

from __future__ import annotations


def calculate_transfer_ratio(transferred_robustness: float, baseline_robustness: float) -> float:
    """Calculate the robustness transfer ratio.

    The transfer ratio indicates how much of the full-cycle robustness
    was successfully transferred to the downstream task via fine-tuning alone.

    Args:
        transferred_robustness: Robustness score of the transfer-fine-tuned model.
        baseline_robustness: Robustness score of the full-cycle nightmare model on the target task.

    Returns:
        Transfer ratio (typically 0.0 to 1.0+).
    """
    if baseline_robustness <= 0.0:
        return 0.0
    return transferred_robustness / baseline_robustness


def evaluate_transfer_efficiency(transfer_ratio: float) -> str:
    """Evaluate the efficiency of the transfer based on the ratio."""
    if transfer_ratio > 0.7:
        return "Highly Efficient (Saves 70%+ of compute)"
    elif transfer_ratio > 0.3:
        return "Moderately Efficient (Partial transfer)"
    else:
        return "Weak (Full cycle still needed)"
