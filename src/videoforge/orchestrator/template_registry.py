"""Template registry — first-class templates for scene graph generation.

A Template wraps recipe metadata + optional multi-scene expansion
into a unified abstraction. Enables planner to generate rich scene
graphs directly from template selections without script writer.

Consumed by:
  - ScenePlanner (plan_from_template, plan_from_templates)
  - UI template picker (to show available templates + inputs)

Deterministic: same registry → same templates, every time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from videoforge.engine.recipes import Recipe, RecipeInput, get_recipe, load_recipes
from videoforge.orchestrator.recipe_scene_plan import get_recipe_scene_plan


@dataclass(frozen=True)
class SceneTemplate:
    """A template for generating scene graphs from a recipe.

    Wraps recipe metadata + optional multi-scene expander into
    a single abstraction the planner uses to build scene graphs.
    """

    id: str
    name: str
    description: str
    scene_kind: str
    preferred_engine: str
    fallback_engines: tuple[str, ...]
    entrance: str
    exit: str
    allowed_inputs: tuple[RecipeInput, ...]
    tags: tuple[str, ...]
    has_multi_scene_plan: bool = False

    def expand(self, content: dict[str, Any]) -> list[dict[str, Any]] | None:
        """Expand template into scene graph (multi-scene) or None (single scene).

        Each returned scene dict matches recipe_scene_plan format:
          title, text, scene_type, estimated_duration_seconds, entrance, exit_.
        Returns None when template has no multi-scene expander — caller
        should treat as single-scene template.
        """
        if not self.has_multi_scene_plan:
            return None
        return get_recipe_scene_plan(self.id, content)


_TemplateCache: dict[str, SceneTemplate] | None = None

# Recipe ids known to have multi-scene expanders in recipe_scene_plan.py
_MULTI_SCENE_RECIPES: frozenset[str] = frozenset({
    "trajectory-timeline",
    "dual-chart",
    "screenflow",
    "launch-promo",
    "device-rise",
})


def _recipe_to_template(recipe: Recipe) -> SceneTemplate:
    return SceneTemplate(
        id=recipe.id,
        name=recipe.name,
        description=recipe.description,
        scene_kind=recipe.scene_kind,
        preferred_engine=recipe.preferred_engine,
        fallback_engines=recipe.fallback_engines,
        entrance=recipe.entrance,
        exit=recipe.exit,
        allowed_inputs=recipe.allowed_inputs,
        tags=recipe.tags,
        has_multi_scene_plan=recipe.id in _MULTI_SCENE_RECIPES,
    )


def load_templates() -> dict[str, SceneTemplate]:
    """Load all templates from recipe registry.

    Returns dict keyed by template id (same as recipe id).
    Cached on first call to avoid re-parsing registry JSON.
    Deterministic: same registry → same templates, every time.
    """
    global _TemplateCache
    if _TemplateCache is not None:
        return _TemplateCache

    recipes = load_recipes()
    templates: dict[str, SceneTemplate] = {}
    for r in recipes:
        templates[r.id] = _recipe_to_template(r)

    _TemplateCache = templates
    return templates


def get_template(template_id: str) -> SceneTemplate | None:
    """Lookup a single template by id. Returns None if not found."""
    return load_templates().get(template_id)


def templates_by_scene_kind(scene_kind: str) -> tuple[SceneTemplate, ...]:
    """Return all templates that map to the given scene kind."""
    return tuple(
        t for t in load_templates().values()
        if t.scene_kind == scene_kind
    )


def templates_by_engine(engine: str) -> tuple[SceneTemplate, ...]:
    """Return all templates preferring the given engine."""
    return tuple(
        t for t in load_templates().values()
        if t.preferred_engine == engine
    )


def templates_by_tag(tag: str) -> tuple[SceneTemplate, ...]:
    """Return all templates tagged with the given tag."""
    return tuple(
        t for t in load_templates().values()
        if tag in t.tags
    )


def clear_template_cache() -> None:
    """Clear template cache (for testing)."""
    global _TemplateCache
    _TemplateCache = None
    from videoforge.engine.recipes import clear_cache as _clear_recipes
    _clear_recipes()
