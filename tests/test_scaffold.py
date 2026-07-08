"""Slice-001: Project scaffold checks."""

from __future__ import annotations

from pathlib import Path


def test_pyproject_toml_exists():
    assert Path("pyproject.toml").exists()


def test_package_init_exists():
    assert Path("src/videoforge/__init__.py").exists()


def test_package_imports():
    import videoforge  # noqa: F401


def test_agents_package_imports():
    import videoforge.agents  # noqa: F401


def test_tools_package_imports():
    import videoforge.tools  # noqa: F401


def test_review_package_imports():
    import videoforge.review  # noqa: F401


def test_test_directories_exist():
    for d in ["tests/mcp", "tests/audio", "tests/review", "tests/fetcher", "tests/validation"]:
        assert Path(d).exists(), f"Missing test directory: {d}"
