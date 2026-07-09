"""Frozen SceneNode IR — the contract between director and engines.

Layer 1 of the v2 architecture: a typed scene graph with a content hash.
Same IR + same engines → byte-identical video. hash(IR) is the cache key.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from videoforge.engine.models import VideoDefinition


class Engine(str, Enum):
    REMOTION = "remotion"
    MANIM = "manim"
    ANIMOTION = "animotion"


class SceneKind(str, Enum):
    TITLE = "title"
    CODE = "code"
    DIFF = "diff"
    BULLETS = "bullets"
    DIAGRAM = "diagram"
    CHART = "chart"
    TIMELINE = "timeline"
    MAP3D = "map3d"
    COMPARISON = "comparison"
    QUOTE = "quote"
    OUTRO = "outro"
    MINDMAP = "mindmap"


@dataclass(frozen=True)
class WordTiming:
    text: str
    startMs: float
    endMs: float


@dataclass(frozen=True)
class NarrationSpec:
    text: str
    words: tuple[WordTiming, ...]
    source: Literal["forced_align", "exact_synthesis", "estimated"]


@dataclass(frozen=True)
class SceneNode:
    id: str
    kind: SceneKind
    payload: str  # JSON string of resolved deterministic data (frozen)
    engine_hint: Engine
    duration_frames: int
    narration: NarrationSpec

    def content_hash(self) -> str:
        data = asdict(self)
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]

    def payload_dict(self) -> dict[str, Any]:
        return json.loads(self.payload)


@dataclass(frozen=True)
class VideoProject:
    title: str
    scenes: tuple[SceneNode, ...]
    fps: int
    width: int
    height: int

    def content_hash(self) -> str:
        return hashlib.sha256(
            (self.title + "".join(s.content_hash() for s in self.scenes)).encode()
        ).hexdigest()[:16]

    @classmethod
    def from_legacy(cls, video_def: "VideoDefinition") -> "VideoProject":
        """Convert from legacy VideoDefinition to new IR."""
        from videoforge.engine.models import VideoDefinition as VD  # noqa: F811

        VD = video_def.__class__
        type_map = {
            "title": SceneKind.TITLE, "code": SceneKind.CODE,
            "code-walkthrough": SceneKind.CODE, "diff": SceneKind.DIFF,
            "bullet": SceneKind.BULLETS, "diagram": SceneKind.DIAGRAM,
            "comparison": SceneKind.COMPARISON, "outro": SceneKind.OUTRO,
            "mindmap": SceneKind.MINDMAP, "image": SceneKind.TITLE,
            "manim": SceneKind.DIAGRAM,
        }
        scenes = []
        for s in video_def.scenes:
            kind = type_map.get(s.type.value, SceneKind.TITLE)
            engine = (
                Engine(s.renderer)
                if s.renderer in ("remotion", "manim", "animotion")
                else Engine.REMOTION
            )
            words = tuple(
                WordTiming(w.text, w.startMs, w.endMs) for w in s.wordTimestamps
            )
            narration = NarrationSpec(
                text=s.text or s.title, words=words, source="estimated"
            )
            payload = json.dumps(
                {
                    "title": s.title, "subtitle": s.subtitle, "text": s.text,
                    "code": s.code, "lang": s.lang, "points": s.points,
                    "caption": s.caption, "cta": s.cta, "src": s.src,
                    "nodeprefix": s.nodeprefix, "highlightLines": s.highlightLines,
                },
                sort_keys=True,
            )
            scenes.append(
                SceneNode(
                    id=f"scene_{len(scenes)}", kind=kind, payload=payload,
                    engine_hint=engine, duration_frames=s.duration, narration=narration,
                )
            )
        return cls(
            title=video_def.title, scenes=tuple(scenes),
            fps=video_def.fps, width=video_def.width, height=video_def.height,
        )
