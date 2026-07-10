"""Director routing tests — every kind x layout combo."""

from __future__ import annotations

import json

from videoforge.engine.director import pick_engine, load_routing_table
from videoforge.engine.ir import Engine, NarrationSpec, SceneKind, SceneNode, WordTiming


def _node(kind: SceneKind, payload: dict | None = None) -> SceneNode:
    return SceneNode(
        id=f"n_{kind.value}",
        kind=kind,
        payload=json.dumps(payload or {}, sort_keys=True),
        engine_hint=Engine.REMOTION,
        duration_frames=90,
        narration=NarrationSpec("t", (), "estimated"),
    )


def test_code_routes_to_remotion():
    assert pick_engine(_node(SceneKind.CODE)) == Engine.REMOTION


def test_diff_routes_to_remotion():
    assert pick_engine(_node(SceneKind.DIFF)) == Engine.REMOTION


def test_bullets_routes_to_remotion():
    assert pick_engine(_node(SceneKind.BULLETS)) == Engine.REMOTION


def test_title_routes_to_remotion():
    assert pick_engine(_node(SceneKind.TITLE)) == Engine.REMOTION


def test_comparison_routes_to_remotion():
    assert pick_engine(_node(SceneKind.COMPARISON)) == Engine.REMOTION


def test_quote_routes_to_remotion():
    assert pick_engine(_node(SceneKind.QUOTE)) == Engine.REMOTION


def test_outro_routes_to_remotion():
    assert pick_engine(_node(SceneKind.OUTRO)) == Engine.REMOTION


def test_mindmap_routes_to_remotion():
    assert pick_engine(_node(SceneKind.MINDMAP)) == Engine.REMOTION


def test_diagram_default_routes_to_remotion():
    assert pick_engine(_node(SceneKind.DIAGRAM, {"layout": "default"})) == Engine.REMOTION


def test_diagram_math_graph_routes_to_manim():
    assert pick_engine(_node(SceneKind.DIAGRAM, {"layout": "math_graph"})) == Engine.MANIM


def test_diagram_interactive_routes_to_animotion():
    assert pick_engine(_node(SceneKind.DIAGRAM, {"interactive": True, "layout": "default"})) == Engine.ANIMOTION


def test_diagram_interactive_false_routes_to_remotion():
    assert pick_engine(_node(SceneKind.DIAGRAM, {"interactive": False})) == Engine.REMOTION


def test_diagram_no_layout_routes_to_remotion():
    assert pick_engine(_node(SceneKind.DIAGRAM, {})) == Engine.REMOTION


def test_chart_routes_to_manim():
    assert pick_engine(_node(SceneKind.CHART)) == Engine.MANIM


def test_timeline_routes_to_manim():
    assert pick_engine(_node(SceneKind.TIMELINE)) == Engine.MANIM


def test_map3d_routes_to_manim():
    assert pick_engine(_node(SceneKind.MAP3D)) == Engine.MANIM


def test_dual_chart_routes_to_manim():
    assert pick_engine(_node(SceneKind.DUAL_CHART)) == Engine.MANIM


def test_three_scene_routes_to_manim():
    assert pick_engine(_node(SceneKind.THREE_SCENE)) == Engine.MANIM


def test_screenflow_routes_to_remotion():
    assert pick_engine(_node(SceneKind.SCREENFLOW)) == Engine.REMOTION


def test_overlay_cta_routes_to_remotion():
    assert pick_engine(_node(SceneKind.OVERLAY_CTA)) == Engine.REMOTION


def test_audio_reactive_routes_to_remotion():
    assert pick_engine(_node(SceneKind.AUDIO_REACTIVE)) == Engine.REMOTION


def test_document_highlight_routes_to_remotion():
    assert pick_engine(_node(SceneKind.DOCUMENT_HIGHLIGHT)) == Engine.REMOTION


def test_svg_morph_routes_to_remotion():
    assert pick_engine(_node(SceneKind.SVG_MORPH)) == Engine.REMOTION


def test_kinetic_text_routes_to_remotion():
    assert pick_engine(_node(SceneKind.KINETIC_TEXT)) == Engine.REMOTION


def test_canvas_composite_routes_to_remotion():
    assert pick_engine(_node(SceneKind.CANVAS_COMPOSITE)) == Engine.REMOTION


def test_real_estate_routes_to_remotion():
    assert pick_engine(_node(SceneKind.REAL_ESTATE)) == Engine.REMOTION


def test_promo_routes_to_remotion():
    assert pick_engine(_node(SceneKind.PROMO)) == Engine.REMOTION


def test_routing_table_loads():
    table = load_routing_table()
    assert table.get("code") == Engine.REMOTION
    assert table.get("chart") == Engine.MANIM
    assert table.get("diagram:layout:math_graph") == Engine.MANIM
    assert table.get("diagram:layout:default") == Engine.REMOTION
    assert table.get("diagram:interactive:true") == Engine.ANIMOTION
    assert table.get("dual-chart") == Engine.MANIM
    assert table.get("three-scene") == Engine.MANIM
    assert table.get("screenflow") == Engine.REMOTION
    assert table.get("overlay-cta") == Engine.REMOTION
    assert table.get("audio-reactive") == Engine.REMOTION
    assert table.get("document-highlight") == Engine.REMOTION
    assert table.get("svg-morph") == Engine.REMOTION
    assert table.get("kinetic-text") == Engine.REMOTION
    assert table.get("canvas-composite") == Engine.REMOTION
    assert table.get("real-estate") == Engine.REMOTION
    assert table.get("promo") == Engine.REMOTION


def test_pick_engine_is_deterministic():
    n = _node(SceneKind.CHART)
    assert pick_engine(n) == pick_engine(n)
