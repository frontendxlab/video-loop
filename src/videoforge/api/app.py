"""FastAPI app factory for VideoForge API.

Mounts SSE router and provides lifetime feed configuration.
"""

from __future__ import annotations

from fastapi import FastAPI

from videoforge.api.adapters import EventFeed, MemoryEventFeed
from videoforge.api.sse import router as sse_router, set_feed


def create_app(feed: EventFeed | None = None) -> FastAPI:
    """Create FastAPI application with SSE endpoint.

    Args:
        feed: Event feed backend. Defaults to MemoryEventFeed.

    Returns:
        Configured FastAPI app ready for ``uvicorn.run()``.
    """
    app = FastAPI(
        title="VideoForge API",
        version="0.1.0",
        description="Deterministic multi-engine video director — SSE event contract",
    )

    if feed is not None:
        set_feed(feed)

    app.include_router(sse_router)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app
