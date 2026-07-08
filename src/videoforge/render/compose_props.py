"""Compose inputProps for Remotion from pipeline output."""

from __future__ import annotations

from typing import Any


class ComposeProps:
    """Builds the inputProps JSON dict from the pipeline's scene plan and asset maps."""

    @staticmethod
    def build(scene_plan: dict, audio_map: dict, image_map: dict) -> dict[str, Any]:
        props: dict[str, Any] = {}

        scenes = scene_plan.get("scenes", [])
        props["scenes"] = scenes

        audio_tracks = []
        for scene in scenes:
            scene_id = scene.get("id")
            audio_file = audio_map.get(str(scene_id)) or audio_map.get(scene_id)
            if audio_file:
                audio_tracks.append({"sceneId": scene_id, "src": audio_file})
        props["audioTracks"] = audio_tracks

        captions = scene_plan.get("captions", [])
        props["captions"] = captions

        voice = scene_plan.get("voice", {})
        props["voice"] = voice

        style = scene_plan.get("style", {})
        props["style"] = style

        return props
