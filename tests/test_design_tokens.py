from __future__ import annotations

from videoforge.design_tokens import animotion_theme_stub, load_design_tokens, manim_theme, remotion_style_defaults
from videoforge.engine.animotion_adapter import get_animotion_render_config
from videoforge.engine.manim_renderer import generate_graph_scene, scene_to_manim_code
from videoforge.engine.models import SceneDefinition, SceneType


def test_design_tokens_load_core_values():
    tokens = load_design_tokens()
    assert tokens["theme"]["primaryColor"] == "#4A90D9"
    assert tokens["fonts"]["mono"]["family"] == "JetBrains Mono"
    assert tokens["code"]["theme"]["name"] == "poimandres"


def test_remotion_and_manim_defaults_stay_in_sync():
    remotion = remotion_style_defaults()
    manim = manim_theme()
    assert remotion["primaryColor"] == manim["primaryColor"]
    assert remotion["font"] == manim["bodyFont"]
    assert remotion["codeTheme"] == load_design_tokens()["animotion"]["theme"]["codeTheme"]


def test_animotion_stub_uses_shared_tokens():
    stub = animotion_theme_stub()
    config = get_animotion_render_config()
    assert config["renderer"] == "animotion"
    assert config["theme"]["accentColor"] == stub["accentColor"] == remotion_style_defaults()["primaryColor"]
    assert config["theme"]["tokenSource"] == "config/design-tokens.json"


def test_scene_to_manim_code_uses_shared_theme_values():
    scene = SceneDefinition(type=SceneType.CODE, duration=90, title="Demo", code="const x = 1;")
    code = scene_to_manim_code(scene)
    assert 'config.background_color = "#0F172A"' in code
    assert 'THEME_MONO_FONT = "JetBrains Mono"' in code
    assert "THEME_CODE_TEXT" in code


def test_graph_generator_uses_shared_theme_values():
    code = generate_graph_scene(nodes=[{"id": "a", "label": "A"}], edges=[])
    assert "THEME_PRIMARY" in code
    assert "THEME_SECONDARY" in code
    assert "THEME_BODY_FONT" in code
