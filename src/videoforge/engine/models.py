"""Typed data models for the video engine — all deterministic."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from videoforge.design_tokens import remotion_style_defaults


_STYLE_DEFAULTS = remotion_style_defaults()


class SceneType(str, Enum):
    TITLE = "title"
    BULLET = "bullet"
    CODE = "code"
    CODE_WALKTHROUGH = "code-walkthrough"
    MINDMAP = "mindmap"
    IMAGE = "image"
    DIAGRAM = "diagram"
    COMPARISON = "comparison"
    DIFF = "diff"
    OUTRO = "outro"
    MANIM = "manim"  # Rendered via Manim (optional engine)
    OVERLAY_CTA = "overlay-cta"  # Rendered with alpha, composited over preceding scene


@dataclass
class WordTiming:
    text: str
    startMs: float
    endMs: float


@dataclass
class AudioTrack:
    src: str
    startFrame: int
    durationFrames: int


@dataclass
class TimelineStep:
    startMs: float
    endMs: float
    durationMs: float
    label: str = ""


@dataclass
class SceneNode:
    id: str
    label: str
    sublabel: str = ""
    children: list[SceneNode] = field(default_factory=list)
    color: str = "#4a90d9"
    timing: WordTiming | None = None


@dataclass
class SceneDefinition:
    """A single scene in the video — fully deterministic."""
    type: SceneType
    duration: int  # frames
    title: str = ""
    subtitle: str = ""
    text: str = ""
    code: str = ""
    lang: str = ""
    points: list[str] = field(default_factory=list)
    caption: str = ""
    cta: str = ""
    src: str = ""
    wordTimestamps: list[WordTiming] = field(default_factory=list)
    sceneStartFrame: int = 0
    nodeprefix: str = ""
    root: SceneNode | None = None
    highlightLines: list[int] = field(default_factory=list)
    renderer: str = "remotion"  # "remotion" | "manim" — which engine renders this scene
    manim_code: str = ""  # Manim Python script (populated when renderer="manim")


@dataclass
class VideoDefinition:
    """Complete video definition — deterministic input."""
    title: str
    scenes: list[SceneDefinition]
    audioTracks: list[AudioTrack]
    captions: list[WordTiming]
    voice: str = "alba"
    fps: int = 30
    width: int = 1920
    height: int = 1080
    primary_color: str = _STYLE_DEFAULTS["primaryColor"]
    font: str = _STYLE_DEFAULTS["font"]
    code_theme: str = _STYLE_DEFAULTS["codeTheme"]

    def total_frames(self) -> int:
        return sum(s.duration for s in self.scenes)

    def total_seconds(self) -> float:
        return self.total_frames() / self.fps

    def content_hash(self) -> str:
        import hashlib
        import json
        props = self.to_remotion_props()
        props["fps"] = self.fps
        props["width"] = self.width
        props["height"] = self.height
        data = json.dumps(props, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def to_remotion_props(self) -> dict[str, Any]:
        """Convert to Remotion inputProps JSON."""
        scenes_json = []
        for s in self.scenes:
            sd: dict[str, Any] = {
                "type": s.type.value,
                "duration": s.duration,
                "wordTimestamps": [{"text": w.text, "startMs": w.startMs, "endMs": w.endMs} for w in s.wordTimestamps],
                "sceneStartFrame": s.sceneStartFrame,
            }
            if s.title: sd["title"] = s.title
            if s.subtitle: sd["subtitle"] = s.subtitle
            if s.text: sd["text"] = s.text
            if s.code: sd["code"] = s.code
            if s.lang: sd["lang"] = s.lang
            if s.points: sd["points"] = s.points
            if s.caption: sd["caption"] = s.caption
            if s.cta: sd["cta"] = s.cta
            if s.src: sd["src"] = s.src
            if s.nodeprefix: sd["nodeprefix"] = s.nodeprefix
            if s.highlightLines: sd["highlightLines"] = s.highlightLines
            scenes_json.append(sd)

        return {
            "title": self.title,
            "scenes": scenes_json,
            "audioTracks": [{"src": a.src, "startFrame": a.startFrame, "durationFrames": a.durationFrames} for a in self.audioTracks],
            "captions": [{"text": c.text, "startMs": c.startMs, "endMs": c.endMs} for c in self.captions],
            "voice": self.voice,
            "style": {"primaryColor": self.primary_color, "font": self.font, "codeTheme": self.code_theme},
        }
