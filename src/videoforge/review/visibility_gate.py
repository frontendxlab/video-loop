"""VisibilityGate — deterministic nonblank/basic visibility check for 3D scenes.

Checks that 3D scene payloads (map3d, three-scene, 3d-ranking, etc.) contain
non-empty data arrays required to produce visible output.  No AI dependency.

Scenarios:
  - ``map3d`` / ``three-scene``: expects ``objects``, ``route_coords``, or
    ``geometry`` non-empty.
  - ``3d-ranking`` / ``chart``: expects ``data_points``, ``bar_values``, or
    ``series`` non-empty.
"""

from __future__ import annotations

from typing import Any


def _collect_data_arrays(payload: dict[str, Any]) -> list[tuple[str, list]]:
    """Return [(key, value), ...] for known data array keys that are lists."""
    known_keys = [
        "objects", "route_coords", "geometry", "data_points",
        "bar_values", "bar_data", "series", "line_data",
        "points", "coordinates", "vertices", "nodes",
    ]
    result: list[tuple[str, list]] = []
    for key in known_keys:
        val = payload.get(key)
        if isinstance(val, list):
            result.append((key, val))
    return result


class VisibilityGate:
    """Deterministic 3D / chart visibility review gate.

    Checks that scene payloads contain the data arrays needed to produce
    visible rendered output.  Pure Python, no AI or video I/O.

    Typical usage::

        gate = VisibilityGate()
        result = gate.run({"data_points": [1, 2, 3], "bar_values": [10, 20]})
        if not result["passed"]:
            for issue in result["issues"]:
                print(issue["type"], issue["detail"])
    """

    # ── Public entry point ────────────────────────────────────────────────

    @staticmethod
    def run(
        scene_payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Run basic visibility checks on scene payload.

        Args:
            scene_payload: Dict of scene props.  Supported keys for data
                arrays: ``objects``, ``route_coords``, ``geometry``,
                ``data_points``, ``bar_values``, ``bar_data``, ``series``,
                ``line_data``, ``points``, ``coordinates``, ``vertices``,
                ``nodes``.

        Returns:
            Dict with keys ``issues`` (list of issue dicts) and ``passed``.
        """
        issues: list[dict[str, Any]] = []

        arrays = _collect_data_arrays(scene_payload)

        # 1. No data arrays found at all — likely blank scene
        if not arrays:
            issues.append({
                "type": "no_data_arrays",
                "detail": (
                    "No known data arrays (objects, route_coords, "
                    "data_points, bar_values, series, etc.) found in "
                    "scene payload — scene may render blank"
                ),
                "severity": "high",
            })
            return {"issues": issues, "passed": False}

        # 2. Check each array for emptiness
        empty_arrays: list[str] = []
        for key, val in arrays:
            if len(val) == 0:
                empty_arrays.append(key)

        if empty_arrays:
            issues.append({
                "type": "empty_data_arrays",
                "detail": (
                    "Data arrays are empty: "
                    f"{', '.join(sorted(empty_arrays))}"
                ),
                "severity": "high",
                "empty_keys": sorted(empty_arrays),
            })

        # 3. Check for suspiciously small payloads (< 3 items in primary array)
        primary_arrays = [v for _, v in arrays if len(v) > 0]
        if primary_arrays:
            smallest = min(len(v) for v in primary_arrays)
            if smallest < 2:
                issues.append({
                    "type": "sparse_data",
                    "detail": (
                        f"Smallest data array has only {smallest} item(s) "
                        "- scene may lack visual richness"
                    ),
                    "severity": "low",
                    "min_count": smallest,
                })

        return {"issues": issues, "passed": len(issues) == 0}
