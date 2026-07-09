"""Output formatters for ensemble benchmarking."""

from __future__ import annotations

import csv
import json
import os
from typing import Any


def to_json(results: dict[str, Any], output_path: str) -> None:
    """Export results to JSON."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)


def to_csv(models_summary: list[dict[str, Any]], output_path: str) -> None:
    """Export summary metrics to CSV."""
    if not models_summary:
        return
    keys = list(models_summary[0].keys())
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(models_summary)


def to_latex_table(models_summary: list[dict[str, Any]], output_path: str) -> None:
    """Generate a LaTeX table for the models summary."""
    if not models_summary:
        return

    lines = [
        "\\begin{table}[h]",
        "\\centering",
        "\\begin{tabular}{lccc}",
        "\\hline",
        "\\textbf{Model} & \\textbf{Robustness Score} & ",
        "\\textbf{Latency (s)} & \\textbf{Parameters} \\\\",
        "\\hline"
    ]

    for m in models_summary:
        model_name = str(m.get("model", "Unknown")).replace("_", "\\_")
        rob = m.get("robustness", 0.0)
        lat = m.get("latency", 0.0)
        params = m.get("params", 0)

        # Format params nicely, e.g., 110M
        if params >= 1_000_000:
            params_str = f"{params / 1_000_000:.1f}M"
        elif params >= 1_000:
            params_str = f"{params / 1_000:.1f}K"
        else:
            params_str = str(params)

        lines.append(f"{model_name} & {rob:.4f} & {lat:.4f} & {params_str} \\\\")

    lines.extend([
        "\\hline",
        "\\end{tabular}",
        "\\caption{Ensemble Robustness Benchmarking Results}",
        "\\label{tab:ensemble_results}",
        "\\end{table}"
    ])

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def format_all(
    results: dict[str, Any],
    formats: list[str],
    output_dir: str,
    prefix: str = "ensemble"
) -> None:
    """Export to all requested formats."""
    os.makedirs(output_dir, exist_ok=True)

    if "json" in formats:
        to_json(results, os.path.join(output_dir, f"{prefix}_results.json"))

    models_summary = results.get("models_summary", [])
    if "csv" in formats:
        to_csv(models_summary, os.path.join(output_dir, f"{prefix}_summary.csv"))

    if "latex" in formats:
        to_latex_table(models_summary, os.path.join(output_dir, f"{prefix}_table.tex"))
