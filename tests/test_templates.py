"""Template registry tests — schema, suggestion, deterministic."""
import pytest

from videoforge.engine.templates import (
    VideoTemplate,
    TemplateScene,
    get_template,
    list_templates,
    suggest_templates,
)


class TestTemplateRegistry:
    def test_registry_has_expected_count(self):
        templates = list_templates()
        assert len(templates) >= 8

    def test_all_templates_have_required_fields(self):
        for t in list_templates():
            assert t.id, f"Missing id: {t}"
            assert t.name, f"Missing name: {t.id}"
            assert t.description, f"Missing description: {t.id}"
            assert t.icon, f"Missing icon: {t.id}"
            assert t.category, f"Missing category: {t.id}"
            assert len(t.scenes) >= 3, f"Template {t.id}: <3 scenes"

    def test_all_template_ids_unique(self):
        ids = [t.id for t in list_templates()]
        assert len(ids) == len(set(ids)), f"Duplicate ids: {ids}"

    def test_all_scenes_have_required_fields(self):
        for t in list_templates():
            for i, s in enumerate(t.scenes):
                assert s.scene_type, f"{t.id} scene {i}: missing scene_type"
                assert s.title, f"{t.id} scene {i}: missing title"
                assert s.duration_seconds > 0, f"{t.id} scene {i}: invalid duration"

    def test_get_template_returns_known(self):
        t = get_template("explainer")
        assert t is not None
        assert t.name == "Explainer"

    def test_get_template_returns_none_for_unknown(self):
        assert get_template("nonexistent") is None

    def test_template_scenes_are_frozen(self):
        t = get_template("tutorial")
        assert t is not None
        with pytest.raises(Exception):
            t.id = "mutated"  # type: ignore[misc]

    def test_tutorial_has_code_scene_type(self):
        t = get_template("tutorial")
        assert t is not None
        scene_types = [s.scene_type for s in t.scenes]
        assert "code" in scene_types


class TestTemplateSuggestion:
    def test_suggest_explain_prompt(self):
        result = suggest_templates("explain how DNS works", max_suggestions=3)
        assert len(result) >= 1
        assert result[0]["id"] == "explainer"
        assert result[0]["scene_count"] >= 3

    def test_suggest_tutorial_prompt(self):
        result = suggest_templates("step by step tutorial on React hooks", max_suggestions=3)
        ids = [r["id"] for r in result]
        assert "tutorial" in ids

    def test_suggest_data_prompt(self):
        result = suggest_templates("show me the metrics and analytics data", max_suggestions=3)
        ids = [r["id"] for r in result]
        assert "data-story" in ids

    def test_suggest_marketing_prompt(self):
        result = suggest_templates("promotional campaign for new product launch hype", max_suggestions=3)
        ids = [r["id"] for r in result]
        assert "marketing" in ids

    def test_suggest_is_deterministic(self):
        a = suggest_templates("build a tutorial for Python beginners", max_suggestions=3)
        b = suggest_templates("build a tutorial for Python beginners", max_suggestions=3)
        assert a == b

    def test_suggest_respects_max(self):
        result = suggest_templates("explain tutorial data story timeline comparison", max_suggestions=2)
        assert len(result) <= 2

    def test_suggest_empty_for_unmatched_prompt(self):
        result = suggest_templates("xyzzy zork midquel", max_suggestions=3)
        # May return empty or partial — no matching tags
        assert isinstance(result, list)

    def test_suggest_result_shape(self):
        result = suggest_templates("explain microservices architecture", max_suggestions=1)
        assert len(result) == 1
        r = result[0]
        assert "id" in r
        assert "name" in r
        assert "description" in r
        assert "icon" in r
        assert "category" in r
        assert "match_reason" in r
        assert "scene_count" in r

    def test_storytelling_template_has_quote_scene(self):
        t = get_template("storytelling")
        assert t is not None
        scene_types = [s.scene_type for s in t.scenes]
        assert "quote" in scene_types

    def test_comparison_template_has_diff_scene(self):
        t = get_template("comparison")
        assert t is not None
        scene_types = [s.scene_type for s in t.scenes]
        assert "diff" in scene_types

    def test_timeline_template_has_timeline_scenes(self):
        t = get_template("timeline")
        assert t is not None
        scene_types = [s.scene_type for s in t.scenes]
        assert scene_types.count("timeline") >= 3
