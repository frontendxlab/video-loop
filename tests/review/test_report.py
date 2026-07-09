"""Tests for assembled-video report artifact (L0 + L1 summary JSON)."""

from __future__ import annotations

import json
from pathlib import Path

from videoforge.review.frame_reviewer import (
    generate_scene_report,
    generate_video_report,
    write_scene_report,
    write_video_report,
)


class TestGenerateVideoReport:
    def test_minimal_args_defaults(self) -> None:
        """Report with only video_path uses sensible defaults."""
        report = generate_video_report(video_path="/tmp/test.mp4")

        assert report["artifact"] == "videoforge-video-report"
        assert report["version"] == 1
        assert report["video_path"].endswith("/tmp/test.mp4")
        assert "report_timestamp" in report

        # Content hash empty when not provided
        assert report["content_hash"] == ""

        # Engine mix defaults to ["remotion"]
        assert report["engine_mix"] == ["remotion"]

        # Render format has pinned defaults
        rf = report["render_format"]
        assert rf["fps"] == 30
        assert rf["width"] == 1920
        assert rf["height"] == 1080
        assert rf["pixel_format"] == "yuv420p"
        assert rf["video_codec"] == "h264"
        assert rf["audio_codec"] == "aac"

        # L0 summary: defaults to pass with 0 issues
        l0 = report["l0_summary"]
        assert l0["status"] == "pass"
        assert l0["passed"] is True
        assert l0["total_issues"] == 0
        assert l0["severity_counts"] == {"high": 0, "medium": 0, "low": 0}
        assert l0["sampled_frames"] == 0

        # L1 summary: defaults to passed=False with 0 issues
        l1 = report["l1_summary"]
        assert l1["passed"] is False
        assert l1["total_frames"] == 0
        assert l1["total_issues"] == 0

    def test_full_args_shape(self) -> None:
        """All fields populated correctly."""
        l0_result = {
            "issues": [
                {"type": "blank_frame", "severity": "high", "frame_index": 0, "detail": "blank"},
                {"type": "palette_drift", "severity": "medium", "frame_index": 5, "detail": "drift"},
                {"type": "codec_mismatch", "severity": "low", "frame_index": 10, "detail": "codec"},
            ],
            "passed": False,
            "sampled_frames": 12,
            "total_frames": 300,
            "duration_seconds": 10.0,
        }
        l1_result = {
            "issues": [
                {"type": "black_frame", "start": 0, "end": 5},
            ],
            "passed": False,
            "total_frames": 300,
        }
        render_format = {
            "fps": 30,
            "width": 1920,
            "height": 1080,
            "pixel_format": "yuv420p",
            "video_codec": "h264",
            "audio_codec": "aac",
        }

        report = generate_video_report(
            video_path="/tmp/build/output.mp4",
            content_hash="a1b2c3d4e5f6g7h8",
            engine_mix=["manim", "remotion", "animotion"],
            render_format=render_format,
            l0_result=l0_result,
            l1_result=l1_result,
            l0_status="fail",
        )

        assert report["content_hash"] == "a1b2c3d4e5f6g7h8"
        # Engine mix sorted
        assert report["engine_mix"] == ["animotion", "manim", "remotion"]

        # Render format
        rf = report["render_format"]
        assert rf["fps"] == 30
        assert rf["width"] == 1920

        # L0 summary
        l0 = report["l0_summary"]
        assert l0["status"] == "fail"
        assert l0["passed"] is False
        assert l0["total_issues"] == 3
        assert l0["severity_counts"] == {"high": 1, "medium": 1, "low": 1}
        assert l0["sampled_frames"] == 12
        assert l0["total_frames"] == 300
        assert l0["duration_seconds"] == 10.0
        assert len(l0["issues"]) == 3

        # L1 summary
        l1 = report["l1_summary"]
        assert l1["passed"] is False
        assert l1["total_frames"] == 300
        assert l1["total_issues"] == 1
        assert len(l1["issues"]) == 1
        assert l1["issues"][0]["type"] == "black_frame"

    def test_severity_counts_aggregated(self) -> None:
        """Severity counts roll up correctly from issues list."""
        l0_result = {
            "issues": [
                {"severity": "high", "type": "blank_frame"},
                {"severity": "high", "type": "all_blank"},
                {"severity": "medium", "type": "palette_drift"},
                {"severity": "low", "type": "codec_mismatch"},
                {"severity": "low", "type": "suspected_freeze"},
            ],
        }
        report = generate_video_report(
            video_path="test.mp4", l0_result=l0_result, l0_status="fail",
        )
        sc = report["l0_summary"]["severity_counts"]
        assert sc["high"] == 2
        assert sc["medium"] == 1
        assert sc["low"] == 2

    def test_severity_counts_empty_issues(self) -> None:
        """Zero issues yields zero counts."""
        report = generate_video_report(
            video_path="test.mp4",
            l0_result={"issues": []},
            l0_status="pass",
        )
        sc = report["l0_summary"]["severity_counts"]
        assert sc == {"high": 0, "medium": 0, "low": 0}

    def test_l1_empty_issues(self) -> None:
        """L1 with no issues still produces valid summary."""
        l1_result = {"issues": [], "passed": True, "total_frames": 300}
        report = generate_video_report(
            video_path="test.mp4",
            l1_result=l1_result,
        )
        l1 = report["l1_summary"]
        assert l1["passed"] is True
        assert l1["total_frames"] == 300
        assert l1["total_issues"] == 0


class TestWriteVideoReport:
    def test_writes_to_dot_report_json(self, temp_dir: Path) -> None:
        """Report file written as <video>.mp4.report.json."""
        video_path = temp_dir / "videos" / "output.mp4"
        video_path.parent.mkdir(parents=True)
        video_path.write_text("dummy")

        report_data = {"artifact": "videoforge-video-report", "version": 1}
        result = write_video_report(report_data, str(video_path))

        expected = video_path.parent / "output.mp4.report.json"
        assert Path(result) == expected
        assert expected.exists()
        data = json.loads(expected.read_text())
        assert data["artifact"] == "videoforge-video-report"

    def test_content_is_serializable(self, temp_dir: Path) -> None:
        """Full report dict serializes to JSON without error."""
        report = generate_video_report(
            video_path=str(temp_dir / "test.mp4"),
            content_hash="deadbeef",
            engine_mix=["remotion", "manim"],
            l0_result={
                "issues": [{"type": "blank_frame", "severity": "high", "detail": "x"}],
                "passed": False,
                "sampled_frames": 6,
                "total_frames": 180,
                "duration_seconds": 6.0,
            },
            l1_result={
                "issues": [{"type": "black_frame", "start": 0, "end": 2}],
                "passed": False,
                "total_frames": 180,
            },
            l0_status="fail",
        )
        dumped = json.dumps(report, indent=2, default=str)
        loaded = json.loads(dumped)
        assert loaded["artifact"] == "videoforge-video-report"
        assert loaded["content_hash"] == "deadbeef"


class TestRunReview:
    """Tests for run_review convenience helper."""

    @pytest.fixture
    def mock_reviewer(self) -> MagicMock:
        from videoforge.review.frame_reviewer import FrameReviewer
        reviewer = MagicMock(spec=FrameReviewer)
        reviewer.check_mixed_engine.return_value = {
            "issues": [], "passed": True, "sampled_frames": 6, "total_frames": 300, "duration_seconds": 10.0,
        }
        reviewer.evaluate_l0_policy.return_value = "pass"
        reviewer.check_integrity.return_value = {
            "issues": [], "passed": True, "total_frames": 300,
        }
        return reviewer

    def test_returns_expected_structure(self, mock_reviewer: MagicMock) -> None:
        """Result dict contains all expected keys."""
        from videoforge.review.frame_reviewer import run_review
        result = run_review("test.mp4", reviewer=mock_reviewer)
        assert set(result.keys()) == {"l0_result", "l0_status", "l1_result", "report", "report_path"}

    def test_runs_l0_and_l1(self, mock_reviewer: MagicMock) -> None:
        """Both L0 and L1 checks called."""
        from videoforge.review.frame_reviewer import run_review
        result = run_review("test.mp4", reviewer=mock_reviewer)
        mock_reviewer.check_mixed_engine.assert_called_once_with("test.mp4")
        mock_reviewer.evaluate_l0_policy.assert_called_once()
        mock_reviewer.check_integrity.assert_called_once_with("test.mp4")

    def test_writes_report_file(self, mock_reviewer: MagicMock, temp_dir: Path) -> None:
        """Report file created alongside video path."""
        from videoforge.review.frame_reviewer import run_review
        video = temp_dir / "videos" / "out.mp4"
        video.parent.mkdir(parents=True)
        video.write_text("dummy")
        result = run_review(str(video), reviewer=mock_reviewer)
        expected = video.parent / "out.mp4.report.json"
        assert Path(result["report_path"]) == expected
        assert expected.exists()

    def test_passes_content_hash_and_engine_mix(self, mock_reviewer: MagicMock) -> None:
        """Content hash and engine mix forwarded to report."""
        from videoforge.review.frame_reviewer import run_review
        result = run_review("test.mp4", content_hash="abc123", engine_mix=["remotion", "manim"],
                            reviewer=mock_reviewer)
        assert result["report"]["content_hash"] == "abc123"
        assert result["report"]["engine_mix"] == ["manim", "remotion"]

    def test_l0_fail_reflected_in_report(self, mock_reviewer: MagicMock) -> None:
        """L0 fail status propagates to report."""
        mock_reviewer.check_mixed_engine.return_value = {
            "issues": [{"severity": "high", "type": "blank_frame", "detail": "blank"}],
            "passed": False, "sampled_frames": 6, "total_frames": 300,
        }
        mock_reviewer.evaluate_l0_policy.return_value = "fail"
        from videoforge.review.frame_reviewer import run_review
        result = run_review("test.mp4", reviewer=mock_reviewer)
        assert result["l0_status"] == "fail"
        assert result["report"]["l0_summary"]["status"] == "fail"
        assert result["report"]["l0_summary"]["total_issues"] == 1


class TestReportShapeIntegration:
    """Verify report shape matches expected keys."""

    def test_all_expected_keys_present(self) -> None:
        """Top-level and nested keys match spec."""
        report = generate_video_report(video_path="/tmp/v.mp4")
        top_keys = {"artifact", "version", "video_path", "report_timestamp",
                     "content_hash", "engine_mix", "render_format",
                     "l0_summary", "l1_summary"}
        assert set(report.keys()) == top_keys

        rf_keys = {"fps", "width", "height", "pixel_format", "video_codec", "audio_codec"}
        assert set(report["render_format"].keys()) == rf_keys

        l0_keys = {"status", "passed", "total_issues", "severity_counts",
                    "sampled_frames", "total_frames", "duration_seconds", "issues"}
        assert set(report["l0_summary"].keys()) == l0_keys

        l1_keys = {"passed", "total_frames", "total_issues", "issues"}
        assert set(report["l1_summary"].keys()) == l1_keys


class TestGenerateSceneReport:
    def test_minimal_args_defaults(self) -> None:
        """Scene report with only required fields uses sensible defaults."""
        report = generate_scene_report(
            scene_index=0,
            engine="remotion",
            duration_frames=180,
            scene_path="/tmp/build/scene_0000.mp4",
        )

        assert report["artifact"] == "videoforge-scene-report"
        assert report["version"] == 1
        assert report["scene_index"] == 0
        assert report["engine"] == "remotion"
        assert report["duration_frames"] == 180
        assert report["scene_path"].endswith("/tmp/build/scene_0000.mp4")
        assert "report_timestamp" in report

        # Content hash empty when not provided
        assert report["content_hash"] == ""

        # Render format has pinned defaults
        rf = report["render_format"]
        assert rf["fps"] == 30
        assert rf["width"] == 1920
        assert rf["height"] == 1080
        assert rf["pixel_format"] == "yuv420p"
        assert rf["video_codec"] == "h264"
        assert rf["audio_codec"] == "aac"

    def test_full_args_shape(self) -> None:
        """All fields populated correctly."""
        report = generate_scene_report(
            scene_index=2,
            engine="manim",
            duration_frames=90,
            scene_path="/tmp/v/scene_0002.mp4",
            render_format={"fps": 60, "width": 3840, "height": 2160, "pixel_format": "yuv444p",
                           "video_codec": "prores", "audio_codec": "pcm_s16le"},
            content_hash="deadbeefcafebabe",
        )

        assert report["scene_index"] == 2
        assert report["engine"] == "manim"
        assert report["duration_frames"] == 90
        assert report["content_hash"] == "deadbeefcafebabe"

        rf = report["render_format"]
        assert rf["fps"] == 60
        assert rf["width"] == 3840
        assert rf["height"] == 2160
        assert rf["pixel_format"] == "yuv444p"
        assert rf["video_codec"] == "prores"
        assert rf["audio_codec"] == "pcm_s16le"

    def test_all_expected_keys_present(self) -> None:
        """Top-level keys match spec."""
        report = generate_scene_report(
            scene_index=0, engine="animotion", duration_frames=120,
            scene_path="/tmp/s.mp4",
        )
        expected = {"artifact", "version", "scene_index", "engine",
                     "duration_frames", "scene_path", "report_timestamp",
                     "content_hash", "render_format"}
        assert set(report.keys()) == expected


class TestWriteSceneReport:
    def test_writes_to_dot_scene_report_json(self, temp_dir: Path) -> None:
        """Scene report file written as <scene>.mp4.scene.report.json."""
        scene_path = temp_dir / "scenes" / "scene_0000.mp4"
        scene_path.parent.mkdir(parents=True)
        scene_path.write_text("dummy")

        report_data = {"artifact": "videoforge-scene-report", "version": 1, "scene_index": 0}
        result = write_scene_report(report_data, str(scene_path))

        expected = scene_path.parent / "scene_0000.mp4.scene.report.json"
        assert Path(result) == expected
        assert expected.exists()
        data = json.loads(expected.read_text())
        assert data["artifact"] == "videoforge-scene-report"

    def test_content_is_serializable(self, temp_dir: Path) -> None:
        """Full scene report dict serializes to JSON without error."""
        report = generate_scene_report(
            scene_index=0,
            engine="remotion",
            duration_frames=180,
            scene_path=str(temp_dir / "scene_0000.mp4"),
            content_hash="deadbeef",
        )
        dumped = json.dumps(report, indent=2, default=str)
        loaded = json.loads(dumped)
        assert loaded["artifact"] == "videoforge-scene-report"
        assert loaded["scene_index"] == 0
        assert loaded["engine"] == "remotion"
        assert loaded["content_hash"] == "deadbeef"
