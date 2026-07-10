"""Tests for jobs REST endpoints — list, detail, seed data, grill, create."""

from __future__ import annotations

from fastapi.testclient import TestClient

from videoforge.api.app import create_app
from videoforge.api.jobs import (
    GrillResult,
    _calc_confidence,
    _extract_keywords,
    _job_store,
    _missing_details,
    grill_prompt,
    store_job,
)


def _clear_store():
    _job_store.clear()


class TestJobsList:
    """GET /api/jobs"""

    def test_empty_list_returns_empty_array(self):
        _clear_store()
        app = create_app()
        client = TestClient(app)
        resp = client.get("/api/jobs")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_returns_seeded_jobs(self):
        _clear_store()
        app = create_app()
        client = TestClient(app)
        # Trigger seed
        from videoforge.api.jobs import seed_jobs as do_seed
        do_seed()
        resp = client.get("/api/jobs")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 4

    def test_list_entry_has_expected_fields(self):
        _clear_store()
        store_job("j1", {
            "id": "j1",
            "title": "Test job",
            "status": "running",
            "stage": "render",
            "progressPct": 50,
            "createdAt": "2025-01-01T00:00:00",
            "startedAt": None,
            "completedAt": None,
            "error": None,
            "subagents": [],
            "scenes": [],
            "artifacts": [],
            "events": [],
        })
        app = create_app()
        client = TestClient(app)
        resp = client.get("/api/jobs")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        j = data[0]
        assert j["id"] == "j1"
        assert j["title"] == "Test job"
        assert j["status"] == "running"
        assert j["progressPct"] == 50


class TestJobDetail:
    """GET /api/jobs/{job_id}"""

    def test_detail_returns_job(self):
        _clear_store()
        store_job("detail-1", {
            "id": "detail-1",
            "title": "Detail test",
            "status": "completed",
            "stage": "done",
            "progressPct": 100,
            "createdAt": "2025-01-01T00:00:00",
            "startedAt": None,
            "completedAt": "2025-01-01T01:00:00",
            "error": None,
            "subagents": [],
            "scenes": [],
            "artifacts": [],
            "events": [],
        })
        app = create_app()
        client = TestClient(app)
        resp = client.get("/api/jobs/detail-1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "detail-1"
        assert data["title"] == "Detail test"
        assert data["status"] == "completed"

    def test_detail_includes_subagents_and_scenes(self):
        _clear_store()
        store_job("detail-2", {
            "id": "detail-2",
            "title": "Rich job",
            "status": "running",
            "stage": "render",
            "progressPct": 60,
            "createdAt": "2025-01-01T00:00:00",
            "startedAt": "2025-01-01T00:01:00",
            "completedAt": None,
            "error": None,
            "subagents": [
                {"id": "sa1", "name": "A", "engine": "e", "task": "t", "status": "running"},
            ],
            "scenes": [
                {"id": "sc1", "kind": "code", "engine": "e", "status": "rendering", "reviewIssues": 0, "retryCount": 0},
            ],
            "artifacts": [],
            "events": [],
        })
        app = create_app()
        client = TestClient(app)
        resp = client.get("/api/jobs/detail-2")
        data = resp.json()
        assert len(data["subagents"]) == 1
        assert data["subagents"][0]["id"] == "sa1"
        assert len(data["scenes"]) == 1
        assert data["scenes"][0]["id"] == "sc1"

    def test_detail_enriches_scene_artifacts_from_disk(self, tmp_path, monkeypatch):
        """Scene detail includes artifact flags+URLs when files exist on disk."""
        from videoforge.api.artifacts import ARTIFACTS_DIR
        monkeypatch.setattr("videoforge.api.artifacts.ARTIFACTS_DIR", tmp_path)
        # Create artifact files for sc1
        (tmp_path / "detail-3" / "thumbnails").mkdir(parents=True)
        (tmp_path / "detail-3" / "thumbnails" / "sc1.jpg").write_bytes(b"thumb")
        (tmp_path / "detail-3" / "frames").mkdir()
        (tmp_path / "detail-3" / "frames" / "sc1.png").write_bytes(b"frame")
        (tmp_path / "detail-3" / "reports").mkdir()
        (tmp_path / "detail-3" / "reports" / "sc1.json").write_text('{"ok":true}')

        _clear_store()
        store_job("detail-3", {
            "id": "detail-3",
            "title": "Artifact rich",
            "status": "running",
            "stage": "render",
            "progressPct": 50,
            "createdAt": "2025-01-01T00:00:00",
            "startedAt": "2025-01-01T00:01:00",
            "completedAt": None,
            "error": None,
            "subagents": [],
            "scenes": [
                {"id": "sc1", "kind": "code", "engine": "remotion", "status": "completed", "reviewIssues": 0, "retryCount": 0},
            ],
            "artifacts": [],
            "events": [],
        })
        client = TestClient(create_app())
        resp = client.get("/api/jobs/detail-3")
        assert resp.status_code == 200
        scene = resp.json()["scenes"][0]
        assert scene["hasThumbnail"] is True
        assert scene["hasFrame"] is True
        assert scene["hasReport"] is True
        assert scene["thumbnailUrl"] == "/api/artifacts/detail-3/scenes/sc1/thumbnail"
        assert scene["frameUrl"] == "/api/artifacts/detail-3/scenes/sc1/frame"
        assert scene["reportUrl"] == "/api/artifacts/detail-3/scenes/sc1/report"
        # Original fields preserved
        assert scene["kind"] == "code"
        assert scene["status"] == "completed"

    def test_detail_failed_job_shows_artifacts(self, tmp_path, monkeypatch):
        """Failed job with partial artifacts still enriches scene detail."""
        monkeypatch.setattr("videoforge.api.artifacts.ARTIFACTS_DIR", tmp_path)
        (tmp_path / "detail-4" / "thumbnails").mkdir(parents=True)
        (tmp_path / "detail-4" / "thumbnails" / "sc_failed.jpg").write_bytes(b"partial")
        _clear_store()
        store_job("detail-4", {
            "id": "detail-4",
            "title": "Failed job",
            "status": "failed",
            "stage": "render",
            "progressPct": 40,
            "createdAt": "2025-01-01T00:00:00",
            "startedAt": "2025-01-01T00:01:00",
            "completedAt": "2025-01-01T00:02:00",
            "error": "Render error",
            "subagents": [],
            "scenes": [
                {"id": "sc_failed", "kind": "diagram", "engine": "manim", "status": "failed", "reviewIssues": 2, "retryCount": 2},
            ],
            "artifacts": [],
            "events": [],
        })
        client = TestClient(create_app())
        resp = client.get("/api/jobs/detail-4")
        assert resp.status_code == 200
        scene = resp.json()["scenes"][0]
        assert scene["hasThumbnail"] is True
        assert scene["thumbnailUrl"] is not None
        assert scene["status"] == "failed"  # original status preserved

    def test_detail_no_scenes_returns_empty(self):
        _clear_store()
        store_job("detail-5", {
            "id": "detail-5",
            "title": "No scenes",
            "status": "queued",
            "stage": "plan",
            "progressPct": 0,
            "createdAt": "2025-01-01T00:00:00",
            "startedAt": None,
            "completedAt": None,
            "error": None,
            "subagents": [],
            "scenes": [],
            "artifacts": [],
            "events": [],
        })
        client = TestClient(create_app())
        resp = client.get("/api/jobs/detail-5")
        assert resp.status_code == 200
        assert resp.json()["scenes"] == []

    def test_detail_404_for_missing_job(self):
        _clear_store()
        app = create_app()
        client = TestClient(app)
        resp = client.get("/api/jobs/nonexistent")
        assert resp.status_code == 404


class TestSeedData:
    """Seed data integrity (matches mock.ts contract)."""

    def test_seeded_jobs_have_all_statuses(self):
        _clear_store()
        from videoforge.api.jobs import seed_jobs as do_seed
        do_seed()
        app = create_app()
        client = TestClient(app)
        resp = client.get("/api/jobs")
        jobs = resp.json()
        statuses = {j["status"] for j in jobs}
        assert "running" in statuses
        assert "queued" in statuses
        assert "completed" in statuses
        assert "failed" in statuses

    def test_seeded_detail_has_events(self):
        _clear_store()
        from videoforge.api.jobs import seed_jobs as do_seed
        do_seed()
        app = create_app()
        client = TestClient(app)
        resp = client.get("/api/jobs/job_001")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["events"]) > 0
        assert data["events"][0]["type"] == "job.started"


GRILL_PAYLOAD = {
    "prompt": "Explain Kubernetes architecture with code examples",
    "options": {
        "voice": "alba",
        "provider": "9router",
        "model": "ocg/deepseek-v4-flash",
        "maxDuration": 180,
        "fps": 30,
    },
}


# ─── Deterministic griller unit tests ──────────────────────────────────────


class TestGriller:
    """Deterministic griller produces stable, structured output."""

    def test_grill_prompt_returns_grill_result(self):
        result = grill_prompt("Explain Kubernetes architecture with code examples")
        assert isinstance(result, GrillResult)
        assert len(result.refinedPrompt) > 20
        assert len(result.suggestedScenes) >= 3
        assert 0 <= result.confidence <= 1

    def test_grill_prompt_is_deterministic(self):
        a = grill_prompt("Build a React component library tutorial")
        b = grill_prompt("Build a React component library tutorial")
        assert a.refinedPrompt == b.refinedPrompt
        assert a.suggestedScenes == b.suggestedScenes
        assert a.missingDetails == b.missingDetails
        assert a.confidence == b.confidence

    def test_different_prompt_different_result(self):
        a = grill_prompt("Build a React component library tutorial")
        b = grill_prompt("Explain Docker networking and container orchestration")
        assert a.refinedPrompt != b.refinedPrompt
        assert a.suggestedScenes != b.suggestedScenes

    def test_code_keyword_triggers_code_scene(self):
        result = grill_prompt("Build a Python API with FastAPI and SQLAlchemy")
        kinds = [s.kind for s in result.suggestedScenes]
        assert "code" in kinds

    def test_architecture_keyword_triggers_diagram_scene(self):
        result = grill_prompt("Explain microservices architecture design patterns")
        kinds = [s.kind for s in result.suggestedScenes]
        assert "diagram" in kinds

    def test_short_prompt_lower_confidence(self):
        short = grill_prompt("Explain Kubernetes")
        long = grill_prompt("Explain Kubernetes architecture with code examples, deployment strategies, and best practices for production")
        assert short.confidence < long.confidence

    def test_minimal_prompt_gets_minimum_scenes(self):
        result = grill_prompt("Show video")
        assert len(result.suggestedScenes) >= 3

    def test_missing_details_has_length_hint_for_short_prompt(self):
        result = grill_prompt("Hi there short prompt")
        assert any("more detail" in d.lower() for d in result.missingDetails)

    def test_extract_keywords_removes_stop_words(self):
        kw = _extract_keywords("the video about a new system for data processing")
        assert "the" not in kw
        assert "data" in kw
        assert "processing" in kw

    def test_calc_confidence_bounds(self):
        assert _calc_confidence("short", {"one", "two"}) >= 0.4
        assert _calc_confidence("short", {"one", "two"}) <= 1.0

    def test_missing_details_empty_for_rich_prompt(self):
        rich = "Create advanced tutorial for expert developers explaining Kubernetes architecture with code examples in 10 minutes with professional tone"
        details = _missing_details(rich)
        assert len(details) < 3


# ─── /api/jobs/grill endpoint ────────────────────────────────────────────


class TestGrillEndpoint:
    """POST /api/jobs/grill returns deterministic GrillResult."""

    def test_grill_returns_200(self):
        _clear_store()
        app = create_app()
        client = TestClient(app)
        resp = client.post("/api/jobs/grill", json=GRILL_PAYLOAD)
        assert resp.status_code == 200

    def test_grill_returns_grill_result_shape(self):
        _clear_store()
        app = create_app()
        client = TestClient(app)
        resp = client.post("/api/jobs/grill", json=GRILL_PAYLOAD)
        data = resp.json()
        assert "refinedPrompt" in data
        assert "suggestedScenes" in data
        assert "missingDetails" in data
        assert "confidence" in data
        assert len(data["suggestedScenes"]) >= 3
        assert 0 <= data["confidence"] <= 1

    def test_grill_is_deterministic(self):
        _clear_store()
        app = create_app()
        client = TestClient(app)
        a = client.post("/api/jobs/grill", json=GRILL_PAYLOAD).json()
        b = client.post("/api/jobs/grill", json=GRILL_PAYLOAD).json()
        assert a == b

    def test_grill_rejects_short_prompt(self):
        _clear_store()
        app = create_app()
        client = TestClient(app)
        resp = client.post("/api/jobs/grill", json={"prompt": "Hi", "options": {}})
        assert resp.status_code == 422

    def test_grill_accepts_minimal_options(self):
        _clear_store()
        app = create_app()
        client = TestClient(app)
        resp = client.post("/api/jobs/grill", json={"prompt": "Explain Kubernetes architecture with code examples"})
        assert resp.status_code == 200

    def test_suggested_scene_shape(self):
        _clear_store()
        app = create_app()
        client = TestClient(app)
        resp = client.post("/api/jobs/grill", json=GRILL_PAYLOAD)
        scene = resp.json()["suggestedScenes"][0]
        assert "kind" in scene
        assert "title" in scene
        assert "description" in scene
        assert "reasoning" in scene


# ─── POST /api/jobs (create job) endpoint ─────────────────────────────────


class TestCreateJobEndpoint:
    """POST /api/jobs creates job, emits events, returns jobId."""

    def test_create_job_returns_200(self):
        _clear_store()
        app = create_app()
        client = TestClient(app)
        resp = client.post("/api/jobs", json=GRILL_PAYLOAD)
        assert resp.status_code == 200

    def test_create_job_returns_job_id(self):
        _clear_store()
        app = create_app()
        client = TestClient(app)
        resp = client.post("/api/jobs", json=GRILL_PAYLOAD)
        data = resp.json()
        assert data["jobId"].startswith("job_")

    def test_create_job_returns_queued_status(self):
        _clear_store()
        app = create_app()
        client = TestClient(app)
        resp = client.post("/api/jobs", json=GRILL_PAYLOAD)
        assert resp.json()["status"] == "queued"

    def test_create_job_returns_grill_result(self):
        _clear_store()
        app = create_app()
        client = TestClient(app)
        resp = client.post("/api/jobs", json=GRILL_PAYLOAD)
        data = resp.json()
        assert "grillResult" in data
        assert data["grillResult"]["confidence"] > 0

    def test_create_job_deterministic_grill_result(self):
        """Same prompt yields same grill result across two creates."""
        _clear_store()
        app = create_app()
        client = TestClient(app)
        a = client.post("/api/jobs", json=GRILL_PAYLOAD).json()
        b = client.post("/api/jobs", json=GRILL_PAYLOAD).json()
        assert a["jobId"] != b["jobId"]
        assert a["grillResult"] == b["grillResult"]

    def test_create_job_scene_suggestions_in_grill_result(self):
        _clear_store()
        app = create_app()
        client = TestClient(app)
        resp = client.post("/api/jobs", json=GRILL_PAYLOAD)
        scenes = resp.json()["grillResult"]["suggestedScenes"]
        assert len(scenes) >= 3
        assert scenes[0]["kind"] == "title"
        assert scenes[-1]["kind"] == "outro"

    def test_create_job_rejects_short_prompt(self):
        _clear_store()
        app = create_app()
        client = TestClient(app)
        resp = client.post("/api/jobs", json={"prompt": "Hi", "options": {}})
        assert resp.status_code == 422

    def test_create_job_stores_job_detail(self):
        _clear_store()
        app = create_app()
        client = TestClient(app)
        resp = client.post("/api/jobs", json=GRILL_PAYLOAD)
        job_id = resp.json()["jobId"]
        detail = client.get(f"/api/jobs/{job_id}")
        assert detail.status_code == 200
        assert detail.json()["status"] == "queued"
        assert len(detail.json()["events"]) == 3


# ─── Provider/Model override in job creation ────────────────────────────


class TestJobProviderOverride:
    """Per-run provider/model overrides stored correctly in job detail."""

    def test_create_job_stores_provider_model(self):
        _clear_store()
        app = create_app()
        client = TestClient(app)
        resp = client.post("/api/jobs", json=GRILL_PAYLOAD)
        job_id = resp.json()["jobId"]
        detail = client.get(f"/api/jobs/{job_id}").json()
        assert detail["provider"] == "9router"
        assert detail["model"] == "ocg/deepseek-v4-flash"

    def test_create_job_override_provider(self):
        _clear_store()
        app = create_app()
        client = TestClient(app)
        payload = {
            **GRILL_PAYLOAD,
            "runOverride": {"provider": "anthropic", "model": "claude-sonnet-4-20250514"},
        }
        resp = client.post("/api/jobs", json=payload)
        job_id = resp.json()["jobId"]
        detail = client.get(f"/api/jobs/{job_id}").json()
        assert detail["provider"] == "anthropic"
        assert detail["model"] == "claude-sonnet-4-20250514"

    def test_create_job_override_model_only(self):
        _clear_store()
        app = create_app()
        client = TestClient(app)
        payload = {
            **GRILL_PAYLOAD,
            "runOverride": {"model": "gpt-4o-mini"},
        }
        resp = client.post("/api/jobs", json=payload)
        job_id = resp.json()["jobId"]
        detail = client.get(f"/api/jobs/{job_id}").json()
        # provider falls back to options.provider since only model overridden
        assert detail["provider"] == "9router"
        assert detail["model"] == "gpt-4o-mini"

    def test_create_job_override_none_provider_uses_options(self):
        _clear_store()
        app = create_app()
        client = TestClient(app)
        payload = {
            **GRILL_PAYLOAD,
            "runOverride": {"provider": None, "model": None},
        }
        resp = client.post("/api/jobs", json=payload)
        job_id = resp.json()["jobId"]
        detail = client.get(f"/api/jobs/{job_id}").json()
        # Both None → fall back to options defaults
        assert detail["provider"] == "9router"
        assert detail["model"] == "ocg/deepseek-v4-flash"

    def test_create_job_override_with_temperature(self):
        _clear_store()
        app = create_app()
        client = TestClient(app)
        payload = {
            **GRILL_PAYLOAD,
            "runOverride": {"provider": "openai", "model": "gpt-4o", "temperature": 0.5},
        }
        resp = client.post("/api/jobs", json=payload)
        assert resp.status_code == 200
        job_id = resp.json()["jobId"]
        detail = client.get(f"/api/jobs/{job_id}").json()
        assert detail["provider"] == "openai"
        assert detail["model"] == "gpt-4o"
        assert detail["runOverride"]["temperature"] == 0.5

    def test_create_job_emit_effective_provider_in_event(self):
        _clear_store()
        app = create_app()
        client = TestClient(app)
        payload = {**GRILL_PAYLOAD, "runOverride": {"provider": "anthropic", "model": "claude-sonnet-4-20250514"}}
        resp = client.post("/api/jobs", json=payload)
        job_id = resp.json()["jobId"]
        detail = client.get(f"/api/jobs/{job_id}").json()
        # First event (job.started) should contain effectiveProvider
        first_event = detail["events"][0]
        assert first_event["payload"]["effectiveProvider"] == "anthropic"
        assert first_event["payload"]["effectiveModel"] == "claude-sonnet-4-20250514"


# ─── Error handling ─────────────────────────────────────────────────────


class TestJobsErrorHandling:
    """Job endpoints handle errors gracefully."""

    def test_grill_malformed_json(self):
        _clear_store()
        app = create_app()
        client = TestClient(app)
        resp = client.post("/api/jobs/grill", data="not-json", headers={"Content-Type": "application/json"})
        assert resp.status_code in (400, 422)

    def test_create_malformed_json(self):
        _clear_store()
        app = create_app()
        client = TestClient(app)
        resp = client.post("/api/jobs", data="not-json", headers={"Content-Type": "application/json"})
        assert resp.status_code in (400, 422)

    def test_grill_extra_fields_ignored(self):
        _clear_store()
        app = create_app()
        client = TestClient(app)
        payload = {**GRILL_PAYLOAD, "extraField": "should be ignored"}
        resp = client.post("/api/jobs/grill", json=payload)
        assert resp.status_code == 200
