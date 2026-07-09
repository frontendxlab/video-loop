"""Tests for videoforge report CLI command."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

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
