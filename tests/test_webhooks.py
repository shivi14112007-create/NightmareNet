"""Unit tests for the NightmareNet webhook notification system."""

from __future__ import annotations

import json
import urllib.error
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from nightmarenet.api.app import app
from nightmarenet.utils.config import validate_config
from nightmarenet.utils.webhooks import _send_webhook_request

client = TestClient(app)


def test_config_validation_valid():
    """Verify that a valid notifications config passes validation."""
    valid_cfg = {
        "model": {"name": "gpt2", "type": "causal_lm", "max_length": 128, "device": "cpu"},
        "dataset": {"name": "wikitext", "text_column": "text"},
        "training": {
            "wake_epochs": 1,
            "dream_epochs": 1,
            "nightmare_epochs": 1,
            "num_cycles": 1,
            "compression_rounds": 0,
            "batch_size": 4,
            "learning_rate": 5e-5,
            "nightmare_lr_multiplier": 1.5,
            "max_grad_norm": 1.0,
            "gradient_accumulation_steps": 1,
        },
        "seed": 42,
        "distortion": {"dream_strength": 0.2, "nightmare_strength": 0.8},
        "compression": {"pruning_ratio": 0.1, "bottleneck_rank_ratio": 0.5},
        "notifications": {
            "webhooks": [
                {
                    "url": "https://hooks.slack.com/services/T/B/X",
                    "events": ["run_complete", "regression_detected"],
                },
                {
                    "url": "https://discord.com/api/webhooks/123/abc",
                },
            ]
        },
    }
    errors = validate_config(valid_cfg)
    assert not errors, f"Config validation failed unexpectedly: {errors}"


def test_config_validation_invalid():
    """Verify that invalid notifications config fails validation."""
    invalid_cfg = {
        "model": {"name": "gpt2", "type": "causal_lm", "max_length": 128, "device": "cpu"},
        "dataset": {"name": "wikitext", "text_column": "text"},
        "training": {
            "wake_epochs": 1,
            "dream_epochs": 1,
            "nightmare_epochs": 1,
            "num_cycles": 1,
            "compression_rounds": 0,
            "batch_size": 4,
            "learning_rate": 5e-5,
            "nightmare_lr_multiplier": 1.5,
            "max_grad_norm": 1.0,
            "gradient_accumulation_steps": 1,
        },
        "seed": 42,
        "distortion": {"dream_strength": 0.2, "nightmare_strength": 0.8},
        "compression": {"pruning_ratio": 0.1, "bottleneck_rank_ratio": 0.5},
        "notifications": {
            "webhooks": [
                {
                    # Missing URL
                    "events": ["invalid_event"],  # Invalid event
                }
            ]
        },
    }
    errors = validate_config(invalid_cfg)
    assert len(errors) >= 2
    assert any("missing required key: 'url'" in e for e in errors)
    assert any("must be one of" in e for e in errors)


@patch("urllib.request.urlopen")
def test_send_slack_webhook(mock_urlopen):
    """Verify Slack webhook payload structure."""
    mock_response = MagicMock()
    mock_response.getcode.return_value = 200
    mock_urlopen.return_value.__enter__.return_value = mock_response

    url = "https://hooks.slack.com/services/T/B/X"
    _send_webhook_request(url, "run_complete", "Pipeline complete message", {"run_id": "123"})

    # Ensure urlopen was called
    assert mock_urlopen.call_count == 1
    args, kwargs = mock_urlopen.call_args
    req = args[0]
    assert req.full_url == url
    assert req.headers["Content-type"] == "application/json"

    # Parse payload
    payload = json.loads(req.data.decode("utf-8"))
    assert "blocks" in payload
    assert payload["blocks"][0]["type"] == "header"
    assert "RUN_COMPLETE" in payload["blocks"][0]["text"]["text"]
    assert "Pipeline complete message" in payload["blocks"][1]["text"]["text"]
    assert "run_id" in payload["blocks"][1]["text"]["text"]


@patch("urllib.request.urlopen")
def test_send_discord_webhook(mock_urlopen):
    """Verify Discord webhook payload structure."""
    mock_response = MagicMock()
    mock_response.getcode.return_value = 204
    mock_urlopen.return_value.__enter__.return_value = mock_response

    url = "https://discord.com/api/webhooks/123/abc"
    _send_webhook_request(url, "alert", "VRAM warning message", {"gpu": "RTX 3050"})

    assert mock_urlopen.call_count == 1
    args, kwargs = mock_urlopen.call_args
    req = args[0]
    payload = json.loads(req.data.decode("utf-8"))

    assert "embeds" in payload
    assert payload["embeds"][0]["title"] == "NightmareNet: ALERT"
    assert payload["embeds"][0]["description"] == "VRAM warning message"
    assert payload["embeds"][0]["fields"][0]["name"] == "gpu"
    assert payload["embeds"][0]["fields"][0]["value"] == "RTX 3050"


@patch("urllib.request.urlopen")
def test_send_teams_webhook(mock_urlopen):
    """Verify MS Teams webhook payload structure."""
    mock_response = MagicMock()
    mock_response.getcode.return_value = 200
    mock_urlopen.return_value.__enter__.return_value = mock_response

    url = "https://outlook.office.com/webhook/abc"
    _send_webhook_request(url, "deploy", "Benchmark completed", {"mode": "quick"})

    assert mock_urlopen.call_count == 1
    args, kwargs = mock_urlopen.call_args
    req = args[0]
    payload = json.loads(req.data.decode("utf-8"))

    assert payload["@type"] == "MessageCard"
    assert payload["title"] == "NightmareNet: DEPLOY"
    assert payload["sections"][0]["activityTitle"] == "Benchmark completed"
    assert payload["sections"][0]["facts"][0]["name"] == "mode"
    assert payload["sections"][0]["facts"][0]["value"] == "quick"


@patch("urllib.request.urlopen")
def test_send_generic_webhook(mock_urlopen):
    """Verify generic fallback webhook payload structure."""
    mock_response = MagicMock()
    mock_response.getcode.return_value = 200
    mock_urlopen.return_value.__enter__.return_value = mock_response

    url = "https://example.com/custom-webhook"
    _send_webhook_request(url, "run_complete", "Custom message", {"val": "12"})

    assert mock_urlopen.call_count == 1
    args, kwargs = mock_urlopen.call_args
    req = args[0]
    payload = json.loads(req.data.decode("utf-8"))

    assert payload["event"] == "run_complete"
    assert payload["message"] == "Custom message"
    assert payload["details"] == {"val": "12"}
    assert "text" in payload
    assert "content" in payload


@patch("urllib.request.urlopen")
def test_test_webhook_endpoint(mock_urlopen):
    """Verify the /api/v1/notifications/test-webhook endpoint."""
    mock_response = MagicMock()
    mock_response.getcode.return_value = 200
    mock_urlopen.return_value.__enter__.return_value = mock_response

    response = client.post(
        "/api/v1/notifications/test-webhook",
        json={
            "url": "https://hooks.slack.com/services/test",
            "event_type": "regression_detected",
        },
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert mock_urlopen.call_count == 1


@patch("urllib.request.urlopen")
@patch("time.sleep")
def test_webhook_retry_success(mock_sleep, mock_urlopen):
    """Verify that a transient error (e.g., 429) triggers a retry and succeeds."""
    mock_err_response = urllib.error.HTTPError(
        url="https://example.com/webhook",
        code=429,
        msg="Too Many Requests",
        hdrs=None,
        fp=None,
    )

    # First call raises 429, second succeeds
    mock_urlopen.side_effect = [mock_err_response, MagicMock(read=MagicMock(return_value=b""))]

    url = "https://example.com/webhook"
    _send_webhook_request(url, "run_complete", "Retry test message", {})

    assert mock_urlopen.call_count == 2
    assert mock_sleep.call_count == 1
    mock_sleep.assert_called_with(2)


@patch("urllib.request.urlopen")
@patch("time.sleep")
def test_webhook_retry_fail(mock_sleep, mock_urlopen):
    """Verify that a permanent error (e.g., 400) does not retry."""
    mock_err_response = urllib.error.HTTPError(
        url="https://example.com/webhook",
        code=400,
        msg="Bad Request",
        hdrs=None,
        fp=None,
    )

    mock_urlopen.side_effect = mock_err_response

    url = "https://example.com/webhook"
    import pytest
    with pytest.raises(urllib.error.HTTPError):
        _send_webhook_request(url, "run_complete", "Failure test message", {})

    assert mock_urlopen.call_count == 1
    assert mock_sleep.call_count == 0
