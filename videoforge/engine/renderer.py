"""Remotion renderer — deterministic video output.

Handles scene-by-scene rendering and FFmpeg concatenation.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any

from videoforge.engine.models import VideoDefinition

logger = logging.getLogger("videoforge.engine.render")


def render_scenes(
    video: VideoDefinition,
    remotion_dir: str | Path,
    output_dir: str | Path,
    tmpdir: str | Path | None = None,
    concurrency: int = 1,
    timeout_per_scene: int = 600,
) -> list[str]:
    """Render each scene individually, return list of MP4 paths.

    This is deterministic: same VideoDefinition always produces same frames.
    """
    remotion_dir = Path(remotion_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if tmpdir:
        os.environ["TMPDIR"] = str(tmpdir)

    # Copy audio files to Remotion's public directory
    public_audio = remotion_dir / "public" / "audio"
    public_audio.mkdir(parents=True, exist_ok=True)
    for track in video.audioTracks:
        src = Path(track.src)
        if src.exists():
            dest = public_audio / src.name
            if not dest.exists():
                import shutil
                shutil.copy2(src, dest)

    rendered: list[str] = []
    for i, scene in enumerate(video.scenes):
        # Build single-scene props
        scene_props = video.to_remotion_props()
        scene_props["scenes"] = [scene_props["scenes"][i]]
        scene_props["audioTracks"] = [video.audioTracks[i]] if i < len(video.audioTracks) else []

        props_path = output_dir / f"props_{i:04d}.json"
        with open(props_path, "w") as f:
            json.dump(scene_props, f)

        output_path = output_dir / f"scene_{i:04d}.mp4"
        cmd = [
            "npx", "remotion", "render",
            "src/index.ts", "VideoComposition",
            str(output_path),
            "--props", str(props_path),
            "--concurrency", str(concurrency),
            "--log", "error",
            "--enforce-audio-track",
        ]

        logger.info("Rendering scene %d/%d (%s, %df)", i + 1, len(video.scenes), scene.type.value, scene.duration)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_per_scene, cwd=str(remotion_dir), env={**os.environ, "TMPDIR": str(tmpdir or output_dir / "tmp")})

        if result.returncode != 0 or not output_path.exists():
            stderr = (result.stderr or "")[-500:]
            raise RuntimeError(f"Scene {i} render failed: {stderr}")

        rendered.append(str(output_path.resolve()))

    return rendered


def concatenate_scenes(
    scene_paths: list[str],
    output_path: str | Path,
) -> str:
    """Concatenate rendered scenes with FFmpeg — lossless copy."""
    output_path = Path(output_path)
    list_file = output_path.parent / "concat_list.txt"

    with open(list_file, "w") as f:
        for p in scene_paths:
            f.write(f"file '{Path(p).name}'\n")

    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(list_file),
        "-c", "copy",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0 or not output_path.exists():
        raise RuntimeError(f"Concatenation failed: {(result.stderr or '')[-500:]}")

    return str(output_path.resolve())


def get_media_info(video_path: str | Path) -> dict[str, Any]:
    """Get video metadata using ffprobe."""
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(video_path)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        return {"error": "ffprobe failed"}
    import json as j
    return j.loads(result.stdout)
