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

    # Run coherence gate on generated scene plan
    from videoforge.validation.coherence_gate import (  # fmt: skip
        extract_script_from_scenes,
        run_coherence_gate,
        write_coherence_report,
    )
    plan_dict: dict = {"scenes": plan}
    script = extract_script_from_scenes(plan) or topic
    coherence = run_coherence_gate(script, plan_dict, plan_path=output_path)
    coherence_report_path = write_coherence_report(coherence, output_path)

    return {
        "scenes": len(plan),
        "path": output_path,
        "coherence": {
            "coherent": coherence["coherent"],
            "issues": coherence["issues"],
            "missing_phases": coherence["narrative_arc"]["missing_phases"],
            "report_path": coherence_report_path,
        },
    }


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
            renderer=s.get("renderer", "remotion"),
            manim_code=s.get("manim_code", ""),
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

    # Run coherence gate on parsed scene data
    from videoforge.validation.coherence_gate import (  # fmt: skip
        extract_script_from_scenes,
        run_coherence_gate,
    )
    plan_dict: dict = {"scenes": data.get("scenes", [])}
    script = extract_script_from_scenes(data.get("scenes", [])) or data.get("title", "")
    coherence_result = run_coherence_gate(script, plan_dict)

    out_dir = Path(build_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    scene_paths = render_scenes(video, remotion_dir, out_dir, tmpdir=out_dir / "tmp")

    # Emit per-scene report artifacts alongside each scene file
    from videoforge.review.frame_reviewer import generate_scene_report, write_scene_report
    scene_reports: list[dict] = []
    for i, (scene, sp) in enumerate(zip(video.scenes, scene_paths)):
        engine = getattr(scene, "renderer", "remotion")
        sr = generate_scene_report(
            scene_index=i,
            engine=engine,
            duration_frames=scene.duration,
            scene_path=sp,
            content_hash=getattr(video, "content_hash", lambda: "")() if callable(getattr(video, "content_hash", None)) else "",
        )
        write_scene_report(sr, sp)
        scene_reports.append(sr)

    final = concatenate_scenes(scene_paths, output_path)

    info = get_media_info(final)
    fmt = info.get("format", {})

    # Generate report artifact with scene summary
    engines = list({s.renderer for s in video.scenes if s.renderer})
    from videoforge.review.frame_reviewer import generate_video_report, write_video_report
    report = generate_video_report(
        video_path=str(final),
        content_hash=video.content_hash(),
        engine_mix=engines,
        render_format={"fps": video.fps, "width": video.width, "height": video.height,
                       "pixel_format": "yuv420p", "video_codec": "h264", "audio_codec": "aac"},
        scene_reports=scene_reports,
        coherence_result=coherence_result,
    )
    report_path = write_video_report(report, str(final))

    # Emit provenance graph artifact linking scenes → engines → assets → reports
    from videoforge.review.frame_reviewer import (
        build_provenance_scenes,
        generate_provenance_graph,
        write_provenance_graph,
    )
    provenance_scenes = build_provenance_scenes(video, scene_paths, build_dir=out_dir)
    provenance = generate_provenance_graph(
        video_path=str(final),
        content_hash=video.content_hash(),
        scenes=provenance_scenes,
        engine_mix=engines,
    )
    provenance_path = write_provenance_graph(provenance, str(final))

    return {
        "video_path": str(Path(final).resolve()),
        "duration_seconds": round(float(fmt.get("duration", 0)), 1),
        "file_size_mb": round(float(fmt.get("size", 0)) / 1e6, 1),
        "scenes": len(scene_paths),
        "frames": video.total_frames(),
        "report_path": report_path,
        "provenance_path": provenance_path,
        "coherence": {
            "coherent": coherence_result["coherent"],
            "issues": coherence_result["issues"],
            "missing_phases": coherence_result["narrative_arc"]["missing_phases"],
        },
    }


@video_mcp.tool()
def engine_generate_manim(
    code: str,
    output_dir: str = "/tmp/vfx-build/manim",
) -> dict:
    """Generate a Manim animation video from Manim Python code.

    Args:
        code: Complete Manim Python script (class SceneName(Scene): ...).
        output_dir: Directory to save the rendered video.

    Returns:
        Rendered video path and status.
    """
    from videoforge.engine.manim_renderer import render_direct
    result = render_direct(code, output_dir)
    return {
        "success": result["success"],
        "video_path": result["video_path"],
        "log": result["log"][:300],
    }


@video_mcp.tool()
def engine_review_video(
    video_path: str,
    elements_json: str = "",
    coherence_result: str = "",
) -> dict:
    """Run full video review (L0 + L1 + L2b layout overlap + coherence).

    L0 samples N frames from the video and checks for blank frames,
    resolution mismatches, palette drift, and freeze. L1 runs ffprobe
    black/frozen frame detection. L2b checks element layout overlap
    and viewport clipping. When ``coherence_result`` is provided, the
    overall verdict also considers narrative coherence.

    Args:
        video_path: Path to the video file.
        elements_json: Optional JSON string or file path with element
            layout metadata (list of dicts with x, y, width, height, id).
        coherence_result: Optional JSON string or file path with
            pre-computed coherence gate result (from ``engine_plan_scenes``
            or ``engine_render_video``).

    Returns:
        Review results with pass/fail per check level.
    """
    from videoforge.review.frame_reviewer import FrameReviewer, _discover_scene_reports, generate_video_report, write_video_report
    from videoforge.review.policy import aggregate

    fr = FrameReviewer()
    l0_result = fr.check_mixed_engine(video_path)
    l0_status = fr.evaluate_l0_policy(l0_result)
    l1_result = fr.check_integrity(video_path)

    # L2b: Layout overlap
    l2_result = None
    l2_status = "pass"
    if elements_json:
        import json as _json
        from pathlib import Path as _Path
        if _Path(elements_json).exists():
            elements = _json.loads(_Path(elements_json).read_text())
        else:
            elements = _json.loads(elements_json)
        l2_result = fr.check_layout_overlap(elements)
        l2_status = fr.evaluate_overlap_policy(l2_result)

    # Coherence result (optional)
    parsed_coherence: dict | None = None
    if coherence_result:
        import json as _json
        from pathlib import Path as _Path
        if _Path(coherence_result).exists():
            parsed_coherence = _json.loads(_Path(coherence_result).read_text())
        else:
            parsed_coherence = _json.loads(coherence_result)

    # Discover per-scene artifacts from disk
    scene_reports = _discover_scene_reports(video_path)

    # Unified policy decision (includes L2 and coherence when provided)
    decision = aggregate(
        l0_result=l0_result,
        l1_result=l1_result,
        l2_result=l2_result,
        coherence_result=parsed_coherence,
    )

    report = generate_video_report(
        video_path=video_path,
        l0_result=l0_result,
        l1_result=l1_result,
        l0_status=l0_status,
        l2_result=l2_result or {"issues": [], "passed": True},
        l2_status=l2_status,
        coherence_result=parsed_coherence,
        scene_reports=scene_reports,
    )
    report["policy_verdict"] = decision["verdict"]
    report_path = write_video_report(report, video_path)

    # Build coherence section for return
    coherence_summary: dict | None = None
    if parsed_coherence:
        coherence_summary = {
            "coherent": parsed_coherence.get("coherent", False),
            "issues": parsed_coherence.get("issues", []),
            "missing_phases": parsed_coherence.get("narrative_arc", {}).get("missing_phases", []),
        }

    return {
        "l0_mixed_engine": {
            "status": l0_status,
            "issues": len(l0_result.get("issues", [])),
            "sampled_frames": l0_result.get("sampled_frames", 0),
            "total_frames": l0_result.get("total_frames", 0),
            "details": l0_result.get("issues", []),
        },
        "l1_frame_integrity": {
            "passed": l1_result.get("passed", False),
            "total_frames": l1_result.get("total_frames", 0),
            "issues": len(l1_result.get("issues", [])),
            "details": l1_result.get("issues", []),
        },
        "l2_layout_overlap": {
            "status": l2_status,
            "issues": len((l2_result or {"issues": []}).get("issues", [])),
            "details": (l2_result or {"issues": []}).get("issues", []),
        },
        "passed": decision["verdict"] == "pass",
        "verdict": decision["verdict"],
        "retry_suggested": decision["retry_suggested"],
        "repair_suggested": decision["repair_suggested"],
        "report_path": report_path,
        "coherence": coherence_summary,
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
