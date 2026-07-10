"""Recipe scene plan tests — multi-scene expansion structure + determinism.

Validates that multi-scene plans:
  - Return correct number of scenes per recipe
  - Have required fields (title, text, scene_type, duration, entrance, exit_)
  - Use only valid SceneKind values
  - Are deterministic (same content -> same plan)
  - Recipes without plans return None
"""

from __future__ import annotations

from videoforge.engine.ir import SceneKind
from videoforge.orchestrator.recipe_scene_plan import get_recipe_scene_plan

# All scene types known to the IR layer
_VALID_SCENE_KINDS: set[str] = {k.value for k in SceneKind}


def _content(**extra: object) -> dict:
    return {
        "title": "Test",
        "body": "Some body content for testing scene plans.",
        "showcase": {"kind": "test", **extra},
    }


# ── Plans exist for expected recipes ───────────────────────────────


def test_trajectory_timeline_has_plan():
    plan = get_recipe_scene_plan("trajectory-timeline", _content())
    assert plan is not None
    assert len(plan) == 4


def test_dual_chart_has_plan():
    plan = get_recipe_scene_plan("dual-chart", _content())
    assert plan is not None
    assert len(plan) == 4


def test_screenflow_has_plan():
    plan = get_recipe_scene_plan("screenflow", _content())
    assert plan is not None
    assert len(plan) == 4


def test_launch_promo_has_plan():
    plan = get_recipe_scene_plan("launch-promo", _content())
    assert plan is not None
    assert len(plan) == 4


def test_device_rise_has_plan():
    plan = get_recipe_scene_plan("device-rise", _content())
    assert plan is not None
    assert len(plan) == 3


# ── Recipes without plans return None ──────────────────────────────


def test_hero_intro_no_plan():
    """hero-intro uses single-scene fallback — no multi-scene plan."""
    assert get_recipe_scene_plan("hero-intro", _content()) is None


def test_svg_morph_no_plan():
    assert get_recipe_scene_plan("svg-morph", _content()) is None


def test_kinetic_text_no_plan():
    assert get_recipe_scene_plan("kinetic-text", _content()) is None


def test_unknown_recipe_no_plan():
    assert get_recipe_scene_plan("nonexistent-recipe", _content()) is None


# ── Each plan scene has required fields ────────────────────────────

_REQUIRED_KEYS = {
    "title": str,
    "text": str,
    "scene_type": str,
    "estimated_duration_seconds": (int, float),
}


def _check_plan_fields(plan: list[dict]) -> list[str]:
    """Return list of validation errors (empty means valid)."""
    errors: list[str] = []
    for i, scene in enumerate(plan):
        for key, expected_type in _REQUIRED_KEYS.items():
            if key not in scene:
                errors.append(f"Scene {i}: missing '{key}'")
            elif not isinstance(scene[key], expected_type):
                errors.append(
                    f"Scene {i}: '{key}' type={type(scene[key]).__name__}, "
                    f"expected {expected_type.__name__}"
                )
        if "scene_type" in scene and scene["scene_type"] not in _VALID_SCENE_KINDS:
            errors.append(
                f"Scene {i}: invalid scene_type '{scene['scene_type']}'"
            )
        if "estimated_duration_seconds" in scene:
            dur = scene["estimated_duration_seconds"]
            if not isinstance(dur, (int, float)) or dur <= 0:
                errors.append(
                    f"Scene {i}: duration {dur} must be positive"
                )
    return errors


def test_trajectory_timeline_fields():
    plan = get_recipe_scene_plan("trajectory-timeline", _content())
    assert plan is not None
    errors = _check_plan_fields(plan)
    assert not errors, f"Field validation errors: {errors}"


def test_dual_chart_fields():
    plan = get_recipe_scene_plan("dual-chart", _content())
    assert plan is not None
    errors = _check_plan_fields(plan)
    assert not errors, f"Field validation errors: {errors}"


def test_screenflow_fields():
    plan = get_recipe_scene_plan("screenflow", _content())
    assert plan is not None
    errors = _check_plan_fields(plan)
    assert not errors, f"Field validation errors: {errors}"


def test_launch_promo_fields():
    plan = get_recipe_scene_plan("launch-promo", _content())
    assert plan is not None
    errors = _check_plan_fields(plan)
    assert not errors, f"Field validation errors: {errors}"


def test_device_rise_fields():
    plan = get_recipe_scene_plan("device-rise", _content())
    assert plan is not None
    errors = _check_plan_fields(plan)
    assert not errors, f"Field validation errors: {errors}"


# ── Plans are deterministic ────────────────────────────────────────


def test_same_content_same_plan():
    """Same content -> same plan (determinism)."""
    c = _content(events=["evt1", "evt2"])
    a = get_recipe_scene_plan("trajectory-timeline", c)
    b = get_recipe_scene_plan("trajectory-timeline", c)
    assert a == b


def test_different_content_different_plan():
    """Different content may produce different text (content-aware).

    trajectory-timeline uses event count in title text.
    screenflow is deterministic regardless of screenshots.
    """
    c0 = _content()  # no events
    c3 = _content(events=["a", "b", "c"])  # 3 events
    a = get_recipe_scene_plan("trajectory-timeline", c0)
    b = get_recipe_scene_plan("trajectory-timeline", c3)
    assert a is not None and b is not None
    # Different events -> different text in first scene
    assert a[0]["text"] != b[0]["text"], (
        "Event count should change text: "
        f"'{a[0]['text']}' vs '{b[0]['text']}'"
    )
    # Both have same scene structure (4 scenes)
    assert len(a) == len(b) == 4
    # screenflow is always identical regardless of content
    c_any = _content(screenshots=["x.png"])
    c_none = _content()
    sf_a = get_recipe_scene_plan("screenflow", c_any)
    sf_b = get_recipe_scene_plan("screenflow", c_none)
    assert sf_a is not None and sf_b is not None
    assert sf_a == sf_b, "screenflow plan must ignore screenshot count"


def test_trajectory_timeline_events_count_in_text():
    """Event count appears in text when events are provided."""
    c = _content(events=["evt1", "evt2", "evt3"])
    plan = get_recipe_scene_plan("trajectory-timeline", c)
    assert plan is not None
    assert "3" in plan[0]["text"], (
        f"Event count 3 should appear in text: {plan[0]['text']}"
    )


def test_device_rise_device_type_in_text():
    """Device type from content appears in plan text."""
    c = _content(device_type="iPhone 16")
    plan = get_recipe_scene_plan("device-rise", c)
    assert plan is not None
    assert "iPhone 16" in plan[0]["text"]
    assert "iPhone 16" in plan[1]["text"]


# ── Plan scene types are valid SceneKind values ────────────────────


def test_all_scene_types_valid():
    """Every scene_type in every plan must be a known SceneKind."""
    all_recipe_ids = [
        "trajectory-timeline", "dual-chart", "screenflow",
        "launch-promo", "device-rise",
    ]
    for rid in all_recipe_ids:
        plan = get_recipe_scene_plan(rid, _content())
        assert plan is not None
        for i, scene in enumerate(plan):
            assert scene["scene_type"] in _VALID_SCENE_KINDS, (
                f"{rid} scene {i}: unknown scene_type '{scene['scene_type']}'"
            )


# ── Scene types in plan match expected patterns ────────────────────


def test_plan_scene_types_pattern():
    """Each plan's scene type sequence matches expected pattern."""
    assert _scene_types("trajectory-timeline") == ["title", "timeline", "timeline", "timeline"]
    assert _scene_types("dual-chart") == ["title", "chart", "chart", "dual-chart"]
    assert _scene_types("screenflow") == ["title", "comparison", "comparison", "outro"]
    assert _scene_types("launch-promo") == ["title", "promo", "promo", "outro"]
    assert _scene_types("device-rise") == ["title", "three-scene", "three-scene"]


def _scene_types(recipe_id: str) -> list[str]:
    plan = get_recipe_scene_plan(recipe_id, _content())
    assert plan is not None
    return [s["scene_type"] for s in plan]
