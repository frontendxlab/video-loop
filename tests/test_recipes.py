"""Recipe registry tests — schema validity, deterministic loading, queries."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from videoforge.engine.recipes import (
    clear_cache,
    get_recipe,
    load_recipes,
    recipes_by_scene_kind,
    recipes_by_engine,
    recipes_by_tag,
)


@pytest.fixture(autouse=True)
def _clear_cache():
    clear_cache()
    yield
    clear_cache()


# ── schema validity ────────────────────────────────────────────────


def test_loads_all_recipes():
    recipes = load_recipes()
    assert len(recipes) >= 28, f"Expected >=28 recipes, got {len(recipes)}"


def test_all_recipes_have_required_fields():
    for r in load_recipes():
        assert r.id, f"Missing id: {r}"
        assert r.name, f"Missing name: {r.id}"
        assert r.scene_kind, f"Missing scene_kind: {r.id}"
        assert r.preferred_engine, f"Missing preferred_engine: {r.id}"


def test_all_recipes_have_unique_ids():
    ids = [r.id for r in load_recipes()]
    assert len(ids) == len(set(ids)), f"Duplicate ids: {ids}"


def test_all_inputs_have_valid_types():
    valid = {"string", "number", "boolean", "array"}
    for r in load_recipes():
        for inp in r.allowed_inputs:
            assert inp.type in valid, (
                f"Recipe {r.id} input {inp.key}: invalid type '{inp.type}'"
            )


def test_all_review_hints_have_valid_severity():
    valid = {"error", "warn", "info"}
    for r in load_recipes():
        for hint in r.review_hints:
            assert hint.severity in valid, (
                f"Recipe {r.id} hint: invalid severity '{hint.severity}'"
            )


def test_all_inputs_have_required_key():
    for r in load_recipes():
        for inp in r.allowed_inputs:
            assert inp.key, f"Recipe {r.id}: input missing key"


def test_all_recipes_have_non_empty_tags():
    for r in load_recipes():
        assert len(r.tags) > 0, f"Recipe {r.id}: no tags"


def test_each_recipe_at_least_one_required_input():
    """Every recipe needs at least one required input to be useful."""
    for r in load_recipes():
        required = [i for i in r.allowed_inputs if i.required]
        assert len(required) >= 1, f"Recipe {r.id}: no required inputs"


# ── deterministic loading ─────────────────────────────────────────


def test_loading_is_deterministic():
    a = load_recipes()
    b = load_recipes()
    assert a == b
    assert [r.id for r in a] == [r.id for r in b]


def test_loading_from_path_is_deterministic():
    default_path = (
        Path(__file__).resolve().parents[1] / "config" / "recipe_registry.json"
    )
    a = load_recipes(default_path)
    b = load_recipes(default_path)
    assert a == b


def test_recipe_fields_are_frozen():
    r = load_recipes()[0]
    with pytest.raises(Exception):
        r.id = "mutated"  # type: ignore[misc]


def test_recipe_input_fields_are_frozen():
    r = load_recipes()[0]
    if r.allowed_inputs:
        inp = r.allowed_inputs[0]
        with pytest.raises(Exception):
            inp.key = "mutated"  # type: ignore[misc]


def test_review_hint_fields_are_frozen():
    r = load_recipes()[0]
    if r.review_hints:
        hint = r.review_hints[0]
        with pytest.raises(Exception):
            hint.check = "mutated"  # type: ignore[misc]


# ── known recipes ──────────────────────────────────────────────────


def test_map3d_recipe_exists():
    r = get_recipe("map3d")
    assert r is not None
    assert r.scene_kind == "map3d"
    assert r.preferred_engine == "manim"


def test_document_highlight_recipe():
    r = get_recipe("document-highlight")
    assert r is not None
    assert r.scene_kind == "title"
    assert r.preferred_engine == "remotion"


def test_screenflow_recipe():
    r = get_recipe("screenflow")
    assert r is not None
    assert r.scene_kind == "comparison"
    assert r.preferred_engine == "remotion"


def test_hero_intro_recipe():
    r = get_recipe("hero-intro")
    assert r is not None
    assert r.scene_kind == "title"
    assert r.preferred_engine == "remotion"


def test_overlay_cta_recipe():
    r = get_recipe("overlay-cta")
    assert r is not None
    assert r.scene_kind == "outro"
    assert r.preferred_engine == "remotion"


def test_trajectory_timeline_recipe():
    r = get_recipe("trajectory-timeline")
    assert r is not None
    assert r.scene_kind == "timeline"
    assert r.preferred_engine == "manim"


def test_3d_ranking_recipe():
    r = get_recipe("3d-ranking")
    assert r is not None
    assert r.scene_kind == "chart"
    assert r.preferred_engine == "remotion"


def test_audio_reactive_recipe():
    r = get_recipe("audio-reactive")
    assert r is not None
    assert r.scene_kind == "title"
    assert r.preferred_engine == "remotion"


def test_dual_chart_recipe():
    r = get_recipe("dual-chart")
    assert r is not None
    assert r.scene_kind == "chart"
    assert r.preferred_engine == "manim"


def test_launch_promo_recipe():
    r = get_recipe("launch-promo")
    assert r is not None
    assert r.scene_kind == "promo"
    assert r.preferred_engine == "remotion"


def test_real_estate_recipe():
    r = get_recipe("real-estate")
    assert r is not None
    assert r.scene_kind == "real-estate"
    assert r.preferred_engine == "remotion"


def test_product_promo_recipe():
    r = get_recipe("product-promo")
    assert r is not None
    assert r.scene_kind == "promo"
    assert r.preferred_engine == "remotion"


def test_svg_morph_recipe():
    r = get_recipe("svg-morph")
    assert r is not None
    assert r.scene_kind == "svg-morph"
    assert r.preferred_engine == "remotion"


def test_three_scene_recipe():
    r = get_recipe("three-scene")
    assert r is not None
    assert r.scene_kind == "three-scene"
    assert r.preferred_engine == "remotion"


def test_kinetic_text_recipe():
    r = get_recipe("kinetic-text")
    assert r is not None
    assert r.scene_kind == "kinetic-text"
    assert r.preferred_engine == "remotion"


def test_canvas_composite_recipe():
    r = get_recipe("canvas-composite")
    assert r is not None
    assert r.scene_kind == "canvas-composite"
    assert r.preferred_engine == "remotion"


def test_cursor_agent_skills_recipe():
    r = get_recipe("cursor-agent-skills")
    assert r is not None
    assert r.scene_kind == "promo"
    assert r.preferred_engine == "remotion"


def test_svg_3d_glitch_recipe():
    r = get_recipe("svg-3d-glitch")
    assert r is not None
    assert r.scene_kind == "three-scene"
    assert r.preferred_engine == "remotion"


def test_retro_pixel_font_recipe():
    r = get_recipe("retro-pixel-font")
    assert r is not None
    assert r.scene_kind == "three-scene"
    assert r.preferred_engine == "remotion"


def test_strava_run_recipe():
    r = get_recipe("strava-run")
    assert r is not None
    assert r.scene_kind == "map3d"
    assert r.preferred_engine == "remotion"


def test_kinetic_marketing_recipe():
    r = get_recipe("kinetic-marketing")
    assert r is not None
    assert r.scene_kind == "kinetic-text"
    assert r.preferred_engine == "remotion"


def test_audio_spectrum_recipe():
    r = get_recipe("audio-spectrum")
    assert r is not None
    assert r.scene_kind == "audio-reactive"
    assert r.preferred_engine == "remotion"


def test_canvas_magnifier_recipe():
    r = get_recipe("canvas-magnifier")
    assert r is not None
    assert r.scene_kind == "canvas-composite"
    assert r.preferred_engine == "remotion"


def test_canvas_glitch_recipe():
    r = get_recipe("canvas-glitch")
    assert r is not None
    assert r.scene_kind == "canvas-composite"
    assert r.preferred_engine == "remotion"


def test_canvas_vintage_recipe():
    r = get_recipe("canvas-vintage")
    assert r is not None
    assert r.scene_kind == "canvas-composite"
    assert r.preferred_engine == "remotion"


def test_bms_animation_recipe():
    r = get_recipe("bms-animation")
    assert r is not None
    assert r.scene_kind == "diagram"
    assert r.preferred_engine == "manim"


def test_solar_system_recipe():
    r = get_recipe("solar-system")
    assert r is not None
    assert r.scene_kind == "three-scene"
    assert r.preferred_engine == "remotion"


def test_device_rise_recipe():
    r = get_recipe("device-rise")
    assert r is not None
    assert r.scene_kind == "three-scene"
    assert r.preferred_engine == "remotion"


# ── query functions ────────────────────────────────────────────────


def test_get_recipe_returns_none_for_missing():
    assert get_recipe("nonexistent-recipe") is None


def test_recipes_by_scene_kind_returns_correct_kinds():
    for r in recipes_by_scene_kind("chart"):
        assert r.scene_kind == "chart"


def test_recipes_by_engine_returns_correct_engines():
    for r in recipes_by_engine("manim"):
        assert r.preferred_engine == "manim"


def test_recipes_by_tag_returns_tagged():
    tagged = recipes_by_tag("data")
    assert len(tagged) >= 1
    for r in tagged:
        assert "data" in r.tags


def test_recipes_by_tag_empty_for_unused_tag():
    assert len(recipes_by_tag("nonexistent-tag-xyz")) == 0


# ── invalid registry rejection ─────────────────────────────────────


def test_duplicate_id_raises(tmp_path: Path):
    bad = tmp_path / "bad_registry.json"
    bad.write_text(
        json.dumps({
            "version": 1,
            "recipes": [
                {"id": "dup", "name": "A", "scene_kind": "title", "preferred_engine": "remotion", "allowed_inputs": [{"key": "x", "type": "string", "required": True, "description": ""}]},
                {"id": "dup", "name": "B", "scene_kind": "code", "preferred_engine": "remotion", "allowed_inputs": [{"key": "y", "type": "string", "required": True, "description": ""}]},
            ],
        })
    )
    with pytest.raises(ValueError, match="Duplicate recipe id"):
        load_recipes(bad)


def test_invalid_input_type_raises(tmp_path: Path):
    bad = tmp_path / "bad_input_type.json"
    bad.write_text(
        json.dumps({
            "version": 1,
            "recipes": [
                {"id": "r1", "name": "R1", "scene_kind": "title", "preferred_engine": "remotion", "allowed_inputs": [{"key": "x", "type": "binary", "required": True, "description": ""}]},
            ],
        })
    )
    with pytest.raises(ValueError, match="invalid type"):
        load_recipes(bad)


def test_invalid_review_severity_raises(tmp_path: Path):
    bad = tmp_path / "bad_severity.json"
    bad.write_text(
        json.dumps({
            "version": 1,
            "recipes": [
                {"id": "r1", "name": "R1", "scene_kind": "title", "preferred_engine": "remotion", "allowed_inputs": [{"key": "x", "type": "string", "required": True, "description": ""}], "review_hints": [{"check": "test", "severity": "critical"}]},
            ],
        })
    )
    with pytest.raises(ValueError, match="invalid severity"):
        load_recipes(bad)


def test_missing_version_raises(tmp_path: Path):
    bad = tmp_path / "no_version.json"
    bad.write_text(json.dumps({"recipes": []}))
    with pytest.raises(ValueError, match="Unsupported recipe registry version"):
        load_recipes(bad)


def test_file_not_found_raises():
    with pytest.raises(FileNotFoundError):
        load_recipes("/nonexistent/path/registry.json")


# ── all_engines helper ─────────────────────────────────────────────


def test_all_engines_preferred_first():
    r = get_recipe("screenflow")
    assert r is not None
    engines = r.all_engines()
    assert engines[0] == r.preferred_engine
    assert len(engines) == len(r.fallback_engines) + 1
