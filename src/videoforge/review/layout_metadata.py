"""Layout metadata model and converters for the overlap gate.

Provides a typed schema for scene layout elements and bidirectional
converters between the model and the overlap gate's dict/Box interfaces.

Typical data flow::

    SceneNode payload  ──>  LayoutMetadata  ──>  OverlapGate.run()
                               │
                               └──>  OverlapGate.compute_overlaps(boxes)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from videoforge.review.overlap_gate import Box

# ── Model ──────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class LayoutElement:
    """Single positioned element in the video layout.

    Fields mirror what renderers emit and the overlap gate consumes.
    ``type_hint`` is an opaque label (e.g. ``"text"``, ``"image"``,
    ``"shape"``, ``"code_block"``) that downstream gates may use for
    category-specific thresholding.
    """

    id: str
    x: float
    y: float
    width: float
    height: float
    z_index: int = 0
    type_hint: str = "shape"


@dataclass(frozen=True)
class LayoutMetadata:
    """Complete layout description for one scene/viewport.

    Carries viewport dimensions alongside elements so the overlap gate
    can validate both pairwise overlap and viewport clipping.
    """

    elements: tuple[LayoutElement, ...]
    viewport_w: float = 1920.0
    viewport_h: float = 1080.0


# ── Model → overlap gate converters ────────────────────────────────────────────


def element_to_box(elem: LayoutElement) -> Box:
    """Convert LayoutElement to (x1, y1, x2, y2) Box tuple."""
    x, y, w, h = float(elem.x), float(elem.y), float(elem.width), float(elem.height)
    return (x, y, x + w, y + h)


def element_to_dict(elem: LayoutElement) -> dict[str, Any]:
    """Convert LayoutElement to dict compatible with OverlapGate.run()."""
    return {
        "id": elem.id,
        "x": elem.x,
        "y": elem.y,
        "width": elem.width,
        "height": elem.height,
        "z_index": elem.z_index,
        "type_hint": elem.type_hint,
    }


def layout_metadata_to_boxes(meta: LayoutMetadata) -> list[Box]:
    """Convert LayoutMetadata to a list of Box tuples (no viewport)."""
    return [element_to_box(e) for e in meta.elements]


def layout_metadata_to_element_dicts(meta: LayoutMetadata) -> list[dict[str, Any]]:
    """Convert LayoutMetadata to list of dicts for OverlapGate.run()."""
    return [element_to_dict(e) for e in meta.elements]


# ── Dict / JSON → model converters ────────────────────────────────────────────


def dict_to_element(d: dict[str, Any]) -> LayoutElement | None:
    """Convert a dict with ``x``, ``y``, ``width``, ``height`` to LayoutElement.

    Returns ``None`` if any required positional key is missing.
    Non-float values are coerced via ``float()``.
    """
    x = d.get("x")
    y = d.get("y")
    w = d.get("width")
    h = d.get("height")
    if None in (x, y, w, h):
        return None
    return LayoutElement(
        id=str(d.get("id", "")),
        x=float(x),
        y=float(y),
        width=float(w),
        height=float(h),
        z_index=int(d.get("z_index", 0)),
        type_hint=str(d.get("type_hint", "shape")),
    )


def dicts_to_layout_metadata(
    element_dicts: list[dict[str, Any]],
    viewport_w: float = 1920.0,
    viewport_h: float = 1080.0,
) -> LayoutMetadata:
    """Convert list of element dicts to LayoutMetadata.

    Dicts missing required keys (x, y, width, height) are silently skipped.
    """
    elements: list[LayoutElement] = []
    for d in element_dicts:
        elem = dict_to_element(d)
        if elem is not None:
            elements.append(elem)
    return LayoutMetadata(
        elements=tuple(elements),
        viewport_w=viewport_w,
        viewport_h=viewport_h,
    )


# ── SceneNode payload converter ────────────────────────────────────────────────


def scene_payload_to_layout_metadata(
    payload_str: str,
    default_viewport_w: float = 1920.0,
    default_viewport_h: float = 1080.0,
) -> LayoutMetadata:
    """Convert SceneNode JSON payload string to LayoutMetadata.

    Extracts element layout data from payload's ``"elements"`` key
    (if present) and viewport from ``"width"`` / ``"height"`` keys.
    Elements missing positional data are silently skipped.
    """
    payload: dict[str, Any] = json.loads(payload_str)
    viewport_w = float(payload.get("width", default_viewport_w))
    viewport_h = float(payload.get("height", default_viewport_h))
    raw_elements = payload.get("elements", [])
    if not isinstance(raw_elements, list):
        raw_elements = []
    return dicts_to_layout_metadata(
        raw_elements,
        viewport_w=viewport_w,
        viewport_h=viewport_h,
    )
