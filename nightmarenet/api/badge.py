"""Robustness badge endpoints (shields.io-style).

Renders a small SVG badge showing a robustness score in the standard
"label | value" layout that drop-cleanly into a GitHub README, plus a
JSON variant for clients that want to render their own badge.

Mounted at ``/api/v1/badge`` by :mod:`nightmarenet.api.app`. The route
intentionally has no API-key requirement (badges are embedded on public
READMEs) and ships a generous ``Cache-Control`` so CDNs can absorb the
traffic.
"""

import json
import logging
from typing import Tuple
from xml.sax.saxutils import escape

logger = logging.getLogger(__name__)

try:
    from fastapi import APIRouter, HTTPException
    from fastapi.responses import Response
except ImportError as e:
    raise ImportError(
        "FastAPI dependencies not installed. Install with: pip install nightmarenet[api]"
    ) from e


router = APIRouter(prefix="/api/v1/badge", tags=["Badge"])


# Shields.io-style colour scale, ordered from best → worst.
_BANDS: Tuple[Tuple[float, str, str], ...] = (
    (0.90, "#22c55e", "elite"),
    (0.75, "#84cc16", "strong"),
    (0.60, "#eab308", "fair"),
    (0.40, "#f97316", "weak"),
    (0.00, "#ef4444", "critical"),
)

_LABEL_TEXT = "robustness"
# Pixel widths sized for Verdana 11px. Conservative; matches shields.io
# rendering closely enough that it sits cleanly next to other badges.
_LABEL_WIDTH = 78
_VALUE_WIDTH = 46
_TOTAL_WIDTH = _LABEL_WIDTH + _VALUE_WIDTH
_HEIGHT = 20
_CACHE_HEADER = "public, max-age=300"
_SVG_CONTENT_TYPE = "image/svg+xml; charset=utf-8"


def _classify(score: float) -> Tuple[str, str]:
    """Return ``(color, label)`` for a normalised score in ``[0, 1]``."""
    for threshold, color, label in _BANDS:
        if score >= threshold:
            return color, label
    return _BANDS[-1][1], _BANDS[-1][2]


def _validate_score(score: float) -> float:
    """Raise 400 if the score is outside ``[0, 1]`` (or NaN)."""
    try:
        s = float(score)
    except (TypeError, ValueError) as e:
        raise HTTPException(
            status_code=400, detail="score must be a real number in [0, 1]"
        ) from e
    # NaN comparisons always return False; trap explicitly.
    if not (s == s):  # noqa: PLR0124
        raise HTTPException(
            status_code=400, detail="score must be a real number in [0, 1]"
        )
    if s < 0.0 or s > 1.0:
        raise HTTPException(
            status_code=400,
            detail=f"score must be in [0, 1]; got {s}",
        )
    return s


def _render_svg(score: float, color: str) -> str:
    """Render the badge as an SVG string. Inputs are trusted (already validated)."""
    score_text = f"{score:.2f}"
    label_safe = escape(_LABEL_TEXT)
    value_safe = escape(score_text)
    color_safe = escape(color)

    label_cx = _LABEL_WIDTH / 2
    value_cx = _LABEL_WIDTH + _VALUE_WIDTH / 2
    # Render text twice (shadow + main) for the classic shields.io
    # legibility trick — a 1px-down dark shadow improves contrast on
    # GitHub's light *and* dark themes.
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{_TOTAL_WIDTH}" height="{_HEIGHT}" '
        f'role="img" aria-label="{label_safe}: {value_safe}">'
        f"<title>{label_safe}: {value_safe}</title>"
        f'<linearGradient id="s" x2="0" y2="100%">'
        f'<stop offset="0" stop-color="#bbb" stop-opacity=".1"/>'
        f'<stop offset="1" stop-opacity=".1"/>'
        f"</linearGradient>"
        f'<clipPath id="r">'
        f'<rect width="{_TOTAL_WIDTH}" height="{_HEIGHT}" rx="3" fill="#fff"/>'
        f"</clipPath>"
        f'<g clip-path="url(#r)">'
        f'<rect width="{_LABEL_WIDTH}" height="{_HEIGHT}" fill="#555"/>'
        f'<rect x="{_LABEL_WIDTH}" width="{_VALUE_WIDTH}" '
        f'height="{_HEIGHT}" fill="{color_safe}"/>'
        f'<rect width="{_TOTAL_WIDTH}" height="{_HEIGHT}" fill="url(#s)"/>'
        f"</g>"
        f'<g fill="#fff" text-anchor="middle" '
        f'font-family="Verdana,Geneva,DejaVu Sans,sans-serif" '
        f'text-rendering="geometricPrecision" font-size="11">'
        f'<text x="{label_cx}" y="15" fill="#010101" '
        f'fill-opacity=".3">{label_safe}</text>'
        f'<text x="{label_cx}" y="14">{label_safe}</text>'
        f'<text x="{value_cx}" y="15" fill="#010101" '
        f'fill-opacity=".3">{value_safe}</text>'
        f'<text x="{value_cx}" y="14">{value_safe}</text>'
        f"</g>"
        f"</svg>"
    )


@router.get(
    "/{score}.svg",
    summary="Render a robustness badge as SVG",
    responses={
        200: {"content": {"image/svg+xml": {}}},
        400: {"description": "Score must be a real number in [0, 1]"},
    },
)
async def badge_svg(score: float) -> Response:
    """Render a shields.io-style SVG badge for ``score`` ∈ ``[0, 1]``."""
    s = _validate_score(score)
    color, _label = _classify(s)
    svg = _render_svg(s, color)
    return Response(
        content=svg,
        media_type=_SVG_CONTENT_TYPE,
        headers={"Cache-Control": _CACHE_HEADER},
    )


@router.get(
    "/{score}.json",
    summary="Return badge metadata as JSON",
    responses={
        200: {"description": "Badge metadata"},
        400: {"description": "Score must be a real number in [0, 1]"},
    },
)
async def badge_json(score: float) -> Response:
    """Return JSON describing the badge so clients can render their own."""
    s = _validate_score(score)
    color, label = _classify(s)
    payload = {
        "score": round(s, 4),
        "color": color,
        "label": label,
        "message": f"{s:.2f}",
    }
    return Response(
        content=json.dumps(payload),
        media_type="application/json",
        headers={"Cache-Control": _CACHE_HEADER},
    )
