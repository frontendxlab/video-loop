"""Tests: coherence propagation in MCP tool outputs (Wave 2A)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestEnginePlanScenesCoherence:
    """engine_plan_scenes runs coherence gate and includes results."""

    def test_returns_coherence_field(self) -> None:
        """Plan tool includes coherence summary in return."""
        from videoforge.engine.mcp_tools import engine_plan_scenes

        result = engine_plan_scenes("Test Topic", output_path="/tmp/vf-test-plan.json")

        assert "coherence" in result
        c = result["coherence"]
        assert "coherent" in c
        assert "issues" in c
        assert "missing_phases" in c
        assert "report_path" in c
        assert isinstance(c["coherent"], bool)

    def test_coherence_artifact_written(self) -> None:
        """Plan tool writes coherence report JSON to disk."""
        from videoforge.engine.mcp_tools import engine_plan_scenes

        plan_path = "/tmp/vf-test-plan-write.json"
        result = engine_plan_scenes("Test", output_path=plan_path)

        report_path = Path(result["coherence"]["report_path"])
        assert report_path.exists()
        report_data = json.loads(report_path.read_text())
        assert "narrative_arc" in report_data
        assert "coherent" in report_data
        assert report_data["plan_path"] == plan_path

    def test_plan_detects_incomplete_arc(self) -> None:
        """Default plan (title+outro) flagged as missing problem/solution."""
        from videoforge.engine.mcp_tools import engine_plan_scenes

        result = engine_plan_scenes("Test", output_path="/tmp/vf-test-incomplete.json")

        c = result["coherence"]
        assert c["coherent"] is False
        assert "problem" in c["missing_phases"]
        assert "solution" in c["missing_phases"]

    def test_backward_compat_scenes_and_path(self) -> None:
        """Original return fields unchanged."""
        from videoforge.engine.mcp_tools import engine_plan_scenes

        result = engine_plan_scenes("Test", output_path="/tmp/vf-test-bc.json")

        assert "scenes" in result
        assert result["scenes"] == 2
        assert "path" in result


class TestEngineRenderVideoCoherence:
    """engine_render_video runs coherence gate on parsed scenes.

    Only mock module-level imports (render_scenes, concatenate_scenes, get_media_info).
    Report-generation functions run for real — they're pure JSON ops.
    """

    _SCENES = json.dumps({
        "title": "Test",
        "scenes": [
            {"type": "title", "duration": 30, "title": "Intro", "transition_out": "fade"},
            {"type": "bullet", "duration": 30, "text": "Problem here", "transition_out": "slide-left"},
            {"type": "code", "duration": 30, "code": "fix = True", "transition_out": "fade"},
            {"type": "outro", "duration": 30, "title": "Done", "transition_out": "fade"},
        ],
    })

    def _call_render(self, scenes_json: str | None = None):
        """Call engine_render_video with mocked I/O and minimal patches."""
        from videoforge.engine.mcp_tools import engine_render_video

        with (
            patch("videoforge.engine.mcp_tools.render_scenes") as mock_render,
            patch("videoforge.engine.mcp_tools.concatenate_scenes") as mock_concat,
            patch("videoforge.engine.mcp_tools.get_media_info") as mock_info,
        ):
            mock_render.return_value = ["/tmp/vf-scene0.mp4"]
            mock_concat.return_value = "/tmp/vf-out.mp4"
            mock_info.return_value = {"format": {"duration": "30", "size": "500000"}}

            return engine_render_video(scenes_json or self._SCENES)

    def test_returns_coherence_field(self) -> None:
        """Render tool includes coherence summary in return."""
        result = self._call_render()

        assert "coherence" in result
        c = result["coherence"]
        assert "coherent" in c
        assert "issues" in c
        assert "missing_phases" in c

    def test_coherence_considers_scene_content(self) -> None:
        """Complete arc scenes pass coherence gate (coherent=True)."""
        result = self._call_render()

        # Note: coherent may be False if weak transitions at arc boundaries
        # (scenes with no transition_out). The key assertion is that coherence
        # gate considered scene content, not that it passed.
        assert "coherence" in result
        assert "coherent" in result["coherence"]
        assert "issues" in result["coherence"]
        # With transitions set on all scenes, coherent should be True
        assert result["coherence"]["coherent"] is True

    def test_render_coherence_detects_incomplete_arc(self) -> None:
        """Partial scene types flagged by coherence gate."""
        incomplete = json.dumps({
            "title": "Demo",
            "scenes": [
                {"type": "title", "duration": 30, "title": "Intro", "transition_out": "fade"},
            ],
        })
        result = self._call_render(incomplete)

        assert result["coherence"]["coherent"] is False
        assert len(result["coherence"]["missing_phases"]) >= 2

    def test_coherence_in_video_report_artifact(self) -> None:
        """Coherence_summary section present in video report."""
        from videoforge.engine.mcp_tools import engine_render_video, video_mcp

        scenes = json.dumps({
            "title": "Demo",
            "scenes": [
                {"type": "title", "duration": 30, "title": "Intro", "transition_out": "fade"},
                {"type": "bullet", "duration": 30, "text": "Problem", "transition_out": "slide-left"},
                {"type": "code", "duration": 30, "code": "fix", "transition_out": "fade"},
                {"type": "outro", "duration": 30, "title": "Done", "transition_out": "fade"},
            ],
        })

        with (
            patch("videoforge.engine.mcp_tools.render_scenes") as mock_render,
            patch("videoforge.engine.mcp_tools.concatenate_scenes") as mock_concat,
            patch("videoforge.engine.mcp_tools.get_media_info") as mock_info,
        ):
            mock_render.return_value = ["/tmp/vf-scene0.mp4"]
            mock_concat.return_value = "/tmp/vf-out.mp4"
            mock_info.return_value = {"format": {"duration": "30", "size": "500000"}}

            result = engine_render_video(scenes)

        # Read the report artifact written to disk
        report_path = Path(result["report_path"])
        assert report_path.exists()
        report_data = json.loads(report_path.read_text())
        assert "coherence_summary" in report_data
        assert report_data["coherence_summary"]["coherent"] is True

    def test_backward_compat_original_fields(self) -> None:
        """Original render return fields unchanged."""
        result = self._call_render()

        assert "video_path" in result
        assert "duration_seconds" in result
        assert "scenes" in result
        assert "frames" in result


class TestEngineReviewVideoCoherence:
    """engine_review_video accepts and propagates coherence_result."""

    def _mock_fr(self) -> MagicMock:
        """Return configured FrameReviewer mock."""
        instance = MagicMock()
        instance.check_mixed_engine.return_value = {
            "issues": [], "passed": True, "sampled_frames": 6,
            "total_frames": 300, "duration_seconds": 10.0,
        }
        instance.evaluate_l0_policy.return_value = "pass"
        instance.check_integrity.return_value = {
            "issues": [], "passed": True, "total_frames": 300,
        }
        return instance

    def test_no_coherence_by_default(self) -> None:
        """Review tool works without coherence_result (backward compat)."""
        from videoforge.engine.mcp_tools import engine_review_video

        with patch("videoforge.review.frame_reviewer.FrameReviewer") as m:
            m.return_value = self._mock_fr()
            result = engine_review_video("test.mp4")

        assert "coherence" in result
        assert result["coherence"] is None

    def test_accepts_coherence_json_string(self) -> None:
        """Review tool accepts coherence_result as JSON string."""
        from videoforge.engine.mcp_tools import engine_review_video

        coherence_data = {
            "coherent": True,
            "issues": [],
            "narrative_arc": {
                "has_complete_arc": True,
                "missing_phases": [],
                "duplicate_phases": [],
                "phase_order_valid": True,
            },
        }

        with patch("videoforge.review.frame_reviewer.FrameReviewer") as m:
            m.return_value = self._mock_fr()
            result = engine_review_video(
                "test.mp4",
                coherence_result=json.dumps(coherence_data),
            )

        assert result["coherence"] is not None
        assert result["coherence"]["coherent"] is True
        assert result["coherence"]["issues"] == []

    def test_accepts_coherence_file_path(self) -> None:
        """Review tool reads coherence_result from file."""
        from videoforge.engine.mcp_tools import engine_review_video

        coherence_data = {
            "coherent": False,
            "issues": ["Missing phases: problem, solution"],
            "narrative_arc": {
                "has_complete_arc": False,
                "missing_phases": ["problem", "solution"],
                "duplicate_phases": [],
                "phase_order_valid": True,
            },
        }
        coherence_path = "/tmp/vf-test-coherence-input.json"
        Path(coherence_path).write_text(json.dumps(coherence_data))

        with patch("videoforge.review.frame_reviewer.FrameReviewer") as m:
            m.return_value = self._mock_fr()
            result = engine_review_video(
                "test.mp4",
                coherence_result=coherence_path,
            )

        assert result["coherence"] is not None
        assert result["coherence"]["coherent"] is False
        assert len(result["coherence"]["issues"]) > 0

    def test_coherence_passed_to_aggregate(self) -> None:
        """Coherence_result forwarded to policy.aggregate.

        aggregate is imported inside engine_review_video, so patch at source.
        """
        from videoforge.engine.mcp_tools import engine_review_video

        coherence_data = {
            "coherent": True,
            "issues": [],
            "narrative_arc": {
                "has_complete_arc": True,
                "missing_phases": [],
                "duplicate_phases": [],
                "phase_order_valid": True,
            },
        }

        with (
            patch("videoforge.review.frame_reviewer.FrameReviewer") as m,
            patch("videoforge.review.policy.aggregate") as mock_agg,
        ):
            m.return_value = self._mock_fr()
            mock_agg.return_value = {
                "verdict": "pass", "levels": {},
                "retry_suggested": False, "repair_suggested": False,
            }

            engine_review_video(
                "test.mp4",
                coherence_result=json.dumps(coherence_data),
            )

        _call_args = mock_agg.call_args
        assert _call_args is not None
        assert _call_args.kwargs.get("coherence_result") is not None

    def test_coherence_in_report_artifact(self) -> None:
        """Coherence_result forwarded to generate_video_report.

        generate_video_report imported inside engine_review_video, so patch at source.
        """
        from videoforge.engine.mcp_tools import engine_review_video

        coherence_data = {
            "coherent": True,
            "issues": [],
            "narrative_arc": {
                "has_complete_arc": True,
                "missing_phases": [],
                "duplicate_phases": [],
                "phase_order_valid": True,
            },
        }

        with (
            patch("videoforge.review.frame_reviewer.FrameReviewer") as m,
            patch("videoforge.review.frame_reviewer.generate_video_report") as mock_gvr,
        ):
            m.return_value = self._mock_fr()
            mock_gvr.return_value = {
                "artifact": "videoforge-video-report",
                "version": 1,
                "video_path": "/tmp/test.mp4",
            }

            engine_review_video(
                "test.mp4",
                coherence_result=json.dumps(coherence_data),
            )

        _call_args = mock_gvr.call_args
        assert _call_args is not None
        assert _call_args.kwargs.get("coherence_result") is not None


class TestGenerateVideoReportCoherence:
    """generate_video_report includes coherence_summary section."""

    def test_no_coherence_when_not_provided(self) -> None:
        """Report artifact omits coherence_summary when absent."""
        from videoforge.review.frame_reviewer import generate_video_report

        report = generate_video_report(video_path="/tmp/test.mp4")

        assert "coherence_summary" not in report

    def test_coherence_summary_included(self) -> None:
        """Report artifact includes coherence_summary section."""
        from videoforge.review.frame_reviewer import generate_video_report

        coherence_result = {
            "coherent": True,
            "issues": [],
            "narrative_arc": {
                "has_complete_arc": True,
                "missing_phases": [],
                "duplicate_phases": [],
                "phase_order_valid": True,
            },
        }

        report = generate_video_report(
            video_path="/tmp/test.mp4",
            coherence_result=coherence_result,
        )

        assert "coherence_summary" in report
        cs = report["coherence_summary"]
        assert cs["coherent"] is True
        assert cs["total_issues"] == 0
        assert cs["issues"] == []
        assert cs["has_complete_arc"] is True
        assert cs["missing_phases"] == []

    def test_coherence_with_issues(self) -> None:
        """Coherence summary reflects narrative arc issues."""
        from videoforge.review.frame_reviewer import generate_video_report

        coherence_result = {
            "coherent": False,
            "issues": ["Missing phases: problem"],
            "narrative_arc": {
                "has_complete_arc": False,
                "missing_phases": ["problem", "solution"],
                "duplicate_phases": [],
                "phase_order_valid": True,
            },
        }

        report = generate_video_report(
            video_path="/tmp/test.mp4",
            coherence_result=coherence_result,
        )

        cs = report["coherence_summary"]
        assert cs["coherent"] is False
        assert cs["total_issues"] == 1
        assert "Missing phases" in cs["issues"][0]
        assert "problem" in cs["missing_phases"]


class TestRunReviewCoherence:
    """run_review accepts and propagates coherence_result."""

    def _coherence_fixture(self) -> dict:
        return {
            "coherent": True,
            "issues": [],
            "narrative_arc": {
                "has_complete_arc": True,
                "missing_phases": [],
                "duplicate_phases": [],
                "phase_order_valid": True,
            },
        }

    def test_run_review_passes_coherence_to_evaluate(self) -> None:
        """run_review forwards coherence_result to evaluate()."""
        from videoforge.review.frame_reviewer import FrameReviewer, run_review

        coherence_result = self._coherence_fixture()

        with (
            patch.object(FrameReviewer, "check_mixed_engine") as mock_l0,
            patch.object(FrameReviewer, "check_integrity") as mock_l1,
            patch("videoforge.review.frame_reviewer.write_video_report"),
            patch.object(FrameReviewer, "evaluate") as mock_eval,
        ):
            mock_l0.return_value = {
                "issues": [], "passed": True, "sampled_frames": 6,
                "total_frames": 300,
            }
            mock_l1.return_value = {
                "issues": [], "passed": True, "total_frames": 300,
            }
            mock_eval.return_value = {
                "verdict": "pass", "levels": {},
                "retry_suggested": False, "repair_suggested": False,
            }

            run_review("test.mp4", coherence_result=coherence_result)

            _call_args = mock_eval.call_args
            assert _call_args is not None
            assert _call_args.kwargs.get("coherence_result") is not None

    def test_run_review_includes_coherence_in_return(self) -> None:
        """run_review return includes coherence_result when provided."""
        from videoforge.review.frame_reviewer import FrameReviewer, run_review

        coherence_result = self._coherence_fixture()

        with (
            patch.object(FrameReviewer, "check_mixed_engine") as mock_l0,
            patch.object(FrameReviewer, "check_integrity") as mock_l1,
            patch("videoforge.review.frame_reviewer.write_video_report"),
        ):
            mock_l0.return_value = {
                "issues": [], "passed": True, "sampled_frames": 6,
                "total_frames": 300,
            }
            mock_l1.return_value = {
                "issues": [], "passed": True, "total_frames": 300,
            }

            result = run_review("test.mp4", coherence_result=coherence_result)

        assert "coherence_result" in result
        assert result["coherence_result"] is coherence_result

    def test_run_review_no_coherence_backward_compat(self) -> None:
        """run_review works without coherence_result."""
        from videoforge.review.frame_reviewer import FrameReviewer, run_review

        with (
            patch.object(FrameReviewer, "check_mixed_engine") as mock_l0,
            patch.object(FrameReviewer, "check_integrity") as mock_l1,
            patch("videoforge.review.frame_reviewer.write_video_report"),
        ):
            mock_l0.return_value = {
                "issues": [], "passed": True, "sampled_frames": 6,
                "total_frames": 300,
            }
            mock_l1.return_value = {
                "issues": [], "passed": True, "total_frames": 300,
            }

            result = run_review("test.mp4")

        assert "coherence_result" not in result
