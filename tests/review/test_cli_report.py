"""Tests for videoforge report CLI command."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from videoforge.app import app

runner = CliRunner()


def _make_report(
    dir: Path,
    l0_status: str = "pass",
    l1_passed: bool = True,
    l0_issues: list[dict[str, Any]] | None = None,
    l1_issues: list[dict[str, Any]] | None = None,
    engine_mix: list[str] | None = None,
    content_hash: str = "abc123",
    scenes_summary: dict[str, Any] | None = None,
) -> Path:
    video = dir / "test.mp4"
    video.write_text("dummy")
    report_path = video.with_suffix(".mp4.report.json")
    l0_issues = l0_issues or []
    l1_issues = l1_issues or []
    sev: dict[str, int] = {"high": 0, "medium": 0, "low": 0}
    for i in l0_issues:
        s = i.get("severity", "low")
        sev[s] = sev.get(s, 0) + 1
    report: dict[str, Any] = {
        "artifact": "videoforge-video-report",
        "version": 1,
        "video_path": str(video.resolve()),
        "report_timestamp": "2026-07-09T14:58:54+00:00",
        "content_hash": content_hash,
        "engine_mix": sorted(engine_mix or ["remotion"]),
        "render_format": {"fps": 30, "width": 1920, "height": 1080, "pixel_format": "yuv420p", "video_codec": "h264", "audio_codec": "aac"},
        "scenes_summary": scenes_summary or {"count": 0, "engines": {}, "total_duration_frames": 0},
        "l0_summary": {
            "status": l0_status,
            "passed": l0_status == "pass",
            "total_issues": len(l0_issues),
            "severity_counts": sev,
            "sampled_frames": 6,
            "total_frames": 300,
            "duration_seconds": 10.0,
            "issues": l0_issues,
        },
        "l1_summary": {
            "passed": l1_passed,
            "total_frames": 300,
            "total_issues": len(l1_issues),
            "issues": l1_issues,
        },
    }
    report_path.write_text(json.dumps(report, indent=2))
    return report_path


class TestReportCommand:
    def test_report_pass(self, temp_dir: Path) -> None:
        """Passing report prints REPORT_status=PASS and exits 0."""
        _make_report(temp_dir)
        result = runner.invoke(app, ["report-summary", str(temp_dir / "test.mp4")])
        assert result.exit_code == 0, result.output
        assert "REPORT_status=PASS" in result.output
        assert "REPORT_l0_status=pass" in result.output
        assert "REPORT_l1_passed=true" in result.output
        assert "REPORT_l0_issues=0" in result.output
        assert "REPORT_l1_issues=0" in result.output

    def test_report_fail_l0(self, temp_dir: Path) -> None:
        """L0 fail causes exit 1 and REPORT_status=FAIL."""
        _make_report(
            temp_dir,
            l0_status="fail",
            l1_passed=True,
            l0_issues=[{"severity": "high", "type": "blank_frame", "detail": "Frame 0 blank"}],
        )
        result = runner.invoke(app, ["report-summary", str(temp_dir / "test.mp4")])
        assert result.exit_code == 1, result.output
        assert "REPORT_status=FAIL" in result.output
        assert "REPORT_l0_status=fail" in result.output
        assert "REPORT_l0_high=1" in result.output

    def test_report_fail_l1(self, temp_dir: Path) -> None:
        """L1 fail causes exit 1."""
        _make_report(
            temp_dir,
            l0_status="pass",
            l1_passed=False,
            l1_issues=[{"type": "black_frame", "start": 0, "end": 5}],
        )
        result = runner.invoke(app, ["report-summary", str(temp_dir / "test.mp4")])
        assert result.exit_code == 1, result.output
        assert "REPORT_status=FAIL" in result.output
        assert "REPORT_l1_passed=false" in result.output
        assert "REPORT_l1_issues=1" in result.output

    def test_report_missing_file(self, temp_dir: Path) -> None:
        """Missing report file exits 1 with error."""
        result = runner.invoke(app, ["report-summary", str(temp_dir / "nonexistent.mp4")])
        assert result.exit_code == 1
        assert "Report not found" in result.output

    def test_report_json_flag(self, temp_dir: Path) -> None:
        """--json flag outputs raw JSON."""
        _make_report(temp_dir)
        result = runner.invoke(app, ["report-summary", str(temp_dir / "test.mp4"), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["artifact"] == "videoforge-video-report"
        assert data["content_hash"] == "abc123"
        assert data["l0_summary"]["status"] == "pass"

    def test_report_engine_mix(self, temp_dir: Path) -> None:
        """Engine mix appears in output."""
        _make_report(temp_dir, engine_mix=["remotion", "manim", "animotion"])
        result = runner.invoke(app, ["report-summary", str(temp_dir / "test.mp4")])
        assert result.exit_code == 0
        assert "animotion,manim,remotion" in result.output

    def test_report_scenes_flag(self, temp_dir: Path) -> None:
        """--scenes flag finds scene report artifacts."""
        _make_report(temp_dir)
        # Create scene artifacts
        scene_dir = temp_dir
        for i in range(2):
            sr = {
                "artifact": "videoforge-scene-report", "version": 1,
                "scene_index": i, "engine": "remotion", "duration_frames": 150,
                "scene_path": str(scene_dir / f"scene_{i:04d}.mp4"),
                "report_timestamp": "2026-07-09T14:58:54+00:00",
                "content_hash": "abc123",
                "render_format": {"fps": 30, "width": 1920, "height": 1080, "pixel_format": "yuv420p", "video_codec": "h264", "audio_codec": "aac"},
            }
            sr_path = scene_dir / f"scene_{i:04d}.mp4.scene.report.json"
            sr_path.write_text(json.dumps(sr, indent=2))

        result = runner.invoke(app, ["report-summary", str(temp_dir / "test.mp4"), "--scenes"])
        assert result.exit_code == 0
        assert "SCENE_0_engine=remotion" in result.output
        assert "SCENE_0_duration_frames=150" in result.output
        assert "SCENE_1_engine=remotion" in result.output

    def test_report_scenes_flag_no_artifacts(self, temp_dir: Path) -> None:
        """--scenes with no artifacts produces no SCENE_ lines."""
        _make_report(temp_dir)
        result = runner.invoke(app, ["report-summary", str(temp_dir / "test.mp4"), "--scenes"])
        assert result.exit_code == 0
        assert "SCENE_" not in result.output

    def test_report_scenes_flag_embedded(self, temp_dir: Path) -> None:
        """--scenes uses embedded scenes_summary when available."""
        scenes_summary = {
            "count": 2,
            "engines": {"remotion": 2},
            "total_duration_frames": 300,
            "scenes": [
                {"index": 0, "engine": "remotion", "duration_frames": 150},
                {"index": 1, "engine": "remotion", "duration_frames": 150},
            ],
        }
        _make_report(temp_dir, scenes_summary=scenes_summary)

        result = runner.invoke(app, ["report-summary", str(temp_dir / "test.mp4"), "--scenes"])
        assert result.exit_code == 0
        assert "SCENE_0_engine=remotion" in result.output
        assert "SCENE_0_duration_frames=150" in result.output
        assert "SCENE_1_engine=remotion" in result.output
        assert "SCENE_1_duration_frames=150" in result.output

    def test_report_exit_zero_on_warn(self, temp_dir: Path) -> None:
        """L0 warn (medium issues) exits 0, shows WARN status."""
        _make_report(
            temp_dir,
            l0_status="warn",
            l1_passed=True,
            l0_issues=[{"severity": "medium", "type": "palette_drift", "detail": "drift at frame 5"}],
        )
        result = runner.invoke(app, ["report-summary", str(temp_dir / "test.mp4")])
        assert result.exit_code == 0, result.output
        assert "REPORT_status=WARN" in result.output
        assert "REPORT_l0_status=warn" in result.output
        assert "REPORT_l0_medium=1" in result.output

    def test_report_verbose_shows_issues(self, temp_dir: Path) -> None:
        """--verbose prints issue details alongside key=value lines."""
        _make_report(
            temp_dir,
            l0_status="fail",
            l1_passed=False,
            l0_issues=[{"severity": "high", "type": "blank_frame", "detail": "Frame 0 blank"}],
            l1_issues=[{"type": "black_frame", "start": 0, "end": 5}],
        )
        result = runner.invoke(app, ["report-summary", str(temp_dir / "test.mp4"), "--verbose"])
        assert result.exit_code == 1
        assert "REPORT_status=FAIL" in result.output
        assert "--- L0 Issues (1) ---" in result.output
        assert "[high] blank_frame: Frame 0 blank" in result.output
        assert "--- L1 Issues (1) ---" in result.output
        assert "black_frame: frames 0-5" in result.output

    def test_report_verbose_no_issues(self, temp_dir: Path) -> None:
        """--verbose with no issues prints no issue sections."""
        _make_report(temp_dir)
        result = runner.invoke(app, ["report-summary", str(temp_dir / "test.mp4"), "--verbose"])
        assert result.exit_code == 0
        assert "REPORT_status=PASS" in result.output
        assert "--- L0 Issues" not in result.output
        assert "--- L1 Issues" not in result.output
        assert "--- L2b Issues" not in result.output

    def test_report_verbose_with_scenes(self, temp_dir: Path) -> None:
        """--verbose with --scenes produces both issue details and scene lines."""
        _make_report(
            temp_dir,
            l0_status="warn",
            l1_passed=True,
            l0_issues=[{"severity": "medium", "type": "palette_drift", "detail": "drift at frame 5"}],
        )
        sr = {
            "artifact": "videoforge-scene-report", "version": 1,
            "scene_index": 0, "engine": "remotion", "duration_frames": 150,
            "scene_path": str(temp_dir / "scene_0000.mp4"),
            "report_timestamp": "2026-07-09T14:58:54+00:00",
            "content_hash": "abc123",
        }
        (temp_dir / "scene_0000.mp4.scene.report.json").write_text(json.dumps(sr, indent=2))

        result = runner.invoke(app, ["report-summary", str(temp_dir / "test.mp4"), "--verbose", "--scenes"])
        assert result.exit_code == 0, result.output
        assert "REPORT_status=WARN" in result.output
        assert "--- L0 Issues (1) ---" in result.output
        assert "[medium] palette_drift: drift at frame 5" in result.output
        assert "SCENE_0_engine=remotion" in result.output

    def test_report_verbose_l2_issues(self, temp_dir: Path) -> None:
        """--verbose shows L2b issues when present."""
        video = temp_dir / "test.mp4"
        video.write_text("dummy")
        report = json.loads((temp_dir / "test.mp4.report.json").read_text()) if (temp_dir / "test.mp4.report.json").exists() else {}
        report_path = _make_report(temp_dir, l0_status="pass", l1_passed=True)
        # Overwrite report with L2b issues
        report_data = json.loads(report_path.read_text())
        report_data["l2_layout_overlap_summary"] = {
            "status": "warn",
            "passed": False,
            "total_issues": 1,
            "severity_counts": {"high": 0, "medium": 1, "low": 0},
            "issues": [{"element": "a", "element_b": "b", "type": "overlap", "iou": 0.9,
                        "severity": "medium", "detail": "Elements a and b overlap by 90%"}],
        }
        report_path.write_text(json.dumps(report_data, indent=2))

        result = runner.invoke(app, ["report-summary", str(temp_dir / "test.mp4"), "--verbose"])
        assert result.exit_code == 0, result.output
        assert "--- L2b Issues (1) ---" in result.output
        assert "[medium] overlap: Elements a and b overlap by 90%" in result.output

    def test_report_malformed_json(self, temp_dir: Path) -> None:
        """Malformed report JSON exits 1."""
        report_path = temp_dir / "test.mp4.report.json"
        report_path.write_text("{invalid json}")
        result = runner.invoke(app, ["report-summary", str(temp_dir / "test.mp4")])
        assert result.exit_code == 1


class TestReviewCommand:
    """Tests for videoforge review CLI command (REVIEW_ key=value output)."""

    _mock_report_path: str = "/tmp/test.mp4.report.json"

    def _mock_decision(self, l0_status: str = "pass", l1_passed: bool = True, l2_status: str = "pass") -> dict[str, Any]:
        """Build minimal decision dict matching policy.aggregate() output shape."""
        severities = {"high", "medium", "low"}
        verdict = "pass"
        if l0_status == "fail" or l2_status == "fail":
            verdict = "fail"
        elif l0_status == "warn" or l2_status == "warn":
            verdict = "warn"
        elif not l1_passed:
            verdict = "fail"
        return {
            "verdict": verdict,
            "levels": {"l0": l0_status, "l1": "fail" if not l1_passed else "pass", "l2": l2_status},
            "details": {},
            "retry_suggested": False,
            "repair_suggested": False,
        }

    def _mock_run_review(self, **kwargs: Any) -> dict[str, Any]:
        l0_status = kwargs.get("l0_status", "pass")
        l1_passed = kwargs.get("l1_passed", True)
        l2_status = kwargs.get("l2_status", "pass")
        verdict = "pass"
        if l0_status == "fail" or l2_status == "fail" or not l1_passed:
            verdict = "fail"
        elif l0_status == "warn" or l2_status == "warn":
            verdict = "warn"
        l0_issues = kwargs.get("l0_issues", [])
        l1_issues = kwargs.get("l1_issues", [])
        return {
            "l0_result": {"issues": l0_issues, "sampled_frames": 6, "total_frames": 300, "duration_seconds": 10.0},
            "l0_status": l0_status,
            "l1_result": {"issues": l1_issues, "passed": l1_passed, "total_frames": 300},
            "l2_result": {"issues": [], "passed": l2_status == "pass"},
            "l2_status": l2_status,
            "report": {
                "artifact": "videoforge-video-report", "version": 1,
                "video_path": "/tmp/test.mp4",
                "l0_summary": {"status": l0_status, "passed": l0_status == "pass", "total_issues": len(l0_issues), "severity_counts": {"high": 0, "medium": 0, "low": 0}, "sampled_frames": 6, "total_frames": 300},
                "l1_summary": {"passed": l1_passed, "total_frames": 300, "total_issues": len(l1_issues)},
                "l2_layout_overlap_summary": {"status": l2_status, "passed": l2_status == "pass", "total_issues": 0, "severity_counts": {"high": 0, "medium": 0, "low": 0}},
            },
            "report_path": self._mock_report_path,
            "decision": {"verdict": verdict, "levels": {"l0": l0_status, "l1": "fail" if not l1_passed else "pass", "l2": l2_status}, "retry_suggested": False, "repair_suggested": False},
        }

    def test_review_outputs_key_value_lines(self, temp_dir: Path) -> None:
        """Review prints REVIEW_ key=value lines."""
        video = temp_dir / "test.mp4"
        video.write_text("dummy")
        with patch("videoforge.review.frame_reviewer.run_review", return_value=self._mock_run_review()):
            result = runner.invoke(app, ["review", str(video)])
        assert result.exit_code == 0, result.output
        lines = [l for l in result.output.splitlines() if l.startswith("REVIEW_")]
        assert "REVIEW_status=PASS" in lines
        assert "REVIEW_l0_status=pass" in lines
        assert "REVIEW_l1_passed=true" in lines
        assert "REVIEW_l2b_status=pass" in lines
        assert "REVIEW_total_issues=0" in lines
        assert f"REVIEW_report_path={self._mock_report_path}" in lines

    def test_review_fail_l0(self, temp_dir: Path) -> None:
        """L0 fail sets REVIEW_status=FAIL and exits 1."""
        video = temp_dir / "test.mp4"
        video.write_text("dummy")
        l0_issues = [{"severity": "high", "type": "blank_frame", "detail": "blank"}]
        mr = self._mock_run_review(l0_status="fail", l0_issues=l0_issues)
        with patch("videoforge.review.frame_reviewer.run_review", return_value=mr):
            result = runner.invoke(app, ["review", str(video)])
        assert result.exit_code == 1, result.output
        assert "REVIEW_status=FAIL" in result.output
        assert "REVIEW_l0_status=fail" in result.output

    def test_review_fail_l2(self, temp_dir: Path) -> None:
        """L2b fail sets REVIEW_status=FAIL and exits 1."""
        video = temp_dir / "test.mp4"
        video.write_text("dummy")
        mr = self._mock_run_review(l2_status="fail")
        with patch("videoforge.review.frame_reviewer.run_review", return_value=mr):
            result = runner.invoke(app, ["review", str(video)])
        assert result.exit_code == 1, result.output
        assert "REVIEW_status=FAIL" in result.output
        assert "REVIEW_l2b_status=fail" in result.output

    def test_review_warn_l0(self, temp_dir: Path) -> None:
        """L0 warn sets REVIEW_status=WARN, exits 0."""
        video = temp_dir / "test.mp4"
        video.write_text("dummy")
        l0_issues = [{"severity": "medium", "type": "palette_drift", "detail": "drift"}]
        mr = self._mock_run_review(l0_status="warn", l0_issues=l0_issues)
        with patch("videoforge.review.frame_reviewer.run_review", return_value=mr):
            result = runner.invoke(app, ["review", str(video)])
        assert result.exit_code == 0, result.output
        assert "REVIEW_status=WARN" in result.output
        assert "REVIEW_l0_status=warn" in result.output
