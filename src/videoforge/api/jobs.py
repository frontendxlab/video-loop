"""Jobs API — grill prompt + create + detail endpoints.

``POST /api/jobs/grill`` — deterministic prompt refinement.
``POST /api/jobs`` — create job, emit events, return job ID.
``GET /api/jobs`` — list all jobs.
``GET /api/jobs/{job_id}`` — job detail snapshot (stages, scenes, subagents, artifacts).
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from videoforge.engine.templates import suggest_templates as _suggest_templates_from_registry
from videoforge.api.adapters import EventFeed
from videoforge.api.events import (
    ArtifactReady,
    DirectorScenePlanned,
    DirectorSceneRouted,
    JobCompleted,
    JobFailed,
    JobStage,
    JobStarted,
    JobTodo,
    PromptGrilled,
    RenderSceneCompleted,
    RenderSceneStarted,
    RepairPlan,
    RetryStarted,
    ReviewIssue,
    SubagentCompleted,
    SubagentFailed,
    SubagentStarted,
    SubagentToken,
    serialize_event,
)
from videoforge.api.sse import get_feed

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

# ─── Request / Response schemas ───────────────────────────────────────────


class CreateOptions(BaseModel):
    voice: str = "alba"
    provider: str = "9router"
    model: str = "ocg/deepseek-v4-flash"
    maxDuration: int = 180
    fps: int = 30


class RunOverride(BaseModel):
    """Per-run provider/model overrides — optional, applied at job start.

    Mirrors frontend RunOverrideSchema. Allows operator to override
    the default provider/model for a specific job without changing
    persisted settings.
    """
    provider: str | None = None
    model: str | None = None
    temperature: float = 0.7
    maxTokens: int = 4096


class GrillRequest(BaseModel):
    prompt: str = Field(..., min_length=10)
    options: CreateOptions = Field(default_factory=CreateOptions)


class SceneSuggestion(BaseModel):
    kind: str
    title: str
    description: str
    reasoning: str


class SuggestedTemplate(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    category: str
    match_reason: str
    scene_count: int


class GrillResult(BaseModel):
    refinedPrompt: str
    suggestedScenes: list[SceneSuggestion]
    suggestedTemplates: list[SuggestedTemplate] = []
    missingDetails: list[str]
    confidence: float = Field(..., ge=0, le=1)


class CreateJobRequest(BaseModel):
    prompt: str = Field(..., min_length=10)
    options: CreateOptions = Field(default_factory=CreateOptions)
    runOverride: RunOverride | None = None
    grillSessionId: str | None = None  # Use multi-turn session result instead of re-grilling


class CreateJobResponse(BaseModel):
    jobId: str
    status: Literal["queued", "running"] = "queued"
    grillResult: GrillResult


# ─── Multi-turn grill schemas ────────────────────────────────────────────


class GrillStartRequest(BaseModel):
    prompt: str = Field(..., min_length=10)
    options: CreateOptions = Field(default_factory=CreateOptions)


class GrillStartResponse(BaseModel):
    sessionId: str
    question: str
    questionId: str
    asked: int
    total: int


class GrillTurnRequest(BaseModel):
    sessionId: str
    answer: str = Field(..., min_length=1)
    done: bool = False


class GrillTurnResponse(BaseModel):
    question: str | None = None
    questionId: str | None = None
    asked: int = 0
    total: int = 0
    done: bool = False
    result: GrillResult | None = None


# ─── Job detail schemas ──────────────────────────────────────────────────


class SubagentDetail(BaseModel):
    id: str
    name: str
    engine: str
    task: str
    status: str  # pending, running, completed, failed
    startedAt: str | None = None
    completedAt: str | None = None
    durationMs: float | None = None
    error: str | None = None
    tokens: int = 0


class SceneDetail(BaseModel):
    id: str
    kind: str
    engine: str
    status: str  # pending, rendering, completed, failed
    reviewIssues: int = 0
    retryCount: int = 0
    # Artifact availability — populated from disk when job detail is fetched
    hasThumbnail: bool = False
    hasFrame: bool = False
    hasReport: bool = False
    thumbnailUrl: str | None = None
    frameUrl: str | None = None
    reportUrl: str | None = None


class ArtifactRef(BaseModel):
    artifactType: str
    path: str
    sceneId: str | None = None


class JobDetailResponse(BaseModel):
    id: str
    title: str
    status: str  # queued, running, completed, failed, cancelled
    stage: str
    progressPct: int = 0
    createdAt: str  # ISO-8601
    startedAt: str | None = None
    completedAt: str | None = None
    error: str | None = None
    provider: str = "9router"
    model: str = "ocg/deepseek-v4-flash"
    runOverride: dict[str, Any] | None = None
    subagents: list[SubagentDetail] = []
    scenes: list[SceneDetail] = []
    artifacts: list[ArtifactRef] = []
    events: list[dict[str, Any]] = []


# ─── Job store (in-memory) ───────────────────────────────────────────────


_job_store: dict[str, dict[str, Any]] = {}


def store_job(job_id: str, data: dict[str, Any]) -> None:
    _job_store[job_id] = data


def get_job(job_id: str) -> dict[str, Any] | None:
    return _job_store.get(job_id)


def list_jobs() -> list[dict[str, Any]]:
    return list(_job_store.values())


# ─── Deterministic griller ────────────────────────────────────────────────

_SCENE_TEMPLATES: dict[str, tuple[str, str, str]] = {
    "title": ("Title", "Opening title card with topic", "Establishes video topic"),
    "bullets": ("Key Concepts", "Core ideas explained with bullet points", "Break down topic into digestible points"),
    "code": ("Code Example", "Live code walkthrough with syntax highlights", "Visual code explanation reinforces learning"),
    "diagram": ("Architecture Diagram", "System architecture or flow diagram", "Visual understanding through diagrams"),
    "comparison": ("Comparison", "Side-by-side comparison of concepts", "Highlight differences clearly"),
    "chart": ("Data Chart", "Chart showing relevant metrics or data", "Data visualization aids comprehension"),
    "quote": ("Key Quote", "Notable quote or takeaway", "Emphasize important insight"),
    "diff": ("Changes Overview", "Before/after or diff visualization", "Show transformation clearly"),
    "callout": ("Callout", "Important note or warning callout", "Draw attention to critical detail"),
    "outro": ("Summary", "Recap and next steps", "Provide closing summary"),
}


def _extract_keywords(prompt: str) -> set[str]:
    """Extract meaningful keywords from prompt."""
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "has", "have", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "can", "shall", "to", "of",
        "in", "for", "on", "with", "at", "by", "from", "as", "into",
        "through", "during", "before", "after", "above", "below",
        "between", "and", "or", "but", "nor", "not", "so", "yet",
        "this", "that", "these", "those", "it", "its", "how", "what",
        "why", "when", "where", "which", "who", "whom", "create",
        "make", "video", "about", "explain", "show", "demonstrate",
        "build", "using", "use", "need", "want", "please", "like",
    }
    tokens = re.findall(r"[a-zA-Z]\w+", prompt.lower())
    return {t for t in tokens if t not in stop_words and len(t) > 2}


def _prompt_hash(prompt: str) -> int:
    """Deterministic hash of prompt for seeded choices."""
    return int(hashlib.sha256(prompt.encode()).hexdigest()[:8], 16)


def _suggest_scenes(keywords: set[str], prompt: str) -> list[SceneSuggestion]:
    """Suggest scenes based on prompt keywords (deterministic)."""
    h = _prompt_hash(prompt)
    kw_lower = {k.lower() for k in keywords}

    # Determine which scene kinds to include
    kinds: list[str] = ["title"]

    code_triggers = {"code", "function", "api", "syntax", "programming", "script", "implement", "source", "language", "python", "javascript", "typescript", "rust", "golang"}
    if kw_lower & code_triggers:
        kinds.append("code")

    diagram_triggers = {"architecture", "diagram", "flow", "system", "design", "structure", "component", "layer", "network", "pipeline"}
    if kw_lower & diagram_triggers:
        kinds.append("diagram")

    comparison_triggers = {"compare", "comparison", "vs", "versus", "difference", "migration", "upgrade", "transition"}
    if kw_lower & comparison_triggers:
        kinds.append("comparison")

    chart_triggers = {"data", "chart", "metric", "statistics", "analytics", "benchmark", "performance", "growth", "trend"}
    if kw_lower & chart_triggers:
        kinds.append("chart")

    callout_triggers = {"warning", "important", "critical", "security", "danger", "caution", "gotcha", "pitfall"}
    if kw_lower & callout_triggers:
        kinds.append("callout")

    quote_triggers = {"quote", "expert", "opinion", "perspective"}
    if kw_lower & quote_triggers:
        kinds.append("quote")

    diff_triggers = {"diff", "change", "before", "after", "upgrade", "migration", "version", "update", "refactor"}
    if kw_lower & diff_triggers:
        kinds.append("diff")

    # Always add bullets and outro for structure
    if len(kinds) > 1 and "code" not in kinds[1:] and "diagram" not in kinds[1:]:
        kinds.append("bullets")
    elif len(kinds) < 3:
        kinds.append("bullets")
        if len(kinds) < 3:
            kinds.append("diagram")
    kinds.append("outro")

    scenes: list[SceneSuggestion] = []
    for i, kind in enumerate(kinds):
        template = _SCENE_TEMPLATES.get(kind, _SCENE_TEMPLATES["bullets"])
        title_suffix = f" — Scene {i+1}" if i > 0 else ""
        scene = SceneSuggestion(
            kind=kind,
            title=f"{template[0]}{title_suffix}",
            description=template[1],
            reasoning=template[2],
        )
        scenes.append(scene)

    return scenes


def _refine_prompt(prompt: str, scenes: list[SceneSuggestion]) -> str:
    """Build a refined, structured version of the prompt."""
    scene_descriptions = [f"{i+1}. {s.kind.title()}: {s.description}" for i, s in enumerate(scenes)]
    scenes_text = "\n".join(scene_descriptions)
    return (
        f"Create a detailed technical video about: {prompt.strip()}.\n\n"
        f"Suggested structure:\n{scenes_text}\n\n"
        "Include clear explanations, relevant visual aids, and a thorough walkthrough."
    )


def _missing_details(prompt: str) -> list[str]:
    """Identify missing details in prompt (deterministic heuristic)."""
    details: list[str] = []
    prompt_lower = prompt.lower()

    if not any(w in prompt_lower for w in ("target", "audience", "beginner", "intermediate", "advanced", "expert", "for")):
        details.append("Target audience not specified")

    if not any(w in prompt_lower for w in ("minute", "minutes", "min", "short", "long", "duration", "length")):
        details.append("Video duration not specified — using default 3 minutes")

    if not any(w in prompt_lower for w in ("style", "tone", "formal", "casual", "professional", "playful", "serious")):
        details.append("Presentation style not specified — defaulting to professional")

    if len(prompt.split()) < 20:
        details.append("Consider adding more detail for richer scene planning")

    # Use hash to make deterministic but varied
    h = _prompt_hash(prompt)
    if len(details) >= 2 and h % 3 == 0:
        details.append("Difficulty level not specified")

    return details


def _calc_confidence(prompt: str, keywords: set[str]) -> float:
    """Calculate confidence score (0-1) for grill result."""
    word_count = len(prompt.split())
    kw_count = len(keywords)

    # Base from word count
    word_score = min(1.0, word_count / 50)

    # Keyword diversity
    kw_score = min(1.0, kw_count / 12)

    # Scene coverage bonus
    coverage_bonus = 0.1 if any(w in prompt.lower() for w in ("example", "show", "walk", "step")) else 0.0

    raw = 0.4 + 0.3 * word_score + 0.2 * kw_score + coverage_bonus
    return round(min(1.0, raw), 2)


def _suggest_templates(prompt: str) -> list[SuggestedTemplate]:
    """Suggest video templates based on prompt keywords."""
    raw = _suggest_templates_from_registry(prompt, max_suggestions=3)
    return [SuggestedTemplate(**t) for t in raw]


def grill_prompt(prompt: str, options: CreateOptions | None = None) -> GrillResult:
    """Deterministic prompt grilling — no LLM, pure heuristics."""
    keywords = _extract_keywords(prompt)
    scenes = _suggest_scenes(keywords, prompt)
    templates = _suggest_templates(prompt)
    refined = _refine_prompt(prompt, scenes)
    missing = _missing_details(prompt)
    confidence = _calc_confidence(prompt, keywords)

    return GrillResult(
        refinedPrompt=refined,
        suggestedScenes=scenes,
        suggestedTemplates=templates,
        missingDetails=missing,
        confidence=confidence,
    )


# ─── Multi-turn interactive griller ───────────────────────────────────────

_GRILL_QUESTIONS: list[tuple[str, str, str]] = [
    ("audience", "Who is the target audience? (beginner, intermediate, advanced, or mixed)", "Know audience → tailor depth & examples"),
    ("duration", "What duration do you want? (e.g. 2-3 min quick explainer, 5-10 min deep dive)", "Right length keeps engagement high"),
    ("style", "What style / tone? (professional, casual, humorous, educational, dramatic)", "Tone sets the emotional frame"),
    ("message", "What is the key message or call to action?", "Sharp message drives retention"),
    ("examples", "Include specific examples or demos? (yes / no — if yes, describe)", "Examples make abstract concrete"),
    ("scenes", "Any specific scene types you want? (code, diagrams, comparisons, charts)", "Scene mix shapes visual pacing"),
]


def _which_questions_to_ask(prompt: str, existing_answers: dict[str, str]) -> list[tuple[str, str, str]]:
    """Return list of (id, question, reasoning) still relevant given prompt + existing answers."""
    prompt_lower = prompt.lower()
    all_text = prompt_lower + " " + " ".join(v.lower() for v in existing_answers.values())

    # If already answered or clearly specified in prompt, skip
    skip: set[str] = set()
    if any(w in all_text for w in ("beginner", "intermediate", "advanced", "expert", "audience", "for ", "target")):
        skip.add("audience")
    if any(w in all_text for w in ("minute", "minutes", "min", "duration", "length", "second", "seconds", "long")):
        skip.add("duration")
    if any(w in all_text for w in ("style", "tone", "formal", "casual", "professional", "playful", "serious", "humor", "fun", "dramatic", "educational")):
        skip.add("style")
    if any(w in all_text for w in ("message", "call to action", "takeaway", "key point", "goal", "purpose")):
        skip.add("message")
    if any(w in all_text for w in ("example", "demo", "walkthrough", "sample", "case study")):
        skip.add("examples")
    if any(w in all_text for w in ("code scene", "diagram", "comparison", "chart", "scene", "shot")):
        skip.add("scenes")

    return [(qid, question, reason) for qid, question, reason in _GRILL_QUESTIONS if qid not in skip]


class _GrillSession:
    """Holds state for one multi-turn grill conversation."""

    def __init__(self, prompt: str, options: CreateOptions) -> None:
        self.prompt = prompt
        self.options = options
        self.answers: dict[str, str] = {}
        self.pending: list[tuple[str, str, str]] = _which_questions_to_ask(prompt, {})
        self.asked: list[str] = []

    @property
    def total(self) -> int:
        return len(_GRILL_QUESTIONS)  # max possible

    @property
    def asked_count(self) -> int:
        return len(self.asked)

    def current_question(self) -> tuple[str, str, str] | None:
        if not self.pending:
            return None
        return self.pending[0]

    def record_answer(self, answer: str) -> None:
        if not self.pending:
            return
        qid, question, reason = self.pending.pop(0)
        self.answers[qid] = answer
        self.asked.append(qid)

    def build_final_result(self) -> GrillResult:
        """Build enriched prompt from original + answers, then run griller."""
        enriched = self.prompt
        for qid, answer in self.answers.items():
            if answer.strip():
                enriched += f" {answer.strip()}"
        return grill_prompt(enriched, self.options)


_grill_sessions: dict[str, _GrillSession] = {}


# ─── Artifact enrichment helpers ──────────────────────────────────────────


def _enrich_scene_artifacts(
    job_id: str,
    scenes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Enrich scene dicts with artifact availability flags and URLs from disk.

    Scans ``{ARTIFACTS_DIR}/{job_id}/thumbnails|frames|reports/``
    for known scene IDs. Non-destructive — preserves all existing keys.
    Returns empty list unchanged (no scene metadata yet).
    """
    from videoforge.api.artifacts import ARTIFACTS_DIR, _SAFE_NAME  # noqa: PLC0415

    if not scenes:
        return scenes

    job_dir = ARTIFACTS_DIR / job_id
    if not job_dir.is_dir():
        return scenes

    thumb_dir = job_dir / "thumbnails"
    frame_dir = job_dir / "frames"
    report_dir = job_dir / "reports"
    IMG_EXTS = (".jpg", ".jpeg", ".png", ".webp")
    prefix = f"/api/artifacts/{job_id}/scenes"

    enriched = []
    for scene in scenes:
        sid = scene.get("id", "")
        if not _SAFE_NAME.match(sid):
            enriched.append(scene)
            continue

        def _find(directory):
            if not directory.is_dir():
                return None
            for ext in IMG_EXTS:
                p = directory / f"{sid}{ext}"
                if p.is_file():
                    return p
            return None

        thumb_path = _find(thumb_dir)
        frame_path = _find(frame_dir)
        report_path = (report_dir / f"{sid}.json") if report_dir.is_dir() else None
        has_rep = report_path is not None and report_path.is_file()

        enriched.append({
            **scene,
            "hasThumbnail": thumb_path is not None,
            "hasFrame": frame_path is not None,
            "hasReport": has_rep,
            "thumbnailUrl": f"{prefix}/{sid}/thumbnail" if thumb_path else None,
            "frameUrl": f"{prefix}/{sid}/frame" if frame_path else None,
            "reportUrl": f"{prefix}/{sid}/report" if has_rep else None,
        })

    return enriched


# ─── Routes ────────────────────────────────────────────────────────────────


@router.post("/grill")
async def grill_endpoint(req: GrillRequest) -> GrillResult:
    """Grill a prompt — deterministic refinement, no LLM."""
    return grill_prompt(req.prompt, req.options)


@router.post("/grill/start")
async def grill_start_endpoint(req: GrillStartRequest) -> GrillStartResponse:
    """Start multi-turn grill — returns first question."""
    session = _GrillSession(req.prompt, req.options)
    sid = uuid.uuid4().hex[:16]
    _grill_sessions[sid] = session

    current = session.current_question()
    if current is None:
        # No questions needed — return result directly
        result = session.build_final_result()
        return GrillStartResponse(
            sessionId=sid,
            question="",
            questionId="",
            asked=0,
            total=session.total,
        )

    qid, question, _reason = current
    return GrillStartResponse(
        sessionId=sid,
        question=question,
        questionId=qid,
        asked=0,
        total=session.total,
    )


@router.post("/grill/turn")
async def grill_turn_endpoint(req: GrillTurnRequest) -> GrillTurnResponse:
    """Submit answer, get next question or final result."""
    session = _grill_sessions.get(req.sessionId)
    if session is None:
        raise HTTPException(status_code=404, detail="Grill session not found")

    session.record_answer(req.answer)

    # If user says done or no more questions, return final result
    if req.done or session.current_question() is None:
        final = session.build_final_result()
        # Clean up session
        _grill_sessions.pop(req.sessionId, None)
        return GrillTurnResponse(
            done=True,
            result=final,
            asked=session.asked_count,
            total=session.total,
        )

    qid, question, _reason = session.current_question()
    return GrillTurnResponse(
        question=question,
        questionId=qid,
        asked=session.asked_count,
        total=session.total,
        done=False,
    )


@router.post("")
async def create_job(
    req: CreateJobRequest,
    feed: EventFeed = Depends(get_feed),
) -> CreateJobResponse:
    """Create a new job: grill prompt, emit events, store job detail."""
    if req.grillSessionId:
        # Restore session to get final result
        session = _grill_sessions.pop(req.grillSessionId, None)
        if session:
            result = session.build_final_result()
        else:
            result = grill_prompt(req.prompt, req.options)
    else:
        result = grill_prompt(req.prompt, req.options)

    # Resolve effective provider/model — runOverride wins over options defaults
    ro = req.runOverride
    effective_provider = ro.provider if (ro and ro.provider) else req.options.provider
    effective_model = ro.model if (ro and ro.model) else req.options.model

    job_id = f"job_{uuid.uuid4().hex[:12]}"

    # Emit job.started event
    started = JobStarted(
        jobId=job_id,
        payload={
            "title": req.prompt[:60],
            "prompt": req.prompt,
            "options": req.options.model_dump(),
            "runOverride": ro.model_dump() if ro else None,
            "effectiveProvider": effective_provider,
            "effectiveModel": effective_model,
            "grillResult": result.model_dump(),
        },
    )
    await feed.append(started)

    # Emit job.stage — grilling complete
    stage = JobStage(
        jobId=job_id,
        payload={
            "stage": "grill",
            "progressPct": 10,
            "phase": "grill",
        },
    )
    await feed.append(stage)

    # Emit prompt.grilled event
    grilled_event = PromptGrilled(
        jobId=job_id,
        payload={
            "refinedPrompt": result.refinedPrompt,
            "sceneCount": len(result.suggestedScenes),
            "confidence": result.confidence,
        },
    )
    await feed.append(grilled_event)

    # Store job detail snapshot
    now_iso = datetime.utcnow().isoformat()
    title = req.prompt[:60] + ("..." if len(req.prompt) > 60 else "")
    store_job(job_id, {
        "id": job_id,
        "title": title,
        "status": "queued",
        "stage": "grill",
        "progressPct": 10,
        "createdAt": now_iso,
        "startedAt": None,
        "completedAt": None,
        "error": None,
        "provider": effective_provider,
        "model": effective_model,
        "runOverride": ro.model_dump() if ro else None,
        "subagents": [],
        "scenes": [],
        "artifacts": [],
        "events": [
            _event_as_dict(started),
            _event_as_dict(stage),
            _event_as_dict(grilled_event),
        ],
    })

    # Kick off background pipeline processing
    asyncio.create_task(_process_job_background(job_id, feed))

    return CreateJobResponse(
        jobId=job_id,
        status="queued",
        grillResult=result,
    )


# ─── GET endpoints ─────────────────────────────────────────────────────────


@router.get("")
async def list_jobs_endpoint() -> list[JobDetailResponse]:
    """List all jobs (summary)."""
    return [JobDetailResponse(**j) for j in list_jobs()]


@router.get("/{job_id}")
async def get_job_endpoint(job_id: str) -> JobDetailResponse:
    """Get full job detail snapshot: stages, scenes, subagents, artifacts.

    Scene artifacts (thumbnail/frame/report flags + URLs) are enriched
    from disk at request time — available regardless of job status.
    """
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    # Enrich scene artifacts from disk (always, even for failed/in-progress)
    job = {**job, "scenes": _enrich_scene_artifacts(job_id, job.get("scenes", []))}
    return JobDetailResponse(**job)


# ─── Helpers ──────────────────────────────────────────────────────────────


def _event_as_dict(event: Any) -> dict[str, Any]:
    """Serialize a JobEvent to a plain dict for storage."""
    return event.model_dump()


# ─── Background pipeline processing ──────────────────────────────────────────


def _make_stage_callback(
    job_id: str,
    feed: EventFeed,
    job: dict[str, Any],
) -> Callable[[str, str, float, str], None]:
    """Create callback that emits events + updates job store on stage transitions."""

    def callback(stage_name: str, status: str, progress: float, message: str) -> None:
        if status in ("running", "complete", "failed"):
            pct = int(progress * 100)
            ev = JobStage(
                jobId=job_id,
                payload={"stage": stage_name, "progressPct": pct, "phase": stage_name},
            )
            asyncio.create_task(feed.append(ev))
            job["stage"] = stage_name
            job["progressPct"] = pct
            job.setdefault("events", []).append(_event_as_dict(ev))

    return callback


async def _process_job_background(job_id: str, feed: EventFeed) -> None:
    """Background task: run pipeline, emit events, update store, produce output."""
    from videoforge.orchestrator.runner import PipelineRunner  # noqa: PLC0415

    job = get_job(job_id)
    if not job:
        return

    now_iso = datetime.utcnow().isoformat()
    job["status"] = "running"
    job["startedAt"] = now_iso

    # Emit initial stage event
    stage_ev = JobStage(
        jobId=job_id,
        payload={"stage": "plan", "progressPct": 5, "phase": "plan"},
    )
    await feed.append(stage_ev)
    job["events"].append(_event_as_dict(stage_ev))

    try:
        # Extract prompt from job start event
        prompt = ""
        for ev in job.get("events", []):
            if isinstance(ev, dict) and ev.get("type") == "job.started":
                prompt = ev.get("payload", {}).get("prompt", "")
                break

        from pathlib import Path as _Path

        topic = prompt[:80] if prompt else "Video generation"
        output_dir = _Path(f"/tmp/videoforge/{job_id}")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(output_dir / "final.mp4")

        runner = PipelineRunner(
            stage_callback=_make_stage_callback(job_id, feed, job),
        )

        final_path = await runner.run_pipeline(
            topic=topic,
            scenes_json="",
            voice=job.get("provider", "alba"),
            tts_url=os.environ.get("TTS_URL", "http://localhost:8001"),
            output_path=output_path,
            remotion_dir="remotion-project",
        )

        # Mark completed
        completed_ev = JobCompleted(
            jobId=job_id,
            payload={"finalVideo": final_path, "duration": 30, "artifactCount": 1},
        )
        await feed.append(completed_ev)
        job["events"].append(_event_as_dict(completed_ev))
        job["status"] = "completed"
        job["stage"] = "done"
        job["progressPct"] = 100
        job["completedAt"] = datetime.utcnow().isoformat()
        job.setdefault("artifacts", []).append({
            "artifactType": "video/mp4",
            "path": final_path,
            "sceneId": None,
        })

    except Exception as exc:
        import traceback  # noqa: PLC0415
        traceback.print_exc()
        failed_ev = JobFailed(
            jobId=job_id,
            payload={
                "error": str(exc),
                "stage": job.get("stage", "unknown"),
                "retryCount": 0,
            },
        )
        await feed.append(failed_ev)
        job["events"].append(_event_as_dict(failed_ev))
        job["status"] = "failed"
        job["error"] = str(exc)
        job["completedAt"] = datetime.utcnow().isoformat()


# ─── Seed ────────────────────────────────────────────────────────────────────


def _ts(ago_seconds: int) -> str:
    """Return ISO-8601 timestamp *ago_seconds* before now."""
    return (datetime.utcnow() - timedelta(seconds=ago_seconds)).isoformat()


def seed_jobs() -> None:
    """Seed mock job data for development and testing."""
    if _job_store:
        return  # already seeded

    import json

    def ev(event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Build a serialized JobEvent dict matching SSE wire format."""
        return {
            "id": f"evt_{uuid.uuid4().hex[:12]}",
            "type": event_type,
            "jobId": event_type,  # placeholder, overridden per job
            "timestamp": (datetime.utcnow() - timedelta(seconds=120)).timestamp(),
            "payload": payload,
        }

    def make_seed_events(job_id: str, events_def: list[tuple[str, dict[str, Any]]]) -> list[dict[str, Any]]:
        result = []
        for i, (etype, payload) in enumerate(events_def):
            result.append({
                "id": f"evt_{uuid.uuid4().hex[:12]}",
                "type": etype,
                "jobId": job_id,
                "timestamp": (datetime.utcnow() - timedelta(seconds=120 - i * 5)).timestamp(),
                "payload": payload,
            })
        return result

    jobs_data = [
        {
            "id": "job_001",
            "title": "PR #142 — Add auth middleware",
            "status": "running",
            "stage": "render",
            "progressPct": 62,
            "createdAt": _ts(120),
            "startedAt": _ts(115),
            "completedAt": None,
            "error": None,
            "subagents": [
                {"id": "sa_1", "name": "Scene Planner", "engine": "director", "task": "Plan scene graph", "status": "completed", "startedAt": _ts(110), "completedAt": _ts(105), "durationMs": 5000, "error": None, "tokens": 340},
                {"id": "sa_2", "name": "Code Highlighter", "engine": "remotion", "task": "Syntax highlight CodeScene", "status": "completed", "startedAt": _ts(100), "completedAt": _ts(92), "durationMs": 8000, "error": None, "tokens": 0},
                {"id": "sa_3", "name": "Diff Renderer", "engine": "remotion", "task": "Render diff scene #3", "status": "running", "startedAt": _ts(80), "completedAt": None, "durationMs": None, "error": None, "tokens": 520},
                {"id": "sa_4", "name": "Review Gate L0", "engine": "review", "task": "Check mixed-engine coherence", "status": "pending", "startedAt": None, "completedAt": None, "durationMs": None, "error": None, "tokens": 0},
            ],
            "scenes": [
                {"id": "scene_1", "kind": "title", "engine": "remotion", "status": "completed", "reviewIssues": 0, "retryCount": 0},
                {"id": "scene_2", "kind": "code", "engine": "remotion", "status": "completed", "reviewIssues": 0, "retryCount": 0},
                {"id": "scene_3", "kind": "diff", "engine": "remotion", "status": "rendering", "reviewIssues": 1, "retryCount": 0},
                {"id": "scene_4", "kind": "bullets", "engine": "remotion", "status": "pending", "reviewIssues": 0, "retryCount": 0},
            ],
            "artifacts": [],
            "events": make_seed_events("job_001", [
                ("job.started", {"title": "PR #142 — Add auth middleware"}),
                ("job.stage", {"stage": "plan", "progressPct": 5, "phase": "plan"}),
                ("director.scene_planned", {"sceneId": "scene_1", "sceneKind": "title"}),
                ("director.scene_routed", {"sceneId": "scene_1", "sceneKind": "title", "engine": "remotion"}),
                ("job.stage", {"stage": "render", "progressPct": 45, "phase": "render"}),
                ("render.scene_started", {"sceneId": "scene_3", "sceneKind": "diff"}),
                ("subagent.started", {"subagentId": "sa_3", "name": "Diff Renderer", "engine": "remotion", "task": "Render diff scene #3"}),
            ]),
        },
        {
            "id": "job_002",
            "title": "Issue #89 — Fix caption sync drift",
            "status": "queued",
            "stage": "plan",
            "progressPct": 0,
            "createdAt": _ts(30),
            "startedAt": None,
            "completedAt": None,
            "error": None,
            "subagents": [],
            "scenes": [],
            "artifacts": [],
            "events": [],
        },
        {
            "id": "job_003",
            "title": "Release v0.5 — Demo video",
            "status": "completed",
            "stage": "done",
            "progressPct": 100,
            "createdAt": _ts(600),
            "startedAt": _ts(590),
            "completedAt": _ts(300),
            "error": None,
            "subagents": [
                {"id": "sa_5", "name": "Scene Planner", "engine": "director", "task": "Plan scene graph", "status": "completed", "startedAt": _ts(580), "completedAt": _ts(575), "durationMs": 5000, "error": None, "tokens": 420},
                {"id": "sa_6", "name": "TTS Engine", "engine": "tts", "task": "Generate narration", "status": "completed", "startedAt": _ts(570), "completedAt": _ts(540), "durationMs": 30000, "error": None, "tokens": 0},
                {"id": "sa_7", "name": "Compositor", "engine": "remotion", "task": "Render all scenes", "status": "completed", "startedAt": _ts(530), "completedAt": _ts(460), "durationMs": 70000, "error": None, "tokens": 0},
            ],
            "scenes": [
                {"id": "scene_5", "kind": "title", "engine": "remotion", "status": "completed", "reviewIssues": 0, "retryCount": 0},
                {"id": "scene_6", "kind": "code", "engine": "remotion", "status": "completed", "reviewIssues": 0, "retryCount": 0},
                {"id": "scene_7", "kind": "diagram", "engine": "manim", "status": "completed", "reviewIssues": 0, "retryCount": 1},
                {"id": "scene_8", "kind": "outro", "engine": "remotion", "status": "completed", "reviewIssues": 0, "retryCount": 0},
            ],
            "artifacts": [
                {"artifactType": "video/mp4", "path": f"/artifacts/job_003/final.mp4", "sceneId": None},
            ],
            "events": make_seed_events("job_003", [
                ("job.started", {"title": "Release v0.5 — Demo video"}),
                ("job.stage", {"stage": "plan", "progressPct": 5, "phase": "plan"}),
                ("job.stage", {"stage": "tts", "progressPct": 25, "phase": "tts"}),
                ("job.stage", {"stage": "render", "progressPct": 55, "phase": "render"}),
                ("subagent.started", {"subagentId": "sa_5", "name": "Scene Planner", "engine": "director", "task": "Plan scene graph"}),
                ("subagent.completed", {"subagentId": "sa_5", "result": "ok", "durationMs": 5000}),
                ("subagent.token", {"subagentId": "sa_5", "token": "Planned 4 scenes"}),
                ("subagent.started", {"subagentId": "sa_6", "name": "TTS Engine", "engine": "tts", "task": "Generate narration"}),
                ("subagent.completed", {"subagentId": "sa_6", "result": "ok", "durationMs": 30000}),
                ("subagent.started", {"subagentId": "sa_7", "name": "Compositor", "engine": "remotion", "task": "Render all scenes"}),
                ("subagent.completed", {"subagentId": "sa_7", "result": "ok", "durationMs": 70000}),
                ("job.completed", {"title": "Release v0.5 — Demo video"}),
            ]),
        },
        {
            "id": "job_004",
            "title": "PR #156 — Fix layout overlap",
            "status": "failed",
            "stage": "repair",
            "progressPct": 78,
            "createdAt": _ts(200),
            "startedAt": _ts(190),
            "completedAt": _ts(50),
            "error": "Repair retry budget exhausted for scene_10",
            "subagents": [
                {"id": "sa_8", "name": "Review Gate L2", "engine": "review", "task": "Check layout overlap", "status": "completed", "startedAt": _ts(100), "completedAt": _ts(95), "durationMs": 5000, "error": None, "tokens": 210},
                {"id": "sa_9", "name": "Auto-Repair", "engine": "repair", "task": "Fix overlap in scene_10", "status": "failed", "startedAt": _ts(90), "completedAt": _ts(50), "durationMs": 40000, "error": "Retry budget exhausted", "tokens": 0},
            ],
            "scenes": [
                {"id": "scene_9", "kind": "comparison", "engine": "remotion", "status": "completed", "reviewIssues": 0, "retryCount": 0},
                {"id": "scene_10", "kind": "diagram", "engine": "manim", "status": "failed", "reviewIssues": 3, "retryCount": 3},
            ],
            "artifacts": [],
            "events": make_seed_events("job_004", [
                ("job.started", {"title": "PR #156 — Fix layout overlap"}),
                ("job.stage", {"stage": "plan", "progressPct": 5, "phase": "plan"}),
                ("job.stage", {"stage": "review", "progressPct": 65, "phase": "review"}),
                ("review.issue", {"sceneId": "scene_10", "issue": "Text overlaps chart boundary", "severity": "high"}),
                ("repair.plan", {"sceneId": "scene_10", "plan": "Reduce font size, increase spacing", "retryCount": 1}),
                ("repair.plan", {"sceneId": "scene_10", "plan": "Reduce font size, increase spacing (attempt 2)", "retryCount": 2}),
                ("job.stage", {"stage": "repair", "progressPct": 78, "phase": "repair"}),
                ("job.failed", {"title": "PR #156 — Fix layout overlap", "error": "Repair retry budget exhausted"}),
            ]),
        },
    ]

    for job in jobs_data:
        _job_store[job["id"]] = job
