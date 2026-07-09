"""Tests for deterministic repair actions for L0 failures."""

from __future__ import annotations

from typing import Any

import pytest

from videoforge.review.repair_actions import (
    ACTION_RERENDER,
    ACTION_RERENDER_WITH_TOKEN_RESET,
    L0_REPAIR_MAP,
    RepairAction,
    build_repair_plan,
    execute_repair_plan,
)


# ── Mapping tests ────────────────────────────────────────────────────────────


class TestRepairMap:
    """L0_REPAIR_MAP covers the three required issue types."""

    def test_blank_frame_mapped_to_rerender(self) -> None:
        assert L0_REPAIR_MAP["blank_frame"] == ACTION_RERENDER

    def test_suspected_freeze_mapped_to_rerender(self) -> None:
        assert L0_REPAIR_MAP["suspected_freeze"] == ACTION_RERENDER

    def test_palette_drift_mapped_to_rerender_with_token_reset(self) -> None:
        assert L0_REPAIR_MAP["palette_drift"] == ACTION_RERENDER_WITH_TOKEN_RESET

    def test_non_repairable_types_excluded(self) -> None:
        """no_video_stream, resolution_mismatch, all_blank etc. are not in map."""
        non_repairable = [
            "no_video_stream",
            "resolution_mismatch",
            "all_blank",
            "aspect_ratio_mismatch",
            "codec_mismatch",
        ]
        for t in non_repairable:
            assert t not in L0_REPAIR_MAP, f"{t} should not be rerender-repairable"


# ── Plan builder tests ───────────────────────────────────────────────────────


class TestBuildRepairPlan:
    def test_empty_issues_returns_empty_plan(self) -> None:
        result: dict[str, Any] = {"issues": [], "passed": True, "sampled_frames": 6}
        plan = build_repair_plan(result)
        assert plan == []

    def test_blank_frame_issue_yields_rerender_action(self) -> None:
        result = {
            "issues": [
                {"type": "blank_frame", "frame_index": 5, "pts": 2.5, "severity": "high"},
            ],
        }
        plan = build_repair_plan(result)
        assert len(plan) == 1
        a = plan[0]
        assert a.issue_type == "blank_frame"
        assert a.action == ACTION_RERENDER
        assert a.params["frame_index"] == 5
        assert "reset_tokens" not in a.params

    def test_suspected_freeze_issue(self) -> None:
        result = {
            "issues": [
                {
                    "type": "suspected_freeze",
                    "frame_a": 10,
                    "frame_b": 20,
                    "pts_a": 0.5,
                    "pts_b": 1.0,
                    "severity": "medium",
                },
            ],
        }
        plan = build_repair_plan(result)
        assert len(plan) == 1
        a = plan[0]
        assert a.issue_type == "suspected_freeze"
        assert a.action == ACTION_RERENDER
        assert a.params["frame_a"] == 10
        assert a.params["frame_b"] == 20

    def test_palette_drift_issue_includes_reset_tokens_flag(self) -> None:
        result = {
            "issues": [
                {
                    "type": "palette_drift",
                    "frame_index": 3,
                    "pts": 1.5,
                    "distance": 150.0,
                    "severity": "medium",
                },
            ],
        }
        plan = build_repair_plan(result)
        assert len(plan) == 1
        a = plan[0]
        assert a.issue_type == "palette_drift"
        assert a.action == ACTION_RERENDER_WITH_TOKEN_RESET
        assert a.params["reset_tokens"] is True
        assert a.params["frame_index"] == 3

    def test_multiple_issues_yield_multiple_actions(self) -> None:
        result = {
            "issues": [
                {"type": "blank_frame", "frame_index": 0, "pts": 0.0, "severity": "high"},
                {"type": "palette_drift", "frame_index": 3, "pts": 1.5, "distance": 150.0, "severity": "medium"},
                {"type": "suspected_freeze", "frame_a": 5, "frame_b": 10, "severity": "medium"},
                {"type": "resolution_mismatch", "severity": "high"},  # skipped
            ],
        }
        plan = build_repair_plan(result)
        assert len(plan) == 3
        assert [a.issue_type for a in plan] == ["blank_frame", "palette_drift", "suspected_freeze"]

    def test_non_repairable_issue_skipped(self) -> None:
        result = {
            "issues": [
                {"type": "no_video_stream", "severity": "high"},
            ],
        }
        plan = build_repair_plan(result)
        assert plan == []

    def test_no_issues_key_returns_empty(self) -> None:
        assert build_repair_plan({}) == []
        assert build_repair_plan({"passed": True}) == []


# ── Hook execution tests ─────────────────────────────────────────────────────


class TestExecuteRepairPlan:
    def test_no_hook_all_skipped(self) -> None:
        plan = [
            RepairAction(issue_type="blank_frame", action=ACTION_RERENDER, description="test"),
        ]
        report = execute_repair_plan(plan, hook=None)
        assert report["total_actions"] == 1
        assert report["results"][0]["skipped"] is True
        assert report["results"][0]["applied"] is False

    def test_hook_returns_true(self) -> None:
        plan = [
            RepairAction(issue_type="blank_frame", action=ACTION_RERENDER, description="test"),
        ]
        called: list[RepairAction] = []

        def hook(action: RepairAction) -> bool:
            called.append(action)
            return True

        report = execute_repair_plan(plan, hook=hook)
        assert report["total_actions"] == 1
        assert report["results"][0]["applied"] is True
        assert report["results"][0]["skipped"] is False
        assert report["all_succeeded"] is True
        assert len(called) == 1
        assert called[0].issue_type == "blank_frame"

    def test_hook_returns_false(self) -> None:
        plan = [
            RepairAction(issue_type="palette_drift", action=ACTION_RERENDER_WITH_TOKEN_RESET, description="test"),
        ]

        def hook(action: RepairAction) -> bool:
            return False

        report = execute_repair_plan(plan, hook=hook)
        assert report["results"][0]["applied"] is False
        assert report["all_succeeded"] is False

    def test_hook_raises_exception(self) -> None:
        plan = [
            RepairAction(issue_type="blank_frame", action=ACTION_RERENDER, description="test"),
        ]

        def hook(action: RepairAction) -> bool:
            raise RuntimeError("render failed")

        report = execute_repair_plan(plan, hook=hook)
        assert report["results"][0]["applied"] is False
        assert report["results"][0]["error"] == "render failed"
        assert report["all_succeeded"] is False

    def test_empty_plan(self) -> None:
        report = execute_repair_plan([], hook=None)
        assert report["total_actions"] == 0
        assert report["results"] == []
        # vacuously true — no actions to fail
        assert report["all_succeeded"] is True

    def test_hook_receives_correct_action(self) -> None:
        plan = [
            RepairAction(
                issue_type="palette_drift",
                action=ACTION_RERENDER_WITH_TOKEN_RESET,
                description="Reset tokens and rerender",
                params={"reset_tokens": True, "frame_index": 7},
            ),
        ]
        received: list[RepairAction] = []

        def hook(action: RepairAction) -> bool:
            received.append(action)
            return True

        execute_repair_plan(plan, hook=hook)
        assert len(received) == 1
        a = received[0]
        assert a.issue_type == "palette_drift"
        assert a.action == ACTION_RERENDER_WITH_TOKEN_RESET
        assert a.params["reset_tokens"] is True


# ── Integration: build + execute chain ───────────────────────────────────────


class TestBuildAndExecuteChain:
    def test_full_chain_from_l0_result(self) -> None:
        l0_result = {
            "issues": [
                {"type": "blank_frame", "frame_index": 0, "pts": 0.0, "severity": "high"},
                {"type": "palette_drift", "frame_index": 3, "pts": 1.5, "distance": 150.0, "severity": "medium"},
            ],
            "passed": False,
            "sampled_frames": 6,
        }

        plan = build_repair_plan(l0_result)
        assert len(plan) == 2

        applied: list[str] = []

        def rerender_hook(action: RepairAction) -> bool:
            applied.append(action.issue_type)
            return True

        report = execute_repair_plan(plan, hook=rerender_hook)

        assert report["total_actions"] == 2
        assert report["all_succeeded"] is True
        assert applied == ["blank_frame", "palette_drift"]

    def test_chain_with_partial_hook_failure(self) -> None:
        l0_result = {
            "issues": [
                {"type": "blank_frame", "frame_index": 0, "severity": "high"},
                {"type": "suspected_freeze", "frame_a": 5, "frame_b": 10, "severity": "medium"},
            ],
        }

        plan = build_repair_plan(l0_result)
        call_count = 0

        def flaky_hook(action: RepairAction) -> bool:
            nonlocal call_count
            call_count += 1
            return call_count == 1  # first succeeds, second fails

        report = execute_repair_plan(plan, hook=flaky_hook)

        assert report["total_actions"] == 2
        assert report["results"][0]["applied"] is True
        assert report["results"][1]["applied"] is False
        assert report["all_succeeded"] is False
