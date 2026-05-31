"""Tests for WebSocket live pipeline progress endpoint."""

import json
from unittest.mock import MagicMock, patch

import pytest

from nightmarenet.api.app import app

try:
    from starlette.testclient import TestClient
    from starlette.websockets import WebSocketDisconnect
except ImportError:
    pytest.skip("starlette not installed", allow_module_level=True)


@pytest.fixture
def client():
    return TestClient(app)


class TestWebSocketPipelineProgress:
    """Tests for /ws/runs/{run_id}."""

    def test_unknown_run_id_returns_error(self, client):
        with client.websocket_connect("/ws/runs/nonexistent-run") as ws:
            data = ws.receive_json()
            assert "error" in data
            assert "not found" in data["error"]

    def test_completed_run_sends_metrics_and_complete(self, client):
        mock_runner = MagicMock()
        mock_runner.status.return_value = {
            "run_id": "test-123",
            "is_running": False,
            "status": "complete",
            "progress_pct": 100.0,
            "current_cycle": 1,
            "total_cycles": 1,
            "current_phase": "done",
            "has_report": True,
        }

        with patch(
            "nightmarenet.pipeline_runner.get_runner",
            return_value=mock_runner,
        ):
            with client.websocket_connect("/ws/runs/test-123") as ws:
                data = ws.receive_json()
                assert data["run_id"] == "test-123"
                assert data["is_running"] is False

                complete_evt = ws.receive_json()
                assert complete_evt["event"] == "complete"

    def test_running_pipeline_streams_progress(self, client):
        call_count = [0]

        def mock_status():
            call_count[0] += 1
            if call_count[0] >= 3:
                return {
                    "run_id": "run-456",
                    "is_running": False,
                    "status": "complete",
                    "progress_pct": 100.0,
                    "current_cycle": 1,
                    "total_cycles": 1,
                    "current_phase": "done",
                    "has_report": False,
                }
            return {
                "run_id": "run-456",
                "is_running": True,
                "status": "running",
                "progress_pct": call_count[0] * 33.0,
                "current_cycle": 1,
                "total_cycles": 1,
                "current_phase": "wake",
                "has_report": False,
            }

        mock_runner = MagicMock()
        mock_runner.status.side_effect = mock_status

        with patch(
            "nightmarenet.pipeline_runner.get_runner",
            return_value=mock_runner,
        ):
            with client.websocket_connect("/ws/runs/run-456") as ws:
                msg1 = ws.receive_json()
                assert msg1["is_running"] is True
                assert msg1["progress_pct"] == 33.0

                msg2 = ws.receive_json()
                assert msg2["is_running"] is True
                assert msg2["progress_pct"] == 66.0

                msg3 = ws.receive_json()
                assert msg3["is_running"] is False

                complete_evt = ws.receive_json()
                assert complete_evt["event"] == "complete"
