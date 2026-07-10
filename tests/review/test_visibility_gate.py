"""Tests for VisibilityGate — deterministic nonblank/visibility check."""

from __future__ import annotations

from videoforge.review.visibility_gate import VisibilityGate


class TestVisibilityGate:
    """VisibilityGate.run() unit tests."""

    def test_no_data_arrays_fails(self) -> None:
        """Empty payload with no data arrays → fail."""
        result = VisibilityGate.run({})
        assert result["passed"] is False
        assert result["issues"][0]["type"] == "no_data_arrays"

    def test_non_3d_payload_fails(self) -> None:
        """Payload with only non-data keys → fail."""
        result = VisibilityGate.run({"title": "hello", "type": "text"})
        assert result["passed"] is False

    def test_populated_data_passes(self) -> None:
        """Payload with non-empty data_points → pass."""
        result = VisibilityGate.run({"data_points": [1, 2, 3, 4, 5]})
        assert result["passed"] is True

    def test_empty_data_array_fails(self) -> None:
        """Payload with empty data array → fail."""
        result = VisibilityGate.run({"objects": []})
        assert result["passed"] is False
        assert result["issues"][0]["type"] == "empty_data_arrays"

    def test_empty_and_non_empty_mixed(self) -> None:
        """One empty array among non-empty → fail."""
        result = VisibilityGate.run({
            "objects": [],
            "data_points": [1, 2, 3],
        })
        assert result["passed"] is False
        assert result["issues"][0]["type"] == "empty_data_arrays"
        assert "objects" in result["issues"][0].get("empty_keys", [])

    def test_route_coords_passes(self) -> None:
        """map3d scene with route_coords → pass."""
        result = VisibilityGate.run({
            "route_coords": [(0, 0), (10, 20), (30, 50), (60, 80)],
        })
        assert result["passed"] is True

    def test_bar_values_passes(self) -> None:
        """3d-ranking scene with bar_values → pass."""
        result = VisibilityGate.run({
            "bar_values": [10, 20, 30, 40, 50],
        })
        assert result["passed"] is True

    def test_geometry_passes(self) -> None:
        """three-scene with geometry → pass (>= 2 items)."""
        result = VisibilityGate.run({
            "geometry": [{"type": "cube", "size": 1}, {"type": "sphere", "size": 2}],
        })
        assert result["passed"] is True

    def test_series_passes(self) -> None:
        """Chart scene with series → pass."""
        result = VisibilityGate.run({
            "series": [{"name": "A", "data": [1, 2, 3]}, {"name": "B", "data": [4, 5]}],
        })
        assert result["passed"] is True

    def test_sparse_data_warns(self) -> None:
        """Single-item data array → low severity issue."""
        result = VisibilityGate.run({"data_points": [42]})
        assert result["passed"] is False
        types = [i["type"] for i in result["issues"]]
        assert "sparse_data" in types

    def test_two_items_no_warning(self) -> None:
        """Two items is borderline but should not trigger sparse_data."""
        result = VisibilityGate.run({"data_points": [1, 2]})
        # sparse_data triggers when smallest < 2, so 2 items == no warning
        types = [i["type"] for i in result["issues"]]
        assert "sparse_data" not in types

    def test_multiple_known_keys(self) -> None:
        """Multiple known keys in payload — picks up both."""
        result = VisibilityGate.run({
            "objects": [{"id": 1}, {"id": 2}],
            "coordinates": [(1, 2), (3, 4)],
            "nodes": ["a", "b", "c"],
        })
        assert result["passed"] is True

    def test_issue_has_detail_and_severity(self) -> None:
        """Issues should have proper fields."""
        result = VisibilityGate.run({})
        for issue in result["issues"]:
            assert "detail" in issue
            assert "severity" in issue


class TestVisibilityGatePolicy:
    """FrameReviewer.evaluate_visibility_policy tests."""

    def test_policy_pass_no_issues(self) -> None:
        from videoforge.review.frame_reviewer import FrameReviewer
        assert FrameReviewer.evaluate_visibility_policy({"issues": []}) == "pass"

    def test_policy_fail_on_high(self) -> None:
        from videoforge.review.frame_reviewer import FrameReviewer
        assert FrameReviewer.evaluate_visibility_policy({
            "issues": [{"severity": "high", "type": "no_data_arrays"}],
        }) == "fail"

    def test_policy_warn_on_sparse(self) -> None:
        from videoforge.review.frame_reviewer import FrameReviewer
        assert FrameReviewer.evaluate_visibility_policy({
            "issues": [{"severity": "low", "type": "sparse_data"}],
        }) == "warn"


class TestFrameReviewerVisibility:
    """FrameReviewer.check_visibility integration tests."""

    def test_check_visibility_delegates(self) -> None:
        from videoforge.review.frame_reviewer import FrameReviewer
        fr = FrameReviewer()
        result = fr.check_visibility({"data_points": [1, 2, 3]})
        assert "issues" in result
        assert "passed" in result
        assert result["passed"] is True

    def test_check_visibility_fails_blank(self) -> None:
        from videoforge.review.frame_reviewer import FrameReviewer
        fr = FrameReviewer()
        result = fr.check_visibility({})
        assert result["passed"] is False
