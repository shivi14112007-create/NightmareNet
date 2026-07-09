"""Main training loop orchestrator.

Manages the full sleep-cycle training pipeline: instantiates phases,
manages checkpointing, and logs per-phase metrics.
"""

from __future__ import annotations

import copy
import json
import logging
import math
import os
import signal
import threading
from typing import Any, Callable, Optional

import torch
import torch.distributed as dist
from datasets import IterableDataset
from torch.utils.data import DataLoader
from transformers import (
    AutoModelForCausalLM,
    AutoModelForMaskedLM,
    AutoModelForSequenceClassification,
    AutoTokenizer,
)

from nightmarenet.distributed.checkpoint import AtomicCheckpointer
from nightmarenet.distributed.ddp_wrapper import DDPWrapper
from nightmarenet.distributed.device_pool import DevicePool
from nightmarenet.distributed.resume import ResumeManager
from nightmarenet.distributed.strategies import apply_phase_strategy
from nightmarenet.training.phases import (
    CompressionPhase,
    DreamPhase,
    NightmarePhase,
    WakePhase,
)
from nightmarenet.training.scheduler import create_scheduler_from_config
from nightmarenet.utils.tracking import create_tracker_from_config
from nightmarenet.utils.webhooks import check_vram_pressure, trigger_webhook

logger = logging.getLogger(__name__)

_MODEL_TYPE_MAP = {
    "causal_lm": AutoModelForCausalLM,
    "masked_lm": AutoModelForMaskedLM,
    "seq_classification": AutoModelForSequenceClassification,
}


def _get_device(config: dict) -> torch.device:
    """Determine the training device from config."""
    device_str = config.get("model", {}).get("device", "auto")
    if device_str == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(device_str)


def _create_amp_scaler(use_amp: bool, device: torch.device) -> Optional[torch.amp.GradScaler]:
    """Create a GradScaler for mixed-precision training, or None if disabled."""
    if use_amp and device.type == "cuda":
        return torch.amp.GradScaler("cuda")
    return None


def _tokenize_dataset(
    dataset: Any,
    tokenizer: Any,
    text_column: str,
    max_length: int,
    batch_size: int,
) -> DataLoader:
    """Tokenize a dataset and return a DataLoader."""

    def tokenize_fn(examples):
        return tokenizer(
            examples[text_column],
            truncation=True,
            padding="max_length",
            max_length=max_length,
            return_tensors="pt",
        )

    if isinstance(dataset, IterableDataset):
        tokenized = dataset.map(
            tokenize_fn,
            batched=True,
            remove_columns=dataset.column_names if dataset.column_names else [text_column],
        )
        tokenized = tokenized.with_format("torch")
        return DataLoader(tokenized, batch_size=batch_size)

    tokenized = dataset.map(
        tokenize_fn,
        batched=True,
        remove_columns=dataset.column_names,
        desc="Tokenizing",
    )
    tokenized.set_format("torch")
    return DataLoader(tokenized, batch_size=batch_size, shuffle=True)


class Trainer:
    """Orchestrates the full sleep-cycle training pipeline.

    Args:
        config: Full configuration dictionary.
        model: Optional pre-loaded model. If None, loads from config.
        tokenizer: Optional pre-loaded tokenizer. If None, loads from config.
    """

    def __init__(
        self,
        config: dict,
        model=None,
        tokenizer=None,
        distributed: Optional[str] = None,
        resume_dir: Optional[str] = None,
    ):
        self.config = config
        self.device = _get_device(config)
        self.training_config = config.get("training", {})
        self.model_config = config.get("model", {})
        self.compression_config = config.get("compression", {})

        # Load model and tokenizer
        resume_from = self.training_config.get("resume_from")
        model_name = self.model_config.get("name", "gpt2")
        self.model_type = self.model_config.get("type", "causal_lm")
        if model is None:
            logger.info(
                "Loading model base architecture: %s (type=%s)",
                model_name,
                self.model_type,
            )
            model_cls = _MODEL_TYPE_MAP.get(self.model_type)
            if model_cls is None:
                raise ValueError(
                    f"Unknown model type '{self.model_type}'. "
                    f"Supported: {list(_MODEL_TYPE_MAP)}"
                )
            try:
                kwargs = {}
                if self.model_type == "seq_classification":
                    kwargs["num_labels"] = self.model_config.get("num_labels", 2)
                self.model = model_cls.from_pretrained(model_name, **kwargs)
            except Exception as exc:
                raise RuntimeError(f"Failed to load model '{model_name}': {exc}") from exc
        else:
            self.model = model
        self.model.to(self.device)

        # Load weights from checkpoint if resuming
        if resume_from:
            from nightmarenet.distributed.checkpoint import load_model_weights
            load_model_weights(self.model, resume_from, self.device)

        if tokenizer is None:
            has_resume = resume_from and os.path.exists(resume_from)
            tokenizer_load_path = resume_from if has_resume else model_name
            self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_load_path)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
        else:
            self.tokenizer = tokenizer

        # Create optimizer
        self.optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=self.training_config.get("learning_rate", 5e-5),
            weight_decay=self.training_config.get("weight_decay", 0.01),
        )

        # Mixed-precision training
        self.use_amp = self.training_config.get("use_amp", False)
        self.scaler = _create_amp_scaler(self.use_amp, self.device)
        if self.use_amp:
            if self.device.type == "cuda":
                logger.info("Mixed-precision training (AMP) enabled.")
            else:
                logger.warning("use_amp=True but device is %s; AMP disabled.", self.device)
                self.use_amp = False
                self.scaler = None

        # Gradient checkpointing
        if self.training_config.get("gradient_checkpointing", False):
            if hasattr(self.model, "gradient_checkpointing_enable"):
                self.model.gradient_checkpointing_enable()
                logger.info("Gradient checkpointing enabled.")
            else:
                logger.warning("Model does not support gradient checkpointing.")

        # Create scheduler
        self.scheduler = create_scheduler_from_config(config)

        # Reference model for KL regularization (created after wake phase)
        self.reference_model = None

        # Training history
        self.history: list[dict] = []

        # Interrupt flag
        self._interrupted = False

        # External stop request (e.g. adaptive termination)
        self._stop_requested = False

        # Checkpoint directory
        self.checkpoint_dir = self.training_config.get("checkpoint_dir", "checkpoints")
        os.makedirs(self.checkpoint_dir, exist_ok=True)

        # Log directory
        self.log_dir = self.training_config.get("log_dir", "logs")
        os.makedirs(self.log_dir, exist_ok=True)

        # Distributed multi-GPU setup
        override_devices = None
        if distributed and distributed != "auto":
            override_devices = [int(x.strip()) for x in distributed.split(",")]
        self.device_pool = DevicePool(override_devices=override_devices)
        self.ddp_wrapper = DDPWrapper()

        if self.device_pool.should_use_ddp():
            self.ddp_wrapper.setup()

        # Checkpointer and Resume
        self.checkpointer = AtomicCheckpointer(self.checkpoint_dir)
        self.resume_manager = ResumeManager(resume_dir) if resume_dir else None

        # Load from resume if provided
        if self.resume_manager:
            metadata = self.resume_manager.verify_and_load(self.model, self.optimizer, self.config)
            self._start_cycle = metadata.get("cycle", 0)
            self._start_phase = metadata.get("phase", None)
            logger.info(f"Resuming from cycle {self._start_cycle}, phase {self._start_phase}")
        else:
            self._start_cycle = 0
            self._start_phase = None

        # Experiment tracker (only on main process)
        if not (dist.is_available() and dist.is_initialized()) or dist.get_rank() == 0:
            self.tracker = create_tracker_from_config(config)
        else:
            self.tracker = create_tracker_from_config({})

        self.run_id = None
        self._vram_alert_sent = False

    def _create_reference_model(self) -> None:
        """Create a frozen copy of the current model for KL regularization."""
        self.reference_model = copy.deepcopy(self.model)
        self.reference_model.eval()  # type: ignore[attr-defined]
        for param in self.reference_model.parameters():  # type: ignore[attr-defined]
            param.requires_grad = False
        logger.info("Created reference model for KL regularization.")

    def _handle_interrupt(self, signum, frame) -> None:
        """Handle SIGINT by flagging for a graceful checkpoint save."""
        logger.warning("Received interrupt signal, will save checkpoint and stop.")
        self._interrupted = True

    def request_stop(self) -> None:
        """Request graceful termination after the current phase."""
        logger.info("External stop requested.")
        self._stop_requested = True

    def _save_checkpoint(self, cycle: int, phase: str):
        """Save a model checkpoint after a phase."""
        if not self.training_config.get("save_every_phase", True):
            return
        if dist.is_available() and dist.is_initialized() and dist.get_rank() != 0:
            return

        run_id_to_use = getattr(self, "run_id", "default_run")
        if not run_id_to_use:
            run_id_to_use = "default_run"

        metrics = self.history[-1] if self.history else None
        devices_used = (
            self.device_pool.available_devices if hasattr(self, "device_pool") else []
        )

        path = self.checkpointer.save(
            run_id=run_id_to_use,
            cycle=cycle,
            phase=phase,
            model=self.model,
            optimizer=self.optimizer,
            config=self.config,
            metrics=metrics,
            devices_used=devices_used,
        )

        # Save tokenizer
        self.tokenizer.save_pretrained(path)

        # Save training state
        import time

        state = {
            "optimizer_state_dict": self.optimizer.state_dict(),
            "scaler_state_dict": self.scaler.state_dict() if self.scaler is not None else None,
            "cycle": cycle,
            "phase": phase,
            "history": self.history,
            "metadata": {
                "timestamp": time.time(),
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
                "trainer_class": self.__class__.__name__,
            },
        }
        torch.save(state, os.path.join(path, "training_state.pt"))
        logger.info("Checkpoint saved: %s (including training state)", path)

        # Post-save validation and complete file hashes update
        meta_path = os.path.join(path, "metadata.json")
        try:
            from nightmarenet.distributed.checkpoint import (
                compute_dir_hashes,
                validate_checkpoint_integrity,
            )
            file_hashes = compute_dir_hashes(path)
            metadata = {}
            if os.path.exists(meta_path):
                with open(meta_path) as f:
                    metadata = json.load(f)
            metadata["file_hashes"] = file_hashes
            with open(meta_path, "w") as f:
                json.dump(metadata, f, indent=2)

            # Post-save validation check
            validate_checkpoint_integrity(path, self.config)
            logger.info("Post-save checkpoint integrity validation passed successfully.")
        except Exception as e:
            logger.error("Post-save checkpoint integrity validation failed: %s", e)
            raise

    def _save_history(self):
        """Save training history to a JSON file."""
        path = os.path.join(self.log_dir, "training_history.json")
        with open(path, "w") as f:
            json.dump(self.history, f, indent=2)
        logger.info("Training history saved: %s", path)

    def train(
        self,
        train_dataloader: DataLoader,
        dream_dataloader: DataLoader,
        nightmare_dataloader: DataLoader,
        val_dataloader: Optional[DataLoader] = None,
        on_progress: Optional[Callable[[dict], None]] = None,
    ) -> list[dict]:
        """Run the full sleep-cycle training pipeline.

        Args:
            train_dataloader: DataLoader for wake phase (real data).
            dream_dataloader: DataLoader for dream phase (mildly distorted).
            nightmare_dataloader: DataLoader for nightmare phase (extreme perturbations).
            val_dataloader: Optional DataLoader for validation.

        Returns:
            List of phase result dicts (training history).
        """
        logger.info("Starting training with schedule:\n%s", self.scheduler.summary())  # type: ignore[union-attr]
        logger.info("Device: %s", self.device)
        self.tracker.log_config(self.config)

        # Native distributed logic is applied per-phase via apply_phase_strategy

        prev_handler = None
        if threading.current_thread() is threading.main_thread():
            prev_handler = signal.getsignal(signal.SIGINT)
            signal.signal(signal.SIGINT, self._handle_interrupt)

        current_cycle = 0
        current_phase = "init"
        total_phases = max(len(self.scheduler), 1)
        completed_phases = 0

        # Load training state if resuming
        resume_from = self.training_config.get("resume_from")
        if resume_from:
            from nightmarenet.distributed.checkpoint import validate_checkpoint_integrity
            try:
                # Explicit structural, version and checksum validation of the checkpoint folder
                validate_checkpoint_integrity(resume_from, self.config)
            except Exception as val_err:
                logger.error("Checkpoint integrity validation failed: %s", val_err)
                raise ValueError(f"Cannot resume from corrupted checkpoint: {val_err}") from val_err

            state_path = os.path.join(resume_from, "training_state.pt")
            if os.path.exists(state_path):
                logger.info("Resuming training state from %s", state_path)
                import copy
                import pickle

                state = None
                try:
                    state = torch.load(state_path, map_location=self.device)
                except (pickle.PickleError, KeyError, RuntimeError) as e:
                    logger.error(
                        "Failed to load training state from %s: %s. "
                        "Continuing with fresh history.",
                        state_path,
                        e,
                    )

                if state is not None:
                    # Validate optimizer state dict compatibility
                    saved_opt = state.get("optimizer_state_dict")
                    if saved_opt and "param_groups" in saved_opt:
                        saved_groups = len(saved_opt["param_groups"])
                        current_groups = len(self.optimizer.param_groups)
                        if saved_groups != current_groups:
                            logger.warning(
                                "Optimizer param group count mismatch (saved: %d, current: %d). "
                                "Skipping loading optimizer state.",
                                saved_groups,
                                current_groups,
                            )
                        else:
                            try:
                                self.optimizer.load_state_dict(saved_opt)
                            except Exception as opt_err:
                                logger.warning(
                                    "Failed to load optimizer state dict: %s", opt_err
                                )

                    if self.scaler is not None and state.get("scaler_state_dict") is not None:
                        try:
                            self.scaler.load_state_dict(state["scaler_state_dict"])
                        except Exception as scaler_err:
                            logger.warning("Failed to load scaler state dict: %s", scaler_err)

                    self.history = copy.deepcopy(state.get("history", []))
                    completed_phases = len(self.history)

                    start_cycle = state.get("cycle", 0)
                    start_phase = state.get("phase")

                    # Validate resume point
                    valid_phases = ["wake", "dream", "nightmare", "compress"]
                    if hasattr(self.scheduler, "PHASE_ORDER"):
                        valid_phases = self.scheduler.PHASE_ORDER
                    elif hasattr(self.scheduler, "base_scheduler") and hasattr(
                        self.scheduler.base_scheduler, "PHASE_ORDER"
                    ):
                        valid_phases = self.scheduler.base_scheduler.PHASE_ORDER

                    if start_phase not in valid_phases:
                        raise ValueError(
                            f"Corrupted start_phase '{start_phase}' in checkpoint state. "
                            f"Must be one of {valid_phases}"
                        )

                    if start_phase:
                        if hasattr(self.scheduler, "base_scheduler"):
                            self.scheduler.base_scheduler.start_cycle = start_cycle
                            self.scheduler.base_scheduler.start_phase = start_phase
                        else:
                            self.scheduler.start_cycle = start_cycle
                            self.scheduler.start_phase = start_phase
                        logger.info(
                            "Scheduler configured to resume after cycle %d, phase %s",
                            start_cycle,
                            start_phase,
                        )
            else:
                logger.warning(
                    "resume_from path specified but training_state.pt not found: %s",
                    state_path,
                )

        try:
            for cycle, phase, num_epochs in self.scheduler:
                if cycle < getattr(self, "_start_cycle", 0):
                    logger.info(f"Skipping cycle {cycle} (resuming from {self._start_cycle})")
                    continue

                if cycle == getattr(self, "_start_cycle", 0):
                    start_phase = getattr(self, "_start_phase", None)
                    if start_phase and not getattr(self, "_resume_caught_up", False):
                        if phase != start_phase:
                            logger.info(
                                f"Skipping phase {phase} in cycle {cycle} (already completed)"
                            )
                            continue
                        else:
                            logger.info(
                                f"Skipping phase {phase} in cycle {cycle} (already completed)"
                            )
                            self._resume_caught_up = True
                            continue

                if self._interrupted:
                    break

                if self._stop_requested:
                    logger.info("Training stop requested. Terminating after cycle %d.", cycle+1)
                    break
                # Early stopping check
                if hasattr(self.scheduler, 'should_stop') and self.scheduler.should_stop:
                    logger.info("Early stopping: halting training at cycle %d.", cycle + 1)
                    break
                current_cycle = cycle
                current_phase = phase
                if on_progress is not None:
                    try:
                        on_progress(
                            {
                                "cycle": cycle,
                                "phase": phase,
                                "progress_pct": (completed_phases / total_phases) * 100.0,
                                "status": "phase_start",
                            }
                        )
                    except Exception:
                        logger.debug("on_progress callback failed", exc_info=True)
                logger.info(
                    "=== Cycle %d - Phase: %s (%d epochs) ===",
                    cycle + 1,
                    phase,
                    num_epochs,
                )

                result: dict

                phase_model = apply_phase_strategy(
                    phase=phase,
                    model=self.model,
                    device_pool=self.device_pool,
                    ddp_wrapper=self.ddp_wrapper
                )

                if phase == "wake":
                    wake_runner = WakePhase(
                        model=phase_model,
                        optimizer=self.optimizer,
                        config=self.training_config,
                        device=self.device,
                        scaler=self.scaler,
                    )
                    result = wake_runner.run(train_dataloader, num_epochs=num_epochs)

                    # Create reference model after first wake phase
                    if cycle == 0:
                        self._create_reference_model()

                elif phase == "dream":
                    if self.reference_model is None:
                        self._create_reference_model()
                    dream_runner = DreamPhase(
                        model=phase_model,
                        optimizer=self.optimizer,
                        config=self.training_config,
                        device=self.device,
                        reference_model=self.reference_model,
                        kl_weight=0.1,
                        scaler=self.scaler,
                    )
                    result = dream_runner.run(dream_dataloader, num_epochs=num_epochs)

                elif phase == "nightmare":
                    lr_multiplier = self.training_config.get("nightmare_lr_multiplier", 2.0)
                    nightmare_runner = NightmarePhase(
                        model=phase_model,
                        optimizer=self.optimizer,
                        config=self.training_config,
                        device=self.device,
                        lr_multiplier=lr_multiplier,
                        scaler=self.scaler,
                    )
                    result = nightmare_runner.run(nightmare_dataloader, num_epochs=num_epochs)

                elif phase == "compress":
                    compress_runner = CompressionPhase(
                        model=phase_model,
                        config=self.compression_config,
                        device=self.device,
                        scaler=self.scaler,
                    )
                    result = compress_runner.run(
                        dataloader=train_dataloader,
                        optimizer=self.optimizer,
                    )
                else:
                    logger.warning("Unknown phase: %s", phase)
                    continue

                # NaN/Inf detection on phase avg_loss
                avg_loss = result.get("avg_loss")
                if avg_loss is not None and (math.isnan(avg_loss) or math.isinf(avg_loss)):
                    logger.critical(
                        "Phase '%s' in cycle %d returned NaN/Inf avg_loss: %s",
                        phase,
                        cycle,
                        avg_loss,
                    )

                result["cycle"] = cycle
                result["phase"] = phase
                self.history.append(result)
                completed_phases += 1

                if on_progress is not None:
                    try:
                        on_progress(
                            {
                                "cycle": cycle,
                                "phase": phase,
                                "avg_loss": result.get("avg_loss"),
                                "progress_pct": (completed_phases / total_phases) * 100.0,
                                "status": "phase_end",
                                "history": list(self.history),
                            }
                        )
                    except Exception:
                        logger.debug("on_progress callback failed", exc_info=True)

                # Log to tracker
                self.tracker.log_phase(cycle, phase, result)

                # Update adaptive scheduler with phase loss
                avg_loss = result.get("avg_loss")
                if hasattr(self.scheduler, 'update') and avg_loss is not None:
                    self.scheduler.update(phase, avg_loss)

                # Save checkpoint
                self._save_checkpoint(cycle, phase)

                # Check GPU VRAM pressure
                if self.device.type == "cuda":
                    device_idx = self.device.index if self.device.index is not None else 0
                    has_pressure = check_vram_pressure(device_idx, threshold=0.85)
                    if not getattr(self, "_vram_alert_sent", False) and has_pressure:
                        self._vram_alert_sent = True
                        try:
                            free, total = torch.cuda.mem_get_info(device_idx)
                            used = total - free
                            pct = (used / total) * 100.0
                            gpu_name = torch.cuda.get_device_name(device_idx)
                            trigger_webhook(
                                self.config,
                                "alert",
                                f"GPU VRAM pressure detected: {pct:.1f}% used on {gpu_name}.",
                                {
                                    "run_id": getattr(self, "run_id", "unknown"),
                                    "gpu": gpu_name,
                                    "used_vram": f"{used / (1024**2):.1f} MB",
                                    "total_vram": f"{total / (1024**2):.1f} MB",
                                    "usage_percent": f"{pct:.1f}%",
                                    "cycle": cycle + 1,
                                    "phase": phase,
                                }
                            )
                        except Exception as e:
                            logger.warning("Failed to record VRAM alert details: %s", e)

                # Log metrics
                logger.info("Phase result: %s", json.dumps(result, indent=2, default=str))

                # Notify pipeline that a full training cycle has completed
                if phase == "compress" and on_progress is not None:
                    try:
                        on_progress(
                            {
                                "event": "cycle_end",
                                "cycle": cycle,
                                "phase": phase,
                                "history": list(self.history),
                            }
                        )
                    except Exception:
                        logger.debug("on_progress callback failed", exc_info=True)
        except KeyboardInterrupt:
            logger.warning("Training interrupted by KeyboardInterrupt.")
        finally:
            if self._interrupted:
                self._save_checkpoint(current_cycle, current_phase)
                logger.info("Training interrupted, checkpoint saved.")
            if prev_handler is not None:
                signal.signal(signal.SIGINT, prev_handler)

        # Save final model and history
        final_path = os.path.join(self.checkpoint_dir, "final")
        os.makedirs(final_path, exist_ok=True)

        if dist.is_available() and dist.is_initialized():
            dist.barrier()

        if not (dist.is_available() and dist.is_initialized()) or dist.get_rank() == 0:
            self.model.save_pretrained(final_path)
            self.tokenizer.save_pretrained(final_path)
            self._save_history()

        if dist.is_available() and dist.is_initialized():
            self.ddp_wrapper.teardown()

        self.tracker.finish()
        logger.info("Training complete. Final model saved to %s", final_path)
        return self.history

def create_trainer_from_config(config: dict, model=None, tokenizer=None) -> Trainer:
    """Create a Trainer instance from a configuration dictionary.

    Args:
        config: Full configuration dictionary.
        model: Optional pre-loaded model.
        tokenizer: Optional pre-loaded tokenizer.

    Returns:
        Configured Trainer instance.
    """
    return Trainer(config=config, model=model, tokenizer=tokenizer)
