"""Template registry tests — loading, expansion, filtering, determinism.

Validates that SceneTemplate dataclass wraps recipe data correctly,
multi-scene flag matches known expanders, expand() returns expected
plans, and query functions (by_kind, by_engine, by_tag) work.
"""

from __future__ import annotations

from videoforge.engine.recipes import clear_cache
from videoforge.orchestrator.template_registry import (
    SceneTemplate,
    clear_template_cache,
    get_template,
    load_templates,
    templates_by_engine,
    templates_by_scene_kind,
    templates_by_tag,
)


def _content(**extra: object) -> dict:
    return {
        "title": "Test",
        "body": "Some body content for testing template expansions.",
        "showcase": {"kind": "test", **extra},
    }


# ── Template loading ────────────────────────────────────────────────


def test_load_templates_returns_dict():
    templates = load_templates()
    assert isinstance(templates, dict)
    assert len(templates) > 0


def test_load_templates_all_are_scene_templates():
    for t in load_templates().values():
        assert isinstance(t, SceneTemplate)


def test_get_template_known():
    t = get_template("hero-intro")
    assert t is not None
    assert t.id == "hero-intro"
    assert isinstance(t.name, str) and t.name
    assert isinstance(t.description, str)


def test_get_template_unknown_returns_none():
    assert get_template("nonexistent-template") is None


def test_get_template_empty_string():
    assert get_template("") is None


# ── Template required fields ────────────────────────────────────────


def test_all_templates_have_scene_kind():
    for tid, t in load_templates().items():
        assert t.scene_kind, f"Template {tid} missing scene_kind"


def test_all_templates_have_preferred_engine():
    for tid, t in load_templates().items():
        assert t.preferred_engine, f"Template {tid} missing preferred_engine"


def test_all_templates_have_entrance():
    for tid, t in load_templates().items():
        assert t.entrance, f"Template {tid} missing entrance"


def test_all_templates_have_exit():
    for tid, t in load_templates().items():
        assert t.exit, f"Template {tid} missing exit"


def test_all_templates_have_allowed_inputs():
    for tid, t in load_templates().items():
        assert isinstance(t.allowed_inputs, tuple)


def test_all_templates_have_tags():
    for tid, t in load_templates().items():
        assert isinstance(t.tags, tuple)


# ── Multi-scene plan flag ───────────────────────────────────────────


def test_multi_scene_templates_have_flag():
    """Recipes known to have multi-scene expanders must be flagged."""
    for tid in ("trajectory-timeline", "dual-chart", "screenflow",
                 "launch-promo", "device-rise"):
        t = get_template(tid)
        assert t is not None, f"Missing template: {tid}"
        assert t.has_multi_scene_plan, (
            f"Template {tid} should have has_multi_scene_plan=True"
        )


def test_single_scene_templates_have_no_flag():
    """Recipes without multi-scene expanders must not be flagged."""
    for tid in ("hero-intro", "svg-morph", "kinetic-text",
                 "audio-spectrum", "overlay-cta"):
        t = get_template(tid)
        assert t is not None, f"Missing template: {tid}"
        assert not t.has_multi_scene_plan, (
            f"Template {tid} should have has_multi_scene_plan=False"
        )


# ── Template expansion ──────────────────────────────────────────────


def test_expand_multi_scene_returns_plan():
    for tid in ("trajectory-timeline", "dual-chart", "screenflow"):
        t = get_template(tid)
        assert t is not None
        plan = t.expand(_content())
        assert plan is not None
        assert len(plan) >= 3  # all multi-scene plans have 3-4 scenes


def test_expand_single_scene_returns_none():
    for tid in ("hero-intro", "svg-morph", "kinetic-text"):
        t = get_template(tid)
        assert t is not None
        assert t.expand(_content()) is None


def test_expand_device_rise_returns_three_scenes():
    t = get_template("device-rise")
    assert t is not None
    plan = t.expand(_content(device_type="iPad"))
    assert plan is not None
    assert len(plan) == 3


def test_expand_launch_promo_returns_four_scenes():
    t = get_template("launch-promo")
    assert t is not None
    plan = t.expand(_content(title="New Product"))
    assert plan is not None
    assert len(plan) == 4


def test_expand_is_deterministic():
    t = get_template("trajectory-timeline")
    assert t is not None
    c = _content(events=["a", "b"])
    a = t.expand(c)
    b = t.expand(c)
    assert a == b


# ── Template queries ────────────────────────────────────────────────


def test_templates_by_scene_kind():
    results = templates_by_scene_kind("title")
    assert len(results) >= 1
    for t in results:
        assert t.scene_kind == "title"


def test_templates_by_scene_kind_unknown():
    assert templates_by_scene_kind("nonexistent-kind") == ()


def test_templates_by_engine():
    remotion_templates = templates_by_engine("remotion")
    assert len(remotion_templates) >= 1
    for t in remotion_templates:
        assert t.preferred_engine == "remotion"


def test_templates_by_engine_unknown():
    assert templates_by_engine("nonexistent-engine") == ()


def test_templates_by_tag():
    results = templates_by_tag("3d")
    assert len(results) >= 1
    for t in results:
        assert "3d" in t.tags


def test_templates_by_tag_unknown():
    assert templates_by_tag("nonexistent-tag") == ()


# ── Cache behavior ──────────────────────────────────────────────────


def test_load_templates_is_cached():
    a = load_templates()
    b = load_templates()
    assert a is b  # same cached object


def test_clear_cache_invalidates():
    a = load_templates()
    clear_template_cache()
    b = load_templates()
    assert a is not b  # new object after clear


def test_get_template_respects_cache():
    clear_template_cache()
    a = get_template("hero-intro")
    b = get_template("hero-intro")
    assert a is b  # from cache

# ── Template engine values are valid ────────────────────────────────


def test_all_engines_are_known():
    known = {"remotion", "manim", "animotion"}
    for t in load_templates().values():
        assert t.preferred_engine in known, (
            f"Template {t.id}: unknown engine '{t.preferred_engine}'"
        )
        for fb in t.fallback_engines:
            assert fb in known, (
                f"Template {t.id}: unknown fallback engine '{fb}'"
            )


# ── Cross-referencing with recipe registry ──────────────────────────


def test_template_count_matches_recipe_count():
    """Template count must match the number of recipes in registry."""
    from videoforge.engine.recipes import load_recipes
    clear_cache()
    recipes = load_recipes()
    templates = load_templates()
    assert len(templates) == len(recipes), (
        f"Template count {len(templates)} != recipe count {len(recipes)}"
    )


def test_every_recipe_has_template():
    from videoforge.engine.recipes import load_recipes
    clear_cache()
    for r in load_recipes():
        t = get_template(r.id)
        assert t is not None, f"Recipe {r.id} has no template"
        assert t.scene_kind == r.scene_kind
        assert t.preferred_engine == r.preferred_engine
        assert t.entrance == r.entrance
        assert t.exit == r.exit
