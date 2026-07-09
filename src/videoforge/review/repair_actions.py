"""Deterministic repair actions for L0 review failures.

Maps L0 issue types to concrete rerender actions. Caller (pipeline / MCP tool)
provides a hook to execute the actual rerender; this module only plans and
reports. Kept lightweight — no retry loop, no workflow orchestration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

# ── Action type constants ────────────────────────────────────────────────────

ACTION_RERENDER = "rerender"
"""Straight rerender of affected scene."""

ACTION_RERENDER_WITH_TOKEN_RESET = "rerender_with_token_reset"
"""Reset design tokens then rerender (addresses palette drift)."""

# ── Deterministic issue-to-action map ────────────────────────────────────────

L0_REPAIR_MAP: dict[str, str] = {
    "blank_frame": ACTION_RERENDER,
    "suspected_freeze": ACTION_RERENDER,
    "palette_drift": ACTION_RERENDER_WITH_TOKEN_RESET,
}
"""L0 issue type → default repair action type.

Extend this dict to add repair mappings for other issue types.
Other issue types (no_video_stream, resolution_mismatch, all_blank,
aspect_ratio_mismatch, codec_mismatch) are **not** rerender-repairable
and are excluded from the map.
"""


# ── Data types ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class RepairAction:
    """One deterministic repair step for a single L0 issue."""

    issue_type: str
    action: str
    description: str
    params: dict[str, Any] = field(default_factory=dict)


RepairHook = Callable[[RepairAction], bool]
"""Signature for an external rerender hook.

Return True if the repair was applied successfully, False on failure.
The hook is responsible for actually re-rendering the scene (or resetting
tokens). This module only invokes it; it does not implement rerender logic.
"""


# ── Plan builder ─────────────────────────────────────────────────────────────


def build_repair_plan(l0_result: dict[str, Any]) -> list[RepairAction]:
    """Build deterministic repair plan from L0 review result.

    Args:
        l0_result: Output from L0MixedEngineReview.run() — must contain
                   an ``"issues"`` key with a list of issue dicts.

    Returns:
        Ordered list of RepairActions (one per repairable issue). Issues
        whose type is not in L0_REPAIR_MAP are silently skipped.
    """
    plan: list[RepairAction] = []
    issues: list[dict[str, Any]] = l0_result.get("issues", [])

    for issue in issues:
        itype = issue.get("type", "")
        action = L0_REPAIR_MAP.get(itype)
        if action is None:
            continue  # not a rerender-repairable issue

        plan.append(
            RepairAction(
                issue_type=itype,
                action=action,
                description=_describe_action(itype, action, issue),
                params=_extract_params(itype, issue),
            )
        )
    return plan


def _describe_action(issue_type: str, action: str, issue: dict[str, Any]) -> str:
    parts: dict[str, str] = {
        "blank_frame": "Blank frame detected — rerender scene",
        "suspected_freeze": "Detected freeze — rerender scene",
        "palette_drift": "Palette drift detected — reset design tokens then rerender",
    }
    return parts.get(issue_type, f"{action} for {issue_type}")


def _extract_params(issue_type: str, issue: dict[str, Any]) -> dict[str, Any]:
    params: dict[str, Any] = {}
    if issue_type == "palette_drift":
        params["reset_tokens"] = True
    # Carry over frame/s timing info so hook can target specific scene if needed
    for key in ("frame_index", "pts", "frame_a", "frame_b", "pts_a", "pts_b"):
        if key in issue:
            params[key] = issue[key]
    return params


# ── Plan executor ─────────────────────────────────────────────────────────────


def execute_repair_plan(
    plan: list[RepairAction],
    hook: RepairHook | None = None,
) -> dict[str, Any]:
    """Execute a repair plan, optionally delegating to an external hook.

    Args:
        plan: Repair plan from build_repair_plan().
        hook: Optional callable invoked for each action. If omitted, actions
              are reported as ``skipped``.

    Returns:
        Report dict with keys:
          - total_actions: int
          - results: list of per-action result dicts
          - all_succeeded: bool
    """
    results: list[dict[str, Any]] = []

    for action in plan:
        applied = False
        skipped = hook is None
        error: str | None = None

        if hook is not None:
            try:
                applied = hook(action)
            except Exception as exc:
                error = str(exc)
                applied = False

        results.append({
            "issue_type": action.issue_type,
            "action": action.action,
            "description": action.description,
            "applied": applied,
            "skipped": skipped,
            "error": error,
        })

    return {
        "total_actions": len(plan),
        "results": results,
        "all_succeeded": all(r["applied"] for r in results if not r["skipped"]),
    }
