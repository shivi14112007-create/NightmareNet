"""Distortion DSL for composable YAML-defined attack chains."""

from nightmarenet.distortions.dsl.executor import ChainExecutor
from nightmarenet.distortions.dsl.parser import parse_chain_config
from nightmarenet.distortions.dsl.preset_loader import list_presets, load_preset
from nightmarenet.distortions.dsl.schema import ChainConfig, ChainStep, Defaults

__all__ = [
    "ChainConfig",
    "ChainStep",
    "Defaults",
    "ChainExecutor",
    "parse_chain_config",
    "list_presets",
    "load_preset",
]
