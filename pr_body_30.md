## Summary

Implement Distributed multi-GPU cycle execution with fault-tolerant checkpointing.

## Motivation

Closes #30

## Changes

- Created `nightmarenet/distributed/` package for GPU discovery, DDP wrapping, and phase-specific strategies.
- Implemented `AtomicCheckpointer` and `ResumeManager` to safely save state with `.complete` sentinels and resume training.
- Updated `cli.py` to add `--distributed` and `--resume` flags.
- Modified `pipeline.py` and `trainer.py` to seamlessly execute distributed strategies per-phase without breaking the pipeline.

## Acceptance Criteria

- [x] Multi-GPU device discovery and memory heuristics are implemented.
- [x] PyTorch `DistributedDataParallel` is integrated correctly per-phase.
- [x] Atomic checkpointing with `.complete` sentinel is functional.
- [x] The pipeline successfully resumes from checkpoints using `--resume`.

## Type

- [ ] Bug fix (non-breaking change that fixes an issue)
- [x] Feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would break existing behavior)
- [ ] Refactor (no functional change)
- [ ] Documentation
- [x] Tests

## Pre-submission Checklist

- [x] I have **starred** this repository
- [x] I have **followed** [@Adit-Jain-srm](https://github.com/Adit-Jain-srm)
- [x] I have read [CONTRIBUTING.md](https://github.com/Adit-Jain-srm/NightmareNet/blob/main/CONTRIBUTING.md)

## Quality Checklist

- [x] `ruff check nightmarenet/ tests/` passes with 0 errors
- [x] `mypy nightmarenet/ --ignore-missing-imports` passes
- [x] `pytest tests/` — all tests pass (445+)
- [x] Added tests for new functionality (if applicable)
- [x] Updated documentation (if applicable)
- [x] Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/)
- [x] All acceptance criteria from the linked issue are satisfied (or exceptions noted above)

## Screenshots (if UI change)
