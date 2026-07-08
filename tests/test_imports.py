"""Verify all module imports work across the package."""

from __future__ import annotations


def test_core_modules_import():
    from videoforge import exceptions  # noqa: F401
    from videoforge import config  # noqa: F401


def test_exceptions_hierarchy():
    from videoforge.exceptions import (
        VideoForgeError, ConfigError, TTSConnectionError,
        GitHubAuthError, RenderError, WebhookAuthError,
    )
    assert issubclass(ConfigError, VideoForgeError)
    assert issubclass(TTSConnectionError, VideoForgeError)
    assert issubclass(GitHubAuthError, VideoForgeError)
    assert issubclass(RenderError, VideoForgeError)
    assert issubclass(WebhookAuthError, VideoForgeError)


def test_dependencies_available():
    import mcp  # noqa: F401
    import yaml  # noqa: F401
    import requests  # noqa: F401
