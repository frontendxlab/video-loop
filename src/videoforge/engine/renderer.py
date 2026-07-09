"""Multi-engine renderer — deterministic video output.

Handles scene-by-scene rendering across Remotion and Manim engines,
then FFmpeg concatenation.
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


CLIP_FORMAT: dict[str, Any] = {
    "fps": 30,
    "width": 1920,
    "height": 1080,
    "pixel_format": "yuv420p",
    "audio_codec": "aac",
    "video_codec": "h264",
}


def _probe_clip_format(path: str | Path) -> dict[str, Any] | None:
    """Return {fps, width, height, pix_fmt, vcodec, acodec} or None on failure."""
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_streams", str(path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if res.returncode != 0:
        return None
    try:
        info = json.loads(res.stdout)
    except json.JSONDecodeError:
        return None
    fmt: dict[str, Any] = {}
    for st in info.get("streams", []):
        if st.get("codec_type") == "video":
            fr = st.get("r_frame_rate", "30/1")
            num, _, den = fr.partition("/")
            try:
                fmt["fps"] = round(int(num) / (int(den) or 1))
            except ValueError:
                fmt["fps"] = 30
            fmt["width"] = int(st.get("width", 1920))
            fmt["height"] = int(st.get("height", 1080))
            fmt["pix_fmt"] = st.get("pix_fmt", "yuv420p")
            fmt["vcodec"] = st.get("codec_name", "h264")
        if st.get("codec_type") == "audio":
            fmt["acodec"] = st.get("codec_name", "aac")
    return fmt or None


def _matches_pinned(fmt: dict[str, Any] | None) -> bool:
    if not fmt:
        return True  # unknown — assume ok, copy
    return (
        fmt.get("fps") == CLIP_FORMAT["fps"]
        and fmt.get("width") == CLIP_FORMAT["width"]
        and fmt.get("height") == CLIP_FORMAT["height"]
        and fmt.get("pix_fmt") == CLIP_FORMAT["pixel_format"]
        and fmt.get("vcodec") == CLIP_FORMAT["video_codec"]
        and fmt.get("acodec") == CLIP_FORMAT["audio_codec"]
    )


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
        scene_renderer = getattr(scene, "renderer", "remotion")
        output_path = output_dir / f"scene_{i:04d}.mp4"

        if scene_renderer == "manim":
            logger.info("Rendering scene %d/%d via Manim (%s, %df)", i + 1, len(video.scenes), scene.type.value, scene.duration)
            from videoforge.engine.manim_renderer import render_scene as manim_render_scene
            result = manim_render_scene(scene, output_dir, fps=video.fps, mode="direct")
            if result["success"] and result["video_path"]:
                src = Path(result["video_path"])
                if src != output_path:
                    import shutil
                    shutil.copy2(str(src), str(output_path))
                rendered.append(str(output_path.resolve()))
            else:
                raise RuntimeError(f"Scene {i} Manim render failed: {result.get('log', '')[-300:]}")
            continue

        # Build single-scene props for Remotion
        scene_props = video.to_remotion_props()
        scene_props["scenes"] = [scene_props["scenes"][i]]
        scene_props["audioTracks"] = [video.audioTracks[i]] if i < len(video.audioTracks) else []

        props_path = output_dir / f"props_{i:04d}.json"
        with open(props_path, "w") as f:
            json.dump(scene_props, f)

        cmd = [
            "npx", "remotion", "render",
            "src/index.ts", "VideoComposition",
            str(output_path),
            "--props", str(props_path),
            "--concurrency", str(concurrency),
            "--log", "error",
            "--enforce-audio-track",
            "--codec", "h264",
            "--pixel-format", CLIP_FORMAT["pixel_format"],
            "--fps", str(CLIP_FORMAT["fps"]),
        ]

        logger.info("Rendering scene %d/%d via Remotion (%s, %df)", i + 1, len(video.scenes), scene.type.value, scene.duration)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_per_scene, cwd=str(remotion_dir), env={**os.environ, "TMPDIR": str(tmpdir or output_dir / "tmp")})

        if result.returncode != 0 or not output_path.exists():
            stderr = (result.stderr or "")[-500:]
            raise RuntimeError(f"Scene {i} Remotion render failed: {stderr}")

        rendered.append(str(output_path.resolve()))

    return rendered


def concatenate_scenes(
    scene_paths: list[str],
    output_path: str | Path,
) -> str:
    """Concatenate rendered scenes with FFmpeg.

    Lossless -c copy when all clips match the pinned CLIP_FORMAT; otherwise
    re-encode to the pinned format (h264/yuv420p/30fps/aac) for safe concat.
    """
    output_path = Path(output_path)
    list_file = output_path.parent / "concat_list.txt"

    with open(list_file, "w") as f:
        for p in scene_paths:
            f.write(f"file '{Path(p).name}'\n")

    all_match = True
    for p in scene_paths:
        if not _matches_pinned(_probe_clip_format(p)):
            all_match = False
            break

    if all_match:
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",
            str(output_path),
        ]
    else:
        logger.info("concat: format mismatch detected, re-encoding to pinned format")
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(list_file),
            "-c:v", "libx264", "-pix_fmt", CLIP_FORMAT["pixel_format"],
            "-r", str(CLIP_FORMAT["fps"]),
            "-c:a", CLIP_FORMAT["audio_codec"],
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
