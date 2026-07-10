"""Tests for AlphaGate — deterministic alpha/overlay validation."""

from __future__ import annotations

from videoforge.review.alpha_gate import AlphaGate


class TestAlphaGate:
    """AlphaGate.run() unit tests."""

    def test_no_alpha_flag_passes(self) -> None:
        """No alpha request, opaque default → pass."""
        result = AlphaGate.run({})
        assert result["passed"] is True
        assert result["issues"] == []

    def test_alpha_without_opaque_bg(self) -> None:
        """alpha=True with full opacity → fail."""
        result = AlphaGate.run({"alpha": True, "background_opacity": 1.0})
        assert result["passed"] is False
        types = [i["type"] for i in result["issues"]]
        assert "alpha_requested_opaque_bg" in types

    def test_alpha_with_transparent_bg_passes(self) -> None:
        """alpha=True with bg < 1.0 → pass."""
        result = AlphaGate.run({"alpha": True, "background_opacity": 0.0})
        assert result["passed"] is True

    def test_alpha_default_opacity_triggers_issue(self) -> None:
        """alpha=True with no bg_opacity → default 1.0 → fail."""
        result = AlphaGate.run({"alpha": True})
        assert result["passed"] is False
        assert result["issues"][0]["type"] == "alpha_requested_opaque_bg"

    def test_transparent_bg_without_alpha_warns(self) -> None:
        """bg_opacity < 1.0 but no alpha flag → warn."""
        result = AlphaGate.run({"background_opacity": 0.5})
        assert result["passed"] is False
        types = [i["type"] for i in result["issues"]]
        assert "transparent_bg_without_alpha" in types

    def test_negative_bg_opacity_fails(self) -> None:
        """alpha=True with negative bg_opacity → high severity."""
        result = AlphaGate.run({"alpha": True, "background_opacity": -0.5})
        assert result["passed"] is False
        types = [i["type"] for i in result["issues"]]
        assert "negative_bg_opacity" in types

    def test_zero_opacity_passes(self) -> None:
        """alpha=True with bg_opacity=0.0 → valid for fully transparent overlay."""
        result = AlphaGate.run({"alpha": True, "background_opacity": 0.0})
        assert result["passed"] is True

    def test_include_transparent_bg_flag(self) -> None:
        """include_transparent_bg=True should be treated as alpha flag."""
        result = AlphaGate.run({"include_transparent_bg": True, "bg_opacity": 0.0})
        assert result["passed"] is True

        # With opaque bg → fail
        result2 = AlphaGate.run({"include_transparent_bg": True, "bg_opacity": 1.0})
        assert result2["passed"] is False

    def test_transparent_flag(self) -> None:
        """transparent=True should be treated as alpha flag."""
        result = AlphaGate.run({"transparent": True, "background_opacity": 0.3})
        assert result["passed"] is True

        result2 = AlphaGate.run({"transparent": True, "background_opacity": 1.0})
        assert result2["passed"] is False

    def test_bg_opacity_alias(self) -> None:
        """bg_opacity should be accepted as alias for background_opacity."""
        result = AlphaGate.run({"alpha": True, "bg_opacity": 0.0})
        assert result["passed"] is True

        result2 = AlphaGate.run({"alpha": True, "bg_opacity": 1.0})
        assert result2["passed"] is False

    def test_partial_opacity_is_valid(self) -> None:
        """bg_opacity between 0 and 1 with alpha → pass."""
        for opacity in [0.1, 0.25, 0.5, 0.75, 0.99]:
            result = AlphaGate.run({"alpha": True, "background_opacity": opacity})
            assert result["passed"] is True, f"failed at opacity {opacity}"

    def test_issue_has_severity(self) -> None:
        """All issues should have severity field."""
        result = AlphaGate.run({"alpha": True})
        for issue in result["issues"]:
            assert "severity" in issue
            assert issue["severity"] in ("low", "medium", "high")

    def test_issue_has_detail(self) -> None:
        """All issues should have detail field."""
        result = AlphaGate.run({"alpha": True})
        for issue in result["issues"]:
            assert "detail" in issue
            assert isinstance(issue["detail"], str)


class TestAlphaGatePolicy:
    """FrameReviewer.evaluate_alpha_policy tests."""

    def test_policy_pass_no_issues(self) -> None:
        from videoforge.review.frame_reviewer import FrameReviewer
        assert FrameReviewer.evaluate_alpha_policy({"issues": []}) == "pass"

    def test_policy_fail_on_high(self) -> None:
        from videoforge.review.frame_reviewer import FrameReviewer
        assert FrameReviewer.evaluate_alpha_policy({
            "issues": [{"severity": "high", "type": "alpha_requested_opaque_bg"}],
        }) == "fail"

    def test_policy_warn_on_medium(self) -> None:
        from videoforge.review.frame_reviewer import FrameReviewer
        assert FrameReviewer.evaluate_alpha_policy({
            "issues": [{"severity": "medium", "type": "transparent_bg_without_alpha"}],
        }) == "warn"


class TestFrameReviewerAlpha:
    """FrameReviewer.check_alpha integration tests."""

    def test_check_alpha_delegates(self) -> None:
        from videoforge.review.frame_reviewer import FrameReviewer
        fr = FrameReviewer()
        result = fr.check_alpha({"alpha": True})
        assert "issues" in result
        assert "passed" in result
        assert result["passed"] is False  # opaque default

    def test_check_alpha_passes_valid(self) -> None:
        from videoforge.review.frame_reviewer import FrameReviewer
        fr = FrameReviewer()
        result = fr.check_alpha({"alpha": True, "background_opacity": 0.0})
        assert result["passed"] is True
