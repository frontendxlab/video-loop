"""Manim generator tests — graph/chart/timeline code generation."""

from __future__ import annotations

import ast

from videoforge.engine.manim_renderer import (
    generate_chart_scene,
    generate_graph_scene,
    generate_timeline_scene,
)


def _parses(code: str) -> bool:
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def test_graph_scene_generates_valid_python():
    code = generate_graph_scene(
        nodes=[{"id": "a", "label": "Node A"}, {"id": "b", "label": "Node B"}],
        edges=[("a", "b")],
        layout="dot",
    )
    assert _parses(code)
    assert "class GraphScene" in code
    assert "Graph(" in code
    assert "dot" in code


def test_graph_scene_deterministic():
    args = (
        [{"id": "a", "label": "A"}, {"id": "b", "label": "B"}],
        [("a", "b")],
    )
    a = generate_graph_scene(*args)
    b = generate_graph_scene(*args)
    assert a == b


def test_chart_bar_generates_valid_python():
    code = generate_chart_scene(
        [{"label": "Q1", "value": 10}, {"label": "Q2", "value": 25}],
        chart_type="bar",
    )
    assert _parses(code)
    assert "BarChart" in code


def test_chart_line_generates_valid_python():
    code = generate_chart_scene(
        [{"label": "Q1", "value": 10}, {"label": "Q2", "value": 25}],
        chart_type="line",
    )
    assert _parses(code)
    assert "NumberLine" in code


def test_chart_scene_deterministic():
    data = [{"label": "A", "value": 1}, {"label": "B", "value": 2}]
    assert generate_chart_scene(data, "bar") == generate_chart_scene(data, "bar")
    assert generate_chart_scene(data, "line") == generate_chart_scene(data, "line")


def test_timeline_generates_valid_python():
    code = generate_timeline_scene(
        [{"label": "Start", "date": "2020"}, {"label": "End", "date": "2024"}],
    )
    assert _parses(code)
    assert "NumberLine" in code
    assert "MoveAlongPath" in code


def test_timeline_deterministic():
    events = [{"label": "A", "date": "2020"}, {"label": "B", "date": "2024"}]
    assert generate_timeline_scene(events) == generate_timeline_scene(events)


def test_graph_scene_layout_variants_parse():
    for layout in ("dot", "spring", "circular"):
        code = generate_graph_scene(
            [{"id": "x", "label": "X"}], [], layout=layout,
        )
        assert _parses(code), f"layout {layout} failed to parse"
