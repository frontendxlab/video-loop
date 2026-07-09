#!/usr/bin/env python3
"""VideoForge CLI — deterministic video generation application.

Usage:
    videoforge plan --topic "..."           # Plan scenes from topic
    videoforge tts --scene scene.json       # Generate TTS audio
    videoforge time --scene scene.json     # Compute frame timing
    videoforge render --video video.json   # Render video
    videoforge review --video video.mp4    # Review quality
    videoforge report video.mp4            # Print report summary
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
from videoforge.validation.coherence_gate import (
    extract_script_from_scenes,
    log_coherence_results,
    run_coherence_gate,
    write_coherence_report,
)

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

    # Coherence gate
    plan_dict: dict[str, Any] = {"scenes": plan_data}
    script = extract_script_from_scenes(plan_data) or topic
    coherence = run_coherence_gate(script, plan_dict, plan_path=output)
    log_coherence_results(coherence)
    write_coherence_report(coherence, output)


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

    # Emit per-scene report artifacts alongside each scene file
    from videoforge.review.frame_reviewer import generate_scene_report, write_scene_report
    for i, (scene, sp) in enumerate(zip(video_def.scenes, scene_paths)):
        engine = getattr(scene, "renderer", "remotion")
        sr = generate_scene_report(
            scene_index=i,
            engine=engine,
            duration_frames=scene.duration,
            scene_path=sp,
            content_hash=video_def.content_hash(),
        )
        write_scene_report(sr, sp)

    logger.info("Concatenating %d scenes...", len(scene_paths))
    final = concatenate_scenes(scene_paths, output)
    logger.info("Video: %s", final)

    info = get_media_info(final)
    if "format" in info:
        fmt = info["format"]
        logger.info("Duration: %.1fs, Size: %.1fMB", float(fmt.get("duration", 0)), float(fmt.get("size", 0)) / 1e6)


@app.command()
def report_summary(
    video: Annotated[str, typer.Argument(help="Video file path (reads <video>.mp4.report.json)")],
    json_output: Annotated[bool, typer.Option("--json", help="Output raw JSON instead of key=value pairs")] = False,
    scenes: Annotated[bool, typer.Option("--scenes", help="Also scan for per-scene report artifacts")] = False,
):
    """Print deterministic summary from <video>.mp4.report.json and scene artifacts.

    Output key=value lines (script-friendly) or --json for raw report.
    Exit code 0 = all pass, 1 = any fail.
    """
    report_path = Path(video).with_suffix(".mp4.report.json")
    if not report_path.exists():
        typer.echo(f"Error: Report not found: {report_path}")
        raise typer.Exit(1)

    report = json.loads(report_path.read_text())
    l0 = report.get("l0_summary", {})
    l1 = report.get("l1_summary", {})
    l2 = report.get("l2_layout_overlap_summary", {})

    if json_output:
        print(json.dumps(report, indent=2))
    else:
        l0_s = l0.get("status", "?")
        l1_p = l1.get("passed", False)
        l2_s = l2.get("status", "pass")
        if l0_s == "fail" or not l1_p or l2_s == "fail":
            overall = "FAIL"
        elif l0_s == "warn" or l2_s == "warn":
            overall = "WARN"
        else:
            overall = "PASS"
        print(f"REPORT_status={overall}")
        print(f"REPORT_video={report.get('video_path', '')}")
        print(f"REPORT_content_hash={report.get('content_hash', '')}")
        engines = ",".join(report.get("engine_mix", []))
        print(f"REPORT_engines={engines}")
        print(f"REPORT_l0_status={l0.get('status', '?')}")
        print(f"REPORT_l0_issues={l0.get('total_issues', 0)}")
        for sev in ("high", "medium", "low"):
            print(f"REPORT_l0_{sev}={l0.get('severity_counts', {}).get(sev, 0)}")
        print(f"REPORT_l0_sampled={l0.get('sampled_frames', 0)}")
        print(f"REPORT_l0_total_frames={l0.get('total_frames', 0)}")
        print(f"REPORT_l1_passed={str(l1.get('passed', False)).lower()}")
        print(f"REPORT_l1_issues={l1.get('total_issues', 0)}")
        print(f"REPORT_l1_total_frames={l1.get('total_frames', 0)}")
        print(f"REPORT_l2b_status={l2.get('status', 'pass')}")
        print(f"REPORT_l2b_issues={l2.get('total_issues', 0)}")

        if scenes:
            _print_scene_artifacts(report_path.parent)

    all_pass = l0.get("status") != "fail" and l1.get("passed", False) and l2.get("status", "pass") != "fail"
    if not all_pass:
        raise typer.Exit(1)


def _print_scene_artifacts(directory: Path) -> None:
    """Print summary of per-scene report artifacts in directory."""
    for p in sorted(directory.glob("*.mp4.scene.report.json")):
        sr = json.loads(p.read_text())
        print(f"SCENE_{sr.get('scene_index', '?')}_engine={sr.get('engine', '?')}")
        print(f"SCENE_{sr.get('scene_index', '?')}_duration_frames={sr.get('duration_frames', 0)}")


@app.command()
def review(
    video: Annotated[str, typer.Argument(help="Video file path")],
    elements: Annotated[str, typer.Option(help="Elements layout metadata JSON file")] = "",
):
    """Review video quality (L0 mixed-engine + L1 frame integrity + L2b layout overlap)."""
    from videoforge.review.frame_reviewer import run_review

    elements_data = None
    if elements:
        elements_data = json.loads(Path(elements).read_text())

    r = run_review(video, elements=elements_data)
    l0_result = r["l0_result"]
    l0_status = r["l0_status"]
    l1_result = r["l1_result"]
    l2_result = r["l2_result"]
    l2_status = r["l2_status"]

    logger.info("L0 Mixed-Engine: status=%s issues=%d sampled=%d total=%d",
                l0_status, len(l0_result.get("issues", [])),
                l0_result.get("sampled_frames", 0), l0_result.get("total_frames", 0))

    l1_passed = l1_result.get("passed", False)
    l1_label = "PASSED" if l1_passed else "FAILED"
    logger.info("L1 Frame Integrity: %s — %d frames, %d issues",
                l1_label, l1_result.get("total_frames", 0), len(l1_result.get("issues", [])))

    l2_issues = l2_result.get("issues", [])
    if elements:
        logger.info("L2b Layout Overlap: status=%s issues=%d",
                    l2_status, len(l2_issues))
        for issue in l2_issues:
            logger.warning("  [%s] %s: %s",
                           issue.get("severity", "?"),
                           issue.get("type", "?"),
                           issue.get("detail", ""))
    else:
        logger.info("L2b Layout Overlap: skipped (no element metadata)")

    # Combine results
    all_passed = l0_status == "pass" and l1_passed and l2_status == "pass"
    all_issues = l0_result.get("issues", []) + l1_result.get("issues", []) + l2_issues

    if all_passed:
        logger.info("Review: PASSED — 0 issues across all gates")
    else:
        logger.warning("Review: %s — %d total issues (L0=%s, L1=%s, L2b=%s)",
                       "FAIL" if l0_status == "fail" else "WARN",
                       len(all_issues), l0_status, l1_label, l2_status)
        for issue in all_issues:
            sev = issue.get("severity", "?")
            typ = issue.get("type", "?")
            logger.warning("  [%s] %s: %s", sev, typ, issue.get("detail", ""))

    logger.info("Review report: %s", r["report_path"])

    # Fail CLI on L0 or L2b high-severity issues
    if l0_status == "fail" or l2_status == "fail":
        raise typer.Exit(1)


@app.command()
def pipeline(
    topic: Annotated[str, typer.Option(help="Video topic")],
    output: Annotated[str, typer.Option(help="Output MP4 path")] = "videos/output.mp4",
    scenes_json: Annotated[str, typer.Option(help="Scene plan JSON")] = "/tmp/scenes.json",
    voice: Annotated[str, typer.Option(help="TTS voice")] = "alba",
    tts_url: Annotated[str, typer.Option(help="TTS URL")] = "http://localhost:8000",
    elements: Annotated[str, typer.Option(help="Elements layout metadata JSON file")] = "",
):
    """Full pipeline: plan → TTS → render → review (L0 + L1 + L2b)."""
    # Step 1: Plan
    plan.callback(topic=topic, output=scenes_json, voice=voice)

    # Step 1b: Coherence gate on planned scenes
    scenes = json.loads(Path(scenes_json).read_text())
    plan_dict: dict[str, Any] = {"scenes": scenes}
    coherence = run_coherence_gate(topic, plan_dict, plan_path=scenes_json)
    log_coherence_results(coherence)
    write_coherence_report(coherence, scenes_json)

    # Step 2: TTS for each scene
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

    # Step 5: Review (L0 mixed-engine + L1 frame integrity + L2b layout overlap)
    from videoforge.review.frame_reviewer import run_review
    elements_data = None
    if elements:
        elements_data = json.loads(Path(elements).read_text())
    engines = list({s.renderer for s in video_def.scenes if s.renderer})
    r = run_review(output, content_hash=video_def.content_hash(), engine_mix=engines, elements=elements_data)
    l0_result = r["l0_result"]
    l0_status = r["l0_status"]
    l1_result = r["l1_result"]
    l2_result = r["l2_result"]
    l2_status = r["l2_status"]
    l1_passed = l1_result.get("passed", False)
    l2_issues = l2_result.get("issues", [])
    if elements:
        logger.info("Pipeline Review — L0=%s (%d issues), L1=%s (%d issues), L2b=%s (%d issues)",
                    l0_status, len(l0_result.get("issues", [])),
                    "PASSED" if l1_passed else "FAILED", len(l1_result.get("issues", [])),
                    l2_status, len(l2_issues))
    else:
        logger.info("Pipeline Review — L0=%s (%d issues), L1=%s (%d issues)",
                    l0_status, len(l0_result.get("issues", [])),
                    "PASSED" if l1_passed else "FAILED", len(l1_result.get("issues", [])))
    logger.info("Pipeline report: %s", r["report_path"])


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
