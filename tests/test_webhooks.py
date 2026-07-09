"""Tests for webhook validation and blocked internal IPs."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from nightmarenet.utils.webhooks import validate_webhook_url


class TestValidateWebhookUrl:
    def test_rejects_http(self):
        assert validate_webhook_url("http://hooks.slack.com/services/T/B/x") is False

    def test_rejects_non_allowlisted_domain(self):
        assert validate_webhook_url("https://evil.com/hook") is False

    def test_rejects_slack_without_services_path(self):
        assert validate_webhook_url("https://hooks.slack.com/other/path") is False

    def test_accepts_slack_with_services_path(self):
        with patch("socket.getaddrinfo") as mock_res:
            mock_res.return_value = [(2, 1, 6, "", ("44.228.100.1", 0))]
            assert validate_webhook_url(
                "https://hooks.slack.com/services/T123/B456/abc"
            ) is True

    def test_accepts_discord(self):
        with patch("socket.getaddrinfo") as mock_res:
            mock_res.return_value = [(2, 1, 6, "", ("162.159.128.1", 0))]
            assert validate_webhook_url(
                "https://discord.com/api/webhooks/123/token"
            ) is True

    def test_rejects_internal_ip_loopback(self):
        with patch("socket.getaddrinfo") as mock_res:
            mock_res.return_value = [(2, 1, 6, "", ("127.0.0.1", 0))]
            assert validate_webhook_url(
                "https://hooks.slack.com/services/T123/B456/abc"
            ) is False

    def test_rejects_internal_ip_private(self):
        with patch("socket.getaddrinfo") as mock_res:
            mock_res.return_value = [(2, 1, 6, "", ("192.168.1.1", 0))]
            assert validate_webhook_url(
                "https://hooks.slack.com/services/T123/B456/abc"
            ) is False

    def test_rejects_if_any_resolved_address_is_private(self):
        with patch("socket.getaddrinfo") as mock_res:
            mock_res.return_value = [
                (2, 1, 6, "", ("44.228.100.1", 0)),
                (2, 1, 6, "", ("10.0.0.1", 0)),
            ]
            assert validate_webhook_url(
                "https://hooks.slack.com/services/T123/B456/abc"
            ) is False

    def test_rejects_dns_failure(self):
        import socket as _socket

        with patch("socket.getaddrinfo", side_effect=_socket.gaierror("fail")):
            assert validate_webhook_url(
                "https://hooks.slack.com/services/T123/B456/abc"
            ) is False


class TestWebhookEndpointBlocksInternalIP:
    """Regression test: the /api/v1/webhooks/test endpoint must reject
    URLs that resolve to internal IPs BEFORE dispatching."""

    @pytest.fixture
    def client(self):
        from starlette.testclient import TestClient

        from nightmarenet.api.app import app
        return TestClient(app)

    def test_rejects_internal_ip_with_400(self, client, monkeypatch):
        monkeypatch.delenv("NIGHTMARENET_API_KEY", raising=False)

        with patch("socket.getaddrinfo") as mock_res:
            mock_res.return_value = [(2, 1, 6, "", ("127.0.0.1", 0))]
            response = client.post(
                "/api/v1/notifications/test-webhook",
                json={
                    "url": "https://hooks.slack.com/services/T/B/x",
                    "event_type": "run_complete",
                },
            )

        assert response.status_code == 400
        assert "Invalid webhook URL" in response.json()["detail"]

    def test_dispatch_not_called_for_blocked_url(self, client, monkeypatch):
        monkeypatch.delenv("NIGHTMARENET_API_KEY", raising=False)

        with patch("socket.getaddrinfo") as mock_res:
            mock_res.return_value = [(2, 1, 6, "", ("10.0.0.1", 0))]
            with patch(
                "nightmarenet.utils.webhooks.trigger_webhook"
            ) as mock_trigger:
                client.post(
                    "/api/v1/notifications/test-webhook",
                    json={
                        "url": "https://hooks.slack.com/services/T/B/x",
                        "event_type": "alert",
                    },
                )

<<<<<<< HEAD
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
=======
        mock_trigger.assert_not_called()
>>>>>>> upstream/main
