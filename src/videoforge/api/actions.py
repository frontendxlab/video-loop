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
from videoforge.api.events import DirectorSceneRouted, JobFailed, RetryStarted
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

    return {"status": "stopped", "job_id": job_id}


@router.post("/{job_id}/retry")
async def retry_job(
    job_id: str,
    feed: EventFeed = Depends(get_feed),
) -> dict[str, Any]:
    """Retry a failed job.

    Emits ``retry.started`` event to SSE stream.
    """
    _validate_id(job_id, "job_id")

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

    return {"status": "retry_queued", "job_id": job_id}


@router.post("/{job_id}/retry/{scene_id}")
async def retry_scene(
    job_id: str,
    scene_id: str,
    feed: EventFeed = Depends(get_feed),
) -> dict[str, Any]:
    """Retry a specific scene/subagent.

    Emits ``retry.started`` event scoped to the scene.
    """
    _validate_id(job_id, "job_id")

    await feed.append(
        RetryStarted(
            jobId=job_id,
            payload={
                "itemType": "scene",
                "itemId": scene_id,
                "sceneId": scene_id,
                "attempt": 1,
                "maxRetries": 3,
                "reason": f"User retried scene {scene_id}",
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
    Emits ``director.scene_routed`` event.
    """
    _validate_id(job_id, "job_id")
    _validate_id(scene_id, "scene_id")

    engine = body.engine if body is not None else "remotion"

    await feed.append(
        DirectorSceneRouted(
            jobId=job_id,
            payload={"sceneId": scene_id, "engine": engine, "reason": "User reroute"},
        )
    )

    return {"status": "rerouted", "job_id": job_id, "scene_id": scene_id, "engine": engine}
