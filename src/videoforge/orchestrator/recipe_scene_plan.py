"""Multi-scene plans for showcase recipes.

Each recipe can expand into multiple deterministic scenes
when a prompt matches its showcase pattern.
Pure functions: same content + same recipe -> same scene plan.

Consumed by ScriptWriter._expand_showcase_scenes to produce richer
scene graphs from single showcase prompts.
"""

from __future__ import annotations

from typing import Any


def _pluck(content: dict[str, Any], key: str) -> Any:
    """Pluck value from content, checking showcase sub-dict first.

    Consistent with recipe_payload._pluck_from_content — callers can
    provide values in either showcase.{key} or top-level {key}.
    """
    showcase = content.get("showcase", {})
    if isinstance(showcase, dict) and key in showcase:
        return showcase[key]
    return content.get(key)


def get_recipe_scene_plan(
    recipe_id: str, content: dict[str, Any]
) -> list[dict[str, Any]] | None:
    """Return multi-scene expansion for a recipe, or None for default single-scene.

    Each returned scene dict has:
      - title: str
      - text: str (narration content)
      - scene_type: str
      - estimated_duration_seconds: float
      - entrance: str | None
      - exit_: str | None

    Recipes without a multi-scene expander return None -> ScriptWriter
    falls back to the existing single-scene insertion.
    """
    expander = _RECIPE_EXPANDERS.get(recipe_id)
    if expander is None:
        return None
    return expander(content)


def _plan_trajectory_timeline(content: dict[str, Any]) -> list[dict[str, Any]]:
    """Rocket Launches Timeline style: 4 scenes

    1. Title intro with event count
    2. Axis + event markers
    3. Trajectory path draw
    4. Event highlights
    """
    events = _pluck(content, "events") or []
    event_count = len(events) if isinstance(events, list) else 0
    event_text = (
        f"Exploring {event_count} key events on this timeline."
        if event_count > 0
        else "Exploring key events on this timeline."
    )

    return [
        {
            "title": "Timeline Overview",
            "text": event_text,
            "scene_type": "title",
            "estimated_duration_seconds": 3.0,
            "entrance": "fade",
            "exit_": "wipe",
        },
        {
            "title": "Timeline Axis",
            "text": "Setting up the timeline axis with event markers.",
            "scene_type": "timeline",
            "estimated_duration_seconds": 3.0,
            "entrance": "wipe",
            "exit_": "fade",
        },
        {
            "title": "Trajectory Path",
            "text": "Tracing the trajectory along this timeline path.",
            "scene_type": "timeline",
            "estimated_duration_seconds": 3.0,
            "entrance": "path_draw",
            "exit_": "fade",
        },
        {
            "title": "Event Highlights",
            "text": "Highlighting key milestones along the trajectory.",
            "scene_type": "timeline",
            "estimated_duration_seconds": 3.0,
            "entrance": "wipe",
            "exit_": "fade",
        },
    ]


def _plan_dual_chart(content: dict[str, Any]) -> list[dict[str, Any]]:
    """Bar + Line Chart combined style: 4 scenes

    1. Title intro
    2. Bar series grows on axes
    3. Line series overlaid
    4. Combined view with annotation
    """
    return [
        {
            "title": "Chart Overview",
            "text": "Visualizing data with a combined bar and line chart.",
            "scene_type": "title",
            "estimated_duration_seconds": 3.0,
            "entrance": "fade",
            "exit_": "fade",
        },
        {
            "title": "Bar Series",
            "text": "Bar chart showing primary data distribution.",
            "scene_type": "chart",
            "estimated_duration_seconds": 3.0,
            "entrance": "axes_draw",
            "exit_": "none",
        },
        {
            "title": "Line Overlay",
            "text": "Line series overlaid on same axes for comparison.",
            "scene_type": "chart",
            "estimated_duration_seconds": 3.0,
            "entrance": "slide-left",
            "exit_": "none",
        },
        {
            "title": "Combined View",
            "text": "Full combined chart showing both series together.",
            "scene_type": "dual-chart",
            "estimated_duration_seconds": 3.0,
            "entrance": "fade",
            "exit_": "fade",
        },
    ]


def _plan_screenflow(content: dict[str, Any]) -> list[dict[str, Any]]:
    """Product Demo for Presscut style: always 4 scenes

    1. Context intro
    2-3. Feature callout scenes (always 2 for deterministic structure)
    4. Feature summary + CTA

    Content screenshots feed the recipe_payload but don't change scene count.
    This keeps the scene graph deterministic regardless of available assets.
    """
    return [
        {
            "title": "Product Demo",
            "text": "Walking through the product demo.",
            "scene_type": "title",
            "estimated_duration_seconds": 3.0,
            "entrance": "fade",
            "exit_": "slide-right",
        },
        {
            "title": "Feature 1",
            "text": "Exploring feature 1 of this product.",
            "scene_type": "comparison",
            "estimated_duration_seconds": 4.0,
            "entrance": "slide_in_right",
            "exit_": "slide_out_left",
        },
        {
            "title": "Feature 2",
            "text": "Exploring feature 2 of this product.",
            "scene_type": "comparison",
            "estimated_duration_seconds": 4.0,
            "entrance": "slide_in_right",
            "exit_": "slide_out_left",
        },
        {
            "title": "Summary",
            "text": "That covers the key features of this product.",
            "scene_type": "outro",
            "estimated_duration_seconds": 3.0,
            "entrance": "fade",
            "exit_": "fade",
        },
    ]


def _plan_launch_promo(content: dict[str, Any]) -> list[dict[str, Any]]:
    """Launch Video on X style: 4 scenes

    1. Hook/title
    2. Product reveal
    3. Feature highlights
    4. CTA / launch date
    """
    title = _pluck(content, "title") or "Launch"

    return [
        {
            "title": "Hook",
            "text": f"Introducing {title}.",
            "scene_type": "title",
            "estimated_duration_seconds": 3.0,
            "entrance": "fade",
            "exit_": "zoom",
        },
        {
            "title": "Product Reveal",
            "text": f"Here is what {title} looks like.",
            "scene_type": "promo",
            "estimated_duration_seconds": 4.0,
            "entrance": "zoom",
            "exit_": "slide-left",
        },
        {
            "title": "Features",
            "text": "Key features designed for you.",
            "scene_type": "promo",
            "estimated_duration_seconds": 4.0,
            "entrance": "slide-left",
            "exit_": "fade",
        },
        {
            "title": "Call to Action",
            "text": "Get started today.",
            "scene_type": "outro",
            "estimated_duration_seconds": 3.0,
            "entrance": "slide_in_right",
            "exit_": "none",
        },
    ]


def _plan_device_rise(content: dict[str, Any]) -> list[dict[str, Any]]:
    """Apple-Style Device Rise Animation style: 3 scenes

    1. Setup / background
    2. Device rise animation
    3. Screen content settle
    """
    device_type = _pluck(content, "device_type") or "device"

    return [
        {
            "title": "Device Showcase",
            "text": f"Introducing the {device_type}.",
            "scene_type": "title",
            "estimated_duration_seconds": 2.0,
            "entrance": "fade",
            "exit_": "fade",
        },
        {
            "title": "Device Rise",
            "text": f"Watch the {device_type} rise into view.",
            "scene_type": "three-scene",
            "estimated_duration_seconds": 4.0,
            "entrance": "device_rise_in",
            "exit_": "none",
        },
        {
            "title": "Screen Highlight",
            "text": "Exploring the screen content in detail.",
            "scene_type": "three-scene",
            "estimated_duration_seconds": 3.0,
            "entrance": "fade",
            "exit_": "device_fall_out",
        },
    ]


_RECIPE_EXPANDERS: dict[str, Any] = {
    "trajectory-timeline": _plan_trajectory_timeline,
    "dual-chart": _plan_dual_chart,
    "screenflow": _plan_screenflow,
    "launch-promo": _plan_launch_promo,
    "device-rise": _plan_device_rise,
}
