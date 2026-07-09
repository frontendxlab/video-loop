"""FastAPI SSE endpoint for job event streaming.

Contract: ``GET /api/jobs/{job_id}/stream``
Returns ``text/event-stream`` per SSE spec.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from videoforge.api.adapters import EventFeed, MemoryEventFeed
from videoforge.api.events import SSE_EVENT_TYPES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


# ─── Dependency injection ─────────────────────────────────────────────────


_feed: EventFeed | None = None


def get_feed() -> EventFeed:
    """Return configured event feed. Falls back to memory feed."""
    global _feed
    if _feed is None:
        _feed = MemoryEventFeed()
    return _feed


def set_feed(feed: EventFeed) -> None:
    """Override feed for testing or configuration."""
    global _feed
    _feed = feed


# ─── SSE endpoint ─────────────────────────────────────────────────────────


async def _event_generator(
    job_id: str,
    feed: EventFeed,
    after_id: str | None,
    request: Request,
    limit: int | None = None,
) -> AsyncGenerator[str, None]:
    """Yield SSE-formatted events until client disconnects or *limit* reached."""
    try:
        count = 0
        async for event_str in feed.stream(job_id, after_id=after_id):
            if await request.is_disconnected():
                return
            yield event_str
            count += 1
            if limit is not None and count >= limit:
                return

        # If limit is set (diagnostic/testing mode), don't poll — close after replay
        if limit is not None:
            return

        last_id = after_id
        while not await request.is_disconnected():
            async for event_str in feed.stream(job_id, after_id=last_id):
                if await request.is_disconnected():
                    return
                yield event_str
                count += 1
                for line in event_str.split("\n"):
                    if line.startswith("id:"):
                        last_id = line[3:].strip()
                        break
            await asyncio.sleep(0.5)
    except Exception:
        logger.exception("SSE stream error for job %s", job_id)
        raise


@router.get("/{job_id}/stream")
async def job_stream(
    job_id: str,
    request: Request,
    feed: Annotated[EventFeed, Depends(get_feed)],
    after_id: str | None = Query(None, description="Only events after this event ID"),
    limit: int | None = Query(None, ge=1, le=100, description="Max events to return (for testing)"),
):
    """SSE endpoint for live job event stream.

    Returns ``text/event-stream``.
    Replays past events then keeps connection open for new events.
    Client can reconnect with ``?after_id=evt_xxx`` to resume.
    Use ``?limit=N`` to close after N events (for testing / diagnostics).
    """
    if not job_id or "/" in job_id or ".." in job_id:
        raise HTTPException(400, "Invalid job_id")

    return StreamingResponse(
        _event_generator(job_id, feed, after_id, request, limit=limit),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Event-Types": ",".join(SSE_EVENT_TYPES),
        },
    )


@router.get("/{job_id}/events")
async def list_events(
    job_id: str,
    feed: Annotated[EventFeed, Depends(get_feed)],
):
    """List all events for a job (replay / historical). Returns JSON list."""
    events = await feed.replay(job_id)
    return [e.model_dump() for e in events]
