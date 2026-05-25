# NightmareNet Benchmark v1 — SST-2 Adversarial Robustness

**Date:** 2026-05-25 (initial), 2026-05-26 (re-run with full nightmare distortion)
**Hardware:** NVIDIA GeForce RTX 3050 Ti Laptop GPU (4 GB VRAM, CC 8.6)
**Software:** Python 3.12.5, PyTorch 2.5.1+cu121, Transformers 5.9.0
**Repro:** `python scripts/run_gpu_benchmark.py --train-samples 500 --eval-samples 200 --batch-size 8`
**Raw results:** [`results/gpu_benchmark.json`](../../results/gpu_benchmark.json)

---

## TL;DR

On a 500-sample SST-2 fine-tune of `distilbert-base-uncased`, NightmareNet's
Wake → Nightmare adversarial-training cycle delivered a **+13.64% relative
improvement in adversarial robustness** (averaged across dream and nightmare
distortions at strengths 0.1–0.9) vs the wake-only baseline — within the 10–30%
target band of the strategic plan, and also **+4.0 absolute points on clean
accuracy** (0.745 → 0.785), so robustness gains come *with* a clean-accuracy
gain rather than a trade-off.

> An earlier run reported +14.49% with the learned-adversarial path disabled
> (faster benchmark, but a less faithful Nightmare phase). The headline number
> is now the +13.64% from the canonical configuration with the full
> rule-based + learned nightmare distortion pipeline; both runs lie in the
> target 10–30% band.

## Setup

| Parameter | Value |
|-----------|-------|
| Model | `distilbert-base-uncased` (66M params) |
| Dataset | GLUE/SST-2 (`nyu-mll/glue`) |
| Train samples | 500 (shuffled, seed 42) |
| Eval samples | 200 (validation split) |
| Batch size | 8 |
| Learning rate | 3e-5 (wake), 1.5e-5 (nightmare) |
| Mixed precision | FP16 via `torch.amp.autocast` |
| Max sequence length | 128 |
| Seed | 42 |

### Training regimes

- **Baseline (wake-only):** 1 epoch over the 500 train examples with clean text.
- **NightmareNet:** 1 epoch wake (clean text) + 1 epoch nightmare (each example replaced
  with `nightmare.distort(text, strength=0.5)` — rule-based contradictions, ambiguity
  injection, cross-domain splicing, misleading context).

The expensive learned-adversarial DistilBERT path is disabled in the benchmark
distorter (`learned: 0.0` in the adversarial config) so per-call latency stays bounded;
the production training loop caches the generator (see `_get_learned_generator`).

### Evaluation

For each regime we measured:
1. **Clean accuracy** on the unmodified validation set.
2. **Distorted accuracy** under `dream` and `nightmare` distortions at strengths
   `{0.1, 0.3, 0.5, 0.7, 0.9}` (10 conditions total).
3. **Robustness drop** = clean accuracy − average distorted accuracy.

## Results

### Clean accuracy

| Regime | Clean Accuracy |
|--------|---------------:|
| Baseline (wake-only) | 0.745 |
| NightmareNet (wake + nightmare) | **0.785** |

NightmareNet does *not* sacrifice clean-input performance for robustness gains
— it improves clean accuracy by 4.0 absolute points (+5.4% relative).

### Distorted accuracy by strength

| Strength | Baseline Dream | NN Dream | Δ Dream | Baseline Nightmare | NN Nightmare | Δ Nightmare |
|---------:|---------------:|---------:|--------:|-------------------:|-------------:|------------:|
| 0.1 | 0.700 | 0.765 | +0.065 | 0.710 | 0.770 | +0.060 |
| 0.3 | 0.665 | 0.725 | +0.060 | 0.655 | 0.735 | +0.080 |
| 0.5 | 0.580 | 0.645 | +0.065 | 0.585 | 0.630 | +0.045 |
| 0.7 | 0.480 | 0.565 | +0.085 | 0.480 | 0.560 | +0.080 |
| 0.9 | 0.490 | 0.590 | +0.100 | 0.485 | 0.640 | +0.155 |

NightmareNet wins at every strength level for both distortion families.
Critically, the improvement *increases with distortion strength* — adversarial
training is most valuable exactly where baselines collapse (the strength-0.9
nightmare condition gains +15.5 absolute points).

### Aggregate metrics

| Metric | Baseline | NightmareNet | Δ |
|--------|---------:|-------------:|---:|
| Clean accuracy | 0.7450 | 0.7850 | +0.0400 |
| Avg distorted accuracy | 0.5830 | 0.6625 | **+0.0795** |
| Robustness drop (clean − distorted) | 0.162 | 0.123 | −0.040 |
| **Relative robustness improvement** | — | — | **+13.64%** |

The relative improvement falls in the 10–30% target band of the strategic plan
(`docs/architecture/PRD.md` → success metrics).

## Reproducibility

1. Create the Python 3.12 + CUDA 12.1 venv:

   ```bash
   py -3.12 -m venv .venv312
   .venv312/Scripts/Activate.ps1   # PowerShell
   pip install torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cu121
   pip install -e ".[dev,api]"
   ```

2. Verify the GPU is detected:

   ```bash
   python scripts/gpu_check.py
   ```

3. Run the benchmark (seed 42 is fixed; outputs are deterministic):

   ```bash
   python scripts/run_gpu_benchmark.py
   ```

The script writes `results/gpu_benchmark.json` with the full per-strength table
and timing data.

## Limitations and future work

- **Sample sizes are small** (500 train, 200 val) due to 4 GB VRAM budget on the
  development GPU. Re-running with larger splits and additional epochs is
  straightforward via `--train-samples` and `--eval-samples`.
- **Single seed.** Production benchmarks should average over 5+ seeds and report
  standard deviation. Add `--seeds 42,1,7,99,123` in a follow-up.
- **Distortion-as-attack proxy.** Our distortion API is a fast, deterministic proxy
  for adversarial inputs; integration with TextFooler / BertAttack will tighten the
  threat model (see `docs/research/paper-draft.md`).
- **Cycle count is 1.** The full Wake → Dream → Nightmare → Compress cycle with
  `num_cycles >= 2` (the sleep-inspired core thesis) is exercised via
  `configs/benchmark_sst2_gpu.yaml` and `nightmarenet train`; this benchmark only
  validates the wake + nightmare half on a fast path.

## Citation

```bibtex
@misc{nightmarenet2026benchmark,
  title = {NightmareNet Benchmark v1: SST-2 Adversarial Robustness on Consumer GPUs},
  author = {Jain, Adit and contributors},
  year = {2026},
  url = {https://github.com/Adit-Jain-srm/NightmareNet/blob/main/docs/research/benchmark-v1.md}
}
```
