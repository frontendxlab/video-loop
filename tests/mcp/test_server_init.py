"""MCP server initialization and handshake tests."""

from __future__ import annotations


def test_server_module_imports():
    from videoforge.server import create_app  # noqa: F401


def test_mcp_app_has_name():
    from videoforge.server import create_app
    app = create_app()
    assert app.name is not None
    assert "VideoForge" in app.name


def test_mcp_app_has_instructions():
    from videoforge.server import create_app
    app = create_app()
    assert app.instructions is not None
    assert len(app.instructions) > 0


def test_tools_are_registered():
    from videoforge.server import create_app
    app = create_app()
    tool_names = [t.name for t in app._tool_manager.list_tools()]
    assert "health_check" in tool_names
    assert "list_voices" in tool_names
