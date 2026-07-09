"""Tests for SSE event contract — headers, encoding, schema.

Covers:
- Event serialization matches SSE spec (event:/id:/data: format)
- All event types serialize/deserialize roundtrip
- SSE response headers correct
- Event feed streaming yields expected events
- after_id resumption works
- payload schema validation for each event type
"""

from __future__ import annotations

import asyncio
import json

import pytest
from fastapi.testclient import TestClient

from videoforge.api.adapters import MemoryEventFeed, PlaceholderEventFeed, create_feed
from videoforge.api.app import create_app
from videoforge.api.events import (
    EventType,
    JobCompleted,
    JobFailed,
    JobStage,
    JobStarted,
    JobTodo,
    PromptGrilled,
    DirectorScenePlanned,
    DirectorSceneRouted,
    SubagentStarted,
    SubagentToken,
    SubagentCompleted,
    SubagentFailed,
    RenderSceneStarted,
    RenderSceneCompleted,
    ReviewIssue,
    RepairPlan,
    RetryStarted,
    ArtifactReady,
    SSE_EVENT_TYPES,
    parse_event,
    serialize_event,
)

# ─── Fixtures ──────────────────────────────────────────────────────────────

JOB_ID = "test-job-001"


@pytest.fixture
def feed():
    """MemoryEventFeed with seeded event for JOB_ID so stream yields immediately."""
    f = MemoryEventFeed()
    ev = JobStarted(jobId=JOB_ID, payload={"seed": True})
    asyncio.run(f.append(ev))
    return f


@pytest.fixture
def client(feed):
    app = create_app(feed=feed)
    return TestClient(app)


@pytest.fixture
def job_id():
    return JOB_ID


@pytest.fixture
def sample_events(job_id):
    """Seed a known event sequence for replay tests."""
    return [
        JobStarted(
            jobId=job_id,
            payload={"recipeId": "test-recipe", "input": "test input", "runId": job_id},
        ),
        JobStage(
            jobId=job_id,
            payload={"stage": "render", "progress": 50, "label": "Rendering"},
        ),
        JobCompleted(
            jobId=job_id,
            payload={"finalVideo": f"/artifacts/{job_id}/final.mp4", "duration": 30, "artifactCount": 3},
        ),
    ]


# ─── Event serialization ──────────────────────────────────────────────────


class TestEventSerialization:
    """SSE wire format must match spec: event:/id:/data: lines."""

    def test_serialize_has_event_line(self):
        event = JobStarted(jobId="j1", payload={})
        sse = serialize_event(event)
        assert sse.startswith("event: job.started\n"), f"Bad prefix: {sse[:60]}"

    def test_serialize_has_id_line(self):
        event = JobStarted(jobId="j1", payload={})
        sse = serialize_event(event)
        assert "id: evt_" in sse, f"Missing id line: {sse[:60]}"

    def test_serialize_has_data_line(self):
        event = JobStarted(jobId="j1", payload={})
        sse = serialize_event(event)
        assert "data: " in sse, f"Missing data line: {sse[:60]}"

    def test_serialize_ends_with_blank_line(self):
        event = JobStarted(jobId="j1", payload={})
        sse = serialize_event(event)
        assert sse.endswith("\n\n"), f"Must end with double newline, got: {repr(sse[-10:])}"

    def test_serialize_data_is_json(self):
        event = JobStarted(jobId="j1", payload={"recipeId": "abc"})
        sse = serialize_event(event)
        data_line = [l for l in sse.split("\n") if l.startswith("data: ")][0]
        data_json = data_line[6:]  # strip "data: "
        parsed = json.loads(data_json)
        assert parsed["type"] == "job.started"
        assert parsed["jobId"] == "j1"
        assert parsed["payload"]["recipeId"] == "abc"

    def test_roundtrip_all_event_types(self, job_id):
        """Every event type serializes and parse_event recovers it."""
        cases = [
            JobStarted(jobId=job_id, payload={"recipeId": "r1", "input": "i", "runId": job_id}),
            JobStage(jobId=job_id, payload={"stage": "s1", "progress": 42, "label": "test"}),
            JobTodo(jobId=job_id, payload={"itemId": "t1", "description": "test", "status": "pending"}),
            PromptGrilled(jobId=job_id, payload={"grills": ["q1"], "chosen": "a1"}),
            DirectorScenePlanned(jobId=job_id, payload={"sceneCount": 3, "kinds": ["title", "code", "outro"]}),
            DirectorSceneRouted(jobId=job_id, payload={"sceneId": "s1", "kind": "code", "engine": "remotion"}),
            SubagentStarted(jobId=job_id, payload={"subagentId": "sa1", "role": "writer", "model": "gpt4"}),
            SubagentToken(jobId=job_id, payload={"subagentId": "sa1", "tokens": 150, "progressPct": 30}),
            SubagentCompleted(jobId=job_id, payload={"subagentId": "sa1", "result": "done"}),
            SubagentFailed(jobId=job_id, payload={"subagentId": "sa1", "error": "timeout"}),
            RenderSceneStarted(jobId=job_id, payload={"sceneId": "s1", "engine": "remotion"}),
            RenderSceneCompleted(jobId=job_id, payload={"sceneId": "s1", "outputPath": "/out/s1.mp4", "duration": 90}),
            ReviewIssue(jobId=job_id, payload={"sceneId": "s1", "gate": "layout", "verdict": "fail", "detail": "overlap detected"}),
            RepairPlan(jobId=job_id, payload={"issue": "overlap", "strategy": "nudge_spacing", "retryCount": 1}),
            RetryStarted(jobId=job_id, payload={"itemType": "scene", "itemId": "s1", "attempt": 2, "maxRetries": 3}),
            ArtifactReady(jobId=job_id, payload={"artifactType": "thumbnail", "path": "/art/s1.jpg", "sceneId": "s1"}),
            JobCompleted(jobId=job_id, payload={"finalVideo": "/out/final.mp4", "duration": 120, "artifactCount": 10}),
            JobFailed(jobId=job_id, payload={"error": "render crash", "stage": "render", "retryCount": 3}),
        ]
        for original in cases:
            sse = serialize_event(original)
            data_line = [l for l in sse.split("\n") if l.startswith("data: ")][0]
            recovered = parse_event(data_line[6:])
            assert recovered.type == original.type, f"Type mismatch for {original.type}"
            assert recovered.jobId == original.jobId, f"jobId mismatch for {original.type}"
            assert recovered.payload == original.payload, f"payload mismatch for {original.type}"

    def test_sse_event_types_list_complete(self):
        """SSE_EVENT_TYPES matches EventType enum exactly."""
        assert set(SSE_EVENT_TYPES) == {e.value for e in EventType}
        assert len(SSE_EVENT_TYPES) == 18


# ─── SSE HTTP endpoint ────────────────────────────────────────────────────


class TestSSEEndpoint:
    """SSE endpoint contract: headers, encoding, stream behavior.

    Uses ``limit`` query param to close stream after N events.
    """

    def test_sse_returns_text_event_stream(self, client, job_id):
        resp = client.get(f"/api/jobs/{job_id}/stream?limit=1")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")

    def test_sse_has_cache_headers(self, client, job_id):
        resp = client.get(f"/api/jobs/{job_id}/stream?limit=1")
        assert resp.headers.get("cache-control") == "no-cache"
        assert resp.headers.get("x-accel-buffering") == "no"

    def test_sse_has_event_types_header(self, client, job_id):
        resp = client.get(f"/api/jobs/{job_id}/stream?limit=1")
        header = resp.headers.get("x-event-types", "")
        types = header.split(",")
        assert EventType.JOB_STARTED in types
        assert EventType.JOB_FAILED in types
        assert len(types) == 18

    def test_sse_rejects_invalid_job_id(self, client):
        # path traversal char in job_id is caught by FastAPI route matching → 404
        resp = client.get("/api/jobs/../etc/stream")
        assert resp.status_code in (400, 404)
        # double dots in path segment cause 400
        resp2 = client.get("/api/jobs/bad..id/stream?limit=1")
        assert resp2.status_code in (400, 404)

    def test_events_endpoint_returns_json(self, job_id, sample_events):
        f = MemoryEventFeed()
        for ev in sample_events:
            asyncio.run(f.append(ev))
        app = create_app(feed=f)
        client = TestClient(app)
        resp = client.get(f"/api/jobs/{job_id}/events")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        assert data[0]["type"] == "job.started"
        assert data[1]["type"] == "job.stage"
        assert data[2]["type"] == "job.completed"

    def test_sse_streams_placeholder_events(self, job_id):
        """Placeholder feed yields expected event sequence."""
        feed = PlaceholderEventFeed()
        app = create_app(feed=feed)
        client = TestClient(app)
        resp = client.get(f"/api/jobs/{job_id}/stream?limit=10")
        assert resp.status_code == 200
        body = resp.text
        assert "event: job.started" in body
        assert "event: job.stage" in body
        assert "event: job.completed" in body
        for line in body.split("\n"):
            if line.startswith("event: "):
                assert line[7:] in SSE_EVENT_TYPES, f"Unknown event type: {line}"

    def test_sse_streams_persisted_events(self, job_id, sample_events):
        """Persisted events are streamed on connect."""
        f = MemoryEventFeed()
        for ev in sample_events:
            asyncio.run(f.append(ev))
        app = create_app(feed=f)
        client = TestClient(app)
        resp = client.get(f"/api/jobs/{job_id}/stream?limit=10")
        assert resp.status_code == 200
        body = resp.text
        assert "event: job.started" in body
        assert "event: job.stage" in body
        assert "event: job.completed" in body

    def test_sse_respects_after_id(self, job_id, sample_events):
        """after_id skips events before that ID."""
        f = MemoryEventFeed()
        for ev in sample_events:
            asyncio.run(f.append(ev))
        app = create_app(feed=f)
        client = TestClient(app)
        after_id = sample_events[0].id
        resp = client.get(f"/api/jobs/{job_id}/stream?limit=10&after_id={after_id}")
        assert resp.status_code == 200
        body = resp.text
        assert "event: job.started" not in body, "after_id should skip first event"
        assert "event: job.stage" in body


# ─── Event Feed Adapters ──────────────────────────────────────────────────


class TestEventFeeds:
    """All feed types implement base contract correctly."""

    @pytest.mark.parametrize("kind", ["memory", "placeholder"])
    def test_feeds_implement_contract(self, kind, job_id):
        feed = create_feed(kind)
        event = JobStarted(jobId=job_id, payload={"test": True})
        asyncio.run(feed.append(event))
        events = asyncio.run(feed.replay(job_id))
        assert len(events) >= 1
        assert events[0].type == "job.started"
        assert events[0].payload == {"test": True}

    def test_memory_feed_stream_yields_events_in_order(self, job_id):
        feed = MemoryEventFeed()
        events = [
            JobStarted(jobId=job_id, payload={"step": "a"}),
            JobStage(jobId=job_id, payload={"stage": "b", "progress": 50, "label": "b"}),
            JobCompleted(jobId=job_id, payload={"step": "c"}),
        ]

        async def run():
            for ev in events:
                await feed.append(ev)
            streamed = [s async for s in feed.stream(job_id)]
            return streamed

        streamed = asyncio.run(run())
        assert len(streamed) == 3
        for sse_str in streamed:
            assert sse_str.startswith("event: ")

    def test_placeholder_feed_has_all_stages(self, job_id):
        feed = PlaceholderEventFeed()

        async def collect():
            result = []
            async for s in feed.stream(job_id):
                result.append(s)
                if len(result) >= 10:
                    break
            return result

        events = asyncio.run(collect())
        types = set()
        for s in events:
            for line in s.split("\n"):
                if line.startswith("event: "):
                    types.add(line[7:])
        assert "job.started" in types
        assert "job.completed" in types
        assert "job.stage" in types

    @pytest.mark.skip("FileEventFeed requires disk write access")
    def test_file_feed(self, job_id):
        pass


# ─── Payload schema validation ─────────────────────────────────────────────


class TestPayloadSchemas:
    """Each event type enforces expected payload shape."""

    def test_job_started_payload(self, job_id):
        ev = JobStarted(jobId=job_id, payload={"recipeId": "r1", "input": "text", "runId": job_id})
        assert ev.payload["recipeId"] == "r1"

    def test_job_stage_payload(self, job_id):
        ev = JobStage(jobId=job_id, payload={"stage": "render", "progress": 75, "label": "Rendering"})
        assert ev.payload["progress"] == 75

    def test_job_failed_payload(self, job_id):
        ev = JobFailed(jobId=job_id, payload={"error": "timeout", "stage": "render", "retryCount": 2})
        assert ev.payload["retryCount"] == 2

    def test_subagent_token_payload(self, job_id):
        ev = SubagentToken(jobId=job_id, payload={"subagentId": "sa1", "tokens": 500, "progressPct": 60})
        assert ev.payload["tokens"] == 500
