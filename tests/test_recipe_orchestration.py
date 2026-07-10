"""Recipe orchestration tests — recipe selection changes scene graph + engine.

Core thesis: choosing different showcase recipes produces materially different
orchestration output (scene kinds, transitions, engine routing, payload shape).
These tests prove the recipe→orchestration link is live, not just metadata.
"""

from __future__ import annotations

from videoforge.engine.director import pick_engine
from videoforge.engine.ir import Engine, NarrationSpec, SceneKind, SceneNode
from videoforge.engine.recipes import clear_cache
from videoforge.orchestrator.scene_planner import ScenePlanner
from videoforge.orchestrator.script_writer import ScriptWriter


def _content(recipe_kind: str, **extra: object) -> dict:
    return {
        "title": "Test",
        "body": "Some body content with multiple sentences. Here is another one. And a third.",
        "diff": "--- a/foo.py\n+++ b/foo.py\n@@ -1 +1 @@\n-old\n+new",
        "files": [{"path": "src/main.py"}],
        "showcase": {"kind": recipe_kind, **extra},
    }


# ── Recipe → scene graph (script writing layer) ───────────────────


def test_different_recipes_produce_different_scene_graphs():
    """Different recipe selection → different scene_type in script output."""
    writer = ScriptWriter()
    screenflow = writer.write_script(_content("screenflow"))
    dual_chart = writer.write_script(_content("dual-chart"))

    sf_types = [s["scene_type"] for s in screenflow["scenes"]]
    dc_types = [s["scene_type"] for s in dual_chart["scenes"]]
    assert sf_types != dc_types, (
        "screenflow and dual-chart produce identical scene types"
    )
    assert "comparison" in sf_types
    assert "chart" in dc_types


def test_recipe_deterministic_scene_graph():
    """Same recipe → same scene graph every time."""
    writer = ScriptWriter()
    a = writer.write_script(_content("screenflow"))
    b = writer.write_script(_content("screenflow"))
    assert a == b


def test_no_recipe_vs_recipe_produces_different_graph():
    """Content without recipe kind produces different scene graph than with one."""
    writer = ScriptWriter()
    base = writer.write_script({"title": "Test", "body": "Some content."})
    recipe = writer.write_script(_content("device-rise"))

    base_types = [s["scene_type"] for s in base["scenes"]]
    recipe_types = [s["scene_type"] for s in recipe["scenes"]]
    assert base_types != recipe_types, (
        "No-recipe and device-rise produce same scene types"
    )


# ── Recipe → scene graph (scene planner layer) ────────────────────


def test_recipe_entrance_changes_planned_transition():
    """Recipe entrance from registry overrides default transition selection."""
    clear_cache()
    writer = ScriptWriter()
    planner = ScenePlanner()

    script = writer.write_script(_content("screenflow"))
    plan = planner.plan_scenes(script, [])
    scene_types = [s["type"] for s in plan["scenes"]]
    assert "comparison" in scene_types
    # Find the recipe-enriched scene
    enrich = [s for s in plan["scenes"] if s.get("recipe_id") == "screenflow"]
    assert len(enrich) == 1
    # screenflow recipe entrance = "slide_in_right"
    assert enrich[0]["transition_in"] == "slide_in_right", (
        f"Expected slide_in_right, got {enrich[0]['transition_in']}"
    )


def test_recipe_exit_appears_in_plan():
    """Recipe exit from registry flows through planner."""
    clear_cache()
    writer = ScriptWriter()
    planner = ScenePlanner()

    script = writer.write_script(_content("device-rise"))
    plan = planner.plan_scenes(script, [])
    enrich = [s for s in plan["scenes"] if s.get("recipe_id") == "device-rise"]
    assert len(enrich) == 1
    assert enrich[0]["transition_out"] == "device_fall_out", (
        f"Expected device_fall_out, got {enrich[0]['transition_out']}"
    )


# ── Recipe → engine routing (director layer) ──────────────────────


def _make_node(kind: SceneKind, recipe_id: str | None = None) -> SceneNode:
    import json as _j
    payload: dict = {}
    if recipe_id:
        payload["recipe_id"] = recipe_id
    return SceneNode(
        id=f"n_{kind.value}",
        kind=kind,
        payload=_j.dumps(payload, sort_keys=True),
        engine_hint=Engine.REMOTION,
        duration_frames=90,
        narration=NarrationSpec("t", (), "estimated"),
    )


def test_dual_chart_recipe_routes_to_manim():
    """dual-chart recipe overrides default chart routing (still manim, but explicitly via recipe)."""
    node = _make_node(SceneKind.CHART, "dual-chart")
    assert pick_engine(node) == Engine.MANIM


def test_device_rise_recipe_routes_to_remotion():
    """device-rise recipe (three-scene kind) routes to remotion via recipe override."""
    node = _make_node(SceneKind.THREE_SCENE, "device-rise")
    assert pick_engine(node) == Engine.REMOTION


def test_screenflow_recipe_routes_to_remotion():
    node = _make_node(SceneKind.SCREENFLOW, "screenflow")
    assert pick_engine(node) == Engine.REMOTION


def test_audio_spectrum_recipe_routes_to_remotion():
    node = _make_node(SceneKind.AUDIO_REACTIVE, "audio-spectrum")
    assert pick_engine(node) == Engine.REMOTION


def test_recipe_engine_override():
    """Recipe preferred_engine overrides default kind→engine mapping.

    dual-chart kind=CHART normally routes to MANIM anyway, but the
    recipe mechanism explicitly confirms it via preferred_engine.
    Changing recipe's preferred_engine would change routing.
    """
    from videoforge.engine.recipes import get_recipe
    r = get_recipe("dual-chart")
    assert r is not None
    assert r.preferred_engine == "manim"
    node = _make_node(SceneKind.CHART, "dual-chart")
    assert pick_engine(node) == Engine(r.preferred_engine)


# ── Recipe → complete orchestration pipeline (end-to-end shape) ───


def test_four_recipes_produce_distinct_outcomes():
    """Each of the 4 showcase recipes produces a unique orchestration signature.

    The signature is (scene_type, engine, entrance) — all 4 must be distinct.
    """
    clear_cache()
    writer = ScriptWriter()
    planner = ScenePlanner()

    recipes = [("screenflow", "comparison"), ("audio-spectrum", "audio-reactive"),
               ("dual-chart", "chart"), ("device-rise", "three-scene")]

    signatures = {}
    for recipe_kind, expected_type in recipes:
        script = writer.write_script(_content(recipe_kind))
        plan = planner.plan_scenes(script, [])
        enrich = [s for s in plan["scenes"] if s.get("recipe_id") == recipe_kind]
        assert len(enrich) == 1, f"Missing recipe scene for {recipe_kind}"
        s = enrich[0]
        sig = (s["type"], s.get("engine_hint"), s["transition_in"], s["transition_out"])
        signatures[recipe_kind] = sig

    # All 4 signatures must be unique
    assert len(set(signatures.values())) == 4, (
        f"Not all recipes produced unique signatures: {signatures}"
    )


# ── Determinism guarantee ──────────────────────────────────────────


def test_entire_orchestration_is_deterministic_across_recipes():
    """Full writer → planner pipeline is deterministic for each recipe."""
    writer = ScriptWriter()
    planner = ScenePlanner()

    for recipe_kind in ("screenflow", "audio-spectrum", "dual-chart", "device-rise"):
        a = planner.plan_scenes(writer.write_script(_content(recipe_kind)), [])
        b = planner.plan_scenes(writer.write_script(_content(recipe_kind)), [])
        assert a == b, f"Non-deterministic orchestration for recipe: {recipe_kind}"
