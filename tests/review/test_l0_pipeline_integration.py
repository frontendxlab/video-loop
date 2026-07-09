"""Integration tests: L0 gate wired into CLI/pipeline paths."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from videoforge.review.frame_reviewer import FrameReviewer, run_review


# ── Policy evaluation ───────────────────────────────────────────────────────


class TestL0Policy:
    def test_policy_pass_no_issues(self) -> None:
        assert FrameReviewer.evaluate_l0_policy({"issues": []}) == "pass"

    def test_policy_fail_on_high(self) -> None:
        assert FrameReviewer.evaluate_l0_policy({
            "issues": [{"severity": "high", "type": "blank_frame"}],
        }) == "fail"

    def test_policy_warn_on_medium(self) -> None:
        assert FrameReviewer.evaluate_l0_policy({
            "issues": [{"severity": "medium", "type": "palette_drift"}],
        }) == "warn"

    def test_policy_warn_on_low(self) -> None:
        assert FrameReviewer.evaluate_l0_policy({
            "issues": [{"severity": "low", "type": "codec_mismatch"}],
        }) == "warn"

    def test_policy_fail_high_overrides_low(self) -> None:
        result = FrameReviewer.evaluate_l0_policy({
            "issues": [
                {"severity": "low", "type": "codec_mismatch"},
                {"severity": "high", "type": "resolution_mismatch"},
            ],
        })
        assert result == "fail"

    def test_policy_warn_medium_overrides_low(self) -> None:
        result = FrameReviewer.evaluate_l0_policy({
            "issues": [
                {"severity": "low", "type": "codec_mismatch"},
                {"severity": "medium", "type": "suspected_freeze"},
            ],
        })
        assert result == "warn"

    def test_policy_missing_severity_defaults_low(self) -> None:
        result = FrameReviewer.evaluate_l0_policy({
            "issues": [{"type": "unknown"}],
        })
        assert result == "warn"


# ── Package import ──────────────────────────────────────────────────────────


class TestPackageExport:
    def test_frame_reviewer_importable_from_package(self) -> None:
        from videoforge.review import FrameReviewer as FR
        assert FR is FrameReviewer

    def test_init_exports_all(self) -> None:
        import videoforge.review
        assert hasattr(videoforge.review, "FrameReviewer")


# ── CLI review command integration (via typer) ────────────────────────────


class TestReviewCommandIntegration:
    """Test that `videoforge review` invokes L0 + L1 and surfaces results."""

    @pytest.fixture
    def mock_fr(self) -> MagicMock:
        """Mock FrameReviewer at definition site (not import site)."""
        with patch("videoforge.review.frame_reviewer.FrameReviewer") as m:
            instance = MagicMock()
            instance.evaluate_l0_policy.return_value = "pass"
            instance.evaluate_overlap_policy.return_value = "pass"
            instance.check_mixed_engine.return_value = {
                "issues": [], "passed": True, "sampled_frames": 6, "total_frames": 300,
            }
            instance.check_integrity.return_value = {
                "issues": [], "passed": True, "total_frames": 300,
            }
            instance.check_layout_overlap.return_value = {"issues": [], "passed": True}
            instance.evaluate.return_value = {
                "verdict": "pass",
                "levels": {"l0": "pass", "l1": "pass", "l2": "pass"},
                "details": {},
                "retry_suggested": False,
                "repair_suggested": False,
            }
            m.return_value = instance
            yield instance

    def test_review_command_runs_l0_and_l1(self, mock_fr: MagicMock, temp_dir: Path) -> None:
        """Verify review command calls both L0 and L1 checks."""
        from typer.testing import CliRunner
        from videoforge.app import app

        video = temp_dir / "test.mp4"
        video.write_text("dummy")
        runner = CliRunner()
        result = runner.invoke(app, ["review", str(video)])

        assert result.exit_code == 0
        mock_fr.check_mixed_engine.assert_called_once_with(str(video))
        mock_fr.evaluate_l0_policy.assert_called_once()
        mock_fr.check_integrity.assert_called_once_with(str(video))

    def test_review_command_fails_on_l0_high(self, mock_fr: MagicMock, temp_dir: Path) -> None:
        """High-severity L0 issues cause non-zero exit."""
        mock_fr.evaluate_l0_policy.return_value = "fail"
        mock_fr.evaluate.return_value = {
            "verdict": "fail",
            "levels": {"l0": "fail", "l1": "pass", "l2": "pass"},
            "details": {},
            "retry_suggested": False,
            "repair_suggested": False,
        }

        from typer.testing import CliRunner
        from videoforge.app import app

        video = temp_dir / "test.mp4"
        video.write_text("dummy")
        runner = CliRunner()
        result = runner.invoke(app, ["review", str(video)])

        assert result.exit_code == 1

    def test_review_command_warns_on_l0_medium(self, mock_fr: MagicMock, temp_dir: Path) -> None:
        """Medium-severity L0 issues warn but exit 0."""
        mock_fr.evaluate_l0_policy.return_value = "warn"
        mock_fr.check_mixed_engine.return_value = {
            "issues": [{"severity": "medium", "type": "palette_drift", "detail": "Color drift"}],
            "passed": False, "sampled_frames": 6, "total_frames": 300,
        }

        from typer.testing import CliRunner
        from videoforge.app import app

        video = temp_dir / "test.mp4"
        video.write_text("dummy")
        runner = CliRunner()
        result = runner.invoke(app, ["review", str(video)])

        # Typed output captured via logging, stdout may be empty.
        # The key behavioral check: L0=warn does NOT cause exit 1.
        assert result.exit_code == 0

    def test_review_command_missing_video(self, temp_dir: Path) -> None:
        """Missing video file fails L0 with high-severity issue -> exit 1."""
        from typer.testing import CliRunner
        from videoforge.app import app

        runner = CliRunner()
        result = runner.invoke(app, ["review", str(temp_dir / "nonexistent.mp4")])

        assert result.exit_code == 1


# ── Pipeline integration ──────────────────────────────────────────────────


class TestPipelineIntegration:
    """Test that pipeline path includes L0 review."""

    @pytest.fixture
    def mock_fr(self) -> MagicMock:
        with patch("videoforge.review.frame_reviewer.FrameReviewer") as m:
            instance = MagicMock()
            instance.evaluate_l0_policy.return_value = "pass"
            instance.check_mixed_engine.return_value = {
                "issues": [], "passed": True, "sampled_frames": 6, "total_frames": 300,
            }
            instance.check_integrity.return_value = {
                "issues": [], "passed": True, "total_frames": 300,
            }
            m.return_value = instance
            yield instance

    def test_pipeline_review_step(self, mock_fr: MagicMock, temp_dir: Path) -> None:
        """Pipeline review step runs L0 then L1 via FrameReviewer."""
        from videoforge.review.frame_reviewer import FrameReviewer as FR
        fr = FR()
        l0 = fr.check_mixed_engine("out.mp4")
        st = fr.evaluate_l0_policy(l0)
        l1 = fr.check_integrity("out.mp4")
        assert st == "pass"
        assert l1["passed"] is True
        mock_fr.check_mixed_engine.assert_called_once_with("out.mp4")

    def test_review_metadata_structure(self) -> None:
        """L0 result dict contains expected keys."""
        from videoforge.review.l0_mixed_engine import L0MixedEngineReview
        r = L0MixedEngineReview()
        result = r.run("dummy.mp4", streams_info=[])
        assert "issues" in result
        assert "passed" in result
        assert "sampled_frames" in result
        assert "total_frames" in result
        assert "duration_seconds" in result


# ── MCP tool integration ──────────────────────────────────────────────────


class TestMcpReviewTool:
    def test_engine_review_video_returns_both_levels(self) -> None:
        """MCP review tool returns L0 and L1 data with combined pass."""
        from videoforge.engine.mcp_tools import engine_review_video

        with patch("videoforge.review.frame_reviewer.FrameReviewer") as m:
            instance = MagicMock()
            instance.check_mixed_engine.return_value = {
                "issues": [], "passed": True, "sampled_frames": 6,
                "total_frames": 300, "duration_seconds": 10.0,
            }
            instance.evaluate_l0_policy.return_value = "pass"
            instance.check_integrity.return_value = {
                "issues": [], "passed": True, "total_frames": 300,
            }
            m.return_value = instance

            result = engine_review_video("test.mp4")

            assert "l0_mixed_engine" in result
            assert "l1_frame_integrity" in result
            assert result["l0_mixed_engine"]["status"] == "pass"
            assert result["l1_frame_integrity"]["passed"] is True
            assert result["passed"] is True

    def test_engine_review_video_fails_on_l0_high(self) -> None:
        """MCP tool reflects L0 fail in combined pass."""
        from videoforge.engine.mcp_tools import engine_review_video

        with patch("videoforge.review.frame_reviewer.FrameReviewer") as m:
            instance = MagicMock()
            instance.check_mixed_engine.return_value = {
                "issues": [{"severity": "high", "type": "blank_frame"}],
                "passed": False, "sampled_frames": 6, "total_frames": 300,
            }
            instance.evaluate_l0_policy.return_value = "fail"
            instance.check_integrity.return_value = {
                "issues": [], "passed": True, "total_frames": 300,
            }
            m.return_value = instance

            result = engine_review_video("test.mp4")

            assert result["l0_mixed_engine"]["status"] == "fail"
            assert result["passed"] is False

    def test_engine_review_video_with_elements_json(self) -> None:
        """MCP tool runs L2b when elements_json provided."""
        from videoforge.engine.mcp_tools import engine_review_video

        with patch("videoforge.review.frame_reviewer.FrameReviewer") as m:
            instance = MagicMock()
            instance.check_mixed_engine.return_value = {
                "issues": [], "passed": True, "sampled_frames": 6,
                "total_frames": 300, "duration_seconds": 10.0,
            }
            instance.evaluate_l0_policy.return_value = "pass"
            instance.evaluate_overlap_policy.return_value = "pass"
            instance.check_integrity.return_value = {
                "issues": [], "passed": True, "total_frames": 300,
            }
            instance.check_layout_overlap.return_value = {"issues": [], "passed": True}
            m.return_value = instance

            result = engine_review_video("test.mp4", elements_json='[{"x":0,"y":0,"width":100,"height":100,"id":"a"}]')

            assert "l2_layout_overlap" in result
            assert result["l2_layout_overlap"]["status"] == "pass"
            assert instance.check_layout_overlap.called


# ── run_review integration ────────────────────────────────────────────────


class TestRunReview:
    def test_run_review_with_elements(self) -> None:
        """run_review includes L2b when elements provided."""
        from videoforge.review.frame_reviewer import FrameReviewer
        with patch.object(FrameReviewer, "check_mixed_engine") as mock_l0, \
             patch.object(FrameReviewer, "check_integrity") as mock_l1, \
             patch.object(FrameReviewer, "check_layout_overlap") as mock_l2, \
             patch("videoforge.review.frame_reviewer.write_video_report") as mock_write:

            mock_l0.return_value = {"issues": [], "passed": True, "sampled_frames": 6, "total_frames": 300}
            mock_l1.return_value = {"issues": [], "passed": True, "total_frames": 300}
            mock_l2.return_value = {"issues": [], "passed": True}
            mock_write.return_value = "/tmp/report.json"

            result = run_review("test.mp4", elements=[{"x": 0, "y": 0, "width": 100, "height": 100}])

            assert "l2_result" in result
            assert "l2_status" in result
            assert result["l2_status"] == "pass"
            mock_l2.assert_called_once()

    def test_run_review_without_elements_skips_l2b(self) -> None:
        """run_review skips L2b when no elements (backward compat)."""
        from videoforge.review.frame_reviewer import FrameReviewer
        with patch.object(FrameReviewer, "check_mixed_engine") as mock_l0, \
             patch.object(FrameReviewer, "check_integrity") as mock_l1, \
             patch.object(FrameReviewer, "check_layout_overlap") as mock_l2, \
             patch("videoforge.review.frame_reviewer.write_video_report") as mock_write:

            mock_l0.return_value = {"issues": [], "passed": True, "sampled_frames": 6, "total_frames": 300}
            mock_l1.return_value = {"issues": [], "passed": True, "total_frames": 300}
            mock_write.return_value = "/tmp/report.json"

            result = run_review("test.mp4")

            assert "l2_result" in result
            assert result["l2_status"] == "pass"
            assert not mock_l2.called

    def test_run_review_l2b_fail_exit(self) -> None:
        """run_review surfaces L2b fail status."""
        from videoforge.review.frame_reviewer import FrameReviewer
        with patch.object(FrameReviewer, "check_mixed_engine") as mock_l0, \
             patch.object(FrameReviewer, "check_integrity") as mock_l1, \
             patch.object(FrameReviewer, "check_layout_overlap") as mock_l2, \
             patch("videoforge.review.frame_reviewer.write_video_report") as mock_write:

            mock_l0.return_value = {"issues": [], "passed": True, "sampled_frames": 6, "total_frames": 300}
            mock_l1.return_value = {"issues": [], "passed": True, "total_frames": 300}
            mock_l2.return_value = {"issues": [{"severity": "high", "type": "overlap", "iou": 0.9}], "passed": False}
            mock_write.return_value = "/tmp/report.json"

            result = run_review("test.mp4", elements=[{"x": 0, "y": 0, "width": 100, "height": 100}])

            assert result["l2_status"] == "fail"
            assert len(result["l2_result"]["issues"]) == 1


# ── CLI review with elements ──────────────────────────────────────────────


class TestReviewCommandL2b:
    """Test that `videoforge review --elements` invokes overlap gate."""

    @pytest.fixture
    def mock_fr(self) -> MagicMock:
        with patch("videoforge.review.frame_reviewer.FrameReviewer") as m:
            instance = MagicMock()
            instance.evaluate_l0_policy.return_value = "pass"
            instance.evaluate_overlap_policy.return_value = "pass"
            instance.check_mixed_engine.return_value = {
                "issues": [], "passed": True, "sampled_frames": 6, "total_frames": 300,
            }
            instance.check_integrity.return_value = {
                "issues": [], "passed": True, "total_frames": 300,
            }
            instance.check_layout_overlap.return_value = {"issues": [], "passed": True}
            instance.evaluate.return_value = {
                "verdict": "pass",
                "levels": {"l0": "pass", "l1": "pass", "l2": "pass"},
                "details": {},
                "retry_suggested": False,
                "repair_suggested": False,
            }
            m.return_value = instance
            yield instance

    def test_review_command_with_elements_file(self, mock_fr: MagicMock, temp_dir: Path) -> None:
        """Review with --elements passes element data to overlap gate."""
        from typer.testing import CliRunner
        from videoforge.app import app

        video = temp_dir / "test.mp4"
        video.write_text("dummy")
        elements_json = temp_dir / "elements.json"
        elements_json.write_text(json.dumps([{"x": 0, "y": 0, "width": 100, "height": 100}]))
        runner = CliRunner()
        result = runner.invoke(app, ["review", str(video), "--elements", str(elements_json)])

        assert result.exit_code == 0
        mock_fr.check_layout_overlap.assert_called_once()

    def test_review_command_l2b_fail_exit(self, mock_fr: MagicMock, temp_dir: Path) -> None:
        """L2b high-severity issues cause non-zero exit."""
        mock_fr.evaluate_overlap_policy.return_value = "fail"
        mock_fr.check_layout_overlap.return_value = {
            "issues": [{"severity": "high", "type": "overlap", "iou": 0.9}], "passed": False,
        }
        mock_fr.evaluate.return_value = {
            "verdict": "fail",
            "levels": {"l0": "pass", "l1": "pass", "l2": "fail"},
            "details": {},
            "retry_suggested": False,
            "repair_suggested": False,
        }

        from typer.testing import CliRunner
        from videoforge.app import app

        video = temp_dir / "test.mp4"
        video.write_text("dummy")
        elements_json = temp_dir / "elements.json"
        elements_json.write_text(json.dumps([{"x": 0, "y": 0, "width": 100, "height": 100}]))
        runner = CliRunner()
        result = runner.invoke(app, ["review", str(video), "--elements", str(elements_json)])

        assert result.exit_code == 1
