"""Webhook notification dispatcher and GPU monitoring utilities for NightmareNet."""

from __future__ import annotations

import json
import logging
import urllib.request
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def trigger_webhook(
    config: dict,
    event_type: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """Send webhook notifications to configured endpoints based on event_type.

    Args:
        config: Full configuration dictionary containing notifications.webhooks.
        event_type: One of 'run_complete', 'regression_detected', 'alert', 'deploy'.
        message: The headline text/message.
        details: A dictionary of key-value details to include.
    """
    webhooks = config.get("notifications", {}).get("webhooks", [])
    if not webhooks:
        return

    for webhook in webhooks:
        url = webhook.get("url")
        if not url:
            continue
        events = webhook.get("events")
        # If events is not specified, default to all event types
        if events is not None and event_type not in events:
            continue

        try:
            _send_webhook_request(url, event_type, message, details or {})
        except Exception as e:
            logger.exception("Failed to send webhook notification to %s: %s", url, e)


def _send_webhook_request(url: str, event_type: str, message: str, details: Dict[str, Any]) -> None:
    # Build payload based on URL/destination
    payload: Dict[str, Any] = {}

    details_str = ""
    if details:
        details_str = "\n".join(f"- **{k}**: {v}" for k, v in details.items())

    if "slack.com" in url:
        payload = {
            "text": f"*{message}*",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"NightmareNet: {event_type.upper()}",
                        "emoji": True,
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{message}\n\n{details_str}" if details_str else message,
                    },
                },
            ],
        }
    elif "discord.com" in url or "discordapp.com" in url:
        payload = {
            "embeds": [
                {
                    "title": f"NightmareNet: {event_type.upper()}",
                    "description": message,
                    "color": (
                        16738304
                        if event_type in ("alert", "regression_detected")
                        else 3447003
                    ),
                    "fields": [
                        {"name": k, "value": str(v), "inline": True} for k, v in details.items()
                    ]
                    if details
                    else [],
                }
            ]
        }
    elif "office.com" in url or "microsoft.com" in url or "webhook.office.com" in url:
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": (
                "FF0000"
                if event_type in ("alert", "regression_detected")
                else "0078D7"
            ),
            "summary": message,
            "title": f"NightmareNet: {event_type.upper()}",
            "sections": [
                {
                    "activityTitle": message,
                    "facts": [{"name": k, "value": str(v)} for k, v in details.items()]
                    if details
                    else [],
                    "markdown": True,
                }
            ],
        }
    else:
        # Generic compatibility payload
        payload = {
            "event": event_type,
            "message": message,
            "details": details,
            "text": f"{message}\n\n{details_str}" if details_str else message,
            "content": f"**NightmareNet: {event_type.upper()}**\n{message}\n\n{details_str}"
            if details_str
            else message,
        }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "NightmareNet-Webhook/0.2.0"},
    )
    with urllib.request.urlopen(req, timeout=5) as response:
        response.read()


def check_vram_pressure(device_index: int = 0, threshold: float = 0.85) -> bool:
    """Check if the GPU VRAM usage ratio exceeds a threshold.

    Args:
        device_index: Index of the CUDA device.
        threshold: Memory usage ratio threshold (default 0.85).

    Returns:
        True if the usage is above the threshold, False otherwise.
    """
    try:
        import torch

        if not torch.cuda.is_available():
            return False
        # Get free and total memory from CUDA (in bytes)
        free, total = torch.cuda.mem_get_info(device_index)
        used = total - free
        ratio = used / total
        return ratio > threshold
    except Exception:
        return False
