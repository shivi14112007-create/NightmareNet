"""Tests for refactored distortion module imports in app.py.

Verifies that the DRY refactor (importing distort() from dream.py/nightmare.py
instead of inline logic) produces correct results.
"""

import pytest

from nightmarenet.distortions.dream import distort as dream_distort
from nightmarenet.distortions.nightmare import distort as nightmare_distort


class TestDistortionModuleExports:
    """Verify dream.distort() and nightmare.distort() are callable and correct."""

    def test_dream_distort_returns_string(self):
        result = dream_distort("Hello world", strength=0.3, seed=42)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_dream_distort_with_zero_strength_preserves_text(self):
        text = "The model achieved high accuracy."
        result = dream_distort(text, strength=0.0, seed=42)
        assert result == text

    def test_nightmare_distort_returns_string(self):
        result = nightmare_distort("Hello world", strength=0.5, seed=42)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_nightmare_distort_high_strength_modifies_text(self):
        text = "Neural networks process information efficiently."
        result = nightmare_distort(text, strength=0.9, seed=42)
        assert result != text

    def test_dream_distort_with_config(self):
        text = "Test input for config."
        config = {"text": {"char_swap": 0.5}}
        result = dream_distort(text, strength=0.5, seed=42, config=config)
        assert isinstance(result, str)

    def test_nightmare_distort_with_config(self):
        text = "Test input for config."
        config = {"adversarial": {"contradiction": 0.5, "ambiguity": 0.5}}
        result = nightmare_distort(text, strength=0.7, seed=42, config=config)
        assert isinstance(result, str)

    def test_dream_deterministic_with_seed(self):
        text = "Reproducible distortion test."
        r1 = dream_distort(text, strength=0.4, seed=123)
        r2 = dream_distort(text, strength=0.4, seed=123)
        assert r1 == r2

    def test_nightmare_deterministic_with_seed(self):
        text = "Reproducible distortion test."
        r1 = nightmare_distort(text, strength=0.6, seed=456)
        r2 = nightmare_distort(text, strength=0.6, seed=456)
        assert r1 == r2

    def test_empty_text_passes_through(self):
        assert dream_distort("", strength=0.5) == ""
        assert nightmare_distort("", strength=0.5) == ""
