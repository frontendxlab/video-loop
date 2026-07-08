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

            transition_type = self._select_transition(i, scene.get("scene_type", ""))

            planned_scenes.append({
                "id": i + 1,
                "type": scene.get("scene_type", "title"),
                "duration_seconds": duration_seconds,
                "duration_frames": duration_frames,
                "start_frame": current_frame,
                "title": scene.get("title", ""),
                "text": scene.get("text", ""),
                "transition_in": transition_type,
                "transition_out": self._select_next_transition(i, script_scenes),
            })

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

    def _select_transition(self, index: int, scene_type: str) -> str:
        return TRANSITIONS[index % (len(TRANSITIONS) - 2) + 1] if index > 0 else "fade"

    def _select_next_transition(self, index: int, scenes: list[dict[str, Any]]) -> str:
        next_idx = index + 1
        if next_idx >= len(scenes):
            return "none"
        t = TRANSITIONS[(next_idx) % (len(TRANSITIONS) - 2) + 1]
        return t
