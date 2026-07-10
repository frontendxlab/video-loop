"""Design token parity tests — verify all 3 engines consume identical theme.

Covers: token loading, cross-engine color parity, generated scene code/config,
and one integration-style test for mixed-engine routing coherence.
"""

from __future__ import annotations

from videoforge.design_tokens import (
    animotion_theme_stub,
    chart_tokens,
    device_tokens,
    glass_tokens,
    hud_tokens,
    load_design_tokens,
    manim_theme,
    remotion_style_defaults,
    showcase_tokens,
)
from videoforge.engine.animotion_adapter import get_animotion_render_config
from videoforge.engine.manim_renderer import (
    generate_chart_scene,
    generate_graph_scene,
    generate_timeline_scene,
    scene_to_manim_code,
)
from videoforge.engine.models import SceneDefinition, SceneType
from videoforge.engine.ir import Engine, NarrationSpec, SceneKind, SceneNode, WordTiming
from videoforge.engine.director import pick_engine


# ── Unit: token loading ──────────────────────────────────────────────────


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


# ── Unit: full cross-engine color parity ─────────────────────────────────


def test_all_engines_share_exact_color_values():
    """Every named color in design-tokens.json must be consistent across
    Remotion defaults, Manim theme, and Animotion theme."""
    tokens = load_design_tokens()
    remotion = remotion_style_defaults()
    manim = manim_theme()
    animotion = tokens["animotion"]["theme"]

    # Primary / accent
    assert remotion["primaryColor"] == tokens["theme"]["primaryColor"]
    assert manim["primaryColor"] == tokens["theme"]["primaryColor"]
    assert animotion["accentColor"] == tokens["theme"]["primaryColor"]

    # Background base
    assert manim["backgroundColor"] == tokens["theme"]["background"]["base"]
    assert animotion["deckBackground"] == tokens["theme"]["background"]["base"]

    # Text colors
    assert manim["textColor"] == tokens["theme"]["text"]["primary"]
    assert animotion["textColor"] == tokens["theme"]["text"]["primary"]
    assert manim["mutedTextColor"] == tokens["theme"]["text"]["muted"]

    # Code colors
    assert manim["codeBackground"] == tokens["code"]["theme"]["background"]
    assert manim["codeTextColor"] == tokens["code"]["theme"]["text"]

    # Font stack
    assert manim["headingFont"] == tokens["fonts"]["heading"]["family"]
    assert animotion["headingFont"] == tokens["fonts"]["heading"]["family"]
    assert manim["bodyFont"] == tokens["fonts"]["body"]["family"]
    assert animotion["bodyFont"] == tokens["fonts"]["body"]["family"]
    assert manim["monoFont"] == tokens["fonts"]["mono"]["family"]
    assert animotion["monoFont"] == tokens["fonts"]["mono"]["family"]

    # Animotion code theme
    assert animotion["codeTheme"] == tokens["code"]["theme"]["name"]

    # Secondary / accent colors
    assert manim["secondaryColor"] == tokens["theme"]["accent"]["secondary"]
    assert manim["successColor"] == tokens["theme"]["accent"]["success"]
    assert manim["errorColor"] == tokens["theme"]["accent"]["error"]


# ── Unit: animotion config fidelity ──────────────────────────────────────


def test_animotion_render_config_matches_token_section():
    """get_animotion_render_config must return the exact animotion theme
    values plus the tokenSource marker."""
    tokens = load_design_tokens()
    config = get_animotion_render_config()
    theme = config["theme"]

    for key in ("deckBackground", "panelBackground", "textColor", "accentColor",
                "codeTheme", "headingFont", "bodyFont", "monoFont"):
        assert theme[key] == tokens["animotion"]["theme"][key], (
            f"animotion.{key} mismatch: {theme[key]} != {tokens['animotion']['theme'][key]}"
        )
    assert theme["tokenSource"] == "config/design-tokens.json"


# ── Unit: VideoDefinition embeds shared tokens ───────────────────────────


def test_video_definition_carries_token_defaults():
    """VideoDefinition.primary_color, .font, .code_theme must come from
    design tokens, not hardcoded constants."""
    from videoforge.engine.models import VideoDefinition, AudioTrack, WordTiming as LegacyWordTiming
    tokens = load_design_tokens()
    video = VideoDefinition(
        title="test",
        scenes=[],
        audioTracks=[],
        captions=[],
    )
    assert video.primary_color == tokens["theme"]["primaryColor"]
    assert video.font == tokens["fonts"]["body"]["family"]
    assert video.code_theme == tokens["code"]["theme"]["name"]

    # Verify style in remotion props matches
    props = video.to_remotion_props()
    assert props["style"]["primaryColor"] == tokens["theme"]["primaryColor"]
    assert props["style"]["font"] == tokens["fonts"]["body"]["family"]
    assert props["style"]["codeTheme"] == tokens["code"]["theme"]["name"]


# ── Unit: chart + timeline generators use tokens ─────────────────────────


def test_chart_generator_uses_shared_theme():
    code = generate_chart_scene(
        data=[{"label": "A", "value": 10}],
        chart_type="bar",
    )
    assert "THEME_PRIMARY" in code
    assert "THEME_SECONDARY" in code
    assert "THEME_BODY_FONT" in code
    assert "THEME_TEXT" in code
    assert "THEME_HEADING_FONT" in code


def test_timeline_generator_uses_shared_theme():
    code = generate_timeline_scene(
        events=[{"label": "Start", "date": "2020"}],
    )
    assert "THEME_TEXT" in code
    assert "THEME_SECONDARY" in code
    assert "THEME_PRIMARY" in code
    assert "THEME_MUTED" in code
    assert "THEME_BODY_FONT" in code


# ── Integration: mixed-engine scene routing with token consistency ────────


def test_mixed_engine_scenes_all_reference_same_tokens():
    """Build a mixed-engine scene set (Remotion + Manim + Animotion),
    verify every scene's rendered config or generated code references the
    shared design-tokens.json values — not hardcoded strings."""
    tokens = load_design_tokens()
    primary = tokens["theme"]["primaryColor"]
    bg = tokens["theme"]["background"]["base"]
    body_font = tokens["fonts"]["body"]["family"]
    mono_font = tokens["fonts"]["mono"]["family"]
    code_text = tokens["code"]["theme"]["text"]
    code_bg = tokens["code"]["theme"]["background"]

    # --- Remotion scene (via to_remotion_props) ---
    from videoforge.engine.models import VideoDefinition
    remotion_scene = SceneDefinition(
        type=SceneType.CODE, duration=90, title="Code Demo",
        code="const x = 1;", lang="js",
    )
    outro_scene = SceneDefinition(
        type=SceneType.TITLE, duration=60, title="The End",
    )
    video = VideoDefinition(
        title="Mixed Engine Demo",
        scenes=[remotion_scene, outro_scene],
        audioTracks=[],
        captions=[],
    )
    props = video.to_remotion_props()
    assert props["style"]["primaryColor"] == primary
    assert props["style"]["font"] == body_font

    # --- Manim scene (via scene_to_manim_code) ---
    manim_code_scene = SceneDefinition(
        type=SceneType.CODE, duration=90, title="Manim Code",
        code="let y = 2;", lang="ts",
    )
    code = scene_to_manim_code(manim_code_scene)
    assert f'config.background_color = "{bg}"' in code
    assert f'THEME_BODY_FONT = "{body_font}"' in code
    assert f'THEME_MONO_FONT = "{mono_font}"' in code
    assert f'THEME_CODE_TEXT = "{code_text}"' in code
    assert f'THEME_CODE_BG = "{code_bg}"' in code

    # --- Animotion scene (via get_animotion_render_config) ---
    animotion_cfg = get_animotion_render_config()
    assert animotion_cfg["theme"]["accentColor"] == primary
    assert animotion_cfg["theme"]["deckBackground"] == bg
    assert animotion_cfg["theme"]["bodyFont"] == body_font
    assert animotion_cfg["theme"]["monoFont"] == mono_font
    assert animotion_cfg["theme"]["codeTheme"] == tokens["code"]["theme"]["name"]
    assert animotion_cfg["theme"]["textColor"] == tokens["theme"]["text"]["primary"]

    # Cross-check: all 3 engines agree on primary color
    assert props["style"]["primaryColor"] == primary
    assert animotion_cfg["theme"]["accentColor"] == primary
    assert f'THEME_PRIMARY = "{primary}"' in code


def test_mixed_engine_scenes_routable_and_renderable():
    """IR-level test: route different scene kinds to different engines,
    then verify each produces output that uses shared tokens.

    Exercises full deterministic layer without Remotion/Manim binaries.
    """
    import json
    from videoforge.engine.ir_adapters import node_to_scene_definition
    tokens = load_design_tokens()
    primary = tokens["theme"]["primaryColor"]

    scene_specs = [
        (SceneKind.CODE, {}, Engine.REMOTION),
        (SceneKind.DIFF, {}, Engine.REMOTION),
        (SceneKind.CHART, {}, Engine.MANIM),
        (SceneKind.TIMELINE, {}, Engine.MANIM),
        (SceneKind.DIAGRAM, {}, Engine.REMOTION),
        (SceneKind.MAP3D, {}, Engine.MANIM),
        (SceneKind.TITLE, {}, Engine.REMOTION),
        (SceneKind.DIAGRAM, {"layout": "math_graph"}, Engine.MANIM),
    ]

    for kind, payload, expected_engine in scene_specs:
        pstr = json.dumps(payload, sort_keys=True)
        node = SceneNode(
            id=f"s_{kind.value}",
            kind=kind,
            payload=pstr,
            engine_hint=Engine.REMOTION,  # placeholder, overwritten by pick_engine
            duration_frames=90,
            narration=NarrationSpec("t", (), "estimated"),
        )
        engine = pick_engine(node)
        assert engine == expected_engine, f"{kind.value} expected {expected_engine.value} got {engine.value}"

        if engine == Engine.MANIM:
            sd = node_to_scene_definition(node)
            if kind == SceneKind.CHART:
                code = generate_chart_scene(data=[])
            elif kind == SceneKind.TIMELINE:
                code = generate_timeline_scene(events=[])
            elif kind == SceneKind.DIAGRAM and payload.get("layout") == "math_graph":
                code = generate_graph_scene(nodes=[{"id": "a", "label": "A"}], edges=[])
            else:
                code = scene_to_manim_code(sd)

            assert f'THEME_PRIMARY = "{primary}"' in code, (
                f"Manim scene {kind.value} missing THEME_PRIMARY"
            )
            assert 'THEME_TEXT' in code, f"Manim scene {kind.value} missing THEME_TEXT"


# ── Unit: HUD tokens ──────────────────────────────────────────────────────


def test_hud_tokens_loaded():
    t = hud_tokens()
    assert t["scanline"] == "rgba(255, 255, 255, 0.03)"
    assert t["grid"] == "rgba(148, 163, 184, 0.06)"
    assert t["reticle"] == "#4A90D9"
    assert isinstance(t["reticleOpacity"], (int, float))
    assert t["cornerBracket"] == "rgba(148, 163, 184, 0.35)"
    dr = t["dataReadout"]
    assert isinstance(dr, dict)
    assert dr["accent"] == "#4A90D9"
    assert dr["label"] == "#94A3B8"
    assert dr["value"] == "#E5EEF8"


# ── Unit: Glass tokens ────────────────────────────────────────────────────


def test_glass_tokens_loaded():
    g = glass_tokens()
    assert g["backdropBlur"] == 12
    assert g["background"] == "rgba(30, 41, 59, 0.6)"
    assert g["border"] == "rgba(255, 255, 255, 0.08)"
    assert g["highlight"] == "rgba(255, 255, 255, 0.03)"
    assert "shadow" in g
    assert g["borderRadius"] == 16


# ── Unit: Device tokens ───────────────────────────────────────────────────


def test_device_tokens_loaded():
    d = device_tokens()
    for form in ("phone", "tablet", "laptop", "monitor"):
        props = d[form]
        assert isinstance(props, dict), f"device.{form} not a dict"
        assert "shadow" in props
        assert "screenRadius" in props or "bezel" in props
    assert d["phone"]["bezel"] == "#1C1C1E"
    assert d["laptop"]["bezel"] == "#1A1A1A"
    assert d["monitor"]["bezel"] == "#222222"


# ── Unit: Chart tokens ────────────────────────────────────────────────────


def test_chart_tokens_loaded():
    c = chart_tokens()
    assert c["gridLine"] == "rgba(255, 255, 255, 0.08)"
    assert c["axisLine"] == "rgba(255, 255, 255, 0.3)"
    assert c["axisLabel"] == "#94A3B8"
    assert isinstance(c["series"], list)
    assert len(c["series"]) >= 4
    assert c["areaFill"] == "rgba(74, 144, 217, 0.12)"
    assert isinstance(c["barRadius"], (int, float))
    assert isinstance(c["dotRadius"], (int, float))
    assert isinstance(c["lineWidth"], (int, float))


# ── Unit: Showcase tokens ─────────────────────────────────────────────────


def test_showcase_tokens_loaded():
    s = showcase_tokens()
    assert "overlayGradient" in s
    assert "heroOverlay" in s
    assert isinstance(s["cta"], dict)
    assert s["cta"]["text"] == "#FFFFFF"
    assert s["cta"]["borderRadius"] == 12
    assert s["accentGlow"] == "rgba(74, 144, 217, 0.25)"
    assert s["particle"] == "#38BDF8"
    assert s["sparkle"] == "#FACC15"
