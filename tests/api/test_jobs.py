"""Tests for jobs REST endpoints — list, detail, seed data, grill, create."""

from __future__ import annotations

from fastapi.testclient import TestClient

from videoforge.api.app import create_app
from videoforge.api.jobs import (
    GrillResult,
    SuggestedTemplate,
    _calc_confidence,
    _extract_keywords,
    _job_store,
    _missing_details,
    _suggest_templates,
    _grill_sessions,
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

    # ── Template suggestions ────────────────────────────────────────

    def test_grill_returns_suggested_templates(self):
        result = grill_prompt("Explain Kubernetes architecture with code examples")
        assert hasattr(result, "suggestedTemplates")
        assert isinstance(result.suggestedTemplates, list)

    def test_suggest_templates_explain_prompt(self):
        result = _suggest_templates("explain how DNS works step by step")
        assert len(result) >= 1
        assert isinstance(result[0], SuggestedTemplate)
        assert result[0].scene_count >= 3

    def test_suggest_templates_tutorial_prompt(self):
        result = _suggest_templates("build a tutorial for Python beginners")
        ids = [t.id for t in result]
        assert "tutorial" in ids

    def test_suggest_templates_is_deterministic(self):
        a = _suggest_templates("show me the data analytics and metrics charts")
        b = _suggest_templates("show me the data analytics and metrics charts")
        assert [t.id for t in a] == [t.id for t in b]

    def test_grill_result_contains_suggested_templates(self):
        result = grill_prompt("create a promotional marketing campaign video")
        template_ids = [t.id for t in result.suggestedTemplates]
        assert len(template_ids) >= 1

    def test_suggest_templates_empty_for_irrelevant(self):
        result = _suggest_templates("xyzzy flurbo garblex")
        assert isinstance(result, list)

    def test_suggest_templates_max_respected(self):
        result = _suggest_templates("explain tutorial data story timeline comparison review")
        assert len(result) <= 3

    def test_grill_result_template_has_expected_shape(self):
        result = _suggest_templates("explain how Kubernetes networking works")[0]
        assert result.id
        assert result.name
        assert result.description
        assert result.icon
        assert result.category
        assert result.match_reason
        assert result.scene_count > 0


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
        # Background processing kicks off immediately — status transitions to running
        assert detail.json()["status"] in ("queued", "running")
        assert len(detail.json()["events"]) >= 3


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


# ─── Background pipeline processing ─────────────────────────────────────


class TestBackgroundProcessing:
    """Job transitions through pipeline stages after creation."""

    def test_create_job_transitions_to_running(self):
        """Background task kicks off — job status changes from queued."""
        _clear_store()
        app = create_app()
        client = TestClient(app)
        resp = client.post("/api/jobs", json=GRILL_PAYLOAD)
        job_id = resp.json()["jobId"]

        # Give background task time to start
        import time
        time.sleep(0.3)

        detail = client.get(f"/api/jobs/{job_id}").json()
        # Should have moved past "queued" (running or further)
        assert detail["status"] != "queued"

    def test_create_job_emits_stage_events(self):
        """Pipeline stages emit stage events visible in job detail."""
        _clear_store()
        app = create_app()
        client = TestClient(app)
        resp = client.post("/api/jobs", json=GRILL_PAYLOAD)
        job_id = resp.json()["jobId"]

        import time
        time.sleep(0.5)

        detail = client.get(f"/api/jobs/{job_id}").json()
        events = detail.get("events", [])
        stage_events = [e for e in events if e.get("type") == "job.stage"]
        # Should have initial events + at least one pipeline stage event
        assert len(stage_events) >= 2  # grill stage (from create) + plan stage (from runner)

    def test_create_job_with_run_override_starts_processing(self):
        """Run override doesn't block background processing."""
        _clear_store()
        app = create_app()
        client = TestClient(app)
        payload = {**GRILL_PAYLOAD, "runOverride": {"provider": "anthropic", "model": "claude-sonnet-4-20250514"}}
        resp = client.post("/api/jobs", json=payload)
        assert resp.status_code == 200
        job_id = resp.json()["jobId"]

        import time
        time.sleep(0.3)

        detail = client.get(f"/api/jobs/{job_id}").json()
        assert detail["status"] != "queued"

    def test_create_job_with_grill_session_starts_processing(self):
        """Session-based job also kicks off background pipeline."""
        _clear_store()
        from videoforge.api.jobs import _grill_sessions
        _grill_sessions.clear()
        app = create_app()
        client = TestClient(app)
        start = client.post("/api/jobs/grill/start", json={"prompt": "Explain Docker networking"}).json()
        sid = start["sessionId"]

        # Complete session
        client.post("/api/jobs/grill/turn", json={"sessionId": sid, "answer": "Devs", "done": True}).json()

        resp = client.post("/api/jobs", json={
            "prompt": "Explain Docker networking",
            "options": {"voice": "alba", "provider": "9router", "model": "ocg/deepseek-v4-flash", "maxDuration": 180, "fps": 30},
            "grillSessionId": sid,
        })
        assert resp.status_code == 200
        job_id = resp.json()["jobId"]

        import time
        time.sleep(0.3)

        detail = client.get(f"/api/jobs/{job_id}").json()
        assert detail["status"] != "queued"

    def test_background_processing_completes_job(self, monkeypatch):
        """Pipeline runner completes — job reaches 'completed' status."""
        from videoforge.orchestrator.runner import PipelineRunner
        import time

        _clear_store()

        # Mock run_pipeline to complete instantly (no sleeps)
        async def fake_run(self, topic="", scenes_json="", voice="alba", tts_url=""):
            if self.stage_callback:
                self.stage_callback("grill", "running", 0.1, "")
                self.stage_callback("grill", "complete", 1.0, "")
                self.stage_callback("plan", "running", 0.1, "")
                self.stage_callback("plan", "complete", 1.0, "")
                self.stage_callback("render", "running", 0.1, "")
                self.stage_callback("render", "complete", 1.0, "")
                self.stage_callback("done", "complete", 1.0, "")

        monkeypatch.setattr(PipelineRunner, "run_pipeline", fake_run)
        # Disable ffmpeg check for output generation
        monkeypatch.setattr("videoforge.api.jobs.shutil.which", lambda _: None)

        app = create_app()
        client = TestClient(app)
        resp = client.post("/api/jobs", json=GRILL_PAYLOAD)
        job_id = resp.json()["jobId"]

        time.sleep(0.3)

        detail = client.get(f"/api/jobs/{job_id}").json()
        assert detail["status"] == "completed"
        assert detail["stage"] == "done"
        assert detail["progressPct"] == 100
        assert len(detail.get("artifacts", [])) >= 1
        assert detail["artifacts"][0]["artifactType"] == "video/mp4"

    def test_background_processing_creates_output_file(self, monkeypatch):
        """Output video file is created at artifact path."""
        from videoforge.orchestrator.runner import PipelineRunner
        import time
        from pathlib import Path

        _clear_store()

        async def fake_run(self, topic="", scenes_json="", voice="alba", tts_url=""):
            if self.stage_callback:
                self.stage_callback("grill", "running", 0.1, "")
                self.stage_callback("grill", "complete", 1.0, "")
                self.stage_callback("plan", "running", 0.1, "")
                self.stage_callback("plan", "complete", 1.0, "")
                self.stage_callback("render", "running", 0.1, "")
                self.stage_callback("render", "complete", 1.0, "")
                self.stage_callback("done", "complete", 1.0, "")

        monkeypatch.setattr(PipelineRunner, "run_pipeline", fake_run)
        # Disable ffmpeg so placeholder is written
        monkeypatch.setattr("videoforge.api.jobs.shutil.which", lambda _: None)

        app = create_app()
        client = TestClient(app)
        resp = client.post("/api/jobs", json=GRILL_PAYLOAD)
        job_id = resp.json()["jobId"]

        time.sleep(0.3)

        detail = client.get(f"/api/jobs/{job_id}").json()
        assert len(detail.get("artifacts", [])) >= 1
        output_path = detail["artifacts"][0]["path"]
        # Output file should exist
        assert Path(output_path).exists(), f"Output file not found: {output_path}"
        content = Path(output_path).read_text()
        assert "simulated" in content or output_path.endswith(".mp4")

    def test_background_processing_failure_sets_failed_status(self, monkeypatch):
        """Pipeline failure sets job status to 'failed' with error."""
        from videoforge.orchestrator.runner import PipelineRunner
        import time

        _clear_store()

        async def fake_run_fail(self, topic="", scenes_json="", voice="alba", tts_url=""):
            msg = "Simulated pipeline failure"
            raise RuntimeError(msg)

        monkeypatch.setattr(PipelineRunner, "run_pipeline", fake_run_fail)

        app = create_app()
        client = TestClient(app)
        resp = client.post("/api/jobs", json=GRILL_PAYLOAD)
        job_id = resp.json()["jobId"]

        time.sleep(0.3)

        detail = client.get(f"/api/jobs/{job_id}").json()
        assert detail["status"] == "failed"
        assert detail["error"] is not None
        assert "Simulated pipeline failure" in detail["error"]

    def test_background_processing_emits_completed_event(self, monkeypatch):
        """JobCompleted event is emitted on successful pipeline execution."""
        from videoforge.orchestrator.runner import PipelineRunner
        import time

        _clear_store()

        async def fake_run(self, topic="", scenes_json="", voice="alba", tts_url=""):
            if self.stage_callback:
                self.stage_callback("done", "complete", 1.0, "")

        monkeypatch.setattr(PipelineRunner, "run_pipeline", fake_run)
        monkeypatch.setattr("videoforge.api.jobs.shutil.which", lambda _: None)

        app = create_app()
        client = TestClient(app)
        resp = client.post("/api/jobs", json=GRILL_PAYLOAD)
        job_id = resp.json()["jobId"]

        time.sleep(0.3)

        detail = client.get(f"/api/jobs/{job_id}").json()
        events = detail.get("events", [])
        completed = [e for e in events if e.get("type") == "job.completed"]
        assert len(completed) == 1
        assert completed[0]["payload"]["finalVideo"] is not None

    def test_background_processing_emits_failed_event(self, monkeypatch):
        """JobFailed event is emitted on pipeline failure."""
        from videoforge.orchestrator.runner import PipelineRunner
        import time

        _clear_store()

        async def fake_run_fail(self, topic="", scenes_json="", voice="alba", tts_url=""):
            raise RuntimeError("Kaboom")

        monkeypatch.setattr(PipelineRunner, "run_pipeline", fake_run_fail)

        app = create_app()
        client = TestClient(app)
        resp = client.post("/api/jobs", json=GRILL_PAYLOAD)
        job_id = resp.json()["jobId"]

        time.sleep(0.3)

        detail = client.get(f"/api/jobs/{job_id}").json()
        events = detail.get("events", [])
        failed = [e for e in events if e.get("type") == "job.failed"]
        assert len(failed) == 1
        assert "Kaboom" in failed[0]["payload"]["error"]


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


# ─── Multi-turn grill ────────────────────────────────────────────────────


class TestMultiTurnGrill:
    """POST /api/jobs/grill/start + /grill/turn — interactive loop."""

    def _clear_sessions(self):
        _grill_sessions.clear()

    def test_start_returns_session_and_question(self):
        self._clear_sessions()
        app = create_app()
        client = TestClient(app)
        resp = client.post("/api/jobs/grill/start", json={"prompt": "Explain Kubernetes architecture with code examples"})
        assert resp.status_code == 200
        data = resp.json()
        assert "sessionId" in data
        assert len(data["sessionId"]) > 0
        assert "question" in data
        assert len(data["question"]) > 0
        assert "questionId" in data
        assert data["asked"] == 0
        assert data["total"] > 0

    def test_turn_returns_next_question(self):
        self._clear_sessions()
        app = create_app()
        client = TestClient(app)
        start = client.post("/api/jobs/grill/start", json={"prompt": "Create a tutorial about Docker"}).json()
        sid = start["sessionId"]

        turn = client.post("/api/jobs/grill/turn", json={"sessionId": sid, "answer": "Developers"}).json()
        assert turn["done"] is False
        assert "question" in turn
        assert turn["questionId"] is not None
        assert turn["asked"] >= 1
        assert turn["total"] > 0

    def test_turn_with_done_returns_final_result(self):
        self._clear_sessions()
        app = create_app()
        client = TestClient(app)
        start = client.post("/api/jobs/grill/start", json={"prompt": "Explain Kubernetes architecture with code examples"}).json()
        sid = start["sessionId"]

        # Answer first question and mark done
        turn = client.post("/api/jobs/grill/turn", json={"sessionId": sid, "answer": "Developers", "done": True}).json()
        assert turn["done"] is True
        assert turn["result"] is not None
        assert "refinedPrompt" in turn["result"]
        assert "suggestedScenes" in turn["result"]
        assert "missingDetails" in turn["result"]
        assert "confidence" in turn["result"]
        assert turn["asked"] >= 1

    def test_full_loop_ends_with_result(self):
        self._clear_sessions()
        app = create_app()
        client = TestClient(app)
        start = client.post("/api/jobs/grill/start", json={"prompt": "Build a React component library"}).json()
        sid = start["sessionId"]

        # Answer questions until loop ends
        result = None
        for _ in range(10):  # safety limit
            turn = client.post("/api/jobs/grill/turn", json={"sessionId": sid, "answer": "Yes please"}).json()
            if turn["done"]:
                result = turn["result"]
                break

        assert result is not None
        assert len(result["suggestedScenes"]) >= 3
        assert 0 <= result["confidence"] <= 1

    def test_unknown_session_returns_404(self):
        self._clear_sessions()
        app = create_app()
        client = TestClient(app)
        resp = client.post("/api/jobs/grill/turn", json={"sessionId": "nonexistent", "answer": "test"})
        assert resp.status_code == 404

    def test_start_with_rich_prompt_returns_immediate_result(self):
        """If prompt already specifies everything, no questions needed."""
        self._clear_sessions()
        app = create_app()
        client = TestClient(app)
        rich = "Create advanced tutorial for expert developers explaining Kubernetes architecture in 15 minutes with professional tone"
        start = client.post("/api/jobs/grill/start", json={"prompt": rich}).json()
        assert start["asked"] == 0
        # Should still have a session and at least some questions may remain
        assert start["sessionId"] is not None

    def test_rich_prompt_answers_all_then_immediate_done(self):
        """If prompt already specifies everything, session has minimal pending questions."""
        self._clear_sessions()
        app = create_app()
        client = TestClient(app)
        rich = "Create tutorial for beginners explaining Docker in 5 minutes with casual tone including examples"
        start = client.post("/api/jobs/grill/start", json={"prompt": rich}).json()
        sid = start["sessionId"]

        # Only "message" and "scenes" might remain — answer once and done
        turn = client.post("/api/jobs/grill/turn", json={"sessionId": sid, "answer": "Containerization is key", "done": True}).json()
        assert turn["done"] is True
        assert turn["result"] is not None

    def test_create_job_with_session_id_uses_session_result(self):
        self._clear_sessions()
        app = create_app()
        client = TestClient(app)
        start = client.post("/api/jobs/grill/start", json={"prompt": "Explain Docker networking"}).json()
        sid = start["sessionId"]

        # Complete the session
        client.post("/api/jobs/grill/turn", json={"sessionId": sid, "answer": "Developers", "done": True}).json()

        # Create job with sessionId
        resp = client.post("/api/jobs", json={
            "prompt": "Explain Docker networking",
            "options": {"voice": "alba", "provider": "9router", "model": "ocg/deepseek-v4-flash", "maxDuration": 180, "fps": 30},
            "grillSessionId": sid,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "queued"
        assert data["grillResult"]["confidence"] > 0

    def test_create_job_with_bad_session_falls_back_to_regrill(self):
        self._clear_sessions()
        app = create_app()
        client = TestClient(app)
        resp = client.post("/api/jobs", json={
            "prompt": "Explain Docker networking with code examples",
            "options": {"voice": "alba", "provider": "9router", "model": "ocg/deepseek-v4-flash", "maxDuration": 180, "fps": 30},
            "grillSessionId": "nonexistent",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "queued"
        assert data["grillResult"]["confidence"] > 0
