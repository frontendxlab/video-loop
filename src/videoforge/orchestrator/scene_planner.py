from __future__ import annotations

from typing import Any

TRANSITIONS = [
    "fade",
    "slide-left",
    "slide-right",
    "zoom",
    "wipe",
    "dissolve",
    "flip",
    "scale",
    "rotate",
    "blur",
    "morph",
    "glitch",
    "warp",
]

# Showcase scene types get bespoke entrance transitions by rule.
SHOWCASE_ENTRANCE: dict[str, str] = {
    "svg-morph": "morph",
    "kinetic-text": "scale",
    "canvas-composite": "glitch",
    "real-estate": "slide-right",
    "promo": "zoom",
    "three-scene": "flip",
    "hero-intro": "zoom",
    "screenflow": "slide-right",
    "trajectory-timeline": "wipe",
}


class ScenePlanner:
    def plan_scenes(self, script: dict[str, Any], audio_metadata: list[dict[str, Any]]) -> dict[str, Any]:
        script_scenes = script.get("scenes", [])
        fps = 30
        resolution = [1920, 1080]
        video_type = script.get("video_type", "PR_WALKTHROUGH")

        planned_scenes: list[dict[str, Any]] = []
        current_frame = 0

        for i, scene in enumerate(script_scenes):
            duration_seconds = scene.get("estimated_duration_seconds", 4.0)
            duration_frames = int(duration_seconds * fps)

            # Recipe-enriched scenes carry entrance/exit from recipe registry.
            # Prefer recipe entrance over SHOWCASE_ENTRANCE lookup.
            entrance_override = scene.get("entrance")
            exit_override = scene.get("exit_")
            transition_type = self._select_transition(
                i, scene.get("scene_type", ""),
                entrance_override=entrance_override,
            )
            transit_out = exit_override or self._select_next_transition(i, script_scenes)

            base: dict[str, Any] = {
                "id": i + 1,
                "type": scene.get("scene_type", "title"),
                "duration_seconds": duration_seconds,
                "duration_frames": duration_frames,
                "start_frame": current_frame,
                "title": scene.get("title", ""),
                "text": scene.get("text", ""),
                "transition_in": transition_type,
                "transition_out": transit_out,
            }

            # Carry recipe enrichment through so downstream (compose_props,
            # ir_adapter) can build recipe-aware SceneNode payloads.
            if scene.get("recipe_id"):
                base["recipe_id"] = scene["recipe_id"]
                base["engine_hint"] = scene.get("engine_hint", "remotion")
                base["recipe_payload"] = scene.get("recipe_payload", {})
                # Use recipe-provided entrance (already applied above) and exit
                base["transition_in"] = transition_type
                base["transition_out"] = transit_out

            planned_scenes.append(base)

            current_frame += duration_frames

        if not planned_scenes:
            planned_scenes.append({
                "id": 1,
                "type": "title",
                "duration_seconds": 4.0,
                "duration_frames": 4 * fps,
                "start_frame": 0,
                "title": script.get("title", "Video"),
                "text": "",
                "transition_in": "fade",
                "transition_out": "none",
            })

        return {
            "version": 1,
            "video_type": video_type,
            "fps": fps,
            "resolution": resolution,
            "scenes": planned_scenes,
        }

    def _select_transition(self, index: int, scene_type: str,
                           entrance_override: str | None = None) -> str:
        # Recipe-driven entrance takes highest priority
        if index > 0 and entrance_override:
            return entrance_override if entrance_override in TRANSITIONS or entrance_override in (
                "slide_out_left", "fade_out", "blur_out", "count_up",
                "device_rise_in", "device_fall_out", "axes_draw",
                "stars_fade_in", "zoom_out_deep",
                "fade_in_3d", "fade_out_3d", "slide_in_right",
                "morph_out", "path_draw",
            ) else "fade"
        # Showcase types get a bespoke entrance transition second
        if index > 0 and scene_type in SHOWCASE_ENTRANCE:
            return SHOWCASE_ENTRANCE[scene_type]
        return TRANSITIONS[index % (len(TRANSITIONS) - 2) + 1] if index > 0 else "fade"

    def _select_next_transition(self, index: int, scenes: list[dict[str, Any]]) -> str:
        next_idx = index + 1
        if next_idx >= len(scenes):
            return "none"
        t = TRANSITIONS[(next_idx) % (len(TRANSITIONS) - 2) + 1]
        return t
