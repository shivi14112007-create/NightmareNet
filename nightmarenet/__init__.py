"""NightmareNet: Autonomous AI Self-Improvement Platform."""

__version__ = "0.2.0"

from nightmarenet.distortions.registry import get_registry as get_registry
from nightmarenet.evaluation.evaluator import Evaluator as Evaluator
from nightmarenet.pipeline import Pipeline as Pipeline

__all__ = ["Pipeline", "Evaluator", "get_registry", "__version__"]
