"""FastAPI endpoint for recipe registry — exposes all recipes from config."""

from __future__ import annotations

from fastapi import APIRouter

from videoforge.engine.recipes import load_recipes

router = APIRouter(prefix="/api/recipes", tags=["recipes"])


def _serialize_recipe(r) -> dict:
    return {
        "id": r.id,
        "name": r.name,
        "description": r.description,
        "sceneKind": r.scene_kind,
        "preferredEngine": r.preferred_engine,
        "fallbackEngines": list(r.fallback_engines),
        "allowedInputs": [
            {"key": i.key, "type": i.type, "required": i.required, "description": i.description}
            for i in r.allowed_inputs
        ],
        "entrance": r.entrance,
        "exit": r.exit,
        "tags": list(r.tags),
    }


@router.get("")
async def list_recipes():
    """Return all recipes from the registry."""
    recipes = load_recipes()
    return [_serialize_recipe(r) for r in recipes]
