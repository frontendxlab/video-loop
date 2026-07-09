"""Tests for OverlapGate — deterministic layout-overlap detection."""

from __future__ import annotations

import pytest

from videoforge.review.overlap_gate import (
    OverlapGate,
    _to_x1y1x2y2,
    compute_iou,
    is_clipped,
)


# ── _to_x1y1x2y2 unit tests ────────────────────────────────────────────────


class TestToX1Y1X2Y2:
    def test_valid_element(self) -> None:
        assert _to_x1y1x2y2({"x": 10, "y": 20, "width": 100, "height": 50}) == (10, 20, 110, 70)

    def test_missing_x(self) -> None:
        assert _to_x1y1x2y2({"y": 20, "width": 100, "height": 50}) is None

    def test_missing_y(self) -> None:
        assert _to_x1y1x2y2({"x": 10, "width": 100, "height": 50}) is None

    def test_missing_width(self) -> None:
        assert _to_x1y1x2y2({"x": 10, "y": 20, "height": 50}) is None

    def test_missing_height(self) -> None:
        assert _to_x1y1x2y2({"x": 10, "y": 20, "width": 100}) is None

    def test_empty_dict(self) -> None:
        assert _to_x1y1x2y2({}) is None

    def test_float_coords(self) -> None:
        result = _to_x1y1x2y2({"x": 10.5, "y": 20.3, "width": 99.5, "height": 49.7})
        assert result == (10.5, 20.3, 110.0, 70.0)


# ── compute_iou unit tests ──────────────────────────────────────────────────


class TestComputeIoU:
    def test_no_overlap(self) -> None:
        a = (0, 0, 10, 10)
        b = (20, 20, 30, 30)
        assert compute_iou(a, b) == 0.0

    def test_complete_overlap(self) -> None:
        a = (0, 0, 10, 10)
        b = (0, 0, 10, 10)
        assert compute_iou(a, b) == 1.0

    def test_half_overlap(self) -> None:
        # Two 10x10 boxes overlap by 5x10 = 50px
        a = (0, 0, 10, 10)
        b = (5, 0, 15, 10)
        # inter = 5*10 = 50, area_a = 100, area_b = 100, union = 150
        assert compute_iou(a, b) == 50.0 / 150.0

    def test_edge_touching_no_area(self) -> None:
        a = (0, 0, 10, 10)
        b = (10, 0, 20, 10)
        assert compute_iou(a, b) == 0.0

    def test_one_inside_other(self) -> None:
        a = (0, 0, 20, 20)
        b = (5, 5, 15, 15)
        # inter = 10*10=100, area_a=400, area_b=100, union=400
        assert compute_iou(a, b) == 100.0 / 400.0

    def test_zero_area_box_a(self) -> None:
        a = (0, 0, 0, 0)
        b = (0, 0, 10, 10)
        assert compute_iou(a, b) == 0.0

    def test_zero_area_box_b(self) -> None:
        a = (0, 0, 10, 10)
        b = (5, 5, 5, 5)
        assert compute_iou(a, b) == 0.0

    def test_both_zero_area(self) -> None:
        assert compute_iou((0, 0, 0, 0), (0, 0, 0, 0)) == 0.0

    def test_negative_coords_overlap(self) -> None:
        a = (-10, -10, 0, 0)
        b = (-5, -5, 5, 5)
        # inter = 5*5=25, area_a=100, area_b=100, union=175
        assert compute_iou(a, b) == 25.0 / 175.0

    def test_partial_overlap_vertical(self) -> None:
        a = (0, 0, 10, 20)
        b = (0, 10, 10, 30)
        # inter = 10*10=100, area_a=200, area_b=200, union=300
        assert compute_iou(a, b) == 100.0 / 300.0

    def test_large_coords(self) -> None:
        a = (0, 0, 1920, 1080)
        b = (100, 100, 500, 500)
        # inter = 400*400=160000, area_a=2073600, area_b=160000, union=2073600
        iou = compute_iou(a, b)
        assert 0.0 < iou < 1.0
        assert iou == pytest.approx(160000.0 / 2073600.0)


# ── is_clipped unit tests ────────────────────────────────────────────────────


class TestIsClipped:
    def test_fully_in_viewport(self) -> None:
        assert is_clipped({"x": 10, "y": 10, "width": 100, "height": 50}, 1920, 1080) is False

    def test_exceeds_right(self) -> None:
        assert is_clipped({"x": 1900, "y": 0, "width": 100, "height": 50}, 1920, 1080) is True

    def test_exceeds_bottom(self) -> None:
        assert is_clipped({"x": 0, "y": 1060, "width": 100, "height": 50}, 1920, 1080) is True

    def test_negative_x(self) -> None:
        assert is_clipped({"x": -10, "y": 0, "width": 100, "height": 50}, 1920, 1080) is True

    def test_negative_y(self) -> None:
        assert is_clipped({"x": 0, "y": -10, "width": 100, "height": 50}, 1920, 1080) is True

    def test_zero_viewport(self) -> None:
        assert is_clipped({"x": 0, "y": 0, "width": 1, "height": 1}, 0, 0) is True

    def test_exact_edge(self) -> None:
        # Exactly at boundary is NOT clipped
        assert is_clipped({"x": 0, "y": 0, "width": 1920, "height": 1080}, 1920, 1080) is False


# ── OverlapGate.run() integration tests ──────────────────────────────────────


class TestOverlapGateRun:
    def test_no_elements_passes(self) -> None:
        gate = OverlapGate()
        result = gate.run([])
        assert result["passed"] is True
        assert result["issues"] == []

    def test_non_overlapping_elements_passes(self) -> None:
        gate = OverlapGate()
        elements = [
            {"id": "title", "x": 0, "y": 0, "width": 400, "height": 100},
            {"id": "body", "x": 0, "y": 200, "width": 400, "height": 300},
            {"id": "footer", "x": 0, "y": 900, "width": 1920, "height": 180},
        ]
        result = gate.run(elements)
        assert result["passed"] is True
        assert result["issues"] == []

    def test_overlapping_elements_detected(self) -> None:
        gate = OverlapGate()  # default threshold 0.3
        # Both 200x200 at (0,0) and (50,50) → iou ≈ 0.39 > 0.3
        elements = [
            {"id": "a", "x": 0, "y": 0, "width": 200, "height": 200},
            {"id": "b", "x": 50, "y": 50, "width": 200, "height": 200},
        ]
        result = gate.run(elements)
        assert result["passed"] is False
        assert len(result["issues"]) == 1
        issue = result["issues"][0]
        assert issue["type"] == "overlap"
        assert issue["element_a"] == "a"
        assert issue["element_b"] == "b"
        assert issue["iou"] > 0.3

    def test_clipped_element_detected(self) -> None:
        gate = OverlapGate()
        elements = [
            {"id": "too_far", "x": 1900, "y": 0, "width": 200, "height": 100},
        ]
        result = gate.run(elements)
        assert result["passed"] is False
        assert len(result["issues"]) == 1
        assert result["issues"][0]["type"] == "clipped"

    def test_overlap_and_clipped_both_reported(self) -> None:
        gate = OverlapGate()  # default threshold 0.3
        # a overlaps b (iou ≈ 0.39 > 0.3); c is clipped (x+w=2100 > 1920)
        elements = [
            {"id": "a", "x": 0, "y": 0, "width": 200, "height": 200},
            {"id": "b", "x": 50, "y": 50, "width": 200, "height": 200},
            {"id": "c", "x": 1900, "y": 0, "width": 200, "height": 100},
        ]
        result = gate.run(elements)
        assert result["passed"] is False
        types = {i["type"] for i in result["issues"]}
        assert "overlap" in types
        assert "clipped" in types

    def test_default_threshold_used(self) -> None:
        # Two elements that overlap slightly but less than default 0.3
        gate = OverlapGate()
        elements = [
            {"id": "a", "x": 0, "y": 0, "width": 100, "height": 100},
            # 10px overlap in x, full 100px in y → inter=1000, union=19000, iou≈0.053
            {"id": "b", "x": 90, "y": 0, "width": 100, "height": 100},
        ]
        result = gate.run(elements)
        # IoU ≈ 0.053, below default 0.3 → no overlap issue
        assert result["passed"] is True

    def test_custom_threshold_catches_small_overlap(self) -> None:
        gate = OverlapGate(iou_threshold=0.01)
        elements = [
            {"id": "a", "x": 0, "y": 0, "width": 100, "height": 100},
            {"id": "b", "x": 90, "y": 0, "width": 100, "height": 100},
        ]
        result = gate.run(elements)
        assert result["passed"] is False
        assert any(i["type"] == "overlap" for i in result["issues"])

    def test_elements_missing_coords_skipped(self) -> None:
        gate = OverlapGate()
        elements = [
            {"id": "no_coords"},
            {"id": "has_coords", "x": 0, "y": 0, "width": 100, "height": 100},
        ]
        result = gate.run(elements)
        assert result["passed"] is True  # only one valid box, no pairs

    def test_invalid_viewport(self) -> None:
        gate = OverlapGate()
        result = gate.run([], viewport=(0, 1080))
        assert result["passed"] is False
        assert result["issues"][0]["type"] == "invalid_viewport"

    def test_invalid_viewport_negative(self) -> None:
        gate = OverlapGate()
        result = gate.run([], viewport=(-1, 1080))
        assert result["passed"] is False

    def test_high_severity_for_large_overlap(self) -> None:
        gate = OverlapGate(iou_threshold=0.1)
        elements = [
            {"id": "a", "x": 0, "y": 0, "width": 100, "height": 100},
            {"id": "b", "x": 0, "y": 0, "width": 100, "height": 100},  # identical → iou=1.0
        ]
        result = gate.run(elements)
        overlap_issues = [i for i in result["issues"] if i["type"] == "overlap"]
        assert len(overlap_issues) == 1
        assert overlap_issues[0]["severity"] == "high"  # iou >= 0.8

    def test_medium_severity_for_moderate_overlap(self) -> None:
        gate = OverlapGate(iou_threshold=0.1)
        elements = [
            {"id": "a", "x": 0, "y": 0, "width": 100, "height": 100},
            {"id": "b", "x": 40, "y": 0, "width": 100, "height": 100},  # iou ≈ 0.43
        ]
        result = gate.run(elements)
        overlap_issues = [i for i in result["issues"] if i["type"] == "overlap"]
        assert len(overlap_issues) == 1
        assert overlap_issues[0]["severity"] == "medium"  # 0.1 < iou < 0.8


# ── OverlapGate constructor tests ────────────────────────────────────────────


class TestOverlapGateInit:
    def test_default_threshold(self) -> None:
        gate = OverlapGate()
        assert gate.iou_threshold == 0.3

    def test_custom_threshold(self) -> None:
        gate = OverlapGate(iou_threshold=0.5)
        assert gate.iou_threshold == 0.5

    def test_zero_threshold(self) -> None:
        gate = OverlapGate(iou_threshold=0.0)
        assert gate.iou_threshold == 0.0

    def test_negative_threshold_raises(self) -> None:
        try:
            OverlapGate(iou_threshold=-0.1)
            assert False, "expected ValueError"
        except ValueError:
            pass

    def test_threshold_above_one_raises(self) -> None:
        try:
            OverlapGate(iou_threshold=1.5)
            assert False, "expected ValueError"
        except ValueError:
            pass


# ── compute_overlaps static method tests ─────────────────────────────────────


class TestComputeOverlaps:
    def test_no_boxes(self) -> None:
        assert OverlapGate.compute_overlaps([]) == []

    def test_single_box(self) -> None:
        assert OverlapGate.compute_overlaps([(0, 0, 10, 10)]) == []

    def test_overlap_detected(self) -> None:
        boxes = [(0, 0, 100, 100), (50, 50, 150, 150)]
        issues = OverlapGate.compute_overlaps(boxes, threshold=0.1)
        assert len(issues) == 1
        assert issues[0]["type"] == "overlap"
        assert issues[0]["index_a"] == 0
        assert issues[0]["index_b"] == 1

    def test_no_overlap_below_threshold(self) -> None:
        boxes = [(0, 0, 100, 100), (200, 200, 300, 300)]
        issues = OverlapGate.compute_overlaps(boxes, threshold=0.1)
        assert issues == []

    def test_multiple_overlaps(self) -> None:
        boxes = [
            (0, 0, 100, 100),
            (50, 50, 150, 150),  # overlaps with 0
            (200, 200, 300, 300),  # no overlap
            (250, 250, 350, 350),  # overlaps with 2
        ]
        issues = OverlapGate.compute_overlaps(boxes, threshold=0.1)
        assert len(issues) == 2

    def test_custom_threshold(self) -> None:
        # Two 100x100 boxes offset by (80,80) → iou ≈ 0.020
        boxes = [(0, 0, 100, 100), (80, 80, 180, 180)]
        # Default threshold 0.3 > 0.020 → no overlap
        issues_default = OverlapGate.compute_overlaps(boxes, threshold=0.3)
        assert issues_default == []
        # Relaxed threshold 0.01 < 0.020 → overlap detected
        issues_relaxed = OverlapGate.compute_overlaps(boxes, threshold=0.01)
        assert len(issues_relaxed) == 1


# ── evaluate_overlap_policy tests ─────────────────────────────────────────────


class TestEvaluateOverlapPolicy:
    def test_policy_pass_no_issues(self) -> None:
        from videoforge.review.frame_reviewer import FrameReviewer
        assert FrameReviewer.evaluate_overlap_policy({"issues": []}) == "pass"

    def test_policy_fail_on_high(self) -> None:
        from videoforge.review.frame_reviewer import FrameReviewer
        result = FrameReviewer.evaluate_overlap_policy({
            "issues": [{"severity": "high", "type": "overlap", "iou": 0.9}],
        })
        assert result == "fail"

    def test_policy_warn_on_medium(self) -> None:
        from videoforge.review.frame_reviewer import FrameReviewer
        result = FrameReviewer.evaluate_overlap_policy({
            "issues": [{"severity": "medium", "type": "clipped"}],
        })
        assert result == "warn"

    def test_policy_warn_on_mixed_low_medium(self) -> None:
        from videoforge.review.frame_reviewer import FrameReviewer
        result = FrameReviewer.evaluate_overlap_policy({
            "issues": [
                {"severity": "low", "type": "unknown"},
                {"severity": "medium", "type": "clipped"},
            ],
        })
        assert result == "warn"

    def test_policy_fail_high_overrides_medium(self) -> None:
        from videoforge.review.frame_reviewer import FrameReviewer
        result = FrameReviewer.evaluate_overlap_policy({
            "issues": [
                {"severity": "medium", "type": "clipped"},
                {"severity": "high", "type": "overlap", "iou": 0.9},
            ],
        })
        assert result == "fail"


# ── FrameReviewer integration tests ──────────────────────────────────────────


class TestFrameReviewerLayoutOverlap:
    def test_check_layout_overlap_delegates(self) -> None:
        from videoforge.review.frame_reviewer import FrameReviewer

        fr = FrameReviewer()
        elements = [{"id": "a", "x": 0, "y": 0, "width": 100, "height": 100}]
        result = fr.check_layout_overlap(elements)
        assert "issues" in result
        assert "passed" in result

    def test_aggregate_review_includes_layout_overlap(self) -> None:
        from unittest.mock import MagicMock, patch
        from videoforge.review.frame_reviewer import FrameReviewer

        fr = FrameReviewer()
        with patch.object(fr._l0, "run") as mock_l0, \
             patch.object(fr, "check_integrity") as mock_l1, \
             patch.object(fr, "check_frames") as mock_l2, \
             patch.object(fr._l3, "run") as mock_l3, \
             patch.object(fr._l4, "run") as mock_l4, \
             patch.object(fr._l5, "run") as mock_l5:

            mock_l0.return_value = {"passed": True, "issues": [], "sampled_frames": 6}
            mock_l1.return_value = {"passed": True, "issues": [], "total_frames": 300}
            mock_l2.return_value = {"passed": True, "issues": []}
            mock_l3.return_value = {"passed": True, "issues": []}
            mock_l4.return_value = {"passed": True, "issues": []}
            mock_l5.return_value = {"passed": True, "issues": []}

            result = fr.aggregate_review("test.mp4", input_props={"elements": []})
            assert "l2_layout_overlap" in result["levels"]
            assert result["levels"]["l2_layout_overlap"]["passed"] is True

    def test_aggregate_review_layout_overlap_skipped_when_l1_fails(self) -> None:
        from unittest.mock import MagicMock, patch
        from videoforge.review.frame_reviewer import FrameReviewer

        fr = FrameReviewer()
        with patch.object(fr._l0, "run") as mock_l0, \
             patch.object(fr, "check_integrity") as mock_l1:

            mock_l0.return_value = {"passed": True, "issues": [], "sampled_frames": 6}
            mock_l1.return_value = {"passed": False, "issues": [{"type": "black_frame"}], "total_frames": 300}

            result = fr.aggregate_review("test.mp4", input_props={"elements": [{"x": 0, "y": 0, "width": 2000, "height": 100}]})
            # If L1 fails, layout overlap should be skipped
            assert "l2_layout_overlap" not in result["levels"]
