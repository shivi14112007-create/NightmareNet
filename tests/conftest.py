"""Global test configuration for NightmareNet.

Disables API authentication during testing by unsetting NIGHTMARENET_API_KEY.
"""


import pytest


@pytest.fixture(autouse=True)
def _disable_api_auth(monkeypatch):
    """Remove API key from env so auth middleware is disabled during tests."""
    monkeypatch.delenv("NIGHTMARENET_API_KEY", raising=False)
