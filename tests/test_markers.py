"""Validate custom pytest markers are registered and applied to test files."""

from __future__ import annotations

import pathlib
import re
import tomllib


def test_markers_registered() -> None:
    """All custom markers are registered in pyproject.toml."""
    with open("pyproject.toml", "rb") as f:
        cfg = tomllib.load(f)
    raw = cfg["tool"]["pytest"]["ini_options"]["markers"]
    registered = {m.split(":", 1)[0].strip() for m in raw}
    for name in ("slow", "render_smoke", "structural"):
        assert name in registered, f"Marker {name!r} not in pyproject.toml"


def test_render_smoke_marker_used_in_multiple_files() -> None:
    """render_smoke marker present across multiple test files."""
    refs: dict[str, int] = {}
    for f in sorted(pathlib.Path("tests").rglob("test_*.py")):
        if f.name == "test_markers.py":
            continue  # skip self
        text = f.read_text()
        # Count pytestmark assignment or decorator usage
        c = len(re.findall(r"pytestmark\s*=|@pytest\.mark\.render_smoke", text))
        if c:
            refs[f.name] = c
    assert len(refs) >= 4, f"Expected >=4 files with render_smoke, got {len(refs)}: {refs}"
    assert sum(refs.values()) >= 5, f"Expected >=5 render_smoke refs, got {sum(refs.values())}: {refs}"
