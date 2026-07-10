"""DualChartAxisGate — deterministic axis-sanity checks for dual-chart scenes.

Validates that x-labels, bar_data, and line_data are consistent and non-empty
for dual-chart scenes.  No AI dependency.

Scenarios (dual-chart):
  - ``x_labels`` should be non-empty when present.
  - If ``dual_axes`` is enabled, secondary axis should have data.
  - Data series lengths should be compatible with label count.
"""

from __future__ import annotations

from typing import Any


class DualChartAxisGate:
    """Deterministic dual-chart axis-sanity review gate.

    Checks that chart axis metadata (labels, data arrays) is internally
    consistent.  Pure Python, no AI or video I/O.

    Typical usage::

        gate = DualChartAxisGate()
        result = gate.run({
            "x_labels": ["Jan", "Feb", "Mar"],
            "bar_data": [10, 20, 15],
        })
        if not result["passed"]:
            for issue in result["issues"]:
                print(issue["type"], issue["detail"])
    """

    # ── Public entry point ────────────────────────────────────────────────

    @staticmethod
    def run(
        scene_payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Run axis-sanity checks on chart scene payload.

        Args:
            scene_payload: Dict of scene props.  Supported keys:
                ``x_labels``, ``bar_data``, ``bar_values``, ``line_data``,
                ``dual_axes``, ``secondary_label``, ``primary_label``,
                ``y_label``, ``x_label``.

        Returns:
            Dict with keys ``issues`` (list of issue dicts) and ``passed``.
        """
        issues: list[dict[str, Any]] = []

        x_labels = scene_payload.get("x_labels")
        bar_data = scene_payload.get("bar_data") or scene_payload.get("bar_values")
        line_data = scene_payload.get("line_data")
        dual_axes = scene_payload.get("dual_axes", False)

        # 1. x_labels should be non-empty when present
        if x_labels is not None:
            if not isinstance(x_labels, list):
                issues.append({
                    "type": "x_labels_not_a_list",
                    "detail": f"x_labels must be a list, got {type(x_labels).__name__}",
                    "severity": "high",
                })
            elif len(x_labels) == 0:
                issues.append({
                    "type": "x_labels_empty",
                    "detail": "x_labels is an empty list — chart may have no ticks",
                    "severity": "high",
                })
            elif any(not isinstance(lbl, str) or lbl.strip() == "" for lbl in x_labels):
                issues.append({
                    "type": "x_labels_blank_entry",
                    "detail": "One or more x_labels entries are blank/whitespace-only",
                    "severity": "medium",
                })

        # 2. At least one data series must be present
        has_bar = isinstance(bar_data, list) and len(bar_data) > 0
        has_line = isinstance(line_data, list) and len(line_data) > 0

        if not has_bar and not has_line:
            issues.append({
                "type": "no_chart_data",
                "detail": (
                    "No non-empty data series found — "
                    "bar_data and line_data are both missing or empty"
                ),
                "severity": "high",
            })

        # 3. If dual_axes is enabled, secondary data (line_data) should exist
        if dual_axes and not has_line:
            issues.append({
                "type": "dual_axes_no_secondary",
                "detail": (
                    "dual_axes is enabled but line_data (secondary axis) "
                    "is missing or empty"
                ),
                "severity": "high",
            })

        # 4. Data lengths should match x_labels if both present
        if x_labels is not None and isinstance(x_labels, list) and len(x_labels) > 0:
            label_count = len(x_labels)
            if has_bar and len(bar_data) != label_count:
                issues.append({
                    "type": "data_label_mismatch",
                    "detail": (
                        f"bar_data length ({len(bar_data)}) does not match "
                        f"x_labels length ({label_count})"
                    ),
                    "severity": "medium",
                    "bar_count": len(bar_data),
                    "label_count": label_count,
                })
            if has_line and len(line_data) != label_count:
                issues.append({
                    "type": "data_label_mismatch",
                    "detail": (
                        f"line_data length ({len(line_data)}) does not match "
                        f"x_labels length ({label_count})"
                    ),
                    "severity": "medium",
                    "line_count": len(line_data),
                    "label_count": label_count,
                })

        # 5. Axis labels should be non-empty when present
        for axis_key, axis_name in [
            ("x_label", "X"), ("y_label", "Y"),
            ("primary_label", "primary"), ("secondary_label", "secondary"),
        ]:
            val = scene_payload.get(axis_key)
            if val is not None and (not isinstance(val, str) or val.strip() == ""):
                issues.append({
                    "type": "axis_label_empty",
                    "detail": f"{axis_name} axis label ({axis_key}) is empty",
                    "severity": "low",
                    "axis_key": axis_key,
                })

        return {"issues": issues, "passed": len(issues) == 0}
