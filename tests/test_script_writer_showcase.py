"""ScriptWriter showcase emission tests — deterministic rule-based pattern detection."""

from __future__ import annotations

from videoforge.orchestrator.script_writer import (
    SHOWCASE_RULES,
    ScriptWriter,
    _detect_showcase_pattern,
    _get_nested,
)


def _default_content(**overrides: object) -> dict:
    return {
        "title": "Test PR",
        "body": "This PR adds a new feature and fixes a bug.",
        "diff": "--- a/foo.py\n+++ b/foo.py\n@@ -1 +1 @@\n-old\n+new",
        "files": [{"path": "src/main.py"}, {"path": "src/utils.py"}],
        **overrides,
    }


# ── _get_nested helper ───────────────────────────────────────────


def test_get_nested_simple_key():
    assert _get_nested({"a": 1}, "a") == 1


def test_get_nested_nested_key():
    assert _get_nested({"a": {"b": 2}}, "a.b") == 2


def test_get_nested_missing_key():
    assert _get_nested({"a": 1}, "b") is None


def test_get_nested_partial_path():
    assert _get_nested({"a": {"b": 2}}, "a.x") is None


def test_get_nested_non_dict_intermediate():
    assert _get_nested({"a": 42}, "a.b") is None


# ── _detect_showcase_pattern ─────────────────────────────────────


def test_detect_no_showcase_returns_none():
    assert _detect_showcase_pattern(_default_content()) is None


def test_detect_empty_showcase_returns_none():
    assert _detect_showcase_pattern(_default_content(showcase={})) is None


def test_detect_hero_intro():
    result = _detect_showcase_pattern(_default_content(showcase={"kind": "hero-intro"}))
    assert result is not None
    assert result["scene_type"] == "title"
    assert "Hero Intro" in result["title"]


def test_detect_svg_morph():
    result = _detect_showcase_pattern(_default_content(showcase={"kind": "svg-morph"}))
    assert result is not None
    assert result["scene_type"] == "svg-morph"
    assert result["estimated_duration_seconds"] == 5.0


def test_detect_kinetic_text():
    result = _detect_showcase_pattern(_default_content(showcase={"kind": "kinetic-text"}))
    assert result is not None
    assert result["scene_type"] == "kinetic-text"


def test_detect_canvas_composite():
    result = _detect_showcase_pattern(_default_content(showcase={"kind": "canvas-composite"}))
    assert result is not None
    assert result["scene_type"] == "canvas-composite"


def test_detect_real_estate():
    result = _detect_showcase_pattern(_default_content(showcase={"kind": "real-estate"}))
    assert result is not None
    assert result["scene_type"] == "real-estate"


def test_detect_promo():
    result = _detect_showcase_pattern(_default_content(showcase={"kind": "promo"}))
    assert result is not None
    assert result["scene_type"] == "promo"


def test_detect_three_scene():
    result = _detect_showcase_pattern(_default_content(showcase={"kind": "three-scene"}))
    assert result is not None
    assert result["scene_type"] == "three-scene"


def test_detect_trajectory_timeline():
    result = _detect_showcase_pattern(_default_content(showcase={"kind": "trajectory-timeline"}))
    assert result is not None
    assert result["scene_type"] == "timeline"


def test_detect_3d_ranking():
    result = _detect_showcase_pattern(_default_content(showcase={"kind": "3d-ranking"}))
    assert result is not None
    assert result["scene_type"] == "chart"


def test_detect_audio_reactive():
    result = _detect_showcase_pattern(_default_content(showcase={"kind": "audio-reactive"}))
    assert result is not None
    assert result["scene_type"] == "title"


def test_detect_dual_chart():
    result = _detect_showcase_pattern(_default_content(showcase={"kind": "dual-chart"}))
    assert result is not None
    assert result["scene_type"] == "chart"
    assert result["estimated_duration_seconds"] == 7.0


def test_detect_document_highlight():
    result = _detect_showcase_pattern(_default_content(showcase={"kind": "document-highlight"}))
    assert result is not None
    assert result["scene_type"] == "title"


def test_detect_overlay_cta():
    result = _detect_showcase_pattern(_default_content(showcase={"kind": "overlay-cta"}))
    assert result is not None
    assert result["scene_type"] == "outro"
    assert result["estimated_duration_seconds"] == 4.0


def test_detect_screenflow():
    result = _detect_showcase_pattern(_default_content(showcase={"kind": "screenflow"}))
    assert result is not None
    assert result["scene_type"] == "comparison"
    assert result["estimated_duration_seconds"] == 8.0


# ── SHOWCASE_RULES table invariants ──────────────────────────────


def test_all_showcase_rules_have_valid_types():
    for path, expected, scene_type, label, duration in SHOWCASE_RULES:
        assert isinstance(path, str) and path, f"Invalid path: {path}"
        assert isinstance(scene_type, str) and scene_type, f"Invalid scene_type: {scene_type}"
        assert isinstance(label, str) and label, f"Invalid label: {label}"
        assert isinstance(duration, (int, float)) and duration > 0, (
            f"Invalid duration: {duration}"
        )


def test_all_showcase_rules_paths_start_with_showcase():
    for path, *_ in SHOWCASE_RULES:
        assert path.startswith("showcase."), f"Path must start with 'showcase.': {path}"


def test_showcase_rules_have_unique_kinds():
    kinds = [expected for _, expected, *_ in SHOWCASE_RULES]
    assert len(kinds) == len(set(kinds)), f"Duplicate showcase kinds: {kinds}"


# ── SceneWriter integration ──────────────────────────────────────


def test_write_script_no_showcase_emits_no_showcase_scene():
    writer = ScriptWriter()
    result = writer.write_script(_default_content())
    scene_types = [s["scene_type"] for s in result["scenes"]]
    showcase_types = {"svg-morph", "kinetic-text", "canvas-composite",
                      "real-estate", "promo", "three-scene"}
    assert not showcase_types.intersection(scene_types), (
        f"Showcase types leaked into non-showcase script: {scene_types}"
    )


def test_write_script_with_hero_intro_includes_showcase_scene():
    writer = ScriptWriter()
    result = writer.write_script(_default_content(showcase={"kind": "hero-intro"}))
    scene_types = [s["scene_type"] for s in result["scenes"]]
    assert "title" in scene_types
    showcase_titles = [s["title"] for s in result["scenes"]]
    assert "Hero Intro" in showcase_titles


def test_write_script_with_svg_morph_includes_showcase_scene():
    writer = ScriptWriter()
    result = writer.write_script(_default_content(showcase={"kind": "svg-morph"}))
    scene_types = [s["scene_type"] for s in result["scenes"]]
    assert "svg-morph" in scene_types


def test_write_script_with_real_estate_includes_showcase_scene():
    writer = ScriptWriter()
    result = writer.write_script(_default_content(showcase={"kind": "real-estate"}))
    scene_types = [s["scene_type"] for s in result["scenes"]]
    assert "real-estate" in scene_types


def test_write_script_showcase_preserves_other_scenes():
    writer = ScriptWriter()
    result = writer.write_script(_default_content(showcase={"kind": "promo"}))
    # Should still have intro + files + code + detail + outro
    assert len(result["scenes"]) >= 5
    assert result["scenes"][0]["scene_type"] == "title"


def test_write_script_showcase_estimated_duration_increases():
    writer = ScriptWriter()
    base = writer.write_script(_default_content())
    showcase = writer.write_script(_default_content(showcase={"kind": "promo"}))
    assert showcase["estimated_duration"] > base["estimated_duration"]


def test_write_script_showcase_is_deterministic():
    writer = ScriptWriter()
    a = writer.write_script(_default_content(showcase={"kind": "svg-morph"}))
    b = writer.write_script(_default_content(showcase={"kind": "svg-morph"}))
    assert a == b
    assert [s["scene_type"] for s in a["scenes"]] == [s["scene_type"] for s in b["scenes"]]
