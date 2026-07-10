"""Artifact generation — thumbnails, sampled frames, best-effort previews."""

from videoforge.artifacts.generator import (
    generate_scene_artifacts,
    generate_scene_thumbnail,
    generate_sampled_frame,
    generate_batch_scene_artifacts,
)

__all__ = [
    "generate_batch_scene_artifacts",
    "generate_scene_artifacts",
    "generate_scene_thumbnail",
    "generate_sampled_frame",
]
