"""Recipe payload builder — construct scene payload from recipe + content.

Bridges recipe registry into scene graph construction. Each recipe defines
allowed_inputs; this module maps content fields into recipe-shaped payload
and attaches recipe metadata (entrance, exit, engine hint) to the scene dict.
Deterministic: same recipe + same content → same payload.
"""

from __future__ import annotations

from typing import Any

from videoforge.engine.recipes import Recipe, get_recipe


def build_recipe_payload(
    content: dict[str, Any],
    recipe_id: str,
) -> dict[str, Any]:
    """Build scene-enrichment dict from a recipe id + user content.

    Returns keys that should be merged into the scene dict after
    _detect_showcase_pattern:
      - recipe_id
      - recipe_name
      - entrance
      - exit
      - engine_hint       (overrides default scene-kind routing)
      - recipe_payload    (resolved payload with recipe-shaped keys)

    All non-required inputs get None / empty defaults so the payload
    shape is deterministic even when content omits them.
    """
    recipe = get_recipe(recipe_id)
    if recipe is None:
        return {}

    resolved: dict[str, Any] = {}
    for inp in recipe.allowed_inputs:
        val = _pluck_from_content(content, inp.key)
        if val is not None:
            resolved[inp.key] = val
        elif inp.required:
            resolved[inp.key] = _default_for_type(inp.type)
        else:
            resolved[inp.key] = None

    return {
        "recipe_id": recipe.id,
        "recipe_name": recipe.name,
        "entrance": recipe.entrance,
        "exit_": recipe.exit,
        "engine_hint": recipe.preferred_engine,
        "recipe_payload": resolved,
    }


def _pluck_from_content(content: dict[str, Any], key: str) -> Any:
    """Pluck value from content dict, checking showcase sub-dict first."""
    showcase = content.get("showcase", {})
    if isinstance(showcase, dict) and key in showcase:
        return showcase[key]
    return content.get(key)


def _default_for_type(t: str) -> Any:
    return {
        "string": "",
        "number": 0,
        "boolean": False,
        "array": [],
    }.get(t, None)
