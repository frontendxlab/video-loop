"""Tests for deterministic rerender orchestration."""

from __future__ import annotations

from typing import Any

import pytest

from videoforge.review.repair_actions import RepairAction
from videoforge.review.rerender_orchestrator import run_orchestrated_review

pytestmark = pytest.mark.render_smoke


def _review_no_issues(path: str) -> dict[str, Any]:
    return {"issues": [], "passed": True, "sampled_frames": 6}


def _review_one_blank(path: str) -> dict[str, Any]:
    return {
        "issues": [{"type": "blank_frame", "frame_index": 5, "pts": 2.5, "severity": "high"}],
        "passed": False,
        "sampled_frames": 6,
    }


def _hook_ok(action: RepairAction) -> bool:
    return True


def _hook_fail(action: RepairAction) -> bool:
    return False


class TestRerenderOrchestrator:
    """Outcome matrix: clean / no_hook / repair_failed / exhausted."""

    def test_clean_no_issues(self) -> None:
        """No issues → outcome clean, 0 rounds."""
        result = run_orchestrated_review("/fake/path.mp4", _review_no_issues)
        assert result["outcome"] == "clean"
        assert result["rounds"] == []
        assert result["total_issues_final"] == 0
        assert result["video_path"] == "/fake/path.mp4"

    def test_clean_no_issues_with_hook(self) -> None:
        """Hook provided but unused when no issues."""
        result = run_orchestrated_review("/fake/path.mp4", _review_no_issues, render_hook=_hook_ok)
        assert result["outcome"] == "clean"

    def test_no_hook_returns_early(self) -> None:
        """Issues exist but no hook → outcome no_hook, 0 rounds."""
        result = run_orchestrated_review("/fake/path.mp4", _review_one_blank)
        assert result["outcome"] == "no_hook"
        assert result["rounds"] == []
        assert result["total_issues_final"] == 1

    def test_repair_failed_hook_returns_false(self) -> None:
        """Hook returns False → outcome repair_failed."""
        result = run_orchestrated_review(
            "/fake/path.mp4", _review_one_blank, render_hook=_hook_fail,
        )
        assert result["outcome"] == "repair_failed"
        assert len(result["rounds"]) == 1
        assert result["rounds"][0]["repair"]["all_succeeded"] is False

    def test_repair_fixed_in_one_round(self) -> None:
        """First repair fixes all issues → outcome clean, 1 round, 2 reviews."""
        call_count: int = 0

        def review_fn(path: str) -> dict[str, Any]:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _review_one_blank(path)
            return _review_no_issues(path)

        result = run_orchestrated_review(
            "/fake/path.mp4", review_fn, render_hook=_hook_ok,
        )
        assert result["outcome"] == "clean"
        assert len(result["rounds"]) == 1
        assert result["rounds"][0]["issues_total"] == 1
        assert result["rounds"][0]["repairable"] == 1
        assert result["rounds"][0]["repair"]["all_succeeded"] is True
        assert call_count == 2  # initial + re-review

    def test_exhausted_max_rounds(self) -> None:
        """Issues persist every round → outcome exhausted."""
        call_count: int = 0

        def review_fn(path: str) -> dict[str, Any]:
            nonlocal call_count
            call_count += 1
            return _review_one_blank(path)

        result = run_orchestrated_review(
            "/fake/path.mp4", review_fn, render_hook=_hook_ok, max_rounds=3,
        )
        assert result["outcome"] == "exhausted"
        assert len(result["rounds"]) == 3
        assert all(r["repair"]["all_succeeded"] for r in result["rounds"])
        assert result["total_issues_final"] == 1
        # max_rounds repairs + 1 final review
        assert call_count == 4

    def test_exhausted_max_rounds_default(self) -> None:
        """Default max_rounds=3 works."""
        call_count: int = 0

        def review_fn(path: str) -> dict[str, Any]:
            nonlocal call_count
            call_count += 1
            return _review_one_blank(path)

        result = run_orchestrated_review(
            "/fake/path.mp4", review_fn, render_hook=_hook_ok,
        )
        assert result["outcome"] == "exhausted"
        assert len(result["rounds"]) == 3

    def test_round_structure(self) -> None:
        """Each round record has expected keys."""
        call_count: int = 0

        def review_fn(path: str) -> dict[str, Any]:
            nonlocal call_count
            call_count += 1
            return _review_one_blank(path)

        result = run_orchestrated_review(
            "/fake/path.mp4", review_fn, render_hook=_hook_ok, max_rounds=1,
        )
        assert len(result["rounds"]) == 1
        r = result["rounds"][0]
        assert r["round"] == 1
        assert r["issues_total"] == 1
        assert r["repairable"] == 1
        assert "repair" in r
        assert r["repair"]["total_actions"] == 1
        assert r["repair"]["results"][0]["applied"] is True

    def test_multiple_issues_some_non_repairable(self) -> None:
        """Non-repairable issues are excluded from plan, don't block clean."""
        call_count: int = 0

        def review_fn(path: str) -> dict[str, Any]:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {
                    "issues": [
                        {"type": "blank_frame", "frame_index": 0, "severity": "high"},
                        {"type": "resolution_mismatch", "severity": "high"},
                    ],
                    "passed": False,
                    "sampled_frames": 6,
                }
            return {
                "issues": [
                    {"type": "resolution_mismatch", "severity": "high"},
                ],
                "passed": False,
                "sampled_frames": 6,
            }

        result = run_orchestrated_review(
            "/fake/path.mp4", review_fn, render_hook=_hook_ok,
        )
        # blank_frame repaired → repairable issues gone → clean
        assert result["outcome"] == "clean"
        assert len(result["rounds"]) == 1
        # But final review still has non-repairable issues
        assert result["total_issues_final"] == 1

    def test_report_keys(self) -> None:
        """Returned dict has all required keys."""
        result = run_orchestrated_review("/fake/path.mp4", _review_no_issues)
        assert set(result.keys()) == {
            "video_path", "max_rounds", "rounds", "final_review", "outcome",
            "total_issues_final",
        }

    def test_hook_exception_handled(self) -> None:
        """Hook raising exception → outcome repair_failed."""

        def hook_raise(action: RepairAction) -> bool:
            raise RuntimeError("render crashed")

        result = run_orchestrated_review(
            "/fake/path.mp4", _review_one_blank, render_hook=hook_raise,
        )
        assert result["outcome"] == "repair_failed"
        assert result["rounds"][0]["repair"]["results"][0]["error"] == "render crashed"

    def test_rerender_with_token_reset_action(self) -> None:
        """Palette drift action flows through orchestrator."""

        call_count: int = 0

        def review_fn(path: str) -> dict[str, Any]:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {
                    "issues": [
                        {"type": "palette_drift", "frame_index": 3, "pts": 1.5,
                         "distance": 150.0, "severity": "medium"},
                    ],
                    "passed": False,
                    "sampled_frames": 6,
                }
            return {"issues": [], "passed": True, "sampled_frames": 6}

        received: list[RepairAction] = []

        def capture_hook(action: RepairAction) -> bool:
            received.append(action)
            return True

        result = run_orchestrated_review(
            "/fake/path.mp4", review_fn, render_hook=capture_hook,
        )
        assert result["outcome"] == "clean"
        assert len(received) == 1
        assert received[0].issue_type == "palette_drift"
        assert received[0].params.get("reset_tokens") is True
