"""L2: Deterministic layout-overlap gate. No AI dependency.

Detects overlapping elements and viewport clipping from scene/layout
box metadata. Accepts structured element dicts or raw synthetic box inputs.

Core:
  - compute_iou: pure-function IoU for two (x1,y1,x2,y2) boxes
  - is_clipped: viewport boundary check for element dict
  - OverlapGate: configurable gate with run() entry point
"""

from __future__ import annotations

from typing import Any

# Type alias: bounding box in pixel coords (x1, y1, x2, y2)
Box = tuple[float, float, float, float]

_DEFAULT_IOU_THRESHOLD = 0.3


def _to_x1y1x2y2(element: dict[str, Any]) -> Box | None:
    """Convert element dict to (x1, y1, x2, y2) pixel box.

    Expects keys: x, y, width, height.  Returns None if any missing.
    """
    x = element.get("x")
    y = element.get("y")
    w = element.get("width")
    h = element.get("height")
    if None in (x, y, w, h):
        return None
    return (float(x), float(y), float(x) + float(w), float(y) + float(h))


def compute_iou(a: Box, b: Box) -> float:
    """Intersection over Union for two pixel-space boxes.

    Returns float in [0.0, 1.0].  0 = no overlap, 1 = complete overlap.
    Edge-touching (zero-area intersection) returns 0.0.
    """
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b

    xi1 = max(ax1, bx1)
    yi1 = max(ay1, by1)
    xi2 = min(ax2, bx2)
    yi2 = min(ay2, by2)

    inter = max(0.0, xi2 - xi1) * max(0.0, yi2 - yi1)
    area_a = (ax2 - ax1) * (ay2 - ay1)
    area_b = (bx2 - bx1) * (by2 - by1)
    union = area_a + area_b - inter

    if union <= 0.0:
        return 0.0
    return inter / union


def is_clipped(element: dict[str, Any], viewport_w: float, viewport_h: float) -> bool:
    """Check if element extends beyond viewport bounds.

    Returns True if any edge is outside [0, 0, viewport_w, viewport_h].
    """
    x = float(element.get("x", 0))
    y = float(element.get("y", 0))
    w = float(element.get("width", 0))
    h = float(element.get("height", 0))
    return x < 0 or y < 0 or x + w > viewport_w or y + h > viewport_h


class OverlapGate:
    """Deterministic layout-overlap review gate.

    Evaluates element overlap (via IoU) and viewport clipping from
    scene/layout box metadata.  Pure Python, no AI or external services.

    Typical usage::

        gate = OverlapGate(iou_threshold=0.3)
        result = gate.run(elements, viewport=(1920, 1080))
        if not result["passed"]:
            for issue in result["issues"]:
                print(issue["type"], issue["detail"])
    """

    def __init__(self, iou_threshold: float = _DEFAULT_IOU_THRESHOLD) -> None:
        if iou_threshold < 0.0 or iou_threshold > 1.0:
            raise ValueError(f"iou_threshold must be in [0, 1], got {iou_threshold}")
        self.iou_threshold = iou_threshold

    # ── Public entry point ────────────────────────────────────────────────

    def run(
        self,
        elements: list[dict[str, Any]],
        viewport: tuple[int, int] = (1920, 1080),
    ) -> dict[str, Any]:
        """Run overlap and clipping detection.

        Args:
            elements: List of element dicts.  Each may contain ``id`` (label),
                ``x``, ``y``, ``width``, ``height``.  Entries missing coords
                are silently skipped.
            viewport: ``(width, height)`` of the output canvas.

        Returns:
            Dict with keys ``issues`` (list of issue dicts) and ``passed``.
        """
        viewport_w, viewport_h = viewport
        if viewport_w <= 0 or viewport_h <= 0:
            return {
                "issues": [
                    {
                        "type": "invalid_viewport",
                        "detail": f"Viewport {viewport} has non-positive dimension",
                        "severity": "high",
                    }
                ],
                "passed": False,
            }

        issues: list[dict[str, Any]] = []

        # 1. Check each element for viewport clipping
        for i, elem in enumerate(elements):
            elem_id: str | int = elem.get("id", i)
            if is_clipped(elem, viewport_w, viewport_h):
                issues.append({
                    "element": elem_id,
                    "type": "clipped",
                    "detail": f"Element #{elem_id} extends beyond viewport",
                    "severity": "medium",
                })

        # 2. Pairwise IoU overlap detection
        boxes: list[tuple[Box, str | int]] = []
        for i, elem in enumerate(elements):
            box = _to_x1y1x2y2(elem)
            if box is not None:
                boxes.append((box, elem.get("id", i)))

        for idx_a in range(len(boxes)):
            box_a, id_a = boxes[idx_a]
            for idx_b in range(idx_a + 1, len(boxes)):
                box_b, id_b = boxes[idx_b]
                iou = compute_iou(box_a, box_b)
                if iou > self.iou_threshold:
                    issues.append({
                        "element_a": id_a,
                        "element_b": id_b,
                        "type": "overlap",
                        "iou": round(iou, 4),
                        "threshold": self.iou_threshold,
                        "detail": (
                            f"IoU {iou:.4f} between elements #{id_a} and #{id_b} "
                            f"exceeds threshold {self.iou_threshold}"
                        ),
                        "severity": "high" if iou >= 0.8 else "medium",
                    })

        return {"issues": issues, "passed": len(issues) == 0}

    # ── Synthetic / raw-box entry point ───────────────────────────────────

    @staticmethod
    def compute_overlaps(
        boxes: list[tuple[float, float, float, float]],
        threshold: float = _DEFAULT_IOU_THRESHOLD,
    ) -> list[dict[str, Any]]:
        """Compute pairwise overlaps for a list of raw pixel boxes.

        Each box is ``(x1, y1, x2, y2)``.  Returns issues list (no viewport
        check — use :meth:`run` for that).  Useful for synthetic or
        pre-normalized inputs.
        """
        issues: list[dict[str, Any]] = []
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                iou = compute_iou(boxes[i], boxes[j])
                if iou > threshold:
                    issues.append({
                        "index_a": i,
                        "index_b": j,
                        "type": "overlap",
                        "iou": round(iou, 4),
                        "threshold": threshold,
                        "detail": (
                            f"IoU {iou:.4f} between box #{i} and box #{j} "
                            f"exceeds threshold {threshold}"
                        ),
                        "severity": "high" if iou >= 0.8 else "medium",
                    })
        return issues
