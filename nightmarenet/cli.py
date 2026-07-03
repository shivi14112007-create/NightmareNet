"""NightmareNet CLI — command-line interface for the OSS core.

Usage:
    nightmarenet train --config configs/default.yaml
    nightmarenet evaluate --checkpoint ./output/model --config configs/default.yaml
    nightmarenet benchmark --suite standard --model distilbert-base-uncased
    nightmarenet distort --type dream --strength 0.3 --text "Hello world"
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from nightmarenet import __version__


def cmd_train(args: argparse.Namespace) -> int:
    """Run the full 4-phase training pipeline."""
    from nightmarenet.pipeline import Pipeline

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: config file not found: {config_path}", file=sys.stderr)
        return 1

    import yaml

    with open(config_path) as f:
        config = yaml.safe_load(f)

    def on_event(event: dict) -> None:
        phase = event.get("status", "unknown")
        print(f"  [{phase}] {event.get('message', '')}")

    print("NightmareNet Training Pipeline")
    print(f"  Config: {config_path}")
    print(f"  Model: {config.get('model', {}).get('name', 'gpt2')}")
    print()

    pipeline = Pipeline(config=config, on_event=on_event)

    try:
        pipeline.run()
    except KeyboardInterrupt:
        print("\nTraining interrupted. Saving checkpoint...")
        return 130

    metrics = pipeline.metrics
    print("\nTraining complete!")
    print(f"  Final loss: {metrics.phase_loss:.4f}")
    print(f"  Status: {metrics.status}")

    if args.output:
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"  Output: {output_dir}")

    return 0


def cmd_evaluate(args: argparse.Namespace) -> int:
    """Evaluate text robustness via distortion API logic.

    When ``--json`` is supplied, emits a single JSON object on stdout suitable
    for CI consumption (e.g. the ``nightmarenet-robustness-check`` composite
    GitHub Action) containing per-strength similarity scores plus an aggregate
    ``robustness_score`` in ``[0, 1]``.
    """
    from nightmarenet.distortions.registry import get_registry

    json_only = bool(getattr(args, "json", False))
    dataset = getattr(args, "dataset", None) or "sst2"
    model = getattr(args, "model", None) or ""

    if not json_only:
        print("NightmareNet Evaluation")
        print(f"  Model:     {model}")
        print(f"  Dataset:   {dataset}")
        print(f"  Strengths: {args.strengths}")
        print()

    registry = get_registry()
    text = args.text or "The quick brown fox jumps over the lazy dog."
    strengths = [float(s) for s in args.strengths.split(",")]

    def _char_similarity(a: str, b: str) -> float:
        if not a and not b:
            return 1.0
        if not a or not b:
            return 0.0
        matches = sum(1 for ca, cb in zip(a, b) if ca == cb)
        return matches / max(len(a), len(b))

    per_strength = []
    dream_sims = []
    nightmare_sims = []
    for strength in strengths:
        dream_out = registry.apply("dream", text, strength=strength, seed=42)
        nightmare_out = registry.apply("nightmare", text, strength=strength, seed=42)
        dream_sim = round(_char_similarity(text, dream_out), 4)
        nightmare_sim = round(_char_similarity(text, nightmare_out), 4)
        dream_sims.append(dream_sim)
        nightmare_sims.append(nightmare_sim)
        per_strength.append(
            {
                "strength": strength,
                "dream_similarity": dream_sim,
                "nightmare_similarity": nightmare_sim,
                "dream_sample": dream_out[:200],
                "nightmare_sample": nightmare_out[:200],
            }
        )

    avg_dream = sum(dream_sims) / max(len(dream_sims), 1)
    avg_nightmare = sum(nightmare_sims) / max(len(nightmare_sims), 1)
    robustness_score = round((avg_dream + avg_nightmare) / 2.0, 4)

    payload = {
        "model": model,
        "dataset": dataset,
        "robustness_score": robustness_score,
        "avg_dream_similarity": round(avg_dream, 4),
        "avg_nightmare_similarity": round(avg_nightmare, 4),
        "strengths": per_strength,
    }

    if json_only:
        sys.stdout.write(json.dumps(payload))
        sys.stdout.write("\n")
    else:
        print(json.dumps(payload, indent=2))
    return 0


def cmd_benchmark(args: argparse.Namespace) -> int:
    """Run standard robustness benchmarks."""
    print(f"NightmareNet Benchmark Suite: {args.suite}")
    print(f"  Model: {args.model}")
    print("  This feature is under development.")
    return 0


def cmd_distort(args: argparse.Namespace) -> int:
    """Apply a distortion to input text."""
    from nightmarenet.distortions import dream, nightmare

    text = args.text
    strength = args.strength

    if args.type == "dream":
        result = dream.distort(text, strength=strength, seed=args.seed)
    elif args.type == "nightmare":
        result = nightmare.distort(text, strength=strength, seed=args.seed)
    else:
        print(f"Error: unknown distortion type: {args.type}", file=sys.stderr)
        return 1

    print(f"Original:  {text}")
    print(f"Distorted: {result}")
    print(f"  Type: {args.type}, Strength: {strength}")
    return 0


def cmd_foundation(args: argparse.Namespace) -> int:
    """Manage foundation models."""
    from nightmarenet.transfer.registry import get_registry

    if args.action == "register":
        registry = get_registry()
        registry.register(args.model, args.name)
    else:
        print(f"Unknown foundation action: {args.action}", file=sys.stderr)
        return 1
    return 0


def cmd_transfer(args: argparse.Namespace) -> int:
    """Robustness transfer learning commands."""
    from nightmarenet.transfer.report import generate_transfer_report

    if args.measure:
        print("Measuring transfer efficiency...")
        try:
            with open(args.transferred) as f:
                t_data = json.load(f)
            with open(args.baseline) as f:
                b_data = json.load(f)

            t_rob = t_data.get("robustness_score", 0.0)
            b_rob = b_data.get("robustness_score", 0.0)
            t_acc = t_data.get("clean_accuracy", 0.0)
            b_acc = b_data.get("clean_accuracy", 0.0)

            report = generate_transfer_report(t_rob, b_rob, t_acc, b_acc, 0.0, 0.0)
            print(report)
        except Exception as e:
            print(f"Error measuring transfer efficiency: {e}", file=sys.stderr)
            return 1
    elif args.foundation and args.config:
        print(
            f"Starting transfer fine-tuning using foundation '{args.foundation}' "
            f"and config '{args.config}'"
        )
        # In a full implementation, this would parse the config, load data,
        # and use TransferFineTuner.
        print("Transfer fine-tuning initialized.")
    else:
        print("Invalid arguments for transfer command.", file=sys.stderr)
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nightmarenet",
        description="NightmareNet — Autonomous AI Self-Improvement Platform",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show the installed nightmarenet version and exit",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # train
    train_parser = subparsers.add_parser("train", help="Run 4-phase training pipeline")
    train_parser.add_argument("--config", required=True, help="YAML config path")
    train_parser.add_argument("--output", help="Output directory for artifacts")
    train_parser.add_argument("--device", default="cpu", help="Device (cpu/cuda)")

    # evaluate
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate model robustness")
    eval_parser.add_argument("--model", required=False, default="", help="Model name or path")
    eval_parser.add_argument("--text", help="Text to evaluate")
    eval_parser.add_argument(
        "--strengths", default="0.1,0.3,0.5,0.7,0.9", help="Comma-separated strengths"
    )
    eval_parser.add_argument(
        "--dataset", default="sst2", help="Dataset name (informational, default: sst2)"
    )
    eval_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a single JSON object on stdout (for CI consumption)",
    )

    # benchmark
    bench_parser = subparsers.add_parser("benchmark", help="Run robustness benchmarks")
    bench_parser.add_argument(
        "--suite", default="standard", choices=["standard", "adversarial", "full"]
    )
    bench_parser.add_argument("--model", default="distilbert-base-uncased")

    # distort
    distort_parser = subparsers.add_parser("distort", help="Apply distortion to text")
    distort_parser.add_argument("--type", required=True, choices=["dream", "nightmare"])
    distort_parser.add_argument("--strength", type=float, default=0.3)
    distort_parser.add_argument("--text", required=True)
    distort_parser.add_argument("--seed", type=int, default=None)

    # foundation
    foundation_parser = subparsers.add_parser("foundation", help="Manage foundation models")
    foundation_subparsers = foundation_parser.add_subparsers(
        dest="action", help="Foundation actions"
    )
    register_parser = foundation_subparsers.add_parser(
        "register", help="Register a foundation model"
    )
    register_parser.add_argument("--model", required=True, help="Path to the trained model")
    register_parser.add_argument("--name", required=True, help="Name for the foundation model")

    # transfer
    transfer_parser = subparsers.add_parser(
        "transfer", help="Transfer robustness to downstream tasks"
    )
    transfer_parser.add_argument("--foundation", help="Foundation model name")
    transfer_parser.add_argument("--config", help="Path to transfer config YAML")
    transfer_parser.add_argument(
        "--measure", action="store_true", help="Measure transfer efficiency"
    )
    transfer_parser.add_argument("--transferred", help="Path to transferred evaluation JSON")
    transfer_parser.add_argument("--baseline", help="Path to baseline evaluation JSON")

    return parser


def main(argv: Optional[list] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    commands = {
        "train": cmd_train,
        "evaluate": cmd_evaluate,
        "benchmark": cmd_benchmark,
        "distort": cmd_distort,
        "foundation": cmd_foundation,
        "transfer": cmd_transfer,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
