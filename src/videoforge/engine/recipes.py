"""Recipe registry — deterministic showcase-inspired video patterns.

Layer between study-driven recipe definitions and the director/orchestrator.
Each recipe encodes: allowed inputs, scene kind mapping, engine preference,
transition pack, and review hints.

Consumed by:
  - director (to route recipe → scene kind → engine)
  - orchestrator (to expand recipe into scene graph)
  - UI recipe picker (to show options + inputs)

Deterministic: same registry file → same Recipe tuples, every time.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_RecipeRegistryCache: tuple[Recipe, ...] | None = None


@dataclass(frozen=True)
class RecipeInput:
    """An allowed input field for a recipe."""

    key: str
    type: str  # "string" | "number" | "boolean" | "array"
    required: bool
    description: str


@dataclass(frozen=True)
class ReviewHint:
    """Hints for reviewing scenes rendered from this recipe."""

    check: str
    severity: str  # "error" | "warn" | "info"


@dataclass(frozen=True)
class Recipe:
    """A deterministic recipe for a showcase-inspired video pattern."""

    id: str
    name: str
    description: str
    scene_kind: str
    preferred_engine: str
    fallback_engines: tuple[str, ...]
    allowed_inputs: tuple[RecipeInput, ...]
    entrance: str
    exit: str
    tags: tuple[str, ...]
    review_hints: tuple[ReviewHint, ...]

    def all_engines(self) -> tuple[str, ...]:
        """Preferred engine first, then fallbacks."""
        return (self.preferred_engine, *self.fallback_engines)


def _dict_to_input(d: dict[str, Any]) -> RecipeInput:
    return RecipeInput(
        key=str(d["key"]),
        type=str(d["type"]),
        required=bool(d["required"]),
        description=str(d.get("description", "")),
    )


def _dict_to_hint(d: dict[str, Any]) -> ReviewHint:
    return ReviewHint(
        check=str(d["check"]),
        severity=str(d.get("severity", "info")),
    )


def _dict_to_recipe(d: dict[str, Any]) -> Recipe:
    return Recipe(
        id=str(d["id"]),
        name=str(d["name"]),
        description=str(d.get("description", "")),
        scene_kind=str(d["scene_kind"]),
        preferred_engine=str(d["preferred_engine"]),
        fallback_engines=tuple(str(e) for e in d.get("fallback_engines", [])),
        allowed_inputs=tuple(
            _dict_to_input(i) for i in d.get("allowed_inputs", [])
        ),
        entrance=str(d.get("entrance", "fade_in")),
        exit=str(d.get("exit", "fade_out")),
        tags=tuple(str(t) for t in d.get("tags", [])),
        review_hints=tuple(
            _dict_to_hint(h) for h in d.get("review_hints", [])
        ),
    )


def _validate_registry(recipes: tuple[Recipe, ...]) -> None:
    """Validate recipe registry invariants. Raises ValueError on failure."""
    seen_ids: set[str] = set()
    for r in recipes:
        if r.id in seen_ids:
            raise ValueError(f"Duplicate recipe id: {r.id}")
        seen_ids.add(r.id)

        if not r.scene_kind:
            raise ValueError(f"Recipe {r.id} missing scene_kind")

        valid_input_types = {"string", "number", "boolean", "array"}
        for inp in r.allowed_inputs:
            if inp.type not in valid_input_types:
                raise ValueError(
                    f"Recipe {r.id} input {inp.key}: "
                    f"invalid type '{inp.type}'"
                )

        valid_severities = {"error", "warn", "info"}
        for hint in r.review_hints:
            if hint.severity not in valid_severities:
                raise ValueError(
                    f"Recipe {r.id} hint: invalid severity '{hint.severity}'"
                )


def load_recipes(path: str | Path | None = None) -> tuple[Recipe, ...]:
    """Load recipe registry from JSON file. Deterministic.

    Returns sorted tuple of Recipe frozen dataclasses.
    Cached on first call when path is None (default config path).
    """
    global _RecipeRegistryCache
    if _RecipeRegistryCache is not None and path is None:
        return _RecipeRegistryCache

    p = (
        Path(path)
        if path
        else Path(__file__).resolve().parents[3] / "config" / "recipe_registry.json"
    )
    if not p.exists():
        raise FileNotFoundError(f"Recipe registry not found: {p}")

    data = json.loads(p.read_text())
    version = data.get("version", 0)
    if version < 1:
        raise ValueError(f"Unsupported recipe registry version: {version}")

    recipes = tuple(
        sorted(
            (_dict_to_recipe(r) for r in data.get("recipes", [])),
            key=lambda r: r.id,
        )
    )
    _validate_registry(recipes)

    if path is None:
        _RecipeRegistryCache = recipes
    return recipes


def get_recipe(recipe_id: str, path: str | Path | None = None) -> Recipe | None:
    """Lookup a single recipe by id. Returns None if not found."""
    for r in load_recipes(path):
        if r.id == recipe_id:
            return r
    return None


def recipes_by_scene_kind(
    scene_kind: str, path: str | Path | None = None
) -> tuple[Recipe, ...]:
    """Return all recipes that map to the given scene kind."""
    return tuple(
        r for r in load_recipes(path) if r.scene_kind == scene_kind
    )


def recipes_by_engine(
    engine: str, path: str | Path | None = None
) -> tuple[Recipe, ...]:
    """Return all recipes that prefer the given engine."""
    return tuple(
        r for r in load_recipes(path) if r.preferred_engine == engine
    )


def recipes_by_tag(tag: str, path: str | Path | None = None) -> tuple[Recipe, ...]:
    """Return all recipes tagged with the given tag."""
    return tuple(
        r for r in load_recipes(path) if tag in r.tags
    )


def clear_cache() -> None:
    """Clear the module-level recipe cache (for testing)."""
    global _RecipeRegistryCache
    _RecipeRegistryCache = None
