"""Job action endpoints: stop, retry, reroute.

Provides backend contracts for job/scene lifecycle actions.
Emits SSE events for each action so frontend reacts in real-time.
Active runner registry bridges pipeline runner for stop capability.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from videoforge.api.adapters import EventFeed
from videoforge.api.events import (
    DirectorSceneRouted,
    JobFailed,
    JobStage,
    JobStarted,
    RenderSceneStarted,
    RetryStarted,
)
from videoforge.api.jobs import get_job, store_job
from videoforge.api.sse import get_feed

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

# ─── Active runner registry ────────────────────────────────────────────────

_active_runners: dict[str, Any] = {}


def register_runner(job_id: str, runner: Any) -> None:
    """Register active pipeline runner so stop can cancel it."""
    _active_runners[job_id] = runner


def unregister_runner(job_id: str) -> None:
    """Remove runner when pipeline completes or is stopped."""
    _active_runners.pop(job_id, None)


def _get_runner(job_id: str) -> Any | None:
    return _active_runners.get(job_id)


# ─── Request schemas ───────────────────────────────────────────────────────


class RerouteRequest(BaseModel):
    """Optional body for reroute endpoint."""
    engine: str = "remotion"
    provider: str | None = None
    model: str | None = None


def _validate_id(component: str, label: str = "ID") -> None:
    if not component or "/" in component or ".." in component:
        raise HTTPException(400, f"Invalid {label}")


# ─── Action endpoints ──────────────────────────────────────────────────────


@router.post("/{job_id}/stop")
async def stop_job(
    job_id: str,
    feed: EventFeed = Depends(get_feed),
) -> dict[str, Any]:
    """Stop a running job.

    Cancels active pipeline runner (if registered) and emits
    ``job.failed`` event to SSE stream.
    """
    _validate_id(job_id, "job_id")

    runner = _get_runner(job_id)
    if runner is not None:
        runner.cancel()
        logger.info("Cancelled runner for job %s", job_id)
        unregister_runner(job_id)
    else:
        logger.warning("No active runner found for job %s", job_id)

    await feed.append(
        JobFailed(
            jobId=job_id,
            payload={"error": "Job stopped by user", "stage": "manual", "retryCount": 0},
        )
    )

    # Update job store so UI sees real status change
    job = get_job(job_id)
    if job is not None:
        job["status"] = "cancelled"
        job["stage"] = "manual"
        job["progressPct"] = 0
        job["error"] = "Job stopped by user"
        store_job(job_id, job)
        await feed.append(
            JobStage(
                jobId=job_id,
                payload={"stage": "cancelled", "progressPct": 0, "phase": "manual"},
            )
        )

    return {"status": "stopped", "job_id": job_id}


@router.post("/{job_id}/retry")
async def retry_job(
    job_id: str,
    feed: EventFeed = Depends(get_feed),
) -> dict[str, Any]:
    """Retry a failed job.

    Cancels active runner, resets job store state, and emits
    ``retry.started`` + ``job.started`` + ``job.stage`` events
    so pipeline and UI restart fresh.
    """
    _validate_id(job_id, "job_id")

    # Cancel any active runner
    runner = _get_runner(job_id)
    if runner is not None:
        runner.cancel()
        unregister_runner(job_id)

    await feed.append(
        RetryStarted(
            jobId=job_id,
            payload={
                "itemType": "job",
                "itemId": job_id,
                "attempt": 1,
                "maxRetries": 3,
                "reason": "User retried job",
            },
        )
    )

    # Reset job store: clear error, reset scenes/subagents
    job = get_job(job_id)
    job_title = job.get("title", "") if job else ""
    if job is not None:
        job["status"] = "queued"
        job["stage"] = "retry_queued"
        job["progressPct"] = 0
        job["error"] = None
        job["completedAt"] = None
        for sa in job.get("subagents", []):
            sa["status"] = "pending"
            sa["startedAt"] = None
            sa["completedAt"] = None
            sa["durationMs"] = None
            sa["error"] = None
        for s in job.get("scenes", []):
            s["status"] = "pending"
        store_job(job_id, job)

    # Emit restart events so pipeline/UI picks up
    await feed.append(
        JobStarted(
            jobId=job_id,
            payload={"title": job_title, "reason": "User retried job"},
        )
    )
    await feed.append(
        JobStage(
            jobId=job_id,
            payload={"stage": "retry_queued", "progressPct": 0, "phase": "retry"},
        )
    )

    return {"status": "retry_queued", "job_id": job_id}


@router.post("/{job_id}/retry/{scene_id}")
async def retry_scene(
    job_id: str,
    scene_id: str,
    feed: EventFeed = Depends(get_feed),
) -> dict[str, Any]:
    """Retry a specific scene/subagent.

    Resets scene status in job store, increments retry count,
    and emits ``retry.started`` + ``render.scene_started`` events
    so pipeline re-renders that scene.
    """
    _validate_id(job_id, "job_id")

    scene_retry_count = 0
    job = get_job(job_id)
    if job is not None:
        for s in job.get("scenes", []):
            if s.get("id") == scene_id:
                scene_retry_count = s.get("retryCount", 0) + 1
                s["status"] = "pending"
                s["retryCount"] = scene_retry_count
                break
        store_job(job_id, job)

    await feed.append(
        RetryStarted(
            jobId=job_id,
            payload={
                "itemType": "scene",
                "itemId": scene_id,
                "sceneId": scene_id,
                "attempt": scene_retry_count or 1,
                "maxRetries": 3,
                "reason": f"User retried scene {scene_id}",
            },
        )
    )

    # Signal re-render for this scene
    await feed.append(
        RenderSceneStarted(
            jobId=job_id,
            payload={
                "sceneId": scene_id,
                "engine": "retry",
                "retryCount": scene_retry_count,
                "reason": "User retried scene",
            },
        )
    )

    return {"status": "retry_queued", "job_id": job_id, "scene_id": scene_id}


@router.post("/{job_id}/reroute/{scene_id}")
async def reroute_scene(
    job_id: str,
    scene_id: str,
    body: RerouteRequest | None = None,
    feed: EventFeed = Depends(get_feed),
) -> dict[str, Any]:
    """Reroute a scene to a different engine.

    Accepts optional JSON body with ``engine`` field.
    Defaults to ``"remotion"``.
    Updates engine in job store and emits ``director.scene_routed``
    + ``render.scene_started`` events so pipeline re-renders.
    """
    _validate_id(job_id, "job_id")
    _validate_id(scene_id, "scene_id")

    # Look up old engine from store
    old_engine = "unknown"
    job = get_job(job_id)
    if job is not None:
        for s in job.get("scenes", []):
            if s.get("id") == scene_id:
                old_engine = s.get("engine", "unknown")
                break

    engine = body.engine if body is not None else "remotion"
    provider = body.provider if (body and body.provider) else None
    model = body.model if (body and body.model) else None

    payload: dict[str, Any] = {"sceneId": scene_id, "engine": engine, "reason": "User reroute"}
    if provider:
        payload["provider"] = provider
    if model:
        payload["model"] = model

    await feed.append(DirectorSceneRouted(jobId=job_id, payload=payload))

    # Update scene engine in job store + mark for re-render
    if job is not None:
        for s in job.get("scenes", []):
            if s.get("id") == scene_id:
                s["engine"] = engine
                s["status"] = "pending"
                break
        store_job(job_id, job)

    # Signal re-render with new engine
    await feed.append(
        RenderSceneStarted(
            jobId=job_id,
            payload={
                "sceneId": scene_id,
                "engine": engine,
                "previousEngine": old_engine,
                "reason": "User reroute",
            },
        )
    )

    result: dict[str, Any] = {"status": "rerouted", "job_id": job_id, "scene_id": scene_id, "engine": engine}
    if provider:
        result["provider"] = provider
    if model:
        result["model"] = model
    return result
