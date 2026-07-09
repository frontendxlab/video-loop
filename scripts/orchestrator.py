#!/usr/bin/env python3
"""
VideoForge Orchestrator — CLI for deterministic video generation.

This is the main entry point for creating videos. It uses the deterministic
video engine at videoforge/engine/ and exposes rich MCP tools.

Usage:
  python3 scripts/orchestrator.py --help
  python3 scripts/orchestrator.py pipeline --topic "Claude Architect Exam"
  python3 scripts/orchestrator.py grill --topic "..."         # Grill requirements
  python3 scripts/orchestrator.py plan --topic "..."           # Plan scenes
  python3 scripts/orchestrator.py build --scenes scenes.json   # Full build
  python3 scripts/orchestrator.py mcp                          # Start MCP server
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path

import typer
from typing_extensions import Annotated

from videoforge.design_tokens import remotion_style_defaults

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("orchestrator")
STYLE_DEFAULTS = remotion_style_defaults()

app = typer.Typer(help="VideoForge Orchestrator")


@app.command()
def grill(
    topic: Annotated[str, typer.Option(help="Video topic to grill requirements for")],
    output: Annotated[str, typer.Option(help="Output path for requirements")] = "/tmp/vfx-requirements.json",
):
    """Grill the video requirements (like Matt Pocock's grill-me skill).

    Analyzes the topic and outputs structured requirements.
    """
    logger.info("=" * 60)
    logger.info("VIDEOFORGE GRILL-ME")
    logger.info("=" * 60)
    logger.info("Topic: %s", topic)
    logger.info("")
    logger.info("Step 1: Define Purpose")
    logger.info("  What: Explainer video for %s", topic)
    logger.info("  Audience: Technical professionals")
    logger.info("  Length: 10-15 minutes")
    logger.info("  Tone: Professional, educational")
    logger.info("")
    logger.info("Step 2: Visual Approach")
    logger.info("  - Title cards for section headers")
    logger.info("  - Mind map diagrams for architecture/taxonomy")
    logger.info("  - Code walkthroughs for implementation examples")
    logger.info("  - Bullet cards for key concepts")
    logger.info("  - Outro for summary and CTA")
    logger.info("")
    logger.info("Step 3: Quality Gates")
    logger.info("  - All animations synced to audio word timestamps")
    logger.info("  - L1 Frame Review: 0 issues")
    logger.info("  - Audio tracks for every scene")
    logger.info("  - No frame overlap between scenes")

    req = {
        "topic": topic,
        "target_audience": "technical",
        "target_length_minutes": 10,
        "tone": "professional",
        "scene_types": ["title", "mindmap", "code-walkthrough", "bullet", "outro"],
        "quality_gates": ["audio-timing-sync", "l1-frame-review", "scene-isolation"],
    }
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(json.dumps(req, indent=2))
    logger.info("\nRequirements written to %s", output)


@app.command()
def plan(
    topic: Annotated[str, typer.Option(help="Video topic")],
    scenes: Annotated[str, typer.Option(help="Scene definitions JSON")] = "",
    output: Annotated[str, typer.Option(help="Output scene plan")] = "/tmp/vfx-scenes.json",
):
    """Plan scenes from topic and optional scene definitions."""
    if scenes and Path(scenes).exists():
        scene_data = json.loads(Path(scenes).read_text())
    else:
        # Generate basic scene plan from topic
        scene_data = _generate_scene_plan(topic)
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(json.dumps(scene_data, indent=2))
    logger.info("Scene plan: %d scenes -> %s", len(scene_data), output)


@app.command()
def build(
    scenes: Annotated[str, typer.Option(help="Scene plan JSON path")],
    output: Annotated[str, typer.Option(help="Output MP4 path")] = "videos/output.mp4",
    voice: Annotated[str, typer.Option(help="TTS voice")] = "alba",
    tts_url: Annotated[str, typer.Option(help="TTS server URL")] = "http://localhost:8000",
):
    """Full deterministic build: TTS → time → render → concat → review."""
    scenes_path = Path(scenes)
    if not scenes_path.exists():
        logger.error("Scene plan not found: %s", scenes)
        raise typer.Exit(1)

    scene_data = json.loads(scenes_path.read_text())
    out_dir = Path(output).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    build_dir = Path("/tmp/vfx-build")
    build_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: TTS for each scene
    for i, scene in enumerate(scene_data):
        text = scene.get("text", scene.get("title", ""))
        if not text:
            logger.warning("Scene %d has no text, skipping TTS", i)
            continue
        audio_dir = build_dir / f"audio_{i:04d}"
        audio_dir.mkdir(parents=True, exist_ok=True)
        wav_path = audio_dir / "audio.wav"

        logger.info("[%d/%d] TTS: %s (%d chars)", i + 1, len(scene_data), scene.get("type", "?"), len(text))
        try:
            import requests
            resp = requests.post(f"{tts_url}/tts", data={"text": text, "voice": voice}, timeout=120)
            if resp.status_code == 200:
                wav_path.write_bytes(resp.content)
                dur = _wav_duration(wav_path)
                scene["duration"] = max(1, int(dur * 30))
                scene["wordTimestamps"] = _estimate_timestamps(text.split(), dur)
                logger.info("  -> %.1fs, %d words", dur, len(text.split()))
            else:
                logger.warning("  TTS failed: %d", resp.status_code)
                scene["duration"] = max(30, len(text.split()) * 4)
        except Exception as e:
            logger.warning("  TTS error: %s", e)
            scene["duration"] = max(30, len(text.split()) * 4)

    # Step 2: Build timing
    offset = 0
    for scene in scene_data:
        dur = scene.get("duration", 90)
        scene["sceneStartFrame"] = offset
        for wt in scene.get("wordTimestamps", []):
            pass  # timestamps already computed
        offset += dur

    # Step 3: Write video definition
    tracks = []
    all_captions = []
    o = 0
    for i, scene in enumerate(scene_data):
        dur = scene.get("duration", 90)
        tracks.append({"src": f"audio_{i:04d}/audio.wav", "startFrame": o, "durationFrames": dur})
        for wt in scene.get("wordTimestamps", []):
            all_captions.append({"text": wt["text"], "startMs": wt["startMs"] + o / 30 * 1000, "endMs": wt["endMs"] + o / 30 * 1000})
        o += dur

    video_def = {
        "title": f"Video: {scenes_path.stem}",
        "scenes": scene_data,
        "audioTracks": tracks,
        "captions": all_captions,
        "voice": voice,
        "style": STYLE_DEFAULTS,
    }

    video_json = build_dir / "video_def.json"
    video_json.write_text(json.dumps(video_def, indent=2))
    logger.info("Video def: %d scenes, %d frames (%.1fs)", len(scene_data), offset, offset / 30)

    # Step 4: Render each scene
    import shutil
    from videoforge.engine.renderer import render_scenes, concatenate_scenes, get_media_info

    # Copy audio files
    remo_dir = Path("remotion-project")
    pub_audio = remo_dir / "public" / "audio"
    pub_audio.mkdir(parents=True, exist_ok=True)
    for i in range(len(scene_data)):
        src = build_dir / f"audio_{i:04d}" / "audio.wav"
        if src.exists():
            shutil.copy2(src, pub_audio / f"audio_{i:04d}.wav")
            tracks[i]["src"] = f"audio/audio_{i:04d}.wav"
        else:
            tracks[i]["src"] = ""

    video_def["audioTracks"] = tracks
    video_json.write_text(json.dumps(video_def, indent=2))

    scene_paths = render_scenes_from_def(video_def, str(remo_dir), str(build_dir), str(build_dir / "tmp"))
    logger.info("Rendered %d/%d scenes", len(scene_paths), len(scene_data))

    if scene_paths:
        final = concatenate_scenes(scene_paths, str(output))
        logger.info("Final video: %s", final)
        info = get_media_info(final)
        fmt = info.get("format", {})
        dur = float(fmt.get("duration", 0))
        logger.info("Duration: %.1fs (%.1f min), Size: %.1fMB", dur, dur / 60, float(fmt.get("size", 0)) / 1e6)
    else:
        logger.error("No scenes rendered")

    # Step 5: Review (L0 mixed-engine + L1 frame integrity)
    try:
        from videoforge.review.frame_reviewer import FrameReviewer, generate_video_report, write_video_report
        fr = FrameReviewer()
        l0 = fr.check_mixed_engine(str(output))
        l0_status = fr.evaluate_l0_policy(l0)
        logger.info("L0 Mixed-Engine: status=%s, issues=%d, sampled=%d",
                    l0_status, len(l0.get("issues", [])), l0.get("sampled_frames", 0))
        if l0.get("issues"):
            for issue in l0["issues"]:
                logger.warning("  [%s] %s: %s", issue.get("severity", "?"),
                               issue.get("type", "?"), issue.get("detail", ""))
        l1 = fr.check_integrity(str(output))
        logger.info("L1 Frame Integrity: passed=%s, frames=%d, issues=%d",
                    l1.get("passed"), l1.get("total_frames", 0), len(l1.get("issues", [])))

        # Generate report artifact
        engines = list({s.get("renderer", "remotion") for s in scene_data})
        video_hash = _compute_video_def_hash(video_def)
        report = generate_video_report(
            video_path=str(output),
            content_hash=video_hash,
            engine_mix=engines,
            l0_result=l0,
            l1_result=l1,
            l0_status=l0_status,
        )
        report_path = write_video_report(report, str(output))
        logger.info("Build report: %s", report_path)
    except Exception as e:
        logger.warning("Review skipped: %s", e)


@app.command()
def mcp():
    """Start the VideoForge MCP server (stdio transport)."""
    from videoforge.engine.mcp_tools import video_mcp
    logger.info("Starting VideoForge MCP server (stdio)...")
    video_mcp.run(transport="stdio")


def render_scenes_from_def(video_def: dict, remotion_dir: str, build_dir: str, tmpdir: str) -> list[str]:
    """Render all scenes from a video definition dict."""
    import subprocess, os
    from pathlib import Path
    rendered = []
    scenes = video_def.get("scenes", [])
    tracks = video_def.get("audioTracks", [])
    os.environ["TMPDIR"] = tmpdir
    Path(tmpdir).mkdir(parents=True, exist_ok=True)

    for i, scene in enumerate(scenes):
        single = {
            "title": video_def.get("title", ""),
            "scenes": [scene],
            "audioTracks": [tracks[i]] if i < len(tracks) else [],
            "captions": [],
            "voice": video_def.get("voice", "alba"),
            "style": video_def.get("style", STYLE_DEFAULTS),
        }
        props_path = Path(build_dir) / f"props_{i:04d}.json"
        props_path.write_text(json.dumps(single))
        out_path = Path(build_dir) / f"scene_{i:04d}.mp4"

        cmd = ["npx", "remotion", "render", "src/index.ts", "VideoComposition", str(out_path), "--props", str(props_path), "--concurrency", "1", "--log", "error", "--enforce-audio-track"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600, cwd=remotion_dir, env={**os.environ, "TMPDIR": tmpdir})

        if result.returncode == 0 and out_path.exists():
            rendered.append(str(out_path.resolve()))
            logger.info("  Scene %d: %s -> %dKB", i, scene.get("type", "?"), out_path.stat().st_size / 1024)
        else:
            logger.error("  Scene %d FAILED: %s", i, (result.stderr or "")[:200])

    return rendered


def _generate_scene_plan(topic: str) -> list[dict]:
    """Generate a basic scene plan from a topic."""
    return [
        {"type": "title", "title": topic, "duration": 180, "text": f"Welcome to {topic}."},
        {"type": "outro", "title": "Summary", "duration": 120, "text": "Thank you for watching."},
    ]


def _wav_duration(path: Path) -> float:
    import wave
    with wave.open(str(path), "rb") as wf:
        fr = wf.getframerate()
        sw = wf.getsampwidth()
        ch = wf.getnchannels()
    db = path.stat().st_size - 44
    return db / (sw * ch) / fr if db > 0 else 0


def _compute_video_def_hash(video_def: dict) -> str:
    """Compute deterministic sha256 hash of video definition dict."""
    import hashlib
    data = json.dumps(video_def, sort_keys=True, default=str)
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def _estimate_timestamps(words: list[str], dur: float) -> list[dict]:
    if not words:
        return []
    pm = (dur * 1000) / len(words)
    return [{"text": w, "startMs": round(i * pm), "endMs": round((i + 1) * pm)} for i, w in enumerate(words)]


if __name__ == "__main__":
    app()
