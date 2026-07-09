"""Tests for Artifacts API — scene thumbnails, sampled frames, scene reports.

Covers:
- List scene artifacts for a job
- Serve thumbnail image
- Serve sampled frame image
- Serve scene report JSON
- 404 for missing artifacts
- 400 for invalid names
- Graceful handling of empty artifact directories
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from videoforge.api.app import create_app


def _setup_artifacts(base_dir: Path) -> None:
    """Create sample artifact files in the given base directory."""
    job_dir = base_dir / "job_test"
    thumb_dir = job_dir / "thumbnails"
    frame_dir = job_dir / "frames"
    report_dir = job_dir / "reports"
    thumb_dir.mkdir(parents=True)
    frame_dir.mkdir()
    report_dir.mkdir()

    # Thumbnail
    (thumb_dir / "scene_a.jpg").write_bytes(b"fake-jpeg-thumbnail-bytes")

    # Sampled frame
    (frame_dir / "scene_a.png").write_bytes(b"fake-png-frame-bytes")

    # Scene report JSON
    report = {
        "artifact": "videoforge-scene-report",
        "version": 1,
        "scene_index": 0,
        "engine": "remotion",
        "duration_frames": 180,
        "content_hash": "abc123",
    }
    (report_dir / "scene_a.json").write_text(json.dumps(report))

    # scene_b has only report (no thumbnail/frame)
    report_b = {
        "artifact": "videoforge-scene-report",
        "version": 1,
        "scene_index": 1,
        "engine": "manim",
        "duration_frames": 120,
        "content_hash": "def456",
    }
    (report_dir / "scene_b.json").write_text(json.dumps(report_b))


# ─── Tests ───────────────────────────────────────────────────────────────


class TestListArtifacts:
    def test_empty_when_no_job_dir(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("videoforge.api.artifacts.ARTIFACTS_DIR", tmp_path)
        client = TestClient(create_app())
        resp = client.get("/api/artifacts/nonexistent/scenes")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_lists_artifacts(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("videoforge.api.artifacts.ARTIFACTS_DIR", tmp_path)
        _setup_artifacts(tmp_path)
        client = TestClient(create_app())
        resp = client.get("/api/artifacts/job_test/scenes")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

        scene_a = next(s for s in data if s["sceneId"] == "scene_a")
        assert scene_a["hasThumbnail"] is True
        assert scene_a["hasFrame"] is True
        assert scene_a["hasReport"] is True

        scene_b = next(s for s in data if s["sceneId"] == "scene_b")
        assert scene_b["hasThumbnail"] is False
        assert scene_b["hasFrame"] is False
        assert scene_b["hasReport"] is True

    def test_invalid_job_id_404(self, tmp_path: Path, monkeypatch):
        """Path traversal in URL gets normalized by HTTP client — ends as 404 from router."""
        monkeypatch.setattr("videoforge.api.artifacts.ARTIFACTS_DIR", tmp_path)
        client = TestClient(create_app())
        resp = client.get("/api/artifacts/../../../etc/scenes")
        assert resp.status_code == 404


class TestGetThumbnail:
    def test_serves_thumbnail(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("videoforge.api.artifacts.ARTIFACTS_DIR", tmp_path)
        _setup_artifacts(tmp_path)
        client = TestClient(create_app())
        resp = client.get("/api/artifacts/job_test/scenes/scene_a/thumbnail")
        assert resp.status_code == 200
        assert resp.content == b"fake-jpeg-thumbnail-bytes"

    def test_missing_thumbnail_404(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("videoforge.api.artifacts.ARTIFACTS_DIR", tmp_path)
        _setup_artifacts(tmp_path)
        client = TestClient(create_app())
        resp = client.get("/api/artifacts/job_test/scenes/scene_b/thumbnail")
        assert resp.status_code == 404

    def test_missing_job_404(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("videoforge.api.artifacts.ARTIFACTS_DIR", tmp_path)
        client = TestClient(create_app())
        resp = client.get("/api/artifacts/nonexistent/scenes/unknown/thumbnail")
        assert resp.status_code == 404

    def test_invalid_scene_id_404(self, tmp_path: Path, monkeypatch):
        """Path traversal via ``..`` gets normalized by HTTP client before handler."""
        monkeypatch.setattr("videoforge.api.artifacts.ARTIFACTS_DIR", tmp_path)
        client = TestClient(create_app())
        resp = client.get("/api/artifacts/job_test/scenes/../../../etc/passwd/thumbnail")
        assert resp.status_code == 404


class TestGetFrame:
    def test_serves_frame(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("videoforge.api.artifacts.ARTIFACTS_DIR", tmp_path)
        _setup_artifacts(tmp_path)
        client = TestClient(create_app())
        resp = client.get("/api/artifacts/job_test/scenes/scene_a/frame")
        assert resp.status_code == 200
        assert resp.content == b"fake-png-frame-bytes"

    def test_missing_frame_404(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("videoforge.api.artifacts.ARTIFACTS_DIR", tmp_path)
        _setup_artifacts(tmp_path)
        client = TestClient(create_app())
        resp = client.get("/api/artifacts/job_test/scenes/scene_b/frame")
        assert resp.status_code == 404

    def test_invalid_job_id_404(self, tmp_path: Path, monkeypatch):
        """Path traversal via ``..`` gets normalized by HTTP client before handler."""
        monkeypatch.setattr("videoforge.api.artifacts.ARTIFACTS_DIR", tmp_path)
        client = TestClient(create_app())
        resp = client.get("/api/artifacts/../malicious/scenes/scene_a/frame")
        assert resp.status_code == 404


class TestGetReport:
    def test_serves_report_json(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("videoforge.api.artifacts.ARTIFACTS_DIR", tmp_path)
        _setup_artifacts(tmp_path)
        client = TestClient(create_app())
        resp = client.get("/api/artifacts/job_test/scenes/scene_a/report")
        assert resp.status_code == 200
        data = resp.json()
        assert data["artifact"] == "videoforge-scene-report"
        assert data["engine"] == "remotion"
        assert data["content_hash"] == "abc123"

    def test_missing_report_404(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("videoforge.api.artifacts.ARTIFACTS_DIR", tmp_path)
        client = TestClient(create_app())
        resp = client.get("/api/artifacts/job_test/scenes/missing/report")
        assert resp.status_code == 404

    def test_reports_content_type_json(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("videoforge.api.artifacts.ARTIFACTS_DIR", tmp_path)
        _setup_artifacts(tmp_path)
        client = TestClient(create_app())
        resp = client.get("/api/artifacts/job_test/scenes/scene_a/report")
        assert resp.headers["content-type"].startswith("application/json")

    def test_invalid_scene_id_400(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("videoforge.api.artifacts.ARTIFACTS_DIR", tmp_path)
        client = TestClient(create_app())
        resp = client.get("/api/artifacts/job_test/scenes/scene@invalid/report")
        assert resp.status_code == 400


class TestCrossSceneIsolation:
    """Verify artifacts from different jobs don't leak."""

    def test_jobs_are_isolated(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("videoforge.api.artifacts.ARTIFACTS_DIR", tmp_path)
        # Setup two jobs
        (tmp_path / "job_a" / "thumbnails").mkdir(parents=True)
        (tmp_path / "job_a" / "thumbnails" / "scene_x.jpg").write_bytes(b"job-a-thumb")
        (tmp_path / "job_b" / "thumbnails").mkdir(parents=True)
        (tmp_path / "job_b" / "thumbnails" / "scene_x.jpg").write_bytes(b"job-b-thumb")

        client = TestClient(create_app())

        resp_a = client.get("/api/artifacts/job_a/scenes/scene_x/thumbnail")
        assert resp_a.status_code == 200
        assert resp_a.content == b"job-a-thumb"

        resp_b = client.get("/api/artifacts/job_b/scenes/scene_x/thumbnail")
        assert resp_b.status_code == 200
        assert resp_b.content == b"job-b-thumb"

        resp_cross = client.get("/api/artifacts/job_a/scenes/scene_x/frame")
        assert resp_cross.status_code == 404


class TestListNoArtifacts:
    def test_job_dir_exists_but_empty(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("videoforge.api.artifacts.ARTIFACTS_DIR", tmp_path)
        (tmp_path / "empty_job" / "thumbnails").mkdir(parents=True)
        client = TestClient(create_app())
        resp = client.get("/api/artifacts/empty_job/scenes")
        assert resp.status_code == 200
        assert resp.json() == []
