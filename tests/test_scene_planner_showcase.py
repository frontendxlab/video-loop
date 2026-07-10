"""ScenePlanner showcase transition tests — deterministic rule-based transitions."""

from __future__ import annotations

from videoforge.orchestrator.scene_planner import ScenePlanner, SHOWCASE_ENTRANCE


def _script(scene_types: list[str]) -> dict:
    return {
        "video_type": "SHOWCASE",
        "scenes": [
            {
                "title": f"Scene {i}",
                "text": "content",
                "scene_type": st,
                "estimated_duration_seconds": 4.0,
            }
            for i, st in enumerate(scene_types)
        ],
    }


def test_plan_scenes_preserves_showcase_types():
    planner = ScenePlanner()
    script = _script(["title", "svg-morph", "outro"])
    result = planner.plan_scenes(script, [])
    types = [s["type"] for s in result["scenes"]]
    assert types == ["title", "svg-morph", "outro"]


def test_svg_morph_gets_morph_transition():
    planner = ScenePlanner()
    script = _script(["title", "svg-morph"])
    result = planner.plan_scenes(script, [])
    # Second scene (index 1) with showcase type gets bespoke entrance
    assert result["scenes"][1]["transition_in"] == "morph"


def test_kinetic_text_gets_scale_transition():
    planner = ScenePlanner()
    script = _script(["title", "kinetic-text"])
    result = planner.plan_scenes(script, [])
    assert result["scenes"][1]["transition_in"] == "scale"


def test_canvas_composite_gets_glitch_transition():
    planner = ScenePlanner()
    script = _script(["title", "canvas-composite"])
    result = planner.plan_scenes(script, [])
    assert result["scenes"][1]["transition_in"] == "glitch"


def test_real_estate_gets_slide_right():
    planner = ScenePlanner()
    script = _script(["title", "real-estate"])
    result = planner.plan_scenes(script, [])
    assert result["scenes"][1]["transition_in"] == "slide-right"


def test_promo_gets_zoom_transition():
    planner = ScenePlanner()
    script = _script(["title", "promo"])
    result = planner.plan_scenes(script, [])
    assert result["scenes"][1]["transition_in"] == "zoom"


def test_three_scene_gets_flip_transition():
    planner = ScenePlanner()
    script = _script(["title", "three-scene"])
    result = planner.plan_scenes(script, [])
    assert result["scenes"][1]["transition_in"] == "flip"


def test_first_scene_always_fade_even_if_showcase():
    """First scene always gets fade regardless of type."""
    planner = ScenePlanner()
    script = _script(["svg-morph"])
    result = planner.plan_scenes(script, [])
    assert result["scenes"][0]["transition_in"] == "fade"


def test_non_showcase_type_gets_normal_transition():
    planner = ScenePlanner()
    script = _script(["title", "code"])
    result = planner.plan_scenes(script, [])
    assert result["scenes"][1]["transition_in"] != "fade"
    assert result["scenes"][1]["transition_in"] in (
        "slide-left", "slide-right", "zoom", "wipe",
        "dissolve", "flip", "scale", "rotate", "blur",
        "morph", "glitch", "warp",
    )


def test_showcase_entrance_maps_all_known_showcase_kinds():
    """Every SHOWCASE_ENTRANCE key maps to a valid transition."""
    valid = {"fade", "slide-left", "slide-right", "zoom", "wipe", "dissolve",
             "flip", "scale", "rotate", "blur", "morph", "glitch", "warp"}
    for kind, transition in SHOWCASE_ENTRANCE.items():
        assert transition in valid, (
            f"{kind} -> {transition} is not a valid transition"
        )


def test_showcase_entrance_is_deterministic():
    planner = ScenePlanner()
    script = _script(["title", "kinetic-text", "outro"])
    a = planner.plan_scenes(script, [])
    b = planner.plan_scenes(script, [])
    assert a["scenes"][1]["transition_in"] == b["scenes"][1]["transition_in"]


def test_showcase_durations_preserved():
    planner = ScenePlanner()
    script = {
        "video_type": "SHOWCASE",
        "scenes": [
            {"title": "S1", "text": "a", "scene_type": "title", "estimated_duration_seconds": 3.0},
            {"title": "S2", "text": "b", "scene_type": "svg-morph", "estimated_duration_seconds": 5.0},
            {"title": "S3", "text": "c", "scene_type": "outro", "estimated_duration_seconds": 4.0},
        ],
    }
    result = planner.plan_scenes(script, [])
    assert result["scenes"][1]["duration_seconds"] == 5.0
    assert result["scenes"][1]["type"] == "svg-morph"
