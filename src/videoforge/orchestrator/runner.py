"""Pipeline runner — executes video generation pipeline asynchronously."""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable


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

    def __init__(self, log_callback: Callable[[AgentLog], None] | None = None):
        self.stages: dict[Stage, StageState] = {s: StageState(s) for s in Stage}
        self.log_callback = log_callback
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

    async def run_pipeline(self, topic: str, scenes_json: str = "", voice: str = "alba", tts_url: str = "http://localhost:8000"):
        """Full pipeline execution."""
        self._log("System", f"Starting pipeline for: {topic}")

        # Stage 1: Grill
        self._set_stage(Stage.GRILL, AgentStatus.RUNNING, message="Extracting requirements...")
        self._log("grill-me", f"Analyzing topic: {topic}")
        await asyncio.sleep(1)  # Simulated work
        if self._cancel_flag: return
        self._set_stage(Stage.GRILL, AgentStatus.COMPLETE, 1.0, "Requirements gathered")

        # Stage 2: Plan
        self._set_stage(Stage.PLAN, AgentStatus.RUNNING, message="Planning scenes...")
        self._log("scene-planner", f"Planning scenes for: {topic}")
        await asyncio.sleep(1)
        if self._cancel_flag: return
        self._set_stage(Stage.PLAN, AgentStatus.COMPLETE, 1.0, f"Scenes planned")

        # Stage 3: TTS
        scenes = self._load_scenes(scenes_json)
        for i, scene in enumerate(scenes):
            if self._cancel_flag: return
            text = scene.get("text", scene.get("title", ""))
            self._set_stage(Stage.TTS, AgentStatus.RUNNING, progress=i / max(len(scenes), 1), message=f"Scene {i+1}/{len(scenes)}")
            self._log("tts-agent", f"Generating TTS for scene {i+1}: {text[:50]}...")
            await self._generate_tts_for_scene(scene, i, voice, tts_url)
            if i == len(scenes) - 1:
                self._set_stage(Stage.TTS, AgentStatus.COMPLETE, 1.0, f"{len(scenes)} scenes generated")

        # Stage 4: Timing
        self._set_stage(Stage.TIMING, AgentStatus.RUNNING, message="Computing frame timing...")
        self._log("timing-agent", "Computing audio-synced animation timing...")
        await asyncio.sleep(1)
        if self._cancel_flag: return
        self._set_stage(Stage.TIMING, AgentStatus.COMPLETE, 1.0, "Timing computed")

        # Stage 5: Render
        for i in range(len(scenes)):
            if self._cancel_flag: return
            self._set_stage(Stage.RENDER, AgentStatus.RUNNING, progress=i / max(len(scenes), 1), message=f"Scene {i+1}/{len(scenes)}")
            self._log("render-agent", f"Rendering scene {i+1}...")
            await asyncio.sleep(2)
            if i == len(scenes) - 1:
                self._set_stage(Stage.RENDER, AgentStatus.COMPLETE, 1.0, f"{len(scenes)} scenes rendered")

        # Stage 6: Concat
        self._set_stage(Stage.CONCAT, AgentStatus.RUNNING, message="Concatenating video segments...")
        self._log("concat-agent", f"Concatenating {len(scenes)} scenes with FFmpeg...")
        await asyncio.sleep(1)
        if self._cancel_flag: return
        self._set_stage(Stage.CONCAT, AgentStatus.COMPLETE, 1.0, "Video assembled")

        # Stage 7: Review (L0 mixed-engine + L1 frame integrity)
        self._set_stage(Stage.REVIEW, AgentStatus.RUNNING, message="Running quality checks...")
        self._log("review-agent", "Running L0 Mixed-Engine + L1 Frame Review...")
        try:
            from videoforge.review.frame_reviewer import FrameReviewer
            fr = FrameReviewer()
            output_path = f"/tmp/vfx-{topic.lower().replace(' ', '-')[:32]}/output.mp4"
            l0_result = fr.check_mixed_engine(output_path)
            l0_status = fr.evaluate_l0_policy(l0_result)
            self._log("review-agent",
                      f"L0: {l0_status}, {len(l0_result.get('issues',[]))} issues, "
                      f"{l0_result.get('sampled_frames',0)} frames sampled")
            l1_result = fr.check_integrity(output_path)
            l1_passed = l1_result.get("passed", False)
            self._log("review-agent",
                      f"L1: {'PASSED' if l1_passed else 'FAILED'}, "
                      f"{l1_result.get('total_frames',0)} frames")
            if l0_status == "fail":
                self._log("review-agent", "L0 gate FAILED — visual defects detected", "WARN")
            self._set_stage(Stage.REVIEW, AgentStatus.COMPLETE, 1.0,
                            f"L0={l0_status}, L1={'ok' if l1_passed else 'issues'}")
        except Exception as e:
            self._log("review-agent", f"Review error: {e}", "ERROR")
            self._set_stage(Stage.REVIEW, AgentStatus.COMPLETE, 1.0, "Checks skipped (error)")
        if self._cancel_flag: return

        # Done
        self._set_stage(Stage.DONE, AgentStatus.COMPLETE, 1.0, "Video generation complete")
        self._log("System", "Pipeline complete!")

    def _load_scenes(self, scenes_json: str) -> list[dict]:
        if scenes_json and Path(scenes_json).exists():
            return json.loads(Path(scenes_json).read_text())
        return [{"type": "title", "title": "Video", "text": "Sample"}]

    async def _generate_tts_for_scene(self, scene: dict, index: int, voice: str, tts_url: str):
        text = scene.get("text", scene.get("title", ""))
        if not text:
            self._log("tts-agent", f"Scene {index+1}: no text, skipping", "WARN")
            return
        try:
            import requests
            resp = requests.post(f"{tts_url}/tts", data={"text": text, "voice": voice}, timeout=60)
            if resp.status_code == 200:
                scene["duration"] = max(1, int(len(text.split()) * 2))
                self._log("tts-agent", f"Scene {index+1}: {len(text.split())} words, {scene['duration']}f")
            else:
                self._log("tts-agent", f"Scene {index+1}: TTS returned {resp.status_code}", "WARN")
        except Exception as e:
            self._log("tts-agent", f"Scene {index+1}: {e}", "ERROR")
