"""Tests for render-related MCP tools."""

from __future__ import annotations

from unittest.mock import patch

import pytest


def test_render_pr_returns_job_id():
    from videoforge.server import create_app
    app = create_app()
    fn = next(t for t in app._tool_manager.list_tools() if t.name == "render_pr")
    with patch("videoforge.server._enqueue_job") as mock:
        mock.return_value = "job-abc-123"
        result = app._tool_manager.execute_tool(fn.name, {"owner": "org", "repo": "repo", "pr_number": 1})
    assert "job_id" in result


def test_render_pr_rejects_missing_params():
    from videoforge.server import create_app
    app = create_app()
    fn = next(t for t in app._tool_manager.list_tools() if t.name == "render_pr")
    with pytest.raises(Exception):
        app._tool_manager.execute_tool(fn.name, {})


def test_render_issue_returns_job_id():
    from videoforge.server import create_app
    app = create_app()
    fn = next(t for t in app._tool_manager.list_tools() if t.name == "render_issue")
    with patch("videoforge.server._enqueue_job") as mock:
        mock.return_value = "job-def-456"
        result = app._tool_manager.execute_tool(fn.name, {"owner": "org", "repo": "repo", "issue_number": 42})
    assert "job_id" in result


def test_status_returns_progress():
    from videoforge.server import create_app
    app = create_app()
    fn = next(t for t in app._tool_manager.list_tools() if t.name == "status")
    with patch("videoforge.server._get_job_status") as mock:
        mock.return_value = {"phase": "COMPLETE", "progress_pct": 100}
        result = app._tool_manager.execute_tool(fn.name, {"job_id": "job-abc-123"})
    assert "phase" in result
    assert "progress_pct" in result
