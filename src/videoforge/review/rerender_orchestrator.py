"""Deterministic rerender orchestration with bounded retry.

Consumes review results, builds repair plans, executes rerenders,
and re-reviews until no repairable issues remain or max rounds reached.

Designed to sit between pipeline review stage and render backend.
Caller provides review_fn (runs quality checks) and render_hook
(triggers rerender). Orchestrator loops deterministically.

Outcomes:
  - clean:         Final review found no repairable issues.
  - no_hook:       No render_hook provided — repairs planned but skipped.
  - repair_failed: A repair action hook returned False or raised.
  - exhausted:     Max rounds reached without clearing all issues.
"""

from __future__ import annotations

from typing import Any, Callable

from videoforge.review.repair_actions import (
    RepairHook,
    build_repair_plan,
    execute_repair_plan,
)


def run_orchestrated_review(
    video_path: str,
    review_fn: Callable[[str], dict[str, Any]],
    render_hook: RepairHook | None = None,
    max_rounds: int = 3,
) -> dict[str, Any]:
    """Run bounded rerender/recheck loop.

    Args:
        video_path: Path to video file to review/rerender.
        review_fn: Callable that takes video_path, returns review result dict
                   with an ``"issues"`` key (list of issue dicts).
        render_hook: Optional callable invoked per repair action.
                     If None, repairs are planned but not executed.
        max_rounds: Maximum repair/review rounds before giving up.

    Returns:
        Dict with keys:
          - video_path: str
          - max_rounds: int
          - rounds: list of per-round dicts (only rounds with repairs)
          - final_review: last review result dict
          - outcome: "clean" | "no_hook" | "repair_failed" | "exhausted"
          - total_issues_final: int
    """
    rounds: list[dict[str, Any]] = []

    for round_num in range(1, max_rounds + 1):
        review_result = review_fn(video_path)
        plan = build_repair_plan(review_result)

        if not plan:
            return _assemble_report(
                video_path=video_path,
                max_rounds=max_rounds,
                rounds=rounds,
                final_review=review_result,
                outcome="clean",
            )

        if render_hook is None:
            return _assemble_report(
                video_path=video_path,
                max_rounds=max_rounds,
                rounds=rounds,
                final_review=review_result,
                outcome="no_hook",
            )

        repair_result = execute_repair_plan(plan, hook=render_hook)
        rounds.append({
            "round": round_num,
            "issues_total": len(review_result.get("issues", [])),
            "repairable": len(plan),
            "repair": repair_result,
        })

        if not repair_result["all_succeeded"]:
            return _assemble_report(
                video_path=video_path,
                max_rounds=max_rounds,
                rounds=rounds,
                final_review=review_result,
                outcome="repair_failed",
            )

    # Exhausted max_rounds — one final review to report current state
    final_review = review_fn(video_path)
    return _assemble_report(
        video_path=video_path,
        max_rounds=max_rounds,
        rounds=rounds,
        final_review=final_review,
        outcome="exhausted",
    )


def _assemble_report(
    video_path: str,
    max_rounds: int,
    rounds: list[dict[str, Any]],
    final_review: dict[str, Any],
    outcome: str,
) -> dict[str, Any]:
    return {
        "video_path": video_path,
        "max_rounds": max_rounds,
        "rounds": rounds,
        "final_review": final_review,
        "outcome": outcome,
        "total_issues_final": len(final_review.get("issues", [])),
    }
