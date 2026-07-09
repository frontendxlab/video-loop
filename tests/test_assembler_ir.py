"""Engine-agnostic assembler wiring — render_scenes accepts VideoProject IR."""

from __future__ import annotations

import inspect

from videoforge.engine.renderer import render_scenes, _ir_scene_props
from videoforge.engine.ir import (
    Engine, NarrationSpec, SceneKind, SceneNode, VideoProject, WordTiming,
)
from videoforge.engine.director import pick_engine


def _project() -> VideoProject:
    n0 = SceneNode(
        id="s0", kind=SceneKind.TITLE,
        payload='{"title":"Hi","text":"hello"}',
        engine_hint=Engine.REMOTION, duration_frames=90,
        narration=NarrationSpec("hello", (WordTiming("hello", 0, 400),), "estimated"),
    )
    n1 = SceneNode(
        id="s1", kind=SceneKind.CHART,
        payload='{"title":"Chart"}',
        engine_hint=Engine.MANIM, duration_frames=120,
        narration=NarrationSpec("chart", (), "estimated"),
    )
    return VideoProject("T", (n0, n1), 30, 1920, 1080)


def test_render_scenes_accepts_video_project():
    sig = inspect.signature(render_scenes)
    ann = str(sig.parameters["video"].annotation)
    assert "VideoProject" in ann or "VideoDefinition" in ann


def test_ir_scene_props_builds_remotion_props():
    p = _project()
    props = _ir_scene_props(p, 0)
    assert props["scenes"][0]["type"] == "title"
    assert props["scenes"][0]["duration"] == 90
    assert props["scenes"][0]["wordTimestamps"][0]["text"] == "hello"


def test_director_routes_ir_scene_to_correct_engine():
    p = _project()
    assert pick_engine(p.scenes[0]) == Engine.REMOTION
    assert pick_engine(p.scenes[1]) == Engine.MANIM


def test_ir_scene_props_includes_payload_fields():
    n = SceneNode(
        id="s0", kind=SceneKind.CODE,
        payload='{"code":"print(1)","lang":"python","highlightLines":[2]}',
        engine_hint=Engine.REMOTION, duration_frames=60,
        narration=NarrationSpec("t", (), "estimated"),
    )
    p = VideoProject("T", (n,), 30, 1920, 1080)
    props = _ir_scene_props(p, 0)
    sc = props["scenes"][0]
    assert sc["code"] == "print(1)"
    assert sc["lang"] == "python"
    assert sc["highlightLines"] == [2]
