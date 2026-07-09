"""Tests for distributed training and checkpointing."""

import os
from unittest import mock

import torch
import torch.nn as nn

from nightmarenet.distributed.checkpoint import AtomicCheckpointer, compute_config_hash
from nightmarenet.distributed.ddp_wrapper import DDPWrapper
from nightmarenet.distributed.device_pool import DevicePool
from nightmarenet.distributed.resume import ResumeManager
from nightmarenet.distributed.strategies import apply_phase_strategy


class SimpleModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(10, 10)


def test_device_pool():
    pool = DevicePool(override_devices=[0, 1, 2])
    assert pool.get_num_devices() == 3
    assert pool.should_use_ddp() is True

    pool2 = DevicePool(override_devices=[0])
    assert pool2.get_num_devices() == 1
    assert pool2.should_use_ddp() is False

    assert pool.estimate_memory_requirements(1000) > 0


def test_compute_config_hash():
    config = {"training": {"batch_size": 32}, "model": {"name": "test"}}
    hash1 = compute_config_hash(config)
    hash2 = compute_config_hash(config)

    config["training"]["batch_size"] = 16
    hash3 = compute_config_hash(config)

    assert hash1 == hash2
    assert hash1 != hash3


def test_atomic_checkpoint_and_resume(tmp_path):
    base_dir = tmp_path / "checkpoints"
    checkpointer = AtomicCheckpointer(str(base_dir))

    model = SimpleModel()
    optimizer = torch.optim.SGD(model.parameters(), lr=0.1)
    config = {"test": 123}

    target_dir = checkpointer.save(
        run_id="test_run",
        cycle=1,
        phase="wake",
        model=model,
        optimizer=optimizer,
        config=config,
        metrics={"loss": 0.5}
    )

    assert os.path.exists(target_dir)
    assert os.path.exists(os.path.join(target_dir, ".complete"))
    assert os.path.exists(os.path.join(target_dir, "metadata.json"))

    # Resume
    resume_mgr = ResumeManager(target_dir)
    new_model = SimpleModel()
    new_optimizer = torch.optim.SGD(new_model.parameters(), lr=0.1)

    metadata = resume_mgr.verify_and_load(new_model, new_optimizer, config)
    assert metadata["cycle"] == 1
    assert metadata["phase"] == "wake"


@mock.patch("nightmarenet.distributed.strategies.logger")
def test_apply_phase_strategy(mock_logger):
    model = SimpleModel()
    device_pool = DevicePool(override_devices=[0, 1])
    ddp_wrapper = DDPWrapper()
    ddp_wrapper.is_initialized = True  # Mock initialized

    # Wake phase
    with mock.patch.object(ddp_wrapper, "wrap_model", return_value="ddp_model"):
        res = apply_phase_strategy("wake", model, device_pool, ddp_wrapper)
        assert res == "ddp_model"

    # Dream phase (DataParallel)
    res = apply_phase_strategy("dream", model, device_pool, ddp_wrapper)
    assert isinstance(res, nn.DataParallel)

    # Compress phase (Single GPU)
    res = apply_phase_strategy("compress", model, device_pool, ddp_wrapper)
    assert res is model
