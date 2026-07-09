"""FastAPI app factory for VideoForge API.

Mounts SSE router and provides lifetime feed configuration.
"""

from __future__ import annotations

from fastapi import FastAPI

from videoforge.api.actions import router as actions_router
from videoforge.api.adapters import EventFeed, MemoryEventFeed
from videoforge.api.artifacts import router as artifacts_router
from videoforge.api.director_preview import router as director_preview_router
from videoforge.api.jobs import router as jobs_router, seed_jobs
from videoforge.api.recipes import router as recipes_router
from videoforge.api.reports import router as reports_router
from videoforge.api.settings import router as settings_router
from videoforge.api.sse import router as sse_router, set_feed


def create_app(feed: EventFeed | None = None) -> FastAPI:
    """Create FastAPI application with SSE + Jobs endpoints.

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

    app.include_router(actions_router)
    app.include_router(artifacts_router)
    app.include_router(director_preview_router)
    app.include_router(recipes_router)
    app.include_router(sse_router)
    app.include_router(settings_router)
    app.include_router(jobs_router)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.on_event("startup")
    async def _seed():
        seed_jobs()

    return app
