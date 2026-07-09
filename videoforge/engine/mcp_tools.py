"""MCP tool wrappers — expose the deterministic video engine as MCP tools.

Any MCP-compatible agent (Claude Code, Cursor, Copilot, Codex) can call
these tools to generate videos deterministically.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from videoforge.engine.tts import generate_audio
from videoforge.engine.renderer import render_scenes, concatenate_scenes, get_media_info

logger = logging.getLogger("videoforge.mcp")

# Create MCP server with video generation tools
video_mcp = FastMCP(
    "VideoForge Engine",
    instructions="Deterministic video generation tools. Plan scenes, generate TTS audio, render videos, and review quality.",
)


@video_mcp.tool()
def engine_plan_scenes(
    topic: str,
    output_path: str = "/tmp/videoforge/scenes.json",
) -> dict:
    """Plan video scenes from a topic description.

    Args:
        topic: The video topic/description.
        output_path: Where to save the scene plan JSON.
    """
    plan = [
        {"type": "title", "title": topic, "duration": 180, "text": f"Welcome to {topic}."},
        {"type": "outro", "title": "Summary", "duration": 120, "text": "Thank you for watching."},
    ]
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(plan, indent=2))
    return {"scenes": len(plan), "path": output_path}


@video_mcp.tool()
def engine_generate_tts(
    text: str,
    output_path: str = "/tmp/videoforge/audio.wav",
    voice: str = "alba",
    tts_url: str = "http://localhost:8000",
) -> dict:
    """Generate TTS audio from text.

    Args:
        text: Text to synthesize.
        output_path: WAV output path.
        voice: TTS voice name.
        tts_url: Pocket TTS server URL.

    Returns:
        Audio metadata with word timestamps.
    """
    result = generate_audio(text, output_path, voice, tts_url)
    return {
        "audio_path": result["audio_path"],
        "duration_seconds": round(result["duration_seconds"], 2),
        "sample_rate": result["sample_rate"],
        "word_count": len(result["word_timestamps"]),
    }


@video_mcp.tool()
def engine_render_video(
    scenes_json: str,
    output_path: str = "/tmp/videoforge/output.mp4",
    remotion_dir: str = "remotion-project",
    build_dir: str = "/tmp/vfx-build",
) -> dict:
    """Render a video from a scene definition JSON.

    Args:
        scenes_json: JSON string or file path with scene definitions.
        output_path: Output MP4 path.
        remotion_dir: Remotion project directory.
        build_dir: Temporary build directory.

    Returns:
        Video metadata (duration, size, frame count).
    """
    import json
    if Path(scenes_json).exists():
        data = json.loads(Path(scenes_json).read_text())
    else:
        data = json.loads(scenes_json)

    from videoforge.engine.models import (
        AudioTrack, SceneDefinition, SceneType, VideoDefinition, WordTiming,
    )

    scenes = []
    for s in data.get("scenes", []):
        scenes.append(SceneDefinition(
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
        ))

    tracks = [AudioTrack(**t) for t in data.get("audioTracks", [])]
    caps = [WordTiming(**c) for c in data.get("captions", [])]

    video = VideoDefinition(
        title=data.get("title", "Video"),
        scenes=scenes,
        audioTracks=tracks,
        captions=caps,
        voice=data.get("voice", "alba"),
    )

    out_dir = Path(build_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    scene_paths = render_scenes(video, remotion_dir, out_dir, tmpdir=out_dir / "tmp")
    final = concatenate_scenes(scene_paths, output_path)

    info = get_media_info(final)
    fmt = info.get("format", {})
    return {
        "video_path": str(Path(final).resolve()),
        "duration_seconds": round(float(fmt.get("duration", 0)), 1),
        "file_size_mb": round(float(fmt.get("size", 0)) / 1e6, 1),
        "scenes": len(scene_paths),
        "frames": video.total_frames(),
    }


@video_mcp.tool()
def engine_review_video(
    video_path: str,
) -> dict:
    """Run L1 Frame Review on a rendered video.

    Args:
        video_path: Path to the video file.

    Returns:
        Review results with pass/fail per check.
    """
    from videoforge.review.frame_reviewer import FrameReviewer
    fr = FrameReviewer()
    result = fr.check_integrity(video_path)
    return {
        "passed": result.get("passed", False),
        "total_frames": result.get("total_frames", 0),
        "issues": len(result.get("issues", [])),
        "details": result.get("issues", []),
    }


@video_mcp.tool()
def engine_estimate_timing(
    word_count: int,
    duration_seconds: float,
) -> dict:
    """Estimate word-level timestamps for audio-synced animations.

    Args:
        word_count: Number of words in the narration.
        duration_seconds: Total audio duration.

    Returns:
        Per-word timing for animation synchronization.
    """
    if word_count <= 0:
        return {"words": []}
    per_word_ms = (duration_seconds * 1000) / word_count
    words = []
    for i in range(word_count):
        words.append({
            "index": i,
            "startMs": round(i * per_word_ms),
            "endMs": round((i + 1) * per_word_ms),
        })
    return {"words": words, "words_per_second": word_count / duration_seconds if duration_seconds > 0 else 0}
