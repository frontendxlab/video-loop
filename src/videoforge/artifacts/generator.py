"""Deterministic frame extraction for scene thumbnails and sampled frames.

Extracts frames from rendered scene MP4s using ffmpeg with exact seek.
All paths are deterministic: same video + same timestamp = same output bytes.

Best-effort: returns gracefully on corrupt/missing video, missing ffmpeg, or
partial renders. Callers decide how to handle failures.
"""

from __future__ import annotations

import subprocess
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("videoforge.artifacts.generator")

_THUMBNAIL_WIDTH = 320
_FRAME_WIDTH = 640
_THUMB_QUALITY = 8  # ffmpeg JPEG quality (1-31, lower=better)
_FRAME_QUALITY = 6
_DEFAULT_POSITION_SEC = 0.0


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def extract_frame(
    video_path: str | Path,
    output_path: str | Path,
    position_sec: float = _DEFAULT_POSITION_SEC,
    scale: str | None = None,
    quality: int = 6,
) -> bool:
    """Extract single frame from video at *position_sec*.

    Uses ffmpeg ``-ss`` before ``-i`` for fast seek, then exact frame
    extraction with ``-frames:v 1``. Deterministic for same input.

    Args:
        video_path: Path to source video.
        output_path: Path for output image (extension determines format).
        position_sec: Timestamp in seconds to extract from.
        scale: Optional ffmpeg scale filter (e.g. ``320:-1``).
        quality: JPEG quality 2-31 (lower=better, default 6).

    Returns:
        True if frame written successfully.
    """
    video = Path(video_path)
    if not video.is_file():
        logger.warning("extract_frame: video not found %s", video)
        return False

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(position_sec),
        "-i", str(video.resolve()),
        "-frames:v", "1",
        "-q:v", str(quality),
    ]
    if scale:
        cmd.extend(["-vf", f"scale={scale}"])
    # Let ffmpeg infer output format from extension; don't force image2
    cmd.append(str(out.resolve()))

    try:
        result = subprocess.run(
            cmd, capture_output=True, timeout=60,
        )
        if result.returncode == 0 and out.is_file() and out.stat().st_size > 0:
            return True
        logger.debug("extract_frame ffmpeg rc=%d size=%d path=%s",
                      result.returncode, out.stat().st_size if out.exists() else 0, out)
        return False
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
        logger.warning("extract_frame failed for %s at %ss: %s", video, position_sec, exc)
        return False


def generate_scene_thumbnail(
    video_path: str | Path,
    output_dir: str | Path,
    scene_id: str,
    position_sec: float = _DEFAULT_POSITION_SEC,
) -> bool:
    """Generate thumbnail (320px wide JPEG) for a scene.

    Args:
        video_path: Rendered scene video.
        output_dir: Directory for thumbnails (subdir per job).
        scene_id: Scene identifier (e.g. ``scene_0000``).
        position_sec: Timestamp to extract from (default 0 = first frame).

    Returns:
        True if thumbnail written successfully.
    """
    out_dir = _ensure_dir(Path(output_dir) / "thumbnails")
    out_path = out_dir / f"{scene_id}.jpg"
    return extract_frame(
        video_path, out_path,
        position_sec=position_sec,
        scale=f"{_THUMBNAIL_WIDTH}:-1",
        quality=_THUMB_QUALITY,
    )


def generate_sampled_frame(
    video_path: str | Path,
    output_dir: str | Path,
    scene_id: str,
    position_sec: float = _DEFAULT_POSITION_SEC,
) -> bool:
    """Generate sampled frame (640px wide JPEG) for a scene.

    Args:
        video_path: Rendered scene video.
        output_dir: Directory for frames (subdir per job).
        scene_id: Scene identifier.
        position_sec: Timestamp to extract from (default 0 = first frame).

    Returns:
        True if frame written successfully.
    """
    out_dir = _ensure_dir(Path(output_dir) / "frames")
    out_path = out_dir / f"{scene_id}.jpg"
    return extract_frame(
        video_path, out_path,
        position_sec=position_sec,
        scale=f"{_FRAME_WIDTH}:-1",
        quality=_FRAME_QUALITY,
    )


def generate_scene_artifacts(
    video_path: str | Path,
    artifacts_dir: str | Path,
    scene_id: str,
    duration_frames: int = 0,
    fps: float = 30.0,
) -> dict[str, Any]:
    """Generate all artifact types for a single scene.

    Produces:
      - Thumbnail (320px, first frame)
      - Sampled frame (640px, first frame)

    When *duration_frames* > 0, also extracts a mid-point frame
    (at duration/2) as a second sampled frame for richer preview
    of longer scenes.

    Best-effort: each artifact is independent; failures are logged
    but do not prevent other artifacts from being generated.

    Args:
        video_path: Path to rendered scene MP4.
        artifacts_dir: Base artifact directory (job-level).
        scene_id: Scene identifier.
        duration_frames: Scene duration in frames (0 = unknown).
        fps: Frames per second (default 30).

    Returns:
        Dict with keys:
          - thumbnail: Path string or empty on failure.
          - frame: Path string or empty on failure.
          - frames_mid: List of path strings (one if duration > 0).
    """
    result: dict[str, Any] = {
        "thumbnail": "",
        "frame": "",
        "frames_mid": [],
    }

    # Thumbnail (first frame)
    if generate_scene_thumbnail(video_path, artifacts_dir, scene_id, position_sec=0.0):
        thumb_path = Path(artifacts_dir) / "thumbnails" / f"{scene_id}.jpg"
        result["thumbnail"] = str(thumb_path.resolve())

    # Sampled frame (first frame)
    if generate_sampled_frame(video_path, artifacts_dir, scene_id, position_sec=0.0):
        frame_path = Path(artifacts_dir) / "frames" / f"{scene_id}.jpg"
        result["frame"] = str(frame_path.resolve())

    # Mid-point frame for longer scenes
    if duration_frames > 0:
        mid_sec = (duration_frames / fps) / 2.0
        mid_id = f"{scene_id}_mid"
        if generate_sampled_frame(video_path, artifacts_dir, mid_id, position_sec=mid_sec):
            mid_path = Path(artifacts_dir) / "frames" / f"{mid_id}.jpg"
            result["frames_mid"].append(str(mid_path.resolve()))

    return result


def generate_batch_scene_artifacts(
    artifacts_dir: str | Path,
    scene_paths: list[str],
    scene_ids: list[str],
    fps: float = 30.0,
) -> list[dict[str, Any]]:
    """Batch-generate artifacts for all rendered scenes.

    One scene per entry. Each entry has the same structure as
    :func:`generate_scene_artifacts` return value.

    Args:
        artifacts_dir: Base artifact directory (job-level).
        scene_paths: List of rendered scene MP4 paths.
        scene_ids: List of scene identifiers (same order).
        fps: Frames per second (default 30).

    Returns:
        List of result dicts, one per scene.
    """
    results: list[dict[str, Any]] = []
    for i, sp in enumerate(scene_paths):
        sid = scene_ids[i] if i < len(scene_ids) else f"scene_{i:04d}"
        # Estimate duration from filename convention or probe
        duration_frames = _probe_duration_frames(sp, fps)
        res = generate_scene_artifacts(sp, artifacts_dir, sid, duration_frames, fps)
        results.append(res)
    return results


def _probe_duration_frames(video_path: str | Path, fps: float = 30.0) -> int:
    """Probe video for total frame count using ffprobe.

    Returns 0 on failure (best-effort).
    """
    import json
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_streams", str(video_path),
            ],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            return 0
        data = json.loads(result.stdout)
        for s in data.get("streams", []):
            if s.get("codec_type") == "video":
                nb = s.get("nb_frames")
                if nb is not None:
                    return int(nb)
                # Fallback: duration * fps
                dur = s.get("duration")
                if dur:
                    return int(float(dur) * fps)
        return 0
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError, OSError):
        return 0
