"""Reporting for robustness transfer learning.

Generates markdown reports of transfer efficiency and compute savings.
"""

from __future__ import annotations

from nightmarenet.transfer.measurement import calculate_transfer_ratio, evaluate_transfer_efficiency


def generate_transfer_report(
    transferred_robustness: float,
    baseline_robustness: float,
    clean_accuracy_transferred: float,
    clean_accuracy_baseline: float,
    transferred_time_s: float,
    baseline_time_s: float,
) -> str:
    """Generate a markdown report comparing transfer learning to a full cycle.

    Args:
        transferred_robustness: Robustness score of the transferred model.
        baseline_robustness: Robustness score of the full-cycle baseline model.
        clean_accuracy_transferred: Clean accuracy of the transferred model.
        clean_accuracy_baseline: Clean accuracy of the full-cycle baseline model.
        transferred_time_s: Training time for the transfer process (seconds).
        baseline_time_s: Training time for the full-cycle baseline (seconds).

    Returns:
        Formatted markdown report string.
    """
    transfer_ratio = calculate_transfer_ratio(transferred_robustness, baseline_robustness)
    efficiency = evaluate_transfer_efficiency(transfer_ratio)

    compute_savings = 0.0
    if baseline_time_s > 0:
        compute_savings = max(0.0, ((baseline_time_s - transferred_time_s) / baseline_time_s) * 100)

    report = [
        "# Robustness Transfer Report",
        "",
        "## Summary",
        f"**Transfer Efficiency**: {efficiency}",
        f"**Transfer Ratio**: {transfer_ratio:.4f}",
        f"**Compute Savings**: {compute_savings:.1f}% "
        f"({transferred_time_s:.1f}s vs {baseline_time_s:.1f}s)",
        "",
        "## Detailed Metrics",
        "| Metric | Transferred Model | Full-Cycle Baseline |",
        "|--------|------------------:|--------------------:|",
        f"| Robustness Score | {transferred_robustness:.4f} | {baseline_robustness:.4f} |",
        f"| Clean Accuracy   | {clean_accuracy_transferred:.4f} | {clean_accuracy_baseline:.4f} |",
        f"| Training Time    | {transferred_time_s:.1f}s | {baseline_time_s:.1f}s |",
        "",
        "## Analysis",
    ]

    if transfer_ratio > 0.6:
        report.append(
            "The transfer ratio exceeds 0.6, validating NightmareNet's core claim: "
            "the 4-phase cycle learns genuinely robust representations that can be "
            "successfully transferred to downstream tasks without running the full "
            "nightmare cycle again."
        )
    else:
        report.append(
            "The transfer ratio is below 0.6. The representations did not transfer "
            "efficiently to the downstream task, suggesting that a full nightmare "
            "cycle may be required to achieve target robustness levels."
        )

    return "\n".join(report)
