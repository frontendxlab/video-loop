"""Tests for job action endpoints: stop, retry, reroute.

Covers:
- Stop emits job.failed event, cancels runner if registered
- Stop updates job store status to cancelled
- Retry job emits retry.started event
- Retry job resets job store state
- Retry scene emits retry.started with scene scope
- Retry scene resets scene status in store, increments retryCount
- Reroute scene emits director.scene_routed event
- Reroute scene updates engine in store, marks scene pending
- ID validation rejects path-traversal chars
- Runner registration/unregister works
"""

from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient

from videoforge.api.actions import register_runner, unregister_runner
from videoforge.api.adapters import MemoryEventFeed
from videoforge.api.app import create_app
from videoforge.api.jobs import get_job, store_job

JOB_ID = "test-job-001"
SCENE_ID = "scene_42"


def _make_test_job(job_id: str = JOB_ID, scenes: list | None = None) -> dict:
    """Create a minimal job dict in the store for action testing."""
    job = {
        "id": job_id,
        "title": "Test job",
        "status": "running",
        "stage": "render",
        "progressPct": 50,
        "createdAt": "2025-01-01T00:00:00",
        "startedAt": "2025-01-01T00:01:00",
        "completedAt": None,
        "error": None,
        "provider": "9router",
        "model": "ocg/deepseek-v4-flash",
        "subagents": [
            {"id": "sa_1", "name": "Scene Planner", "engine": "director", "task": "Plan",
             "status": "completed", "startedAt": "2025-01-01T00:01:00",
             "completedAt": "2025-01-01T00:02:00", "durationMs": 60000, "error": None, "tokens": 340},
            {"id": "sa_2", "name": "Render Agent", "engine": "remotion", "task": "Render",
             "status": "running", "startedAt": "2025-01-01T00:02:00",
             "completedAt": None, "durationMs": None, "error": None, "tokens": 120},
        ],
        "scenes": scenes or [
            {"id": "scene_1", "kind": "title", "engine": "remotion", "status": "completed",
             "reviewIssues": 0, "retryCount": 0},
            {"id": "scene_2", "kind": "code", "engine": "remotion", "status": "rendering",
             "reviewIssues": 0, "retryCount": 1},
        ],
        "artifacts": [],
        "events": [],
    }
    store_job(job_id, job)
    return job


@pytest.fixture
def feed():
    return MemoryEventFeed()


@pytest.fixture
def client(feed):
    app = create_app(feed=feed)
    return TestClient(app)


class FakeRunner:
    """Minimal runner stub for testing stop callback."""
    def __init__(self):
        self.cancelled = False

    def cancel(self):
        self.cancelled = True


# ─── Stop ──────────────────────────────────────────────────────────────────


class TestStopJob:
    def test_stop_returns_200(self, client):
        resp = client.post(f"/api/jobs/{JOB_ID}/stop")
        assert resp.status_code == 200

    def test_stop_returns_status_stopped(self, client):
        resp = client.post(f"/api/jobs/{JOB_ID}/stop")
        data = resp.json()
        assert data["status"] == "stopped"
        assert data["job_id"] == JOB_ID

    def test_stop_emits_job_failed_event(self, feed: MemoryEventFeed, client):
        client.post(f"/api/jobs/{JOB_ID}/stop")
        events = asyncio.run(feed.replay(JOB_ID))
        assert any(e.type == "job.failed" for e in events)

    def test_stop_cancels_registered_runner(self, client):
        runner = FakeRunner()
        register_runner(JOB_ID, runner)
        client.post(f"/api/jobs/{JOB_ID}/stop")
        assert runner.cancelled is True
        unregister_runner(JOB_ID)

    def test_stop_unregisters_runner(self, client):
        runner = FakeRunner()
        register_runner(JOB_ID, runner)
        client.post(f"/api/jobs/{JOB_ID}/stop")
        # Second stop should not crash (runner already unregistered)
        resp = client.post(f"/api/jobs/{JOB_ID}/stop")
        assert resp.status_code == 200

    def test_stop_works_without_registered_runner(self, client):
        """No runner registered — still returns success and emits event."""
        resp = client.post(f"/api/jobs/{JOB_ID}/stop")
        assert resp.status_code == 200

    def test_stop_rejects_invalid_job_id(self, client):
        resp = client.post("/api/jobs/../stop")
        assert resp.status_code in (400, 404)
        resp2 = client.post("/api/jobs/bad..id/stop")
        assert resp2.status_code == 400

    def test_stop_rejects_empty_job_id(self, client):
        resp = client.post("/api/jobs//stop")
        # FastAPI treats empty segment as different route
        assert resp.status_code in (400, 404, 405)

    def test_stop_updates_job_store_status(self, client):
        _make_test_job()
        client.post(f"/api/jobs/{JOB_ID}/stop")
        job = get_job(JOB_ID)
        assert job is not None
        assert job["status"] == "cancelled"
        assert job["stage"] == "manual"
        assert job["progressPct"] == 0
        assert job["error"] == "Job stopped by user"

    def test_stop_unregisters_runner_and_updates_store(self, client):
        runner = FakeRunner()
        register_runner(JOB_ID, runner)
        _make_test_job()
        client.post(f"/api/jobs/{JOB_ID}/stop")
        # Runner should be cancelled and unregistered
        assert runner.cancelled is True
        # Store should reflect cancellation
        job = get_job(JOB_ID)
        assert job["status"] == "cancelled"

    def test_stop_emits_cancelled_stage_event(self, feed: MemoryEventFeed, client):
        _make_test_job()
        client.post(f"/api/jobs/{JOB_ID}/stop")
        events = asyncio.run(feed.replay(JOB_ID))
        stage_events = [e for e in events if e.type == "job.stage"]
        assert any(e.payload.get("stage") == "cancelled" for e in stage_events)


# ─── Retry Job ─────────────────────────────────────────────────────────────


class TestRetryJob:
    def test_retry_job_returns_200(self, client):
        resp = client.post(f"/api/jobs/{JOB_ID}/retry")
        assert resp.status_code == 200

    def test_retry_job_returns_retry_queued(self, client):
        resp = client.post(f"/api/jobs/{JOB_ID}/retry")
        data = resp.json()
        assert data["status"] == "retry_queued"
        assert data["job_id"] == JOB_ID

    def test_retry_job_emits_retry_started(self, feed: MemoryEventFeed, client):
        client.post(f"/api/jobs/{JOB_ID}/retry")
        events = asyncio.run(feed.replay(JOB_ID))
        assert any(e.type == "retry.started" for e in events)

    def test_retry_job_payload_has_item_type_job(self, feed: MemoryEventFeed, client):
        client.post(f"/api/jobs/{JOB_ID}/retry")
        events = asyncio.run(feed.replay(JOB_ID))
        retry_events = [e for e in events if e.type == "retry.started"]
        assert len(retry_events) == 1
        assert retry_events[0].payload["itemType"] == "job"
        assert retry_events[0].payload["itemId"] == JOB_ID

    def test_retry_job_rejects_invalid_id(self, client):
        resp = client.post("/api/jobs/bad..id/retry")
        assert resp.status_code == 400

    def test_retry_job_resets_store_state(self, client):
        _make_test_job()
        client.post(f"/api/jobs/{JOB_ID}/retry")
        job = get_job(JOB_ID)
        assert job is not None
        assert job["status"] == "queued"
        assert job["stage"] == "retry_queued"
        assert job["progressPct"] == 0
        assert job["error"] is None
        # Subagents reset
        for sa in job["subagents"]:
            assert sa["status"] == "pending"
            assert sa["startedAt"] is None
            assert sa["completedAt"] is None
        # Scenes reset
        for s in job["scenes"]:
            assert s["status"] == "pending"

    def test_retry_job_emits_additional_restart_events(self, feed: MemoryEventFeed, client):
        _make_test_job()
        client.post(f"/api/jobs/{JOB_ID}/retry")
        events = asyncio.run(feed.replay(JOB_ID))
        types = [e.type for e in events]
        assert "retry.started" in types
        assert "job.started" in types
        assert "job.stage" in types

    def test_retry_job_works_without_job_in_store(self, client):
        """No job in store — still returns success and emits event (backward compat)."""
        resp = client.post(f"/api/jobs/{JOB_ID}/retry")
        assert resp.status_code == 200
        assert resp.json()["status"] == "retry_queued"


# ─── Retry Scene ───────────────────────────────────────────────────────────


class TestRetryScene:
    def test_retry_scene_returns_200(self, client):
        resp = client.post(f"/api/jobs/{JOB_ID}/retry/{SCENE_ID}")
        assert resp.status_code == 200

    def test_retry_scene_returns_scene_id(self, client):
        resp = client.post(f"/api/jobs/{JOB_ID}/retry/{SCENE_ID}")
        data = resp.json()
        assert data["scene_id"] == SCENE_ID
        assert data["job_id"] == JOB_ID

    def test_retry_scene_emits_retry_started(self, feed: MemoryEventFeed, client):
        client.post(f"/api/jobs/{JOB_ID}/retry/{SCENE_ID}")
        events = asyncio.run(feed.replay(JOB_ID))
        assert any(e.type == "retry.started" for e in events)

    def test_retry_scene_payload_has_scene_scope(self, feed: MemoryEventFeed, client):
        client.post(f"/api/jobs/{JOB_ID}/retry/{SCENE_ID}")
        events = asyncio.run(feed.replay(JOB_ID))
        retry_events = [e for e in events if e.type == "retry.started"]
        assert len(retry_events) == 1
        assert retry_events[0].payload["itemType"] == "scene"
        assert retry_events[0].payload["sceneId"] == SCENE_ID

    def test_retry_scene_rejects_invalid_id(self, client):
        resp = client.post("/api/jobs/../retry/scene_1")
        assert resp.status_code in (400, 404)

    def test_retry_scene_resets_scene_in_store(self, client):
        _make_test_job()
        client.post(f"/api/jobs/{JOB_ID}/retry/scene_2")
        job = get_job(JOB_ID)
        assert job is not None
        scene = next(s for s in job["scenes"] if s["id"] == "scene_2")
        assert scene["status"] == "pending"
        assert scene["retryCount"] == 2  # was 1, incremented

    def test_retry_scene_leaves_other_scenes_unchanged(self, client):
        _make_test_job()
        client.post(f"/api/jobs/{JOB_ID}/retry/scene_2")
        job = get_job(JOB_ID)
        scene1 = next(s for s in job["scenes"] if s["id"] == "scene_1")
        # scene_1 should be untouched
        assert scene1["status"] == "completed"
        assert scene1["retryCount"] == 0

    def test_retry_scene_emits_render_scene_started(self, feed: MemoryEventFeed, client):
        _make_test_job()
        client.post(f"/api/jobs/{JOB_ID}/retry/scene_2")
        events = asyncio.run(feed.replay(JOB_ID))
        render_events = [e for e in events if e.type == "render.scene_started"]
        assert len(render_events) == 1
        assert render_events[0].payload["sceneId"] == "scene_2"
        assert render_events[0].payload["retryCount"] == 2

    def test_retry_scene_works_without_job_in_store(self, client):
        """No job in store — still returns success (backward compat)."""
        resp = client.post(f"/api/jobs/{JOB_ID}/retry/scene_42")
        assert resp.status_code == 200
        assert resp.json()["status"] == "retry_queued"


# ─── Reroute Scene ─────────────────────────────────────────────────────────


class TestRerouteScene:
    def test_reroute_returns_200(self, client):
        resp = client.post(f"/api/jobs/{JOB_ID}/reroute/{SCENE_ID}")
        assert resp.status_code == 200

    def test_reroute_returns_engine_default(self, client):
        resp = client.post(f"/api/jobs/{JOB_ID}/reroute/{SCENE_ID}")
        data = resp.json()
        assert data["status"] == "rerouted"
        assert data["engine"] == "remotion"

    def test_reroute_accepts_engine_in_body(self, client):
        resp = client.post(
            f"/api/jobs/{JOB_ID}/reroute/{SCENE_ID}",
            json={"engine": "manim"},
        )
        data = resp.json()
        assert data["engine"] == "manim"

    def test_reroute_emits_scene_routed(self, feed: MemoryEventFeed, client):
        client.post(f"/api/jobs/{JOB_ID}/reroute/{SCENE_ID}", json={"engine": "animotion"})
        events = asyncio.run(feed.replay(JOB_ID))
        routed_events = [e for e in events if e.type == "director.scene_routed"]
        assert len(routed_events) == 1
        assert routed_events[0].payload["engine"] == "animotion"
        assert routed_events[0].payload["sceneId"] == SCENE_ID

    def test_reroute_with_provider_override(self, feed: MemoryEventFeed, client):
        resp = client.post(
            f"/api/jobs/{JOB_ID}/reroute/{SCENE_ID}",
            json={"engine": "remotion", "provider": "9router", "model": "ocg/deepseek-v4-flash"},
        )
        data = resp.json()
        assert data["provider"] == "9router"
        assert data["model"] == "ocg/deepseek-v4-flash"
        events = asyncio.run(feed.replay(JOB_ID))
        routed = [e for e in events if e.type == "director.scene_routed"]
        assert routed[0].payload["provider"] == "9router"
        assert routed[0].payload["model"] == "ocg/deepseek-v4-flash"

    def test_reroute_rejects_invalid_job_id(self, client):
        resp = client.post("/api/jobs/../reroute/scene_1")
        assert resp.status_code in (400, 404)

    def test_reroute_rejects_invalid_scene_id(self, client):
        resp = client.post(f"/api/jobs/{JOB_ID}/reroute/bad..id")
        assert resp.status_code == 400

    def test_reroute_updates_engine_in_store(self, client):
        _make_test_job()
        resp = client.post(f"/api/jobs/{JOB_ID}/reroute/scene_1", json={"engine": "manim"})
        assert resp.status_code == 200
        job = get_job(JOB_ID)
        scene = next(s for s in job["scenes"] if s["id"] == "scene_1")
        assert scene["engine"] == "manim"
        assert scene["status"] == "pending"  # marked for re-render

    def test_reroute_leaves_other_scenes_unchanged(self, client):
        _make_test_job()
        client.post(f"/api/jobs/{JOB_ID}/reroute/scene_1", json={"engine": "manim"})
        job = get_job(JOB_ID)
        scene2 = next(s for s in job["scenes"] if s["id"] == "scene_2")
        # scene_2 should be untouched
        assert scene2["engine"] == "remotion"
        assert scene2["status"] == "rendering"

    def test_reroute_emits_render_scene_started(self, feed: MemoryEventFeed, client):
        _make_test_job()
        client.post(f"/api/jobs/{JOB_ID}/reroute/scene_1", json={"engine": "animotion"})
        events = asyncio.run(feed.replay(JOB_ID))
        routed = [e for e in events if e.type == "director.scene_routed"]
        render = [e for e in events if e.type == "render.scene_started"]
        assert len(routed) == 1
        assert routed[0].payload["engine"] == "animotion"
        assert len(render) == 1
        assert render[0].payload["engine"] == "animotion"
        assert render[0].payload["previousEngine"] == "remotion"
        assert render[0].payload["reason"] == "User reroute"

    def test_reroute_defaults_to_remotion_when_no_scene_in_store(self, client):
        """No scenes in store — defaults to remotion (backward compat)."""
        _make_test_job(scenes=[])
        resp = client.post(f"/api/jobs/{JOB_ID}/reroute/scene_1")
        assert resp.status_code == 200
        assert resp.json()["engine"] == "remotion"


# ─── Runner Registry ───────────────────────────────────────────────────────


class TestRunnerRegistry:
    def test_register_unregister_cycle(self):
        runner = FakeRunner()
        register_runner("j1", runner)
        register_runner("j2", FakeRunner())
        unregister_runner("j2")
        # j1 should still be registered
        from videoforge.api.actions import _get_runner
        assert _get_runner("j1") is runner
        assert _get_runner("j2") is None
        unregister_runner("j1")

    def test_unregister_nonexistent_does_not_error(self):
        unregister_runner("nonexistent")
