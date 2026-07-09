"""Tests for job action endpoints: stop, retry, reroute.

Covers:
- Stop emits job.failed event, cancels runner if registered
- Retry job emits retry.started event
- Retry scene emits retry.started with scene scope
- Reroute scene emits director.scene_routed event
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

JOB_ID = "test-job-001"
SCENE_ID = "scene_42"


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

    def test_reroute_rejects_invalid_job_id(self, client):
        resp = client.post("/api/jobs/../reroute/scene_1")
        assert resp.status_code in (400, 404)

    def test_reroute_rejects_invalid_scene_id(self, client):
        resp = client.post(f"/api/jobs/{JOB_ID}/reroute/bad..id")
        assert resp.status_code == 400


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
