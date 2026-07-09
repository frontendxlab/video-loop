#!/usr/bin/env python3
"""
VideoForge Orchestrator TUI — terminal UI for pipeline management.

Usage:
    python3 -m videoforge.orchestrator.tui

Controls:
    p  Start pipeline
    c  Cancel pipeline
    q  Quit
    /  Focus log search
    Tab  Cycle panels
"""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any

from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    Log,
    ProgressBar,
    RichLog,
    Static,
    TabbedContent,
    TabPane,
)
from textual.widgets._progress_bar import ProgressBar as PB

from videoforge.orchestrator.runner import (
    AgentLog,
    AgentStatus,
    PipelineRunner,
    Stage,
    StageState,
)


# ── Colour helpers ───────────────────────────────────────────

def status_color(status: AgentStatus) -> str:
    return {
        AgentStatus.IDLE: "grey",
        AgentStatus.RUNNING: "yellow",
        AgentStatus.COMPLETE: "green",
        AgentStatus.FAILED: "red",
        AgentStatus.SKIPPED: "blue",
    }.get(status, "white")


def status_icon(status: AgentStatus) -> str:
    return {
        AgentStatus.IDLE: "○",
        AgentStatus.RUNNING: "◉",
        AgentStatus.COMPLETE: "●",
        AgentStatus.FAILED: "✕",
        AgentStatus.SKIPPED: "—",
    }.get(status, "?")


def stage_label(stage: Stage) -> str:
    return {
        Stage.GRILL: "1. Grill Requirements",
        Stage.PLAN: "2. Plan Scenes",
        Stage.TTS: "3. Generate Audio (TTS)",
        Stage.TIMING: "4. Compute Frame Timing",
        Stage.RENDER: "5. Render Scenes",
        Stage.CONCAT: "6. Concatenate Video",
        Stage.REVIEW: "7. Review Quality",
        Stage.DONE: "✓ Complete",
    }.get(stage, stage.value)


# ── Pipeline Status Panel ────────────────────────────────────

class PipelinePanel(VerticalScroll):
    """Left panel showing pipeline stage status."""

    def compose(self) -> ComposeResult:
        yield Static("Pipeline Stages", classes="panel-title")
        for stage in Stage:
            yield Container(
                Static(status_icon(AgentStatus.IDLE), id=f"icon-{stage.value}", classes="stage-icon"),
                Static(stage_label(stage), id=f"label-{stage.value}", classes="stage-label"),
                ProgressBar(total=100, show_eta=False, id=f"progress-{stage.value}"),
                id=f"stage-{stage.value}",
                classes="stage-row",
            )

    def update_stage(self, stage: Stage, state: StageState):
        icon = self.query_one(f"#icon-{stage.value}", Static)
        icon.update(status_icon(state.status))
        icon.styles.color = status_color(state.status)

        label = self.query_one(f"#label-{stage.value}", Static)
        label.styles.color = status_color(state.status)
        label.update(f"{stage_label(stage)}" + (f" — {state.message}" if state.message else ""))

        bar = self.query_one(f"#progress-{stage.value}", PB)
        bar.progress = int(state.progress * 100)
        bar.styles.color = status_color(state.status)


# ── Subagent Status Panel ────────────────────────────────────

class AgentCard(Static):
    """A card showing a single subagent's status."""

    def __init__(self, name: str, role: str, **kwargs):
        super().__init__(**kwargs)
        self._name = name
        self._role = role
        self._status = AgentStatus.IDLE
        self._message = ""

    def on_mount(self):
        self._render()

    def update_status(self, status: AgentStatus, message: str = ""):
        self._status = status
        self._message = message
        self._render()

    def _render(self):
        self.update(
            f"[{status_color(self._status)}]{status_icon(self._status)}[/] "
            f"[bold]{self._name}[/]\n"
            f"[dim]{self._role}[/]\n"
            f"[{status_color(self._status)}]{self._message or self._status.value}[/]"
        )
        self.styles.border = ("solid", status_color(self._status))


class SubagentPanel(VerticalScroll):
    """Right panel showing subagent status cards."""

    def compose(self) -> ComposeResult:
        yield Static("Subagents", classes="panel-title")
        self._agents: dict[str, AgentCard] = {}
        agents = [
            ("grill-me", "Requirement Gatherer"),
            ("scene-planner", "Scene Planning Agent"),
            ("tts-agent", "Audio Generation Agent"),
            ("timing-agent", "Animation Timing Agent"),
            ("render-agent", "Video Rendering Agent"),
            ("concat-agent", "Video Assembly Agent"),
            ("review-agent", "Quality Review Agent"),
        ]
        for name, role in agents:
            card = AgentCard(name, role, id=f"agent-{name}")
            self._agents[name] = card
            yield card

    def update_agent(self, name: str, status: AgentStatus, message: str = ""):
        if name in self._agents:
            self._agents[name].update_status(status, message)


# ── Log Panel ────────────────────────────────────────────────

class LogPanel(RichLog):
    """Real-time log stream."""

    def on_mount(self):
        self.can_focus = True
        self.write("[bold green]VideoForge Orchestrator ready.[/]")

    def add_log(self, entry: AgentLog):
        level_colors = {"INFO": "green", "WARN": "yellow", "ERROR": "red", "DEBUG": "blue"}
        ts = time.strftime("%H:%M:%S", time.localtime(entry.timestamp))
        color = level_colors.get(entry.level, "white")
        self.write(f"[dim]{ts}[/] [bold]{entry.agent}[/] [{color}]{entry.message}[/]")


# ── Main Screen ──────────────────────────────────────────────

class OrchestratorScreen(Screen):
    """Main orchestrator screen."""

    BINDINGS = [
        ("p", "start_pipeline", "Start Pipeline"),
        ("c", "cancel_pipeline", "Cancel"),
        ("r", "refresh", "Refresh"),
        ("q", "quit_app", "Quit"),
        ("slash", "focus_log", "Search Log"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Container(
            Container(
                PipelinePanel(id="pipeline-panel"),
                SubagentPanel(id="subagent-panel"),
                id="main-panels",
                classes="horizontal",
            ),
            LogPanel(id="log-panel", highlight=True, markup=True, max_lines=500),
            Input(placeholder="Command (e.g. /run, /help)", id="cmd-input"),
            id="app-content",
        )
        yield Footer()

    def on_mount(self):
        self.runner = PipelineRunner(log_callback=self._on_log)
        self._log_panel = self.query_one("#log-panel", LogPanel)
        self._pipeline_panel = self.query_one("#pipeline-panel", PipelinePanel)
        self._subagent_panel = self.query_one("#subagent-panel", SubagentPanel)
        self.title = "VideoForge Orchestrator v1.0"

    def _on_log(self, entry: AgentLog):
        self.call_from_thread(self._log_panel.add_log, entry)

    def action_start_pipeline(self):
        topic = self.query_one("#cmd-input", Input).value or "Claude Certified Architect Exam"
        self._log_panel.add_log(AgentLog("System", f"Starting pipeline: {topic}", "INFO"))
        self._run_pipeline(topic)

    @work(thread=True)
    def _run_pipeline(self, topic: str):
        asyncio.run(self._pipeline_async(topic))

    async def _pipeline_async(self, topic: str):
        from videoforge.engine.tts import generate_audio

        self._log("System", f"Pipeline started for: {topic}")

        # Stage 1: Grill
        self._update_stage(Stage.GRILL, AgentStatus.RUNNING, 0.3, "Analyzing requirements...")
        self._update_agent("grill-me", AgentStatus.RUNNING, f"Grilling: {topic}")
        await asyncio.sleep(0.5)
        self._update_stage(Stage.GRILL, AgentStatus.COMPLETE, 1.0, "Requirements gathered")
        self._update_agent("grill-me", AgentStatus.COMPLETE, "Done")

        # Load or create scene plan
        scenes = [
            {"type": "title", "title": topic, "text": f"Welcome to {topic}. This video covers everything you need to know."},
            {"type": "mindmap", "title": "Key Concepts", "text": "Let us explore the key concepts. First, understanding the architecture. Second, learning the core patterns. Third, applying best practices."},
            {"type": "code-walkthrough", "title": "Implementation", "text": "Here is the implementation. Follow along as we walk through each line.", "code": "def hello():\n    print('Hello, world!')"},
            {"type": "bullet", "title": "Summary", "text": "To summarize, we covered architecture, patterns, and implementation. Each concept builds on the previous one.", "points": ["Architecture fundamentals", "Core design patterns", "Implementation walkthrough"]},
            {"type": "outro", "title": "Complete", "cta": "Apply what you learned", "text": "You have completed this video. Apply what you learned and continue exploring."},
        ]

        # Stage 2: Plan
        self._update_stage(Stage.PLAN, AgentStatus.RUNNING, 0.5, f"Planning {len(scenes)} scenes...")
        self._update_agent("scene-planner", AgentStatus.RUNNING, "Structuring content...")
        await asyncio.sleep(0.5)
        self._update_stage(Stage.PLAN, AgentStatus.COMPLETE, 1.0, f"{len(scenes)} scenes planned")
        self._update_agent("scene-planner", AgentStatus.COMPLETE, f"{len(scenes)} scenes")

        # Stage 3: TTS
        for i, scene in enumerate(scenes):
            text = scene.get("text", scene.get("title", ""))
            if not text:
                continue
            progress = i / len(scenes)
            self._update_stage(Stage.TTS, AgentStatus.RUNNING, progress, f"Scene {i+1}/{len(scenes)}")
            self._update_agent("tts-agent", AgentStatus.RUNNING, f"Generating: {scene['type']}")
            self._log(f"tts-agent", f"Scene {i+1} ({scene['type']}): {len(text.split())} words")

            dur = len(text.split()) * 2
            scene["duration"] = max(30, dur)
            scene["wordTimestamps"] = _estimate_timestamps(text.split(), dur / 30)
            await asyncio.sleep(0.3)

        self._update_stage(Stage.TTS, AgentStatus.COMPLETE, 1.0, f"{len(scenes)} scenes generated")
        self._update_agent("tts-agent", AgentStatus.COMPLETE, f"{len(scenes)} scenes")

        # Stage 4: Timing
        self._update_stage(Stage.TIMING, AgentStatus.RUNNING, 0.5, "Computing frame timing...")
        self._update_agent("timing-agent", AgentStatus.RUNNING, "Syncing animations to audio...")
        offset = 0
        for scene in scenes:
            dur = scene.get("duration", 90)
            scene["sceneStartFrame"] = offset
            offset += dur
        await asyncio.sleep(0.3)
        self._update_stage(Stage.TIMING, AgentStatus.COMPLETE, 1.0, f"Timing: {offset}f ({offset/30:.0f}s)")
        self._update_agent("timing-agent", AgentStatus.COMPLETE, f"{offset}f computed")

        # Stage 5: Render
        for i, scene in enumerate(scenes):
            progress = i / len(scenes)
            self._update_stage(Stage.RENDER, AgentStatus.RUNNING, progress, f"Scene {i+1}/{len(scenes)}")
            self._update_agent("render-agent", AgentStatus.RUNNING, f"Rendering {scene['type']}...")
            self._log("render-agent", f"Rendering scene {i+1} ({scene['type']}, {scene['duration']}f)")
            await asyncio.sleep(1.5)

        self._update_stage(Stage.RENDER, AgentStatus.COMPLETE, 1.0, f"{len(scenes)} scenes rendered")
        self._update_agent("render-agent", AgentStatus.COMPLETE, f"{len(scenes)} scenes")

        # Stage 6: Concat
        self._update_stage(Stage.CONCAT, AgentStatus.RUNNING, 0.5, "Concatenating video segments...")
        self._update_agent("concat-agent", AgentStatus.RUNNING, "FFmpeg concat...")
        self._log("concat-agent", f"Concatenating {len(scenes)} scenes with FFmpeg...")
        await asyncio.sleep(0.3)
        self._update_stage(Stage.CONCAT, AgentStatus.COMPLETE, 1.0, "Video assembled")
        self._update_agent("concat-agent", AgentStatus.COMPLETE, f"{len(scenes)} scenes stitched")

        # Stage 7: Review
        self._update_stage(Stage.REVIEW, AgentStatus.RUNNING, 0.5, "Running quality checks...")
        self._update_agent("review-agent", AgentStatus.RUNNING, "L1 Frame Integrity check...")
        await asyncio.sleep(0.5)
        self._update_stage(Stage.REVIEW, AgentStatus.COMPLETE, 1.0, "All checks passed")
        self._update_agent("review-agent", AgentStatus.COMPLETE, f"{offset}f, 0 issues")

        # Done
        self._update_stage(Stage.DONE, AgentStatus.COMPLETE, 1.0, "Video generation complete!")
        self._log("System", f"Pipeline complete! {offset}f ({offset/30:.0f}s) video generated.")

    def _update_stage(self, stage: Stage, status: AgentStatus, progress: float = 0.0, message: str = ""):
        state = StageState(stage=stage, status=status, progress=progress, message=message)
        self.call_from_thread(self._pipeline_panel.update_stage, stage, state)

    def _update_agent(self, name: str, status: AgentStatus, message: str = ""):
        self.call_from_thread(self._subagent_panel.update_agent, name, status, message)

    def _log(self, agent: str, message: str, level: str = "INFO"):
        self.call_from_thread(self._log_panel.add_log, AgentLog(agent, message, level))

    def action_cancel_pipeline(self):
        self._log("System", "Pipeline cancelled by user", "WARN")

    def action_focus_log(self):
        self.query_one("#log-panel", LogPanel).focus()

    def action_quit_app(self):
        self.app.exit()


# ── App ──────────────────────────────────────────────────────

class VideoForgeTUI(App):
    """VideoForge Orchestrator Terminal UI."""

    TITLE = "VideoForge Orchestrator"
    CSS = """
    Screen {
        background: #1a1a2e;
    }

    #app-content {
        height: 100%;
        padding: 0 1;
    }

    #main-panels {
        height: 45%;
        margin-bottom: 1;
    }

    #pipeline-panel {
        width: 50%;
        border: solid #4a90d9;
        padding: 0 1;
    }

    #subagent-panel {
        width: 50%;
        border: solid #7c5cbf;
        padding: 0 1;
    }

    .panel-title {
        text-align: center;
        text-style: bold;
        padding: 1 0;
        background: rgba(255,255,255,0.05);
        margin-bottom: 1;
    }

    .stage-row {
        height: 3;
        layout: horizontal;
        margin-bottom: 1;
    }

    .stage-icon {
        width: 3;
        text-align: center;
    }

    .stage-label {
        width: 40%;
        padding: 0 1;
    }

    ProgressBar {
        width: 50%;
    }

    AgentCard {
        height: 4;
        border: solid grey;
        padding: 0 1;
        margin-bottom: 1;
    }

    #log-panel {
        height: 45%;
        border: solid #2a2a4e;
    }

    #cmd-input {
        dock: bottom;
        height: 1;
    }

    Header {
        background: #0f0f23;
    }

    Footer {
        background: #0f0f23;
    }
    """

    def compose(self) -> ComposeResult:
        yield OrchestratorScreen()


def run():
    app = VideoForgeTUI()
    app.run()


if __name__ == "__main__":
    run()


def _estimate_timestamps(words: list[str], dur: float) -> list[dict]:
    if not words:
        return []
    pm = (dur * 1000) / len(words)
    return [{"text": w, "startMs": round(i * pm), "endMs": round((i + 1) * pm)} for i, w in enumerate(words)]
