"""Head factory for downstream task transfer learning.

Instantiates task-specific heads on top of robust foundation backbones.
"""

from __future__ import annotations

import logging
from typing import Any

from transformers import (
    AutoModelForSequenceClassification,
    AutoModelForTokenClassification,
    PreTrainedModel,
)

logger = logging.getLogger(__name__)


def create_transfer_model(
    foundation_path: str,
    task_type: str = "seq_classification",
    **kwargs: Any,
) -> PreTrainedModel:
    """Create a new model for a downstream task using a foundation backbone.

    The foundation model is expected to contain only the base model weights.
    The HuggingFace library will automatically initialize a new, random
    classification head for the specified task type.

    Args:
        foundation_path: Path to the directory containing the foundation model.
        task_type: String specifying the task ("seq_classification", "token_classification").
        **kwargs: Additional arguments to pass to the from_pretrained call (e.g. num_labels).

    Returns:
        A PyTorch model ready for transfer fine-tuning.
    """
    logger.info("Instantiating new %s model from foundation at %s", task_type, foundation_path)

    if task_type == "seq_classification":
        model = AutoModelForSequenceClassification.from_pretrained(
            foundation_path,
            **kwargs,
        )
    elif task_type == "token_classification":
        model = AutoModelForTokenClassification.from_pretrained(
            foundation_path,
            **kwargs,
        )
    else:
        raise ValueError(
            f"Unsupported task_type '{task_type}'. "
            "Supported types: seq_classification, token_classification."
        )

    return model
