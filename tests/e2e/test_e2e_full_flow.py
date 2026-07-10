"""E2E test: grill loop → create job → pipeline → video output.

Uses httpx.AsyncClient so background async tasks progress between requests.
"""

from __future__ import annotations

import asyncio
import io
import struct
import time
import wave
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest
from fastapi.testclient import TestClient

from videoforge.api.app import create_app
from videoforge.api.jobs import _grill_sessions, _job_store


# ─── Fixtures ───────────────────────────────────────────────────────────

GRILL_PROMPT = "Explain Docker networking with code examples and architecture diagrams"
VIDEOS_DIR = Path("/tmp/videoforge")


def _fake_wav_bytes(duration_secs: float = 0.25) -> bytes:
    buf = io.BytesIO()
    sr = 24000
    n = int(sr * duration_secs)
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(struct.pack(f"<{n}h", *([0] * n)))
    return buf.getvalue()


class _FakeResponse:
    """Simulate requests.Response with proper headers for generate_audio()."""
    def __init__(self, content: bytes, status_code: int = 200):
        self.status_code = status_code
        self.content = content
        self.headers = {"content-type": "audio/wav"}
        self.text = ""

    def json(self):
        return {}


@pytest.fixture(autouse=True)
def clean_state():
    _job_store.clear()
    _grill_sessions.clear()
    yield


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture(autouse=True)
def mock_externals(monkeypatch, tmp_path):
    """Mock TTS, render_scenes, and concatenate_scenes so pipeline doesn't need external services."""
    # Mock TTS HTTP
    def _mock_post(*args, **kwargs):
        return _FakeResponse(content=_fake_wav_bytes(0.3))
    monkeypatch.setattr("requests.post", _mock_post)

    # Mock render_scenes — write a tiny valid mp4 for each scene
    def _mock_render(video_def, remotion_dir, output_dir, **kw):
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        paths = []
        for i in range(len(video_def.scenes)):
            p = output_dir / f"scene_{i:04d}.mp4"
            # Write minimal valid MP4 header (ftyp box) so ffprobe/concat doesn't crash
            p.write_bytes(
                b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42mp41"
                b"\x00\x00\x00\x08moov"
            )
            paths.append(str(p.resolve()))
        return paths

    # Mock concatenate_scenes — write a padded mp4 that passes size checks
    def _mock_concat(scene_paths, output_path):
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # Write enough data to pass >1000 byte assertion in tests
        output_path.write_bytes(
            b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42mp41"
            + b"\x00" * 2000
        )
        return str(output_path.resolve())

    monkeypatch.setattr("videoforge.orchestrator.runner.render_scenes", _mock_render)
    monkeypatch.setattr("videoforge.orchestrator.runner.concatenate_scenes", _mock_concat)


# ─── Async support ─────────────────────────────────────────────────────


@pytest.fixture
async def async_client(app):
    """Async HTTP client that shares event loop with background tasks."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ─── E2E Tests ─────────────────────────────────────────────────────────


class TestGrillAndJobApi:
    """Grill + job creation using sync TestClient (no background task dependency)."""

    def test_grill_loop_answers_all_questions(self, client):
        start = client.post("/api/jobs/grill/start", json={"prompt": GRILL_PROMPT})
        assert start.status_code == 200
        sdata = start.json()
        session_id = sdata["sessionId"]
        assert session_id and sdata["asked"] == 0 and sdata["total"] > 0

        answers = ["beginner", "3 minutes", "educational",
                   "Learn Docker networking basics", "Yes Compose example", "code and diagram"]
        result = None
        for idx in range(12):
            ans = answers[idx] if idx < len(answers) else "Yes"
            turn = client.post("/api/jobs/grill/turn", json={"sessionId": session_id, "answer": ans})
            assert turn.status_code == 200
            tdata = turn.json()
            if tdata["done"]:
                result = tdata["result"]
                break

        assert result is not None
        assert len(result["refinedPrompt"]) > 20
        assert len(result["suggestedScenes"]) >= 3
        assert 0 <= result["confidence"] <= 1
        kinds = {s["kind"] for s in result["suggestedScenes"]}
        assert "code" in kinds
        assert "diagram" in kinds

    def test_grill_early_done(self, client):
        start = client.post("/api/jobs/grill/start", json={"prompt": GRILL_PROMPT})
        sid = start.json()["sessionId"]
        turn = client.post("/api/jobs/grill/turn", json={"sessionId": sid, "answer": "Devs", "done": True})
        assert turn.json()["done"] is True
        assert turn.json()["result"] is not None

    def test_create_job_with_session(self, client):
        start = client.post("/api/jobs/grill/start", json={"prompt": GRILL_PROMPT})
        sid = start.json()["sessionId"]
        client.post("/api/jobs/grill/turn", json={"sessionId": sid, "answer": "Devs", "done": True})

        resp = client.post("/api/jobs", json={"prompt": GRILL_PROMPT, "grillSessionId": sid})
        assert resp.status_code == 200
        assert resp.json()["jobId"].startswith("job_")
        assert resp.json()["status"] == "queued"

    def test_create_job_detail(self, client):
        resp = client.post("/api/jobs", json={"prompt": GRILL_PROMPT})
        job_id = resp.json()["jobId"]

        detail = client.get(f"/api/jobs/{job_id}")
        assert detail.status_code == 200
        d = detail.json()
        assert d["id"] == job_id
        assert len(d["events"]) >= 3
        assert d["events"][0]["type"] == "job.started"


class TestFullPipeline:
    """Full prompt→video flow with async client for background task progress."""

    async def test_full_flow_completes(self, async_client):
        # 1. Create job (background task starts in same event loop)
        resp = await async_client.post("/api/jobs", json={"prompt": GRILL_PROMPT})
        assert resp.status_code == 200
        data = resp.json()
        job_id = data["jobId"]
        assert job_id.startswith("job_")

        # 2. Poll for completion — background task runs because event loop is shared
        for _ in range(60):
            await asyncio.sleep(0.5)
            detail = await async_client.get(f"/api/jobs/{job_id}")
            assert detail.status_code == 200
            d = detail.json()
            if d["status"] == "completed":
                break
            if d["status"] == "failed":
                pytest.fail(f"Job failed: {d.get('error', 'unknown')}")
        else:
            pytest.fail("Job did not complete within 30s")

        # 3. Verify completion
        assert d["stage"] == "done"
        assert d["progressPct"] == 100
        assert d["completedAt"] is not None
        event_types = {e["type"] for e in d["events"]}
        assert "job.completed" in event_types

        # 4. Verify video file
        output_path = VIDEOS_DIR / job_id / "final.mp4"
        assert output_path.exists(), f"Video not found at {output_path}"
        assert output_path.stat().st_size > 1000, f"Video too small: {output_path.stat().st_size}b"

        # 5. Verify artifact
        artifacts = d.get("artifacts", [])
        assert len(artifacts) >= 1
        assert artifacts[0]["artifactType"] == "video/mp4"

        output_path.unlink(missing_ok=True)

    @pytest.mark.timeout(40)
    async def test_grill_session_full_flow(self, async_client):
        # 1. Grill session
        start = await async_client.post("/api/jobs/grill/start", json={"prompt": GRILL_PROMPT})
        sid = start.json()["sessionId"]

        answers = ["Developers", "5 minutes", "professional",
                   "Learn Docker networking", "Yes", "code, diagram"]
        for idx in range(10):
            ans = answers[idx] if idx < len(answers) else "Yes"
            turn = await async_client.post("/api/jobs/grill/turn", json={"sessionId": sid, "answer": ans})
            if turn.json()["done"]:
                break

        # 2. Create job reusing session
        resp = await async_client.post("/api/jobs", json={
            "prompt": GRILL_PROMPT,
            "grillSessionId": sid,
        })
        assert resp.status_code == 200
        job_id = resp.json()["jobId"]

        # 3. Poll for completion
        for _ in range(60):
            await asyncio.sleep(0.5)
            detail = await async_client.get(f"/api/jobs/{job_id}")
            d = detail.json()
            if d["status"] == "completed":
                break
            if d["status"] == "failed":
                pytest.fail(f"Job failed: {d.get('error', 'unknown')}")
        else:
            pytest.fail("Job did not complete within 30s")

        # 4. Verify
        assert d["stage"] == "done"
        assert d["progressPct"] == 100
        output_path = VIDEOS_DIR / job_id / "final.mp4"
        assert output_path.exists()
        output_path.unlink(missing_ok=True)
