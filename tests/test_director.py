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


def test_diagram_no_layout_routes_to_remotion():
    assert pick_engine(_node(SceneKind.DIAGRAM, {})) == Engine.REMOTION


def test_chart_routes_to_manim():
    assert pick_engine(_node(SceneKind.CHART)) == Engine.MANIM


def test_timeline_routes_to_manim():
    assert pick_engine(_node(SceneKind.TIMELINE)) == Engine.MANIM


def test_map3d_routes_to_manim():
    assert pick_engine(_node(SceneKind.MAP3D)) == Engine.MANIM


def test_routing_table_loads():
    table = load_routing_table()
    assert table.get("code") == Engine.REMOTION
    assert table.get("chart") == Engine.MANIM
    assert table.get("diagram:math_graph") == Engine.MANIM
    assert table.get("diagram:default") == Engine.REMOTION


def test_pick_engine_is_deterministic():
    n = _node(SceneKind.CHART)
    assert pick_engine(n) == pick_engine(n)
