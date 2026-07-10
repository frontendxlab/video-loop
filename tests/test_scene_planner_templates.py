"""ScenePlanner template-based planning tests.

Validates that plan_from_template() and plan_from_templates()
generate correct scene graphs directly from templates:
  - Single-scene templates produce 1 scene
  - Multi-scene templates produce correct scene count + types
  - Engine hints flow from template definition
  - Transition overrides work
  - Multiple templates combine with contiguous frame numbering
"""

from __future__ import annotations

import pytest

from videoforge.engine.recipes import clear_cache
from videoforge.orchestrator.scene_planner import ScenePlanner
from videoforge.orchestrator.template_registry import clear_template_cache


def _content(**extra: object) -> dict:
    return {
        "title": "Test Video",
        "body": "This is the body content for template planning tests.",
        "showcase": {"kind": "test", **extra},
    }


@pytest.fixture(autouse=True)
def _clear_caches():
    """Clear all caches before each test for clean state."""
    clear_cache()
    clear_template_cache()


# ── plan_from_template: single-scene templates ──────────────────────


def test_single_scene_template_produces_one_scene():
    planner = ScenePlanner()
    result = planner.plan_from_template("hero-intro", _content())
    assert len(result["scenes"]) == 1


def test_single_scene_template_correct_type():
    planner = ScenePlanner()
    result = planner.plan_from_template("svg-morph", _content())
    assert result["scenes"][0]["type"] == "svg-morph"


def test_single_scene_template_engine_hint():
    planner = ScenePlanner()
    result = planner.plan_from_template("kinetic-text", _content())
    assert result["scenes"][0]["engine_hint"] == "remotion"


def test_single_scene_template_entrance_from_registry():
    """Entrance should come from recipe registry when not overridden."""
    planner = ScenePlanner()
    result = planner.plan_from_template("document-highlight", _content())
    assert "zoom_in" in result["scenes"][0]["transition_in"]


def test_single_scene_exit_from_registry():
    planner = ScenePlanner()
    result = planner.plan_from_template("document-highlight", _content())
    assert "blur_out" in result["scenes"][0]["transition_out"]


def test_single_scene_override_duration():
    planner = ScenePlanner()
    result = planner.plan_from_template(
        "hero-intro", _content(), duration_seconds=10.0
    )
    assert result["scenes"][0]["duration_seconds"] == 10.0


def test_single_scene_override_entrance():
    planner = ScenePlanner()
    result = planner.plan_from_template(
        "hero-intro", _content(), entrance="slide-left"
    )
    assert result["scenes"][0]["transition_in"] == "slide-left"


def test_single_scene_override_exit():
    planner = ScenePlanner()
    result = planner.plan_from_template(
        "hero-intro", _content(), exit_="zoom"
    )
    assert result["scenes"][0]["transition_out"] == "zoom"


# ── plan_from_template: multi-scene templates ───────────────────────


def test_multi_scene_template_screenflow_produces_four_scenes():
    planner = ScenePlanner()
    result = planner.plan_from_template("screenflow", _content())
    assert len(result["scenes"]) == 4


def test_multi_scene_template_dual_chart_produces_four_scenes():
    planner = ScenePlanner()
    result = planner.plan_from_template("dual-chart", _content())
    assert len(result["scenes"]) == 4


def test_multi_scene_template_device_rise_produces_three_scenes():
    planner = ScenePlanner()
    result = planner.plan_from_template("device-rise", _content())
    assert len(result["scenes"]) == 3


def test_multi_scene_launch_promo_produces_four_scenes():
    planner = ScenePlanner()
    result = planner.plan_from_template("launch-promo", _content())
    assert len(result["scenes"]) == 4


def test_multi_scene_trajectory_timeline_produces_four_scenes():
    planner = ScenePlanner()
    result = planner.plan_from_template("trajectory-timeline", _content())
    assert len(result["scenes"]) == 4


def test_multi_scene_screenflow_scene_types():
    planner = ScenePlanner()
    result = planner.plan_from_template("screenflow", _content())
    types = [s["type"] for s in result["scenes"]]
    assert types == ["title", "comparison", "comparison", "outro"]


def test_multi_scene_dual_chart_scene_types():
    planner = ScenePlanner()
    result = planner.plan_from_template("dual-chart", _content())
    types = [s["type"] for s in result["scenes"]]
    assert types == ["title", "chart", "chart", "dual-chart"]


def test_multi_scene_device_rise_scene_types():
    planner = ScenePlanner()
    result = planner.plan_from_template("device-rise", _content())
    types = [s["type"] for s in result["scenes"]]
    assert types == ["title", "three-scene", "three-scene"]


def test_multi_scene_entrance_from_plan():
    """Multi-scene plan entrance should take priority over recipe entrance."""
    planner = ScenePlanner()
    result = planner.plan_from_template("screenflow", _content())
    # Title scene fades, first comparison has slide_in_right from plan
    assert result["scenes"][0]["transition_in"] == "fade"
    assert result["scenes"][1]["transition_in"] == "slide_in_right"
    assert result["scenes"][2]["transition_in"] == "slide_in_right"


def test_multi_scene_exit_from_plan():
    planner = ScenePlanner()
    result = planner.plan_from_template("device-rise", _content())
    # Last scene has device_fall_out from plan
    assert result["scenes"][-1]["transition_out"] == "device_fall_out"
    # Middle scene has device_rise_in
    assert result["scenes"][1]["transition_in"] == "device_rise_in"


def test_multi_scene_engine_hint():
    planner = ScenePlanner()
    result = planner.plan_from_template("dual-chart", _content())
    for s in result["scenes"]:
        assert s["engine_hint"] == "manim"


def test_multi_scene_scene_index_and_total():
    planner = ScenePlanner()
    result = planner.plan_from_template("device-rise", _content())
    for i, s in enumerate(result["scenes"]):
        assert s["scene_index"] == i
        assert s["total_scenes"] == 3


def test_multi_scene_frame_continuity():
    """Frame numbers must be contiguous across multi-scene plan."""
    planner = ScenePlanner()
    result = planner.plan_from_template("screenflow", _content())
    for i in range(len(result["scenes"]) - 1):
        current_end = (result["scenes"][i]["start_frame"]
                       + result["scenes"][i]["duration_frames"])
        next_start = result["scenes"][i + 1]["start_frame"]
        assert current_end == next_start, (
            f"Frame gap between scene {i} and {i+1}: "
            f"{current_end} != {next_start}"
        )


# ── plan_from_template: error handling ──────────────────────────────


def test_unknown_template_raises_value_error():
    planner = ScenePlanner()
    with pytest.raises(ValueError, match="Unknown template"):
        planner.plan_from_template("nonexistent", _content())


def test_empty_template_id_raises_value_error():
    planner = ScenePlanner()
    with pytest.raises(ValueError, match="Unknown template"):
        planner.plan_from_template("", _content())


# ── plan_from_template: output shape ────────────────────────────────


def test_plan_output_has_expected_keys():
    planner = ScenePlanner()
    result = planner.plan_from_template("hero-intro", _content())
    assert "version" in result
    assert "fps" in result
    assert "resolution" in result
    assert "scenes" in result
    assert result["video_type"] == "TEMPLATE"


def test_scene_has_required_keys():
    planner = ScenePlanner()
    result = planner.plan_from_template("screenflow", _content())
    required = {"id", "type", "duration_seconds", "duration_frames",
                "start_frame", "title", "text", "transition_in",
                "transition_out", "template_id", "engine_hint"}
    for s in result["scenes"]:
        missing = required - set(s.keys())
        assert not missing, f"Scene missing keys: {missing}"


# ── plan_from_templates: template composition ───────────────────────


def test_plan_from_templates_combines_two_templates():
    planner = ScenePlanner()
    result = planner.plan_from_templates(
        {"intro": "hero-intro", "outro": "overlay-cta"},
        _content(),
    )
    assert len(result["scenes"]) == 2  # 1 + 1


def test_plan_from_templates_combines_multi_and_single():
    planner = ScenePlanner()
    result = planner.plan_from_templates(
        {"intro": "hero-intro", "body": "screenflow", "outro": "overlay-cta"},
        _content(),
    )
    # hero-intro=1, screenflow=4, overlay-cta=1 = 6
    assert len(result["scenes"]) == 6


def test_plan_from_templates_sections_labeled():
    planner = ScenePlanner()
    result = planner.plan_from_templates(
        {"a": "hero-intro", "b": "svg-morph"},
        _content(),
    )
    assert result["scenes"][0]["section"] == "a"
    assert result["scenes"][1]["section"] == "b"


def test_plan_from_templates_contiguous_frames():
    """Frame numbers must be contiguous across template boundaries."""
    planner = ScenePlanner()
    result = planner.plan_from_templates(
        {"intro": "hero-intro", "body": "screenflow"},
        _content(),
    )
    for i in range(len(result["scenes"]) - 1):
        current_end = (result["scenes"][i]["start_frame"]
                       + result["scenes"][i]["duration_frames"])
        next_start = result["scenes"][i + 1]["start_frame"]
        assert current_end == next_start, (
            f"Frame gap between scene {i} and {i+1} "
            f"(sections {result['scenes'][i].get('section')} -> "
            f"{result['scenes'][i+1].get('section')}): "
            f"{current_end} != {next_start}"
        )


def test_plan_from_templates_scene_ids_sequential():
    """Scene IDs must be sequential across all templates."""
    planner = ScenePlanner()
    result = planner.plan_from_templates(
        {"a": "hero-intro", "b": "device-rise"},
        _content(),
    )
    ids = [s["id"] for s in result["scenes"]]
    assert ids == list(range(1, len(ids) + 1))


def test_plan_from_templates_video_type():
    planner = ScenePlanner()
    result = planner.plan_from_templates(
        {"intro": "hero-intro"}, _content(),
    )
    assert result["video_type"] == "MULTI_TEMPLATE"


def test_plan_from_templates_default_fps():
    planner = ScenePlanner()
    result = planner.plan_from_templates(
        {"intro": "hero-intro"}, _content(),
    )
    assert result["fps"] == 30
    assert result["resolution"] == [1920, 1080]


def test_plan_from_templates_custom_fps():
    planner = ScenePlanner()
    result = planner.plan_from_templates(
        {"intro": "hero-intro"}, _content(),
        fps=60, resolution=[3840, 2160],
    )
    assert result["fps"] == 60
    assert result["resolution"] == [3840, 2160]


def test_plan_from_templates_per_section_override():
    """Per-section overrides should only affect that section."""
    planner = ScenePlanner()
    result = planner.plan_from_templates(
        {"intro": "hero-intro", "body": "screenflow"},
        _content(),
        intro={"duration_seconds": 8.0},
    )
    assert result["scenes"][0]["duration_seconds"] == 8.0  # overridden
    # screenflow scenes should use plan defaults
    for s in result["scenes"][1:]:
        assert s["duration_seconds"] in (3.0, 4.0)


# ── Determinism ─────────────────────────────────────────────────────


def test_plan_from_template_is_deterministic():
    planner = ScenePlanner()
    c = _content()
    a = planner.plan_from_template("screenflow", c)
    b = planner.plan_from_template("screenflow", c)
    assert a == b


def test_plan_from_templates_is_deterministic():
    planner = ScenePlanner()
    c = _content()
    tm = {"intro": "hero-intro", "body": "screenflow"}
    a = planner.plan_from_templates(tm, c)
    b = planner.plan_from_templates(tm, c)
    assert a == b


def test_plan_from_templates_different_content_different():
    """Different content for content-aware templates should differ."""
    planner = ScenePlanner()
    c0 = _content(events=[])
    c3 = _content(events=["a", "b", "c"])
    a = planner.plan_from_template("trajectory-timeline", c0)
    b = planner.plan_from_template("trajectory-timeline", c3)
    # Both have 4 scenes but text differs
    assert len(a["scenes"]) == len(b["scenes"]) == 4
    assert a["scenes"][0]["text"] != b["scenes"][0]["text"]
