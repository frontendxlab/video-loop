"""Central review policy engine — maps L0/L1/L2/coherence results to decisions.

Single source of truth for pass/warn/fail/retry/repair decisions.
CLI, pipeline, and MCP tools all call here instead of reimplementing logic.

Usage::

    from videoforge.review.policy import aggregate, ReviewVerdict

    decision = aggregate(l0_result=l0, l1_result=l1)
    if decision["verdict"] == ReviewVerdict.FAIL:
        ...
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class ReviewVerdict(str, Enum):
    """Possible review decisions across all gate levels."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    RETRY = "retry"
    REPAIR = "repair"


_SEVERITY_ORDER: list[ReviewVerdict] = [
    ReviewVerdict.FAIL,
    ReviewVerdict.RETRY,
    ReviewVerdict.REPAIR,
    ReviewVerdict.WARN,
    ReviewVerdict.PASS,
]

# ── L0: Mixed-engine severity policy ────────────────────────────────────────


def evaluate_l0(result: dict[str, Any]) -> ReviewVerdict:
    """Map L0 mixed-engine issues to pass/warn/fail.

    Policy:
        - 0 issues                          -> PASS
        - only low severity                  -> WARN
        - any medium severity                -> WARN
        - any high severity                  -> FAIL

    Backward-compatible with ``FrameReviewer.evaluate_l0_policy``.

    Args:
        result: L0 result dict with ``"issues"`` key.

    Returns:
        ReviewVerdict.
    """
    issues = result.get("issues", [])
    if not issues:
        return ReviewVerdict.PASS
    severities = {i.get("severity", "low") for i in issues}
    if "high" in severities:
        return ReviewVerdict.FAIL
    if "medium" in severities:
        return ReviewVerdict.WARN
    return ReviewVerdict.WARN  # low only


# ── L1: Frame integrity policy ──────────────────────────────────────────────


def evaluate_l1(result: dict[str, Any]) -> ReviewVerdict:
    """Map L1 integrity result to pass / fail / retry.

    - No issues                             -> PASS
    - Infrastructure error (ffprobe/ffmpeg) -> RETRY
    - Black/frozen frame issues             -> FAIL

    Args:
        result: L1 result dict with ``"issues"`` key.

    Returns:
        ReviewVerdict.
    """
    issues = result.get("issues", [])
    if not issues:
        return ReviewVerdict.PASS

    for issue in issues:
        if issue.get("type") == "error":
            return ReviewVerdict.RETRY

    return ReviewVerdict.FAIL


# ── L2: Layout overlap policy ────────────────────────────────────────────────


def evaluate_l2(result: dict[str, Any]) -> ReviewVerdict:
    """Map L2 layout-overlap result to pass / warn / fail.

    - No issues                             -> PASS
    - Any high severity (iou >= 0.8)        -> FAIL
    - Medium severity (clipped / overlap)   -> WARN

    Args:
        result: L2 ``OverlapGate.run()`` result dict.

    Returns:
        ReviewVerdict.
    """
    issues = result.get("issues", [])
    if not issues:
        return ReviewVerdict.PASS
    severities = {i.get("severity", "low") for i in issues}
    if "high" in severities:
        return ReviewVerdict.FAIL
    return ReviewVerdict.WARN


# ── Coherence gate policy ────────────────────────────────────────────────────


def evaluate_coherence(result: dict[str, Any]) -> ReviewVerdict:
    """Map coherence gate result to pass / warn.

    - No issues, ``coherent=True``          -> PASS
    - Any coherence issues                  -> WARN

    Args:
        result: ``CoherenceGate.check_scenes()`` result dict.

    Returns:
        ReviewVerdict.
    """
    issues = result.get("issues", [])
    if not issues and result.get("coherent", True):
        return ReviewVerdict.PASS
    return ReviewVerdict.WARN


# ── Retry / Repair helpers ───────────────────────────────────────────────────


def should_retry(result: dict[str, Any], level: str = "l0") -> bool:
    """Check if result suggests a retry may resolve the issue.

    Args:
        result: Level result dict.
        level: Level name (``"l0"``, ``"l1"``).

    Returns:
        True if retry may resolve.
    """
    if level == "l0":
        return (
            result.get("sampled_frames", 0) == 0
            and result.get("total_frames", 0) > 0
        )
    if level == "l1":
        for issue in result.get("issues", []):
            if issue.get("type") == "error":
                return True
        return False
    return False


def should_repair(result: dict[str, Any]) -> bool:
    """Check if result has issues mappable to repair actions.

    Args:
        result: Level result dict with ``"issues"`` key.

    Returns:
        True if any issue maps to a known repair action.
    """
    from videoforge.review.repair_actions import L0_REPAIR_MAP

    for issue in result.get("issues", []):
        if issue.get("type", "") in L0_REPAIR_MAP:
            return True
    return False


# ── Aggregate decision ───────────────────────────────────────────────────────


def aggregate(
    l0_result: dict[str, Any] | None = None,
    l1_result: dict[str, Any] | None = None,
    l2_result: dict[str, Any] | None = None,
    coherence_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate all provided level results into a single unified decision.

    Single entry point for CLI, pipeline, and MCP tools.  Each level is
    optional — pass ``None`` to skip.

    Decision hierarchy (most to least severe):
        **fail > retry > repair > warn > pass**

    Args:
        l0_result: L0 mixed-engine result dict.
        l1_result: L1 frame integrity result dict.
        l2_result: L2 layout overlap result dict.
        coherence_result: Coherence gate result dict.

    Returns:
        Dict with keys:

        - ``verdict``: most severe :class:`ReviewVerdict` across all levels.
        - ``levels``: dict of ``level_name -> ReviewVerdict``.
        - ``details``: per-level original result dicts.
        - ``retry_suggested``: ``bool``.
        - ``repair_suggested``: ``bool``.
        - ``repair_plan``: list of ``RepairAction`` (only when repair suggested).
    """
    levels: dict[str, ReviewVerdict] = {}
    details: dict[str, Any] = {}
    retry_suggested = False
    repair_suggested = False
    all_verdicts: list[ReviewVerdict] = []

    if l0_result is not None:
        v = evaluate_l0(l0_result)
        if v == ReviewVerdict.PASS and should_retry(l0_result, "l0"):
            v = ReviewVerdict.RETRY
        levels["l0"] = v
        details["l0"] = l0_result
        all_verdicts.append(v)
        if v == ReviewVerdict.RETRY:
            retry_suggested = True
        if should_repair(l0_result):
            repair_suggested = True

    if l1_result is not None:
        v = evaluate_l1(l1_result)
        if v == ReviewVerdict.PASS and should_retry(l1_result, "l1"):
            v = ReviewVerdict.RETRY
        levels["l1"] = v
        details["l1"] = l1_result
        all_verdicts.append(v)
        if v == ReviewVerdict.RETRY:
            retry_suggested = True

    if l2_result is not None:
        v = evaluate_l2(l2_result)
        levels["l2"] = v
        details["l2"] = l2_result
        all_verdicts.append(v)

    if coherence_result is not None:
        v = evaluate_coherence(coherence_result)
        levels["coherence"] = v
        details["coherence"] = coherence_result
        all_verdicts.append(v)

    # Most severe verdict wins
    final_verdict = ReviewVerdict.PASS
    for sv in _SEVERITY_ORDER:
        if sv in all_verdicts:
            final_verdict = sv
            break

    result: dict[str, Any] = {
        "verdict": final_verdict,
        "levels": levels,
        "details": details,
        "retry_suggested": retry_suggested,
        "repair_suggested": repair_suggested,
    }

    if repair_suggested and l0_result is not None:
        from videoforge.review.repair_actions import build_repair_plan

        result["repair_plan"] = build_repair_plan(l0_result)

    return result
