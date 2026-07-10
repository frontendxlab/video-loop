"""Tests for DualChartAxisGate — deterministic axis-sanity checks."""

from __future__ import annotations

from videoforge.review.axis_gate import DualChartAxisGate


class TestDualChartAxisGate:
    """DualChartAxisGate.run() unit tests."""

    def test_minimal_chart_passes(self) -> None:
        """Chart with bar_data only → pass."""
        result = DualChartAxisGate.run({"bar_data": [10, 20, 30]})
        assert result["passed"] is True

    def test_no_data_fails(self) -> None:
        """No data series at all → fail."""
        result = DualChartAxisGate.run({})
        assert result["passed"] is False
        assert result["issues"][0]["type"] == "no_chart_data"

    def test_x_labels_required(self) -> None:
        """x_labels with empty list → fail."""
        result = DualChartAxisGate.run({"x_labels": [], "bar_data": [10]})
        assert result["passed"] is False
        assert result["issues"][0]["type"] == "x_labels_empty"

    def test_x_labels_with_data_matches(self) -> None:
        """Labels and data same length → pass."""
        result = DualChartAxisGate.run({
            "x_labels": ["Jan", "Feb", "Mar"],
            "bar_data": [10, 20, 30],
        })
        assert result["passed"] is True

    def test_x_labels_blank_entry(self) -> None:
        """x_labels with blank entry → medium severity."""
        result = DualChartAxisGate.run({
            "x_labels": ["Jan", "", "Mar"],
            "bar_data": [10, 20, 30],
        })
        assert result["passed"] is False
        types = [i["type"] for i in result["issues"]]
        assert "x_labels_blank_entry" in types

    def test_data_label_mismatch(self) -> None:
        """bar_data length != x_labels → medium."""
        result = DualChartAxisGate.run({
            "x_labels": ["Jan", "Feb", "Mar"],
            "bar_data": [10, 20],
        })
        assert result["passed"] is False
        types = [i["type"] for i in result["issues"]]
        assert "data_label_mismatch" in types

    def test_dual_axes_with_secondary_passes(self) -> None:
        """dual_axes enabled with line_data → pass."""
        result = DualChartAxisGate.run({
            "x_labels": ["A", "B"],
            "bar_data": [10, 20],
            "line_data": [15, 25],
            "dual_axes": True,
        })
        assert result["passed"] is True

    def test_dual_axes_no_secondary_fails(self) -> None:
        """dual_axes enabled without line_data → fail."""
        result = DualChartAxisGate.run({
            "x_labels": ["A", "B"],
            "bar_data": [10, 20],
            "dual_axes": True,
        })
        assert result["passed"] is False
        types = [i["type"] for i in result["issues"]]
        assert "dual_axes_no_secondary" in types

    def test_bar_values_alias(self) -> None:
        """bar_values accepted as alias for bar_data."""
        result = DualChartAxisGate.run({"bar_values": [1, 2, 3]})
        assert result["passed"] is True

    def test_line_data_without_bar_passes(self) -> None:
        """Only line_data (no bar) → pass."""
        result = DualChartAxisGate.run({"line_data": [5, 10, 15]})
        assert result["passed"] is True

    def test_axis_label_empty(self) -> None:
        """Empty y_label → low severity issue."""
        result = DualChartAxisGate.run({
            "bar_data": [1, 2],
            "y_label": "",
        })
        assert result["passed"] is False
        types = [i["type"] for i in result["issues"]]
        assert "axis_label_empty" in types

    def test_x_labels_not_a_list(self) -> None:
        """x_labels as string → high severity."""
        result = DualChartAxisGate.run({
            "x_labels": "not_a_list",
            "bar_data": [1, 2],
        })
        assert result["passed"] is False
        assert result["issues"][0]["type"] == "x_labels_not_a_list"

    def test_line_data_mismatch(self) -> None:
        """line_data length != x_labels → medium."""
        result = DualChartAxisGate.run({
            "x_labels": ["A", "B", "C"],
            "bar_data": [1, 2, 3],
            "line_data": [10, 20],
        })
        assert result["passed"] is False
        mismatches = [i for i in result["issues"] if i["type"] == "data_label_mismatch"]
        assert len(mismatches) >= 1  # line_data mismatch

    def test_secondary_label_empty(self) -> None:
        """Empty secondary_label → low severity issue."""
        result = DualChartAxisGate.run({
            "bar_data": [1, 2],
            "secondary_label": "",
        })
        assert result["passed"] is False
        types = [i["type"] for i in result["issues"]]
        assert "axis_label_empty" in types

    def test_multiple_issues(self) -> None:
        """Multiple axis issues reported together."""
        result = DualChartAxisGate.run({
            "x_labels": [],
            "dual_axes": True,
        })
        assert result["passed"] is False
        types = {i["type"] for i in result["issues"]}
        assert "x_labels_empty" in types
        assert "no_chart_data" in types
        assert "dual_axes_no_secondary" in types


class TestDualChartAxisGatePolicy:
    """FrameReviewer.evaluate_axis_policy tests."""

    def test_policy_pass_no_issues(self) -> None:
        from videoforge.review.frame_reviewer import FrameReviewer
        assert FrameReviewer.evaluate_axis_policy({"issues": []}) == "pass"

    def test_policy_fail_on_high(self) -> None:
        from videoforge.review.frame_reviewer import FrameReviewer
        assert FrameReviewer.evaluate_axis_policy({
            "issues": [{"severity": "high", "type": "no_chart_data"}],
        }) == "fail"

    def test_policy_warn_on_medium(self) -> None:
        from videoforge.review.frame_reviewer import FrameReviewer
        assert FrameReviewer.evaluate_axis_policy({
            "issues": [{"severity": "medium", "type": "data_label_mismatch"}],
        }) == "warn"


class TestFrameReviewerAxis:
    """FrameReviewer.check_axis_sanity integration tests."""

    def test_check_axis_delegates(self) -> None:
        from videoforge.review.frame_reviewer import FrameReviewer
        fr = FrameReviewer()
        result = fr.check_axis_sanity({"bar_data": [1, 2, 3]})
        assert "issues" in result
        assert "passed" in result
        assert result["passed"] is True

    def test_check_axis_fails_empty(self) -> None:
        from videoforge.review.frame_reviewer import FrameReviewer
        fr = FrameReviewer()
        result = fr.check_axis_sanity({})
        assert result["passed"] is False
