"""YAML parser for distortion chain configurations."""

from pathlib import Path
from typing import Tuple, Union

import yaml

from nightmarenet.distortions.dsl.schema import ChainConfig
from nightmarenet.distortions.registry import get_registry


def parse_chain_config(
    config_path: Union[str, Path],
    validate_engines: bool = True,
) -> ChainConfig:
    """Parse a YAML distortion chain configuration file.

    Args:
        config_path: Path to the YAML configuration file
        validate_engines: If True, verify all referenced engines are registered

    Returns:
        Validated ChainConfig object

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML parsing fails
        ValueError: If validation fails (schema or engine validation)
    """
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path) as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError("Config file must contain a YAML dictionary")

    # Validate with Pydantic
    try:
        chain_config = ChainConfig(**data)
    except Exception as e:
        raise ValueError(f"Schema validation failed: {e}") from e

    # Validate engines if requested
    if validate_engines:
        registry = get_registry()
        for step in chain_config.chain:
            if step.engine not in registry:
                available = ", ".join(registry.engine_names)
                raise ValueError(
                    f"Unknown engine '{step.engine}' in step. Available: {available}"
                )

    return chain_config


def validate_chain_config(config_path: Union[str, Path]) -> Tuple[bool, str]:
    """Validate a distortion chain configuration file without loading it.

    Args:
        config_path: Path to the YAML configuration file

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        parse_chain_config(config_path, validate_engines=True)
        return True, "Configuration is valid"
    except FileNotFoundError as e:
        return False, f"File not found: {e}"
    except yaml.YAMLError as e:
        return False, f"YAML parsing error: {e}"
    except ValueError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Unexpected error: {e}"
