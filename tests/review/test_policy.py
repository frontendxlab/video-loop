"""Focused tests for central review policy engine.

Covers :mod:`videoforge.review.policy` — the single source of truth for
pass/warn/fail/retry/repair decisions across L0/L1/L2/coherence levels.
"""

from __future__ import annotations

from typing import Any

import pytest

from videoforge.review.policy import (
    ReviewVerdict,
    aggregate,
    evaluate_coherence,
    evaluate_l0,
    evaluate_l1,
    evaluate_l2,
    should_repair,
    should_retry,
)


# ── ReviewVerdict enum ────────────────────────────────────────────────────────


class TestReviewVerdict:
    def test_values_match_expected_strings(self) -> None:
        assert ReviewVerdict.PASS.value == "pass"
        assert ReviewVerdict.WARN.value == "warn"
        assert ReviewVerdict.FAIL.value == "fail"
        assert ReviewVerdict.RETRY.value == "retry"
        assert ReviewVerdict.REPAIR.value == "repair"

    def test_all_five_verdicts_defined(self) -> None:
        assert len(ReviewVerdict) == 5


# ── evaluate_l0: mixed-engine severity policy ─────────────────────────────────


class TestEvaluateL0:
    def test_no_issues_returns_pass(self) -> None:
        assert evaluate_l0({"issues": []}) == ReviewVerdict.PASS

    def test_only_low_returns_warn(self) -> None:
        assert evaluate_l0({
            "issues": [{"severity": "low", "type": "codec_mismatch"}],
        }) == ReviewVerdict.WARN

    def test_medium_returns_warn(self) -> None:
        assert evaluate_l0({
            "issues": [{"severity": "medium", "type": "palette_drift"}],
        }) == ReviewVerdict.WARN

    def test_high_returns_fail(self) -> None:
        assert evaluate_l0({
            "issues": [{"severity": "high", "type": "blank_frame"}],
        }) == ReviewVerdict.FAIL

    def test_high_overrides_low(self) -> None:
        result = evaluate_l0({
            "issues": [
                {"severity": "low", "type": "codec_mismatch"},
                {"severity": "high", "type": "resolution_mismatch"},
            ],
        })
        assert result == ReviewVerdict.FAIL

    def test_medium_overrides_low(self) -> None:
        result = evaluate_l0({
            "issues": [
                {"severity": "low", "type": "codec_mismatch"},
                {"severity": "medium", "type": "suspected_freeze"},
            ],
        })
        assert result == ReviewVerdict.WARN

    def test_missing_severity_defaults_low(self) -> None:
        assert evaluate_l0({
            "issues": [{"type": "unknown"}],
        }) == ReviewVerdict.WARN

    def test_empty_result_dict(self) -> None:
        assert evaluate_l0({}) == ReviewVerdict.PASS

    def test_missing_issues_key(self) -> None:
        assert evaluate_l0({"passed": True}) == ReviewVerdict.PASS


# ── evaluate_l1: frame integrity policy ───────────────────────────────────────


class TestEvaluateL1:
    def test_no_issues_returns_pass(self) -> None:
        assert evaluate_l1({"issues": [], "passed": True}) == ReviewVerdict.PASS

    def test_black_frame_returns_fail(self) -> None:
        assert evaluate_l1({
            "issues": [{"type": "black_frame", "start": 0, "end": 5}],
        }) == ReviewVerdict.FAIL

    def test_frozen_frame_returns_fail(self) -> None:
        assert evaluate_l1({
            "issues": [{"type": "frozen_frame", "start": 10, "end": 20}],
        }) == ReviewVerdict.FAIL

    def test_infrastructure_error_returns_retry(self) -> None:
        assert evaluate_l1({
            "issues": [{"type": "error", "detail": "Failed to probe video"}],
        }) == ReviewVerdict.RETRY

    def test_mixed_issues_retry_takes_priority(self) -> None:
        """Infrastructure error → RETRY even alongside other issues."""
        assert evaluate_l1({
            "issues": [
                {"type": "error", "detail": "ffprobe timeout"},
                {"type": "black_frame", "start": 0},
            ],
        }) == ReviewVerdict.RETRY

    def test_empty_issues_returns_pass(self) -> None:
        assert evaluate_l1({"issues": []}) == ReviewVerdict.PASS

    def test_empty_result_dict(self) -> None:
        assert evaluate_l1({}) == ReviewVerdict.PASS


# ── evaluate_l2: layout overlap policy ────────────────────────────────────────


class TestEvaluateL2:
    def test_no_issues_returns_pass(self) -> None:
        assert evaluate_l2({"issues": [], "passed": True}) == ReviewVerdict.PASS

    def test_overlap_high_severity_returns_fail(self) -> None:
        assert evaluate_l2({
            "issues": [{"type": "overlap", "severity": "high", "iou": 0.9}],
        }) == ReviewVerdict.FAIL

    def test_overlap_medium_severity_returns_warn(self) -> None:
        assert evaluate_l2({
            "issues": [{"type": "overlap", "severity": "medium", "iou": 0.5}],
        }) == ReviewVerdict.WARN

    def test_clipped_medium_returns_warn(self) -> None:
        assert evaluate_l2({
            "issues": [{"type": "clipped", "severity": "medium"}],
        }) == ReviewVerdict.WARN

    def test_high_and_medium_mixed_returns_fail(self) -> None:
        result = evaluate_l2({
            "issues": [
                {"type": "clipped", "severity": "medium"},
                {"type": "overlap", "severity": "high", "iou": 0.85},
            ],
        })
        assert result == ReviewVerdict.FAIL

    def test_empty_result_dict(self) -> None:
        assert evaluate_l2({}) == ReviewVerdict.PASS


# ── evaluate_coherence: narrative arc policy ──────────────────────────────────


class TestEvaluateCoherence:
    def test_coherent_returns_pass(self) -> None:
        assert evaluate_coherence({
            "issues": [],
            "coherent": True,
        }) == ReviewVerdict.PASS

    def test_missing_phases_returns_warn(self) -> None:
        assert evaluate_coherence({
            "issues": ["Missing phases: impact"],
            "coherent": False,
        }) == ReviewVerdict.WARN

    def test_duplicate_phases_returns_warn(self) -> None:
        assert evaluate_coherence({
            "issues": ["Duplicate sections: solution"],
            "coherent": False,
        }) == ReviewVerdict.WARN

    def test_phase_content_issues_returns_warn(self) -> None:
        assert evaluate_coherence({
            "issues": ["Phase 'impact' lacks both keyword coverage and scene content"],
            "coherent": False,
        }) == ReviewVerdict.WARN

    def test_no_issues_but_not_coherent_still_pass(self) -> None:
        """Edge case: if no issues but coherent=False, still WARN."""
        assert evaluate_coherence({
            "issues": [],
            "coherent": False,
        }) == ReviewVerdict.WARN

    def test_empty_result_dict(self) -> None:
        """No issues + no coherent flag → PASS (vacuously coherent)."""
        assert evaluate_coherence({}) == ReviewVerdict.PASS


# ── should_retry ──────────────────────────────────────────────────────────────


class TestShouldRetry:
    def test_l0_no_frames_sampled_returns_true(self) -> None:
        assert should_retry(
            {"sampled_frames": 0, "total_frames": 300}, level="l0",
        ) is True

    def test_l0_frames_sampled_returns_false(self) -> None:
        assert should_retry(
            {"sampled_frames": 6, "total_frames": 300}, level="l0",
        ) is False

    def test_l0_both_zero_returns_false(self) -> None:
        assert should_retry(
            {"sampled_frames": 0, "total_frames": 0}, level="l0",
        ) is False

    def test_l1_error_returns_true(self) -> None:
        assert should_retry(
            {"issues": [{"type": "error"}]}, level="l1",
        ) is True

    def test_l1_no_error_returns_false(self) -> None:
        assert should_retry(
            {"issues": [{"type": "black_frame"}]}, level="l1",
        ) is False

    def test_l1_no_issues_returns_false(self) -> None:
        assert should_retry({"issues": []}, level="l1") is False

    def test_unknown_level_returns_false(self) -> None:
        assert should_retry({}, level="l3") is False


# ── should_repair ─────────────────────────────────────────────────────────────


class TestShouldRepair:
    def test_blank_frame_repairable(self) -> None:
        assert should_repair({
            "issues": [{"type": "blank_frame"}],
        }) is True

    def test_suspected_freeze_repairable(self) -> None:
        assert should_repair({
            "issues": [{"type": "suspected_freeze"}],
        }) is True

    def test_palette_drift_repairable(self) -> None:
        assert should_repair({
            "issues": [{"type": "palette_drift"}],
        }) is True

    def test_no_video_stream_not_repairable(self) -> None:
        assert should_repair({
            "issues": [{"type": "no_video_stream"}],
        }) is False

    def test_resolution_mismatch_not_repairable(self) -> None:
        assert should_repair({
            "issues": [{"type": "resolution_mismatch"}],
        }) is False

    def test_all_blank_not_repairable(self) -> None:
        assert should_repair({
            "issues": [{"type": "all_blank"}],
        }) is False

    def test_mixed_issues(self) -> None:
        assert should_repair({
            "issues": [
                {"type": "no_video_stream"},
                {"type": "blank_frame"},  # repairable
            ],
        }) is True

    def test_no_issues_returns_false(self) -> None:
        assert should_repair({"issues": []}) is False

    def test_empty_result_dict(self) -> None:
        assert should_repair({}) is False


# ── aggregate: unified decision ───────────────────────────────────────────────


class TestAggregate:
    def test_all_pass(self) -> None:
        result = aggregate(
            l0_result={"issues": []},
            l1_result={"issues": [], "passed": True},
            l2_result={"issues": [], "passed": True},
            coherence_result={"issues": [], "coherent": True},
        )
        assert result["verdict"] == ReviewVerdict.PASS
        assert result["levels"] == {
            "l0": ReviewVerdict.PASS,
            "l1": ReviewVerdict.PASS,
            "l2": ReviewVerdict.PASS,
            "coherence": ReviewVerdict.PASS,
        }
        assert result["retry_suggested"] is False
        assert result["repair_suggested"] is False

    def test_fail_wins_over_warn(self) -> None:
        """Most severe verdict (fail) wins over warn/pass."""
        result = aggregate(
            l0_result={"issues": [{"severity": "high", "type": "blank_frame"}]},
            l1_result={"issues": [], "passed": True},
        )
        assert result["verdict"] == ReviewVerdict.FAIL
        assert result["levels"]["l0"] == ReviewVerdict.FAIL
        assert result["levels"]["l1"] == ReviewVerdict.PASS

    def test_retry_wins_over_warn(self) -> None:
        result = aggregate(
            l0_result={"issues": [], "sampled_frames": 0, "total_frames": 300},
            l1_result={"issues": [], "passed": True},
        )
        assert result["verdict"] == ReviewVerdict.RETRY
        assert result["retry_suggested"] is True

    def test_retry_l1_wins(self) -> None:
        result = aggregate(
            l0_result={"issues": [{"severity": "medium", "type": "palette_drift"}]},
            l1_result={"issues": [{"type": "error", "detail": "timeout"}]},
        )
        # L1 retry beats L0 warn
        assert result["verdict"] == ReviewVerdict.RETRY

    def test_repair_suggested_when_repairable(self) -> None:
        result = aggregate(
            l0_result={"issues": [{"type": "blank_frame", "severity": "high"}]},
            l1_result={"issues": [], "passed": True},
        )
        assert result["repair_suggested"] is True
        assert "repair_plan" in result
        assert len(result["repair_plan"]) == 1

    def test_repair_not_suggested_for_non_repairable(self) -> None:
        result = aggregate(
            l0_result={"issues": [{"type": "no_video_stream", "severity": "high"}]},
            l1_result={"issues": [], "passed": True},
        )
        assert result["repair_suggested"] is False
        assert "repair_plan" not in result

    def test_warn_from_l2(self) -> None:
        result = aggregate(
            l0_result={"issues": []},
            l1_result={"issues": [], "passed": True},
            l2_result={"issues": [{"type": "clipped", "severity": "medium"}]},
        )
        assert result["verdict"] == ReviewVerdict.WARN

    def test_warn_from_coherence(self) -> None:
        result = aggregate(
            l0_result={"issues": []},
            l1_result={"issues": [], "passed": True},
            coherence_result={"issues": ["Missing phases: impact"], "coherent": False},
        )
        assert result["verdict"] == ReviewVerdict.WARN

    def test_all_none_returns_pass(self) -> None:
        result = aggregate()
        assert result["verdict"] == ReviewVerdict.PASS
        assert result["levels"] == {}
        assert result["retry_suggested"] is False
        assert result["repair_suggested"] is False

    def test_details_contains_original_results(self) -> None:
        l0 = {"issues": [], "sampled_frames": 6, "total_frames": 300}
        l1 = {"issues": [], "passed": True}
        result = aggregate(l0_result=l0, l1_result=l1)
        assert result["details"]["l0"] is l0
        assert result["details"]["l1"] is l1


# ── Backward compatibility with FrameReviewer ───────────────────────────────


class TestBackwardCompat:
    """FrameReviewer.evaluate_l0_policy still returns correct strings."""

    def test_evaluate_l0_policy_pass(self) -> None:
        from videoforge.review.frame_reviewer import FrameReviewer
        assert FrameReviewer.evaluate_l0_policy({"issues": []}) == "pass"

    def test_evaluate_l0_policy_fail(self) -> None:
        from videoforge.review.frame_reviewer import FrameReviewer
        assert FrameReviewer.evaluate_l0_policy({
            "issues": [{"severity": "high", "type": "blank_frame"}],
        }) == "fail"

    def test_evaluate_l0_policy_warn(self) -> None:
        from videoforge.review.frame_reviewer import FrameReviewer
        assert FrameReviewer.evaluate_l0_policy({
            "issues": [{"severity": "medium", "type": "palette_drift"}],
        }) == "warn"

    def test_evaluate_l0_policy_low_warn(self) -> None:
        from videoforge.review.frame_reviewer import FrameReviewer
        assert FrameReviewer.evaluate_l0_policy({
            "issues": [{"severity": "low", "type": "codec_mismatch"}],
        }) == "warn"

    def test_evaluate_l1_policy_new_method(self) -> None:
        from videoforge.review.frame_reviewer import FrameReviewer
        assert FrameReviewer.evaluate_l1_policy({"issues": []}) == "pass"
        assert FrameReviewer.evaluate_l1_policy({
            "issues": [{"type": "black_frame"}],
        }) == "fail"
        assert FrameReviewer.evaluate_l1_policy({
            "issues": [{"type": "error", "detail": "timeout"}],
        }) == "retry"

    def test_evaluate_overlap_policy(self) -> None:
        from videoforge.review.frame_reviewer import FrameReviewer
        assert FrameReviewer.evaluate_overlap_policy({"issues": []}) == "pass"
        assert FrameReviewer.evaluate_overlap_policy({
            "issues": [{"type": "overlap", "severity": "high"}],
        }) == "fail"
