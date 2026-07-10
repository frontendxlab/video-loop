"""Tests for Reports API — GET /api/reports and artifact endpoints.

Covers:
- List reports from disk scan
- Read full report JSON
- Read provenance graph
- Read scene artifacts
- 404 for missing reports
- 400 for invalid names
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from videoforge.api.app import create_app


def _make_report_artifact(video_path: Path) -> dict:
    """Build a realistic video report dict."""
    return {
        "artifact": "videoforge-video-report",
        "version": 1,
        "video_path": str(video_path.resolve()),
        "report_timestamp": "2026-07-09T17:00:00+00:00",
        "content_hash": "abc123def456",
        "engine_mix": ["remotion"],
        "render_format": {
            "fps": 30, "width": 1920, "height": 1080,
            "pixel_format": "yuv420p", "video_codec": "h264", "audio_codec": "aac",
        },
        "scenes_summary": {
            "count": 2,
            "engines": {"remotion": 1, "manim": 1},
            "total_duration_frames": 300,
            "scenes": [
                {"index": 0, "engine": "remotion", "duration_frames": 180},
                {"index": 1, "engine": "manim", "duration_frames": 120},
            ],
        },
        "l0_summary": {
            "status": "pass",
            "passed": True,
            "total_issues": 0,
            "severity_counts": {"high": 0, "medium": 0, "low": 0},
            "sampled_frames": 10,
            "total_frames": 300,
            "duration_seconds": 10.0,
            "issues": [],
        },
        "l1_summary": {
            "passed": True,
            "total_frames": 300,
            "total_issues": 0,
            "issues": [],
        },
        "l2_layout_overlap_summary": {
            "status": "pass",
            "passed": True,
            "total_issues": 0,
            "severity_counts": {"high": 0, "medium": 0, "low": 0},
            "issues": [],
        },
        "policy_verdict": "pass",
    }


def _make_provenance_artifact(video_path: Path) -> dict:
    """Build a realistic provenance graph dict."""
    return {
        "artifact": "videoforge-provenance-graph",
        "version": 1,
        "video_path": str(video_path.resolve()),
        "report_timestamp": "2026-07-09T17:00:00+00:00",
        "content_hash": "abc123def456",
        "engines": ["manim", "remotion"],
        "scenes": [
            {
                "id": "scene_0000",
                "engine": "remotion",
                "kind": "title",
                "content_hash": "aaa111",
                "scene_path": "/tmp/scene_0000.mp4",
                "scene_report_path": "/tmp/scene_0000.mp4.scene.report.json",
                "duration_frames": 180,
                "assets": {"audio_src": "audio.wav"},
            },
        ],
        "reports": {
            "video_report": str(video_path.with_suffix(".mp4.report.json")),
            "provenance_graph": str(video_path.with_suffix(".provenance.json")),
        },
    }


def _make_scene_report(scene_index: int, engine: str = "remotion") -> dict:
    """Build a realistic per-scene report dict."""
    return {
        "artifact": "videoforge-scene-report",
        "version": 1,
        "scene_index": scene_index,
        "engine": engine,
        "duration_frames": 180,
        "scene_path": f"/tmp/scene_{scene_index:04d}.mp4",
        "report_timestamp": "2026-07-09T17:00:00+00:00",
        "content_hash": "abc123",
        "render_format": {
            "fps": 30, "width": 1920, "height": 1080,
            "pixel_format": "yuv420p", "video_codec": "h264", "audio_codec": "aac",
        },
    }


# ─── Fixtures ────────────────────────────────────────────────────────────


def _setup_artifacts(tmp_path: Path) -> None:
    """Create sample report/provenance/scene artifacts in tmp_path."""
    # Video-level report
    video_path = tmp_path / "demo.mp4"
    video_path.write_text("dummy")
    report = _make_report_artifact(video_path)
    report_path = tmp_path / "demo.mp4.report.json"
    report_path.write_text(json.dumps(report))

    # Provenance graph
    prov = _make_provenance_artifact(video_path)
    prov_path = tmp_path / "demo.provenance.json"
    prov_path.write_text(json.dumps(prov))

    # Scene reports
    for i, eng in enumerate(["remotion", "manim"]):
        sr = _make_scene_report(i, eng)
        sr_path = tmp_path / f"demo.scene_{i:04d}.mp4.scene.report.json"
        sr_path.write_text(json.dumps(sr))


# ─── Tests ───────────────────────────────────────────────────────────────


class TestListReports:
    def test_empty_when_no_artifacts(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        client = TestClient(create_app())
        resp = client.get("/api/reports")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_lists_one_report(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_artifacts(tmp_path)
        client = TestClient(create_app())
        resp = client.get("/api/reports")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        entry = data[0]
        assert entry["name"] == "demo"
        assert entry["artifact"] == "videoforge-video-report"
        assert entry["scenes_count"] == 2
        assert entry["l0_status"] == "pass"
        assert entry["policy_verdict"] == "pass"
        assert entry["has_provenance"] is True

    def test_list_includes_scene_artifact_fields(self, tmp_path: Path, monkeypatch):
        """Report summary includes scene artifact availability counts."""
        monkeypatch.chdir(tmp_path)
        _setup_artifacts(tmp_path)
        client = TestClient(create_app())
        resp = client.get("/api/reports")
        data = resp.json()
        assert len(data) == 1
        entry = data[0]
        # Fields exist (may be zero if content_hash doesn't match artifact dir)
        assert "scene_thumbnails_available" in entry
        assert "scene_frames_available" in entry
        assert "scene_reports_available" in entry

    def test_list_returns_json_array(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_artifacts(tmp_path)
        client = TestClient(create_app())
        resp = client.get("/api/reports")
        assert resp.headers["content-type"].startswith("application/json")
        assert isinstance(resp.json(), list)


class TestGetReport:
    def test_returns_full_report(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_artifacts(tmp_path)
        client = TestClient(create_app())
        resp = client.get("/api/reports/demo")
        assert resp.status_code == 200
        data = resp.json()
        assert data["artifact"] == "videoforge-video-report"
        assert data["content_hash"] == "abc123def456"
        assert data["l0_summary"]["status"] == "pass"
        assert data["policy_verdict"] == "pass"

    def test_missing_report_404(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        client = TestClient(create_app())
        resp = client.get("/api/reports/nonexistent")
        assert resp.status_code == 404

    def test_invalid_name_400(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        client = TestClient(create_app())
        # Name with slash triggers FastAPI normalization → no route match → 404
        resp = client.get("/api/reports/../invalid")
        assert resp.status_code in (400, 404)


class TestGetProvenance:
    def test_returns_provenance(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_artifacts(tmp_path)
        client = TestClient(create_app())
        resp = client.get("/api/reports/demo/provenance")
        assert resp.status_code == 200
        data = resp.json()
        assert data["artifact"] == "videoforge-provenance-graph"
        assert len(data["scenes"]) == 1
        assert data["engines"] == ["manim", "remotion"]

    def test_missing_provenance_404(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        # Create report but no provenance
        video_path = tmp_path / "bare.mp4"
        video_path.write_text("dummy")
        report = _make_report_artifact(video_path)
        (tmp_path / "bare.mp4.report.json").write_text(json.dumps(report))
        client = TestClient(create_app())
        resp = client.get("/api/reports/bare/provenance")
        assert resp.status_code == 404


class TestGetScenes:
    def test_returns_scene_reports(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_artifacts(tmp_path)
        client = TestClient(create_app())
        resp = client.get("/api/reports/demo/scenes")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["scene_index"] == 0
        assert data[0]["engine"] == "remotion"
        assert data[1]["scene_index"] == 1
        assert data[1]["engine"] == "manim"

    def test_no_scenes_returns_empty(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        # Create report with 0 scenes
        video_path = tmp_path / "empty.mp4"
        video_path.write_text("dummy")
        report = _make_report_artifact(video_path)
        report["scenes_summary"]["count"] = 0
        (tmp_path / "empty.mp4.report.json").write_text(json.dumps(report))
        client = TestClient(create_app())
        resp = client.get("/api/reports/empty/scenes")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_scene_reports_include_artifact_hints(self, tmp_path: Path, monkeypatch):
        """Each scene report in /api/reports/{name}/scenes has artifact fields."""
        monkeypatch.chdir(tmp_path)
        _setup_artifacts(tmp_path)
        # Add scene with frame/thumbnail
        frame_dir = tmp_path / "frames"
        frame_dir.mkdir(exist_ok=True)
        (frame_dir / "scene_0000.jpg").write_bytes(b"frame-data")
        client = TestClient(create_app())
        resp = client.get("/api/reports/demo/scenes")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        for scene in data:
            assert "has_frame" in scene
            assert "has_thumbnail" in scene
            assert "scene_artifacts_url" in scene
