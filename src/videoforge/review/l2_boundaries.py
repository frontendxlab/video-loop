from __future__ import annotations


class L2Boundaries:
    def run(self, video_path: str, input_props: dict | None = None) -> dict:
        if input_props is None:
            return {
                "issues": [],
                "passed": True,
                "note": "No input_props provided, skipping boundary check",
            }

        issues: list[dict] = []
        elements = input_props.get("elements", [])

        for i, a in enumerate(elements):
            box_a = self._get_box(a)
            if box_a is None:
                continue

            if not self._in_viewport(box_a, input_props):
                issues.append({
                    "element": a.get("id", i),
                    "issue": "clipped",
                    "detail": "Element extends beyond viewport",
                })

            for j, b in enumerate(elements):
                if i >= j:
                    continue
                box_b = self._get_box(b)
                if box_b is None:
                    continue
                iou = self._iou(box_a, box_b)
                if iou > 0.3:
                    issues.append({
                        "element_a": a.get("id", i),
                        "element_b": b.get("id", j),
                        "issue": "overlap",
                        "iou": round(iou, 3),
                        "detail": f"IoU {iou:.3f} exceeds threshold of 0.3",
                    })

        return {
            "issues": issues,
            "passed": len(issues) == 0,
        }

    @staticmethod
    def _get_box(element: dict) -> tuple[int, int, int, int] | None:
        x = element.get("x")
        y = element.get("y")
        w = element.get("width")
        h = element.get("height")
        if None in (x, y, w, h):
            return None
        return (x, y, x + w, y + h)

    @staticmethod
    def _in_viewport(box: tuple[int, int, int, int], props: dict) -> bool:
        vw = props.get("width", 1920)
        vh = props.get("height", 1080)
        x1, y1, x2, y2 = box
        return x1 >= 0 and y1 >= 0 and x2 <= vw and y2 <= vh

    @staticmethod
    def _iou(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
        ax1, ay1, ax2, ay2 = a
        bx1, by1, bx2, by2 = b

        xi1 = max(ax1, bx1)
        yi1 = max(ay1, by1)
        xi2 = min(ax2, bx2)
        yi2 = min(ay2, by2)

        inter = max(0, xi2 - xi1) * max(0, yi2 - yi1)

        area_a = (ax2 - ax1) * (ay2 - ay1)
        area_b = (bx2 - bx1) * (by2 - by1)

        union = area_a + area_b - inter
        if union == 0:
            return 0.0

        return inter / union
