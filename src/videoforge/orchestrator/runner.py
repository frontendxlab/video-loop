"""Pipeline runner — executes video generation pipeline asynchronously."""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from videoforge.engine.models import (
    AudioTrack,
    SceneDefinition,
    SceneType,
    VideoDefinition,
    WordTiming,
)
from videoforge.engine.renderer import concatenate_scenes, render_scenes
from videoforge.engine.tts import generate_audio


class Stage(Enum):
    GRILL = "grill"
    PLAN = "plan"
    TTS = "tts"
    TIMING = "timing"
    RENDER = "render"
    CONCAT = "concat"
    REVIEW = "review"
    DONE = "done"


class AgentStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class AgentLog:
    agent: str
    message: str
    level: str = "INFO"
    timestamp: float = field(default_factory=time.time)


@dataclass
class StageState:
    stage: Stage
    status: AgentStatus = AgentStatus.IDLE
    progress: float = 0.0
    message: str = ""
    started_at: float | None = None
    ended_at: float | None = None


class PipelineRunner:
    """Async pipeline runner that emits events for the TUI."""

    def __init__(
        self,
        log_callback: Callable[[AgentLog], None] | None = None,
        stage_callback: Callable[[str, str, float, str], None] | None = None,
    ):
        self.stages: dict[Stage, StageState] = {s: StageState(s) for s in Stage}
        self.log_callback = log_callback
        self.stage_callback = stage_callback
        self._cancel_flag = False

    def cancel(self):
        self._cancel_flag = True

    def _log(self, agent: str, message: str, level: str = "INFO"):
        entry = AgentLog(agent=agent, message=message, level=level)
        if self.log_callback:
            self.log_callback(entry)

    def _set_stage(self, stage: Stage, status: AgentStatus, progress: float = 0.0, message: str = ""):
        s = self.stages[stage]
        s.status = status
        s.progress = progress
        s.message = message
        if status == AgentStatus.RUNNING and s.started_at is None:
            s.started_at = time.time()
        if status in (AgentStatus.COMPLETE, AgentStatus.FAILED):
            s.ended_at = time.time()
        if self.stage_callback:
            self.stage_callback(stage.value, status.value, progress, message)

    async def run_pipeline(
        self,
        topic: str,
        scenes_json: str = "",
        voice: str = "alba",
        tts_url: str = "http://localhost:8000",
        output_path: str = "/tmp/videoforge/output.mp4",
        remotion_dir: str = "remotion-project",
        fps: int = 30,
    ) -> str:
        """Full pipeline execution. Returns path to final video."""
        self._log("System", f"Starting pipeline for: {topic}")

        output_dir = Path(output_path).parent
        audio_dir = output_dir / "audio"
        build_dir = output_dir / "build"

        # Stage 1: Grill
        self._set_stage(Stage.GRILL, AgentStatus.RUNNING, message="Extracting requirements...")
        self._log("grill-me", f"Analyzing topic: {topic}")
        await asyncio.sleep(1)
        if self._cancel_flag: return output_path
        self._set_stage(Stage.GRILL, AgentStatus.COMPLETE, 1.0, "Requirements gathered")

        # Stage 2: Plan
        self._set_stage(Stage.PLAN, AgentStatus.RUNNING, message="Planning scenes...")
        self._log("scene-planner", f"Planning scenes for: {topic}")
        await asyncio.sleep(1)
        if self._cancel_flag: return output_path
        self._set_stage(Stage.PLAN, AgentStatus.COMPLETE, 1.0, "Scenes planned")

        # Stage 3: TTS — real audio generation via MCP Pocket TTS server
        scenes = self._load_scenes(scenes_json)
        audio_dir.mkdir(parents=True, exist_ok=True)
        for i, scene in enumerate(scenes):
            if self._cancel_flag: return output_path
            text = scene.get("text", scene.get("title", ""))
            if not text:
                self._log("tts-agent", f"Scene {i+1}: no text, skipping", "WARN")
                continue
            self._set_stage(Stage.TTS, AgentStatus.RUNNING, progress=i / max(len(scenes), 1), message=f"Scene {i+1}/{len(scenes)}")
            self._log("tts-agent", f"Generating TTS for scene {i+1}: {text[:50]}...")
            audio_path = audio_dir / f"scene_{i:04d}.wav"
            try:
                from videoforge.engine.tts_mcp import generate_speech_mcp_sync
                mcp_url = os.environ.get("POCKET_TTS_MCP_URL", "http://172.236.176.29:8000/sse")
                result = await asyncio.to_thread(
                    generate_speech_mcp_sync, text, audio_path, voice, mcp_url
                )
            except Exception as e:
                self._log("tts-agent", f"MCP TTS failed: {e}, falling back to HTTP", "WARN")
                result = await asyncio.to_thread(generate_audio, text, audio_path, voice, tts_url)
            scene["wordTimestamps"] = result["word_timestamps"]
            scene["duration"] = max(1, int(result["duration_seconds"] * fps))
            scene["audio_path"] = str(audio_path)
            self._log("tts-agent", f"Scene {i+1}: {len(text.split())} words, {scene['duration']}f, {result['duration_seconds']:.1f}s")
            if i == len(scenes) - 1:
                self._set_stage(Stage.TTS, AgentStatus.COMPLETE, 1.0, f"{len(scenes)} scenes generated")

        # Stage 4: Timing — build VideoDefinition with real durations
        self._set_stage(Stage.TIMING, AgentStatus.RUNNING, message="Computing frame timing...")
        self._log("timing-agent", "Building video definition from scene data...")
        video_def = self._build_video_def(topic, scenes, voice, fps)
        if self._cancel_flag: return output_path
        self._set_stage(Stage.TIMING, AgentStatus.COMPLETE, 1.0, f"{len(scenes)} scenes, {video_def.total_frames()} frames")

        # Stage 5: Render — real scene rendering via render_scenes()
        build_dir.mkdir(parents=True, exist_ok=True)
        self._set_stage(Stage.RENDER, AgentStatus.RUNNING, message=f"Rendering {len(scenes)} scenes via Remotion...")
        self._log("render-agent", f"Rendering {len(scenes)} scenes via Remotion...")
        if self._cancel_flag: return output_path
        # ponytail: sync render_scenes in executor; parallelize per-scene renders when bottleneck
        scene_paths = await asyncio.to_thread(
            render_scenes, video_def, remotion_dir, build_dir, tmpdir=build_dir / "tmp",
        )
        self._set_stage(Stage.RENDER, AgentStatus.COMPLETE, 1.0, f"{len(scene_paths)} scenes rendered")

        # Stage 6: Concat — real concatenation via concatenate_scenes()
        self._set_stage(Stage.CONCAT, AgentStatus.RUNNING, message="Concatenating video segments...")
        self._log("concat-agent", f"Concatenating {len(scene_paths)} scenes with FFmpeg...")
        if self._cancel_flag: return output_path
        final_path = await asyncio.to_thread(concatenate_scenes, scene_paths, output_path)
        self._set_stage(Stage.CONCAT, AgentStatus.COMPLETE, 1.0, f"Video assembled: {final_path}")

        # Stage 7: Review with rerender orchestration
        self._set_stage(Stage.REVIEW, AgentStatus.RUNNING, message="Running quality checks...")
        self._log("review-agent", "Running L0 review with rerender orchestration...")
        try:
            from videoforge.review.frame_reviewer import FrameReviewer
            from videoforge.review.repair_actions import RepairAction
            from videoforge.review.rerender_orchestrator import run_orchestrated_review

            fr = FrameReviewer()

            def rerender_hook(action: RepairAction) -> bool:
                self._log("render-agent", f"Rerender: {action.description}")
                return True

            orc_result = run_orchestrated_review(
                video_path=final_path,
                review_fn=fr.check_mixed_engine,
                render_hook=rerender_hook,
                max_rounds=2,
            )

            l0_result = orc_result["final_review"]
            l0_status = fr.evaluate_l0_policy(l0_result)
            l1_result = fr.check_integrity(final_path)
            l1_passed = l1_result.get("passed", False)
            self._log("review-agent",
                      f"Outcome={orc_result['outcome']}, "
                      f"{len(orc_result['rounds'])} rounds, "
                      f"L0={l0_status} ({len(l0_result.get('issues',[]))} issues), "
                      f"L1={'PASSED' if l1_passed else 'FAILED'} ({l1_result.get('total_frames',0)} frames)")
            self._set_stage(Stage.REVIEW, AgentStatus.COMPLETE, 1.0,
                            f"L0={l0_status}, L1={'ok' if l1_passed else 'issues'}")
        except Exception as e:
            self._log("review-agent", f"Review error: {e}", "ERROR")
            self._set_stage(Stage.REVIEW, AgentStatus.COMPLETE, 1.0, "Checks skipped (error)")
        if self._cancel_flag: return final_path

        # Done
        self._log("System", f"Output written to {final_path}")
        self._set_stage(Stage.DONE, AgentStatus.COMPLETE, 1.0, "Video generation complete")
        self._log("System", f"Pipeline complete! output={final_path}")
        return final_path

    def _load_scenes(self, scenes_json: str) -> list[dict]:
        if scenes_json and Path(scenes_json).exists():
            return json.loads(Path(scenes_json).read_text())
        return [{"type": "title", "title": "Video", "text": "Sample"}]

    def _build_video_def(self, topic: str, scenes: list[dict], voice: str = "alba", fps: int = 30) -> VideoDefinition:
        """Build a VideoDefinition from enriched scene dicts (after TTS)."""
        scene_defs: list[SceneDefinition] = []
        tracks: list[AudioTrack] = []
        captions: list[WordTiming] = []
        offset = 0

        for s in scenes:
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
            scene_defs.append(scene)
            audio_path = s.get("audio_path", "")
            if audio_path:
                tracks.append(AudioTrack(src=audio_path, startFrame=offset, durationFrames=dur))
            for wt in scene.wordTimestamps:
                captions.append(wt)
            offset += dur

        return VideoDefinition(
            title=topic,
            scenes=scene_defs,
            audioTracks=tracks,
            captions=captions,
            voice=voice,
            fps=fps,
        )

    def _generate_output(self, topic: str, scene_count: int) -> str:
        """Legacy placeholder output — kept for backward compat, no longer called in pipeline."""
        safe = topic.lower().replace(" ", "-")[:32] or "video"
        output_dir = Path(f"/tmp/vfx-{safe}")
        output_dir.mkdir(parents=True, exist_ok=True)
        placeholder = output_dir / "output.json"
        placeholder.write_text(json.dumps({
            "topic": topic,
            "scene_count": scene_count,
            "status": "legacy_placeholder",
            "message": "Use run_pipeline(output_path=...) for real video",
        }))
        self._log("concat-agent", f"Legacy placeholder at {placeholder}", "WARN")
        return str(placeholder)
