"""Multi-engine renderer — deterministic video output.

Handles scene-by-scene rendering across Remotion and Manim engines,
then FFmpeg concatenation.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
from dataclasses import asdict
from pathlib import Path
from typing import Any

from videoforge.design_tokens import remotion_style_defaults
from videoforge.engine.models import SceneType, VideoDefinition
from videoforge.engine.ir import Engine, VideoProject

logger = logging.getLogger("videoforge.engine.render")
STYLE_DEFAULTS = remotion_style_defaults()


CLIP_FORMAT: dict[str, Any] = {
    "fps": 30,
    "width": 1920,
    "height": 1080,
    "pixel_format": "yuv420p",
    "audio_codec": "aac",
    "video_codec": "h264",
}

CLIP_FORMAT_ALPHA: dict[str, Any] = {
    **CLIP_FORMAT,
    "pixel_format": "yuva420p",  # alpha-capable variant for overlay scenes
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


def _track_count(video: VideoDefinition | VideoProject) -> int:
    """Number of audio tracks — works for both legacy VideoDefinition and VideoProject IR."""
    if isinstance(video, VideoProject):
        return len(video.audio_tracks)
    return len(video.audioTracks)


def _get_track(video: VideoDefinition | VideoProject, index: int) -> Any | None:
    """Get audio track by index — works for both legacy and IR."""
    if isinstance(video, VideoProject):
        if index < len(video.audio_tracks):
            return video.audio_tracks[index]
    elif index < len(video.audioTracks):
        return video.audioTracks[index]
    return None


_OVERLAY_POSITIONS: dict[str, tuple[str, str]] = {
    "center": ("(W-w)/2", "(H-h)/2"),
    "bottom-left": ("0", "H-h"),
    "bottom-right": ("W-w", "H-h"),
    "top-left": ("0", "0"),
    "top-right": ("W-w", "0"),
    "bottom-center": ("(W-w)/2", "H-h"),
}


def _parse_position(position: str) -> tuple[str, str]:
    """Parse overlay position string to FFmpeg overlay x:y coordinates."""
    return _OVERLAY_POSITIONS.get(position, _OVERLAY_POSITIONS["center"])


def _is_overlay_scene(scene: Any, is_ir: bool = False) -> bool:
    """Check if scene is an overlay-type scene.

    Overlay scenes render with alpha and composite over preceding base scene
    rather than concatenating sequentially.
    """
    if is_ir:
        from videoforge.engine.ir import SceneKind
        return scene.kind in (SceneKind.OVERLAY_CTA,)
    return (
        hasattr(scene, "type")
        and scene.type == SceneType.OVERLAY_CTA
    )


def _overlay_position_for_scene(scene: Any, is_ir: bool = False) -> str:
    """Determine overlay position based on scene kind.

    Lower-third overlays position at bottom-left / bottom-center.
    Center overlays (CTA) stay centered.
    """
    if is_ir:
        return "center"  # default for overlay-cta
    return "center"


def composite_overlay(
    base_path: str | Path,
    overlay_path: str | Path,
    output_path: str | Path,
    position: str = "center",
    opacity: float = 1.0,
) -> str:
    """Composite overlay video over base video using FFmpeg overlay filter.

    Base video uses pinned format (yuv420p). Overlay video must have alpha
    (yuva420p). Output is pinned format (yuv420p). Audio preserved from base.

    Returns path to composited MP4.
    """
    base_path = Path(base_path)
    overlay_path = Path(overlay_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    x, y = _parse_position(position)

    if opacity < 1.0:
        # Scale opacity via colorchannelmixer on overlay
        filter_complex = (
            f"[1:v]format=yuva420p,"
            f"colorchannelmixer=aa={opacity}[overlay_adj];"
            f"[0:v][overlay_adj]overlay={x}:{y}:format=auto[outv]"
        )
    else:
        filter_complex = (
            f"[0:v][1:v]overlay={x}:{y}:format=auto[outv]"
        )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(base_path.resolve()),
        "-i", str(overlay_path.resolve()),
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "0:a?",
        "-c:a", "copy",
        "-c:v", "libx264",
        "-pix_fmt", CLIP_FORMAT["pixel_format"],
        "-r", str(CLIP_FORMAT["fps"]),
        str(output_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0 or not output_path.exists():
        raise RuntimeError(
            f"Overlay compositing failed: {(result.stderr or '')[-500:]}"
        )

    return str(output_path.resolve())


def _mux_audio_track(
    track: Any,  # AudioTrack or AudioTrackIR
    output_path: Path,
    output_dir: Path,
    index: int,
) -> None:
    """Replace silent audio in scene clip with real narration audio."""
    audio_src = Path(track.src)
    if not audio_src.exists():
        logger.warning("Audio src %s not found for scene %d", audio_src, index)
        return
    muxed = output_dir / f"scene_{index:04d}_muxed.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-i", str(output_path),
        "-i", str(audio_src.resolve()),
        "-c:v", "copy",
        "-c:a", "aac",
        "-ac", "2",
        "-ar", "48000",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        str(muxed),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0 or not muxed.exists():
        raise RuntimeError(
            f"Audio mux failed for scene {index}: {(result.stderr or '')[-300:]}"
        )
    import shutil as _sh
    _sh.move(str(muxed), str(output_path))


def render_scenes(
    video: VideoDefinition | VideoProject,
    remotion_dir: str | Path,
    output_dir: str | Path,
    tmpdir: str | Path | None = None,
    concurrency: int = 1,
    timeout_per_scene: int = 600,
    artifacts_dir: str | Path | None = None,
) -> list[str]:
    """Render each scene individually, return list of MP4 paths.

    Accepts either legacy VideoDefinition or new VideoProject IR. When given
    a VideoProject, uses pick_engine() from the director to route each scene
    to Remotion or Manim. Deterministic: same input always produces same frames.

    When *artifacts_dir* is provided, generates thumbnail + sampled frame
    for each scene after successful render. Artifacts survive pipeline
    failures — generated inline, not deferred.
    """
    remotion_dir = Path(remotion_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if tmpdir:
        os.environ["TMPDIR"] = str(tmpdir)

    is_ir = isinstance(video, VideoProject)
    from videoforge.engine.director import pick_engine

    # Copy audio files to Remotion's public directory (both legacy and IR)
    public_audio = remotion_dir / "public" / "audio"
    public_audio.mkdir(parents=True, exist_ok=True)
    for idx in range(_track_count(video)):
        track = _get_track(video, idx)
        if track is None:
            continue
        src = Path(track.src)
        if src.exists():
            dest = public_audio / src.name
            if not dest.exists():
                import shutil
                shutil.copy2(src, dest)

    rendered: list[str] = []
    n_scenes = len(video.scenes)
    i = 0
    while i < n_scenes:
        # ── Detect overlay scene following this one ────────────────────────
        # Overlay scenes composite over predecessor rather than concatenating.
        # Both scenes render individually, then FFmpeg composites.
        next_is_overlay = False
        if i + 1 < n_scenes:
            if is_ir:
                next_is_overlay = _is_overlay_scene(video.scenes[i + 1], is_ir=True)
            else:
                next_is_overlay = _is_overlay_scene(video.scenes[i + 1])

        output_path = output_dir / f"scene_{i:04d}.mp4"

        if is_ir:
            node = video.scenes[i]
            engine = pick_engine(node)
            kind = node.kind.value
            duration = node.duration_frames
        else:
            scene = video.scenes[i]
            engine = Engine(getattr(scene, "renderer", "remotion"))
            kind = scene.type.value
            duration = scene.duration

        if engine == Engine.ANIMOTION:
            logger.info("Rendering scene %d/%d via Animotion (%s, %df)", i + 1, n_scenes, kind, duration)
            if is_ir:
                from videoforge.engine.ir_adapters import node_to_scene_definition
                sd = node_to_scene_definition(video.scenes[i], video.fps)
            else:
                sd = video.scenes[i]
            from videoforge.engine.animotion_renderer import render_scene as animotion_render_scene
            result = animotion_render_scene(sd, output_dir, fps=video.fps)
            if result["success"] and result["video_path"]:
                src = Path(result["video_path"])
                if src != output_path:
                    import shutil
                    shutil.copy2(str(src), str(output_path))

                track = _get_track(video, i)
                if track is not None:
                    _mux_audio_track(track, output_path, output_dir, i)

                if next_is_overlay:
                    pass  # Defer — composite after overlay rendered
                else:
                    rendered.append(str(output_path.resolve()))
            else:
                raise RuntimeError(f"Scene {i} Animotion render failed: {result.get('log', '')[-300:]}")
            i += 1
            if next_is_overlay:
                overlay_path = _render_overlay_composite(video, i, is_ir, output_dir, output_path, remotion_dir, tmpdir, concurrency, timeout_per_scene)
                rendered.append(str(overlay_path.resolve()))
                i += 1
            continue

        if engine == Engine.MANIM:
            logger.info("Rendering scene %d/%d via Manim (%s, %df)", i + 1, n_scenes, kind, duration)
            if is_ir:
                from videoforge.engine.ir_adapters import node_to_scene_definition
                sd = node_to_scene_definition(video.scenes[i], video.fps)
            else:
                sd = video.scenes[i]
            from videoforge.engine.manim_renderer import render_scene as manim_render_scene
            result = manim_render_scene(sd, output_dir, fps=video.fps, mode="direct")
            if result["success"] and result["video_path"]:
                src = Path(result["video_path"])
                if src != output_path:
                    import shutil
                    shutil.copy2(str(src), str(output_path))

                track = _get_track(video, i)
                if track is not None:
                    _mux_audio_track(track, output_path, output_dir, i)

                if next_is_overlay:
                    pass  # Defer — composite after overlay rendered
                else:
                    rendered.append(str(output_path.resolve()))
            else:
                raise RuntimeError(f"Scene {i} Manim render failed: {result.get('log', '')[-300:]}")
            i += 1
            if next_is_overlay:
                overlay_path = _render_overlay_composite(video, i, is_ir, output_dir, output_path, remotion_dir, tmpdir, concurrency, timeout_per_scene)
                rendered.append(str(overlay_path.resolve()))
                i += 1
            continue

        # Remotion path
        if is_ir:
            scene_props = _ir_scene_props(video, i)
        else:
            scene_props = video.to_remotion_props()
            scene_props["scenes"] = [scene_props["scenes"][i]]
            scene_props["audioTracks"] = [asdict(video.audioTracks[i])] if i < len(video.audioTracks) else []

        props_path = output_dir / f"props_{i:04d}.json"
        with open(props_path, "w") as f:
            json.dump(scene_props, f)

        is_overlay = (is_ir and _is_overlay_scene(video.scenes[i], is_ir=True)) or (not is_ir and _is_overlay_scene(video.scenes[i]))
        render_pix_fmt = CLIP_FORMAT_ALPHA["pixel_format"] if is_overlay else CLIP_FORMAT["pixel_format"]

        cmd = [
            "npx", "remotion", "render",
            "src/index.ts", "VideoComposition",
            str(output_path),
            "--props", str(props_path),
            "--concurrency", str(concurrency),
            "--log", "error",
            "--codec", "h264",
            "--pixel-format", render_pix_fmt,
            "--fps", str(CLIP_FORMAT["fps"]),
        ]
        if not is_overlay:
            cmd.append("--enforce-audio-track")

        logger.info("Rendering scene %d/%d via Remotion (%s, %df)", i + 1, n_scenes, kind, duration)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_per_scene, cwd=str(remotion_dir), env={**os.environ, "TMPDIR": str(tmpdir or output_dir / "tmp")})

        if result.returncode != 0 or not output_path.exists():
            stderr = (result.stderr or "")[-500:]
            raise RuntimeError(f"Scene {i} Remotion render failed: {stderr}")

        if is_overlay:
            if rendered:
                base_path = rendered.pop()
                composited = output_dir / f"composited_{i:04d}.mp4"
                pos = _overlay_position_for_scene(video.scenes[i], is_ir)
                composite_overlay(base_path, output_path, composited, position=pos)
                rendered.append(str(composited.resolve()))
            else:
                logger.warning("Overlay scene %d has no base scene — rendering standalone", i)
                rendered.append(str(output_path.resolve()))
        else:
            if next_is_overlay:
                i += 1
                overlay_path = _render_overlay_composite(video, i, is_ir, output_dir, output_path, remotion_dir, tmpdir, concurrency, timeout_per_scene)
                rendered.append(str(overlay_path.resolve()))
            else:
                rendered.append(str(output_path.resolve()))

        i += 1

    # ── Scene artifact generation ──────────────────────────────────────────
    # Generate thumbnails + sampled frames for all successfully rendered
    # scenes. Best-effort: errors logged, pipeline not blocked.
    if artifacts_dir and rendered:
        try:
            from videoforge.artifacts.generator import generate_batch_scene_artifacts as _gen_batch
            _scene_ids = [Path(p).stem for p in rendered]
            _gen_batch(
                artifacts_dir=str(artifacts_dir),
                scene_paths=rendered,
                scene_ids=_scene_ids,
                fps=CLIP_FORMAT["fps"],
            )
        except Exception:
            logger.warning("Scene artifact generation failed", exc_info=True)

    return rendered


def _render_overlay_composite(
    video: Any, i: int, is_ir: bool,
    output_dir: Path, base_path: Path,
    remotion_dir: Path, tmpdir: Any, concurrency: int,
    timeout_per_scene: int,
) -> Path:
    """Render overlay scene with alpha, composite over base scene.

    Called when scene[i] is an overlay scene. The base scene is already
    rendered at base_path. This renders the overlay with alpha and
    composites using FFmpeg overlay filter.
    """
    overlay_path = output_dir / f"scene_{i:04d}_overlay.mp4"

    if is_ir:
        from videoforge.engine.director import pick_engine as _pe
        node = video.scenes[i]
        engine = _pe(node)
        kind = node.kind.value
    else:
        scene = video.scenes[i]
        engine = Engine(getattr(scene, "renderer", "remotion"))
        kind = scene.type.value

    if engine == Engine.MANIM:
        from videoforge.engine.ir_adapters import node_to_scene_definition
        sd = node_to_scene_definition(video.scenes[i], video.fps)
        from videoforge.engine.manim_renderer import render_scene as manim_render_scene
        result = manim_render_scene(sd, output_dir, fps=video.fps, mode="direct")
        if not result["success"] or not result["video_path"]:
            raise RuntimeError(f"Overlay scene {i} Manim render failed: {result.get('log', '')[-300:]}")
        src = Path(result["video_path"])
        if src != overlay_path:
            import shutil
            shutil.copy2(str(src), str(overlay_path))
    elif engine == Engine.ANIMOTION:
        from videoforge.engine.ir_adapters import node_to_scene_definition
        sd = node_to_scene_definition(video.scenes[i], video.fps)
        from videoforge.engine.animotion_renderer import render_scene as animotion_render_scene
        result = animotion_render_scene(sd, output_dir, fps=video.fps)
        if not result["success"] or not result["video_path"]:
            raise RuntimeError(f"Overlay scene {i} Animotion render failed: {result.get('log', '')[-300:]}")
        src = Path(result["video_path"])
        if src != overlay_path:
            import shutil
            shutil.copy2(str(src), str(overlay_path))
    else:
        # Remotion path — render with alpha
        if is_ir:
            scene_props = _ir_scene_props(video, i)
        else:
            scene_props = video.to_remotion_props()
            scene_props["scenes"] = [scene_props["scenes"][i]]

        props_path = output_dir / f"props_{i:04d}_overlay.json"
        with open(props_path, "w") as f:
            json.dump(scene_props, f)

        cmd = [
            "npx", "remotion", "render",
            "src/index.ts", "VideoComposition",
            str(overlay_path),
            "--props", str(props_path),
            "--concurrency", str(concurrency),
            "--log", "error",
            "--codec", "h264",
            "--pixel-format", CLIP_FORMAT_ALPHA["pixel_format"],
            "--fps", str(CLIP_FORMAT["fps"]),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_per_scene, cwd=str(remotion_dir), env={**os.environ, "TMPDIR": str(tmpdir or output_dir / "tmp")})
        if result.returncode != 0 or not overlay_path.exists():
            stderr = (result.stderr or "")[-500:]
            raise RuntimeError(f"Overlay scene {i} Remotion render failed: {stderr}")

    # Composite overlay over base
    composited_path = output_dir / f"composited_{i:04d}.mp4"
    if is_ir:
        pos = _overlay_position_for_scene(video.scenes[i], is_ir=True)
    else:
        pos = _overlay_position_for_scene(video.scenes[i])

    # No audio mux for overlay scenes — audio comes from base
    composite_overlay(base_path, overlay_path, composited_path, position=pos)

    # Clean up intermediate overlay file
    if overlay_path.exists() and overlay_path != composited_path:
        overlay_path.unlink(missing_ok=True)

    return composited_path


def _ir_scene_props(project: VideoProject, index: int) -> dict[str, Any]:
    """Build Remotion inputProps for a single scene from a VideoProject IR."""
    node = project.scenes[index]
    payload = node.payload_dict()
    scene_json: dict[str, Any] = {
        "type": node.kind.value,
        "duration": node.duration_frames,
        "wordTimestamps": [
            {"text": w.text, "startMs": w.startMs, "endMs": w.endMs}
            for w in node.narration.words
        ],
        "sceneStartFrame": 0,
    }
    for key in ("title", "subtitle", "text", "code", "lang", "points",
                "caption", "cta", "src", "nodeprefix", "highlightLines"):
        if key in payload and payload[key]:
            scene_json[key] = payload[key]
    if node.overlays:
        scene_json["overlays"] = [
            {
                "kind": o.kind,
                "startOffsetMs": o.start_offset_ms,
                "endOffsetMs": o.end_offset_ms,
                "payload": json.loads(o.payload),
            }
            for o in node.overlays
        ]
    audio_tracks_list: list[dict[str, Any]] = []
    if index < len(project.audio_tracks):
        audio_tracks_list.append(asdict(project.audio_tracks[index]))
    return {
        "title": project.title,
        "scenes": [scene_json],
        "audioTracks": audio_tracks_list,
        "captions": [],
        "voice": "alba",
        "style": STYLE_DEFAULTS,
    }


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
