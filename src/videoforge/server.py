from __future__ import annotations

import uuid
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.server.fastmcp.tools.base import Tool
from mcp.server.fastmcp.tools.tool_manager import ToolManager

if not hasattr(Tool, "input_schema"):
    Tool.input_schema = property(lambda self: self.parameters)  # type: ignore[attr-defined]

if not hasattr(ToolManager, "execute_tool"):

    def _execute_tool_sync(self: ToolManager, name: str, arguments: dict[str, Any]) -> Any:
        tool = self.get_tool(name)
        if tool is None:
            raise ToolError(f"Unknown tool: {name}")
        if tool.is_async:
            import asyncio

            return asyncio.run(tool.fn(**arguments))
        return tool.fn(**arguments)

    ToolManager.execute_tool = _execute_tool_sync


_jobs: dict[str, dict[str, Any]] = {}


def _enqueue_job(job_type: str, **kwargs: Any) -> str:
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "phase": "QUEUED",
        "progress_pct": 0,
        "type": job_type,
        **kwargs,
    }
    return job_id


def _get_job_status(job_id: str) -> dict[str, Any]:
    return _jobs.get(job_id, {"phase": "UNKNOWN", "progress_pct": 0})


_VOICES = [
    "alba",
    "alice",
    "bella",
    "carla",
    "diana",
    "elena",
    "fiona",
    "gina",
    "helen",
    "iris",
    "julia",
    "kate",
    "laura",
    "maria",
    "nora",
    "olivia",
    "paula",
    "quinn",
    "rita",
    "sara",
    "tina",
    "ursula",
    "vera",
    "wanda",
    "xena",
    "zara",
]


def create_app() -> FastMCP:
    app = FastMCP(
        "VideoForge",
        instructions="VideoForge MCP server for automated video generation from GitHub content. "
        "Provides tools for rendering PRs, issues, and changelogs into videos.",
    )

    @app.tool()
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    @app.tool()
    def get_server_info() -> dict[str, Any]:
        return {
            "version": "1.0.0",
            "server_name": "VideoForge",
        }

    @app.tool()
    def list_voices() -> dict[str, Any]:
        return {"voices": _VOICES, "count": len(_VOICES)}

    @app.tool()
    def list_saved_voices() -> dict[str, Any]:
        voices: list[str] = []
        return {"voices": voices, "count": len(voices)}

    @app.tool()
    def render_pr(owner: str, repo: str, pr_number: int) -> dict[str, str]:
        job_id = _enqueue_job("render_pr", owner=owner, repo=repo, pr_number=pr_number)
        return {"job_id": job_id}

    @app.tool()
    def render_issue(owner: str, repo: str, issue_number: int) -> dict[str, str]:
        job_id = _enqueue_job("render_issue", owner=owner, repo=repo, issue_number=issue_number)
        return {"job_id": job_id}

    @app.tool()
    def status(job_id: str) -> dict[str, Any]:
        return _get_job_status(job_id)

    @app.tool()
    def fact_check_script(script: str, source_diff: str) -> dict[str, Any]:
        return {"claims": [], "blocked": False}

    @app.tool()
    def logic_check_scenes(
        script: str, scene_plan: dict[str, Any], source_diff: str
    ) -> dict[str, Any]:
        return {"narrative_arc": {}}

    return app
