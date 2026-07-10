"""AlphaGate — deterministic alpha/overlay validation for transparent scenes.

Checks scene payload metadata for consistent alpha-channel configuration.
No AI dependency. Pure Python, operates on structured props.

Scenarios (overlay-cta, lower-third overlays):
  - ``alpha=True`` or ``include_transparent_bg=True`` requires that
    ``background_opacity`` or ``bg_opacity`` be < 1.0.
  - Reports inconsistency when alpha is enabled but background opacity
    is fully opaque (1.0 or missing with default opaque).
"""

from __future__ import annotations

from typing import Any

_DEFAULT_BG_OPACITY = 1.0


def _extract_alpha_flag(payload: dict[str, Any]) -> bool:
    """Return True if payload requests alpha/transparency."""
    return bool(
        payload.get("alpha", False)
        or payload.get("include_transparent_bg", False)
        or payload.get("transparent", False)
    )


def _extract_bg_opacity(payload: dict[str, Any]) -> float:
    """Return background opacity from payload, falling back to default."""
    raw = payload.get("background_opacity")
    if raw is None:
        raw = payload.get("bg_opacity")
    if raw is None:
        return _DEFAULT_BG_OPACITY
    return float(raw)


class AlphaGate:
    """Deterministic alpha/overlay review gate.

    Validates that scene payload metadata for transparent scenes is
    internally consistent.  Pure Python, no AI or video I/O required.

    Typical usage::

        gate = AlphaGate()
        result = gate.run({"alpha": True, "background_opacity": 0.0})
        if not result["passed"]:
            for issue in result["issues"]:
                print(issue["type"], issue["detail"])
    """

    # ── Public entry point ────────────────────────────────────────────────

    @staticmethod
    def run(
        scene_payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Run alpha-configuration consistency checks.

        Args:
            scene_payload: Dict of scene props (from recipe payload or
                ``SceneNode.payload_dict()``).  Supported keys:
                ``alpha``, ``include_transparent_bg``, ``transparent``,
                ``background_opacity``, ``bg_opacity``.

        Returns:
            Dict with keys ``issues`` (list of issue dicts) and ``passed``.
        """
        issues: list[dict[str, Any]] = []

        alpha_requested = _extract_alpha_flag(scene_payload)
        bg_opacity = _extract_bg_opacity(scene_payload)

        # 1. If alpha requested, background must not be fully opaque
        if alpha_requested and bg_opacity >= 1.0:
            issues.append({
                "type": "alpha_requested_opaque_bg",
                "detail": (
                    "Alpha/transparency requested but background_opacity "
                    f"is {bg_opacity:.1f} (must be < 1.0 for visible overlay)"
                ),
                "severity": "high",
            })

        # 2. If alpha NOT requested, warn if background is transparent
        if not alpha_requested and bg_opacity < 1.0:
            issues.append({
                "type": "transparent_bg_without_alpha",
                "detail": (
                    f"Background opacity is {bg_opacity:.1f} but alpha "
                    "channel is not enabled — transparent areas may render "
                    "as opaque black"
                ),
                "severity": "medium",
            })

        # 3. If alpha requested, warn if bg_opacity is negative (invalid)
        if alpha_requested and bg_opacity < 0.0:
            issues.append({
                "type": "negative_bg_opacity",
                "detail": (
                    f"Background opacity is {bg_opacity:.1f} — "
                    "negative values are invalid"
                ),
                "severity": "high",
            })

        return {"issues": issues, "passed": len(issues) == 0}
