#!/usr/bin/env python3
"""VideoForge CLI — deterministic video generation application.

Usage:
    videoforge plan --topic "..."           # Plan scenes from topic
    videoforge tts --scene scene.json       # Generate TTS audio
    videoforge time --scene scene.json     # Compute frame timing
    videoforge render --video video.json   # Render video
    videoforge review --video video.mp4    # Review quality
    videoforge pipeline --topic "..."      # Full pipeline
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

import typer
from typing_extensions import Annotated

from videoforge.engine.models import (
    AudioTrack,
    SceneDefinition,
    SceneNode,
    SceneType,
    VideoDefinition,
    WordTiming,
)
from videoforge.engine.tts import generate_audio, build_scene_timing
from videoforge.engine.renderer import render_scenes, concatenate_scenes, get_media_info

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("videoforge")

app = typer.Typer(name="videoforge", help="Deterministic video generation engine")


@app.command()
def plan(
    topic: Annotated[str, typer.Option(help="Video topic")],
    output: Annotated[str, typer.Option(help="Output path for scene plan")] = "scenes.json",
    voice: Annotated[str, typer.Option(help="TTS voice")] = "alba",
):
    """Plan scenes from a topic description."""
    # This produces a scene plan with timing placeholders
    # (In production, this would use an LLM for intelligent scene planning)
    logger.info("Planning scenes for: %s", topic)
    plan_data: list[dict[str, Any]] = [
        {"type": "title", "title": topic, "duration": 180, "text": f"Welcome to {topic}."},
    ]
    Path(output).write_text(json.dumps(plan_data, indent=2))
    logger.info("Scene plan written to %s", output)


@app.command()
def tts(
    scene: Annotated[str, typer.Argument(help="Scene JSON file")],
    output: Annotated[str, typer.Option(help="Output dir for audio")] = "audio",
    voice: Annotated[str, typer.Option(help="TTS voice")] = "alba",
    tts_url: Annotated[str, typer.Option(help="TTS server URL")] = "http://localhost:8000",
):
    """Generate TTS audio for a scene."""
    scene_data = json.loads(Path(scene).read_text())
    text = scene_data.get("text", scene_data.get("title", ""))
    if not text:
        logger.error("Scene has no text")
        raise typer.Exit(1)

    out_dir = Path(output)
    out_dir.mkdir(parents=True, exist_ok=True)
    wav_path = out_dir / "audio.wav"

    logger.info("Generating TTS (%d chars)...", len(text))
    result = generate_audio(text, wav_path, voice, tts_url)

    scene_data["wordTimestamps"] = result["word_timestamps"]
    scene_data["duration"] = max(1, int(result["duration_seconds"] * 30))
    Path(scene).write_text(json.dumps(scene_data, indent=2))

    logger.info("Audio: %.1fs, %d words timed", result["duration_seconds"], len(result["word_timestamps"]))


@app.command()
def render(
    video: Annotated[str, typer.Option(help="Video definition JSON")],
    output: Annotated[str, typer.Option(help="Output MP4 path")] = "output.mp4",
    remotion_dir: Annotated[str, typer.Option(help="Remotion project dir")] = "remotion-project",
    build_dir: Annotated[str, typer.Option(help="Build directory")] = "/tmp/vfx-build",
):
    """Render a video from definition."""
    video_def = _load_video_def(video)
    out_dir = Path(build_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Rendering %d scenes (%d frames = %.1fs)...", len(video_def.scenes), video_def.total_frames(), video_def.total_seconds())
    scene_paths = render_scenes(video_def, remotion_dir, out_dir, tmpdir=out_dir / "tmp")

    logger.info("Concatenating %d scenes...", len(scene_paths))
    final = concatenate_scenes(scene_paths, output)
    logger.info("Video: %s", final)

    info = get_media_info(final)
    if "format" in info:
        fmt = info["format"]
        logger.info("Duration: %.1fs, Size: %.1fMB", float(fmt.get("duration", 0)), float(fmt.get("size", 0)) / 1e6)


@app.command()
def review(
    video: Annotated[str, typer.Argument(help="Video file path")],
):
    """Review video quality (L1 frame check)."""
    from videoforge.review.frame_reviewer import FrameReviewer
    fr = FrameReviewer()
    result = fr.check_integrity(video)
    if result.get("passed"):
        logger.info("L1 Review: PASSED — %d frames, 0 issues", result.get("total_frames", 0))
    else:
        logger.error("L1 Review: FAILED — %d issues", len(result.get("issues", [])))
        for issue in result.get("issues", []):
            logger.error("  %s", issue)


@app.command()
def pipeline(
    topic: Annotated[str, typer.Option(help="Video topic")],
    output: Annotated[str, typer.Option(help="Output MP4 path")] = "videos/output.mp4",
    scenes_json: Annotated[str, typer.Option(help="Scene plan JSON")] = "/tmp/scenes.json",
    voice: Annotated[str, typer.Option(help="TTS voice")] = "alba",
    tts_url: Annotated[str, typer.Option(help="TTS URL")] = "http://localhost:8000",
):
    """Full pipeline: plan → TTS → render → review."""
    # Step 1: Plan
    plan.callback(topic=topic, output=scenes_json, voice=voice)

    # Step 2: TTS for each scene
    scenes = json.loads(Path(scenes_json).read_text())
    for i, scene in enumerate(scenes):
        scene_file = Path(f"/tmp/scene_{i:04d}.json")
        scene_file.write_text(json.dumps(scene, indent=2))
        tts.callback(scene=str(scene_file), output=f"/tmp/audio_{i:04d}", voice=voice, tts_url=tts_url)
        scene.update(json.loads(scene_file.read_text()))

    # Step 3: Build video definition
    video_def = _build_video_def(f"Video: {topic}", scenes)

    # Step 4: Render
    video_json = "/tmp/video_def.json"
    Path(video_json).write_text(json.dumps(video_def.to_remotion_props(), indent=2))
    render.callback(video=video_json, output=output)

    # Step 5: Review
    review.callback(video=output)


def _load_video_def(path: str | Path) -> VideoDefinition:
    data = json.loads(Path(path).read_text())
    scenes_list = data.get("scenes", [])
    tracks_list = data.get("audioTracks", [])
    caps_list = data.get("captions", [])

    scenes = []
    for s in scenes_list:
        scene = SceneDefinition(
            type=SceneType(s.get("type", "title")),
            duration=s.get("duration", 90),
            title=s.get("title", ""),
            subtitle=s.get("subtitle", ""),
            text=s.get("text", ""),
            code=s.get("code", ""),
            lang=s.get("lang", ""),
            points=s.get("points", []),
            caption=s.get("caption", ""),
            cta=s.get("cta", ""),
            src=s.get("src", ""),
            nodeprefix=s.get("nodeprefix", ""),
            highlightLines=s.get("highlightLines", []),
            wordTimestamps=[WordTiming(**w) for w in s.get("wordTimestamps", [])],
            sceneStartFrame=s.get("sceneStartFrame", 0),
        )
        if "root" in s:
            scene.root = _load_node(s["root"])
        scenes.append(scene)

    return VideoDefinition(
        title=data.get("title", "Video"),
        scenes=scenes,
        audioTracks=[AudioTrack(**t) for t in tracks_list],
        captions=[WordTiming(**c) for c in caps_list],
        voice=data.get("voice", "alba"),
    )


def _load_node(data: dict) -> SceneNode:
    return SceneNode(
        id=data.get("id", ""),
        label=data.get("label", ""),
        sublabel=data.get("sublabel", ""),
        children=[_load_node(c) for c in data.get("children", [])],
        color=data.get("color", "#4a90d9"),
    )


def _build_video_def(title: str, scenes_data: list[dict]) -> VideoDefinition:
    scenes = []
    tracks = []
    captions = []
    offset = 0

    for s in scenes_data:
        dur = s.get("duration", 90)
        scene = SceneDefinition(
            type=SceneType(s.get("type", "title")),
            duration=dur,
            title=s.get("title", ""),
            subtitle=s.get("subtitle", ""),
            text=s.get("text", ""),
            code=s.get("code", ""),
            lang=s.get("lang", ""),
            points=s.get("points", []),
            caption=s.get("caption", ""),
            cta=s.get("cta", ""),
            src=s.get("src", ""),
            nodeprefix=s.get("nodeprefix", ""),
            highlightLines=s.get("highlightLines", []),
            wordTimestamps=[WordTiming(**w) for w in s.get("wordTimestamps", [])],
            sceneStartFrame=offset,
        )
        scenes.append(scene)
        tracks.append(AudioTrack(src=f"audio_{len(scenes)-1:04d}/audio.wav", startFrame=offset, durationFrames=dur))
        for wt in scene.wordTimestamps:
            captions.append(wt)
        offset += dur

    return VideoDefinition(
        title=title,
        scenes=scenes,
        audioTracks=tracks,
        captions=captions,
    )



def main():
    import sys
    if len(sys.argv) <= 1:
        sys.argv.append("--help")
    app()


if __name__ == "__main__":
    main()
