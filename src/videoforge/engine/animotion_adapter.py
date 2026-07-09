"""Animotion-facing theme adapter stub.

Future web renderer should consume this normalized shape, not invent its own.
"""

from __future__ import annotations

from typing import Any

from videoforge.design_tokens import animotion_theme_stub


def get_animotion_render_config() -> dict[str, Any]:
    return {
        "renderer": "animotion",
        "theme": animotion_theme_stub(),
    }
