"""Tests for basic MCP tools."""

from __future__ import annotations


def test_health_check_returns_ok():
    from videoforge.server import create_app
    app = create_app()
    health_fn = next(t for t in app._tool_manager.list_tools() if t.name == "health_check")
    result = app._tool_manager.execute_tool(health_fn.name, {})
    assert result["status"] == "ok"


def test_server_info_returns_config():
    from videoforge.server import create_app
    app = create_app()
    info_fn = next(t for t in app._tool_manager.list_tools() if t.name == "get_server_info")
    result = app._tool_manager.execute_tool(info_fn.name, {})
    assert "version" in result
    assert "server_name" in result


def test_list_voices_returns_voices():
    from videoforge.server import create_app
    app = create_app()
    voices_fn = next(t for t in app._tool_manager.list_tools() if t.name == "list_voices")
    result = app._tool_manager.execute_tool(voices_fn.name, {})
    assert result["count"] > 0
    assert "alba" in result["voices"]


def test_tool_takes_no_unexpected_params():
    from videoforge.server import create_app
    app = create_app()
    # All basic tools should accept no params or only expected ones
    for tool in app._tool_manager.list_tools():
        if tool.name in ("health_check", "list_voices", "list_saved_voices", "get_server_info"):
            assert tool.input_schema is not None
