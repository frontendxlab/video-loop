"""IR adapters — convert SceneNode IR to legacy engine inputs."""

from __future__ import annotations

import json

from videoforge.engine.ir import SceneKind, SceneNode, VideoProject, WordTiming
from videoforge.engine.models import SceneDefinition, SceneType, WordTiming as LegacyWordTiming


_KIND_TO_SCENE_TYPE = {
    SceneKind.TITLE: SceneType.TITLE,
    SceneKind.CODE: SceneType.CODE,
    SceneKind.DIFF: SceneType.DIFF,
    SceneKind.BULLETS: SceneType.BULLET,
    SceneKind.DIAGRAM: SceneType.DIAGRAM,
    SceneKind.CHART: SceneType.DIAGRAM,
    SceneKind.TIMELINE: SceneType.DIAGRAM,
    SceneKind.MAP3D: SceneType.DIAGRAM,
    SceneKind.COMPARISON: SceneType.COMPARISON,
    SceneKind.QUOTE: SceneType.TITLE,
    SceneKind.OUTRO: SceneType.OUTRO,
    SceneKind.MINDMAP: SceneType.MINDMAP,
}


def node_to_scene_definition(node: SceneNode, fps: int = 30) -> SceneDefinition:
    """Convert a SceneNode IR to a legacy SceneDefinition for engine consumption."""
    payload = node.payload_dict()
    scene_type = _KIND_TO_SCENE_TYPE.get(node.kind, SceneType.TITLE)
    return SceneDefinition(
        type=scene_type,
        duration=node.duration_frames,
        title=payload.get("title", ""),
        subtitle=payload.get("subtitle", ""),
        text=node.narration.text or payload.get("text", ""),
        code=payload.get("code", ""),
        lang=payload.get("lang", ""),
        points=payload.get("points", []),
        caption=payload.get("caption", ""),
        cta=payload.get("cta", ""),
        src=payload.get("src", ""),
        nodeprefix=payload.get("nodeprefix", ""),
        highlightLines=payload.get("highlightLines", []),
        wordTimestamps=[
            LegacyWordTiming(w.text, w.startMs, w.endMs)
            for w in node.narration.words
        ],
        renderer=node.engine_hint.value,
    )
