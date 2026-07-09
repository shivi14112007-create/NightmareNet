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

        mock_trigger.assert_not_called()
