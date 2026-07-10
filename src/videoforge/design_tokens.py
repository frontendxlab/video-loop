"""Shared design token loader for all renderers."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


@lru_cache(maxsize=1)
def load_design_tokens() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    return json.loads((root / "config" / "design-tokens.json").read_text(encoding="utf-8"))


def remotion_style_defaults() -> dict[str, str]:
    tokens = load_design_tokens()
    return {
        "primaryColor": tokens["theme"]["primaryColor"],
        "font": tokens["fonts"]["body"]["family"],
        "codeTheme": tokens["code"]["theme"]["name"],
    }


def animotion_theme_stub() -> dict[str, Any]:
    tokens = load_design_tokens()
    theme = dict(tokens["animotion"]["theme"])
    theme["tokenSource"] = "config/design-tokens.json"
    return theme


def manim_theme() -> dict[str, Any]:
    tokens = load_design_tokens()
    return dict(tokens["manim"])


def hud_tokens() -> dict[str, Any]:
    tokens = load_design_tokens()
    return dict(tokens["hud"])


def glass_tokens() -> dict[str, Any]:
    return dict(load_design_tokens()["glass"])


def device_tokens() -> dict[str, Any]:
    return dict(load_design_tokens()["device"])


def chart_tokens() -> dict[str, Any]:
    return dict(load_design_tokens()["chart"])


def showcase_tokens() -> dict[str, Any]:
    return dict(load_design_tokens()["showcase"])
