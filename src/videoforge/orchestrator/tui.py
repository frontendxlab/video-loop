#!/usr/bin/env python3
"""
VideoForge Orchestrator TUI — terminal UI for pipeline management.

Usage:
    python3 -m videoforge.orchestrator.tui
    ./vfx-tui
"""

from __future__ import annotations

import asyncio
import time
from pathlib import Path

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, ProgressBar, RichLog, Static

from videoforge.orchestrator.runner import AgentLog, AgentStatus, Stage, StageState


def status_color(status: AgentStatus) -> str:
    return {"idle": "grey", "running": "yellow", "complete": "green", "failed": "red", "skipped": "blue"}.get(status.value, "white")


def status_icon(status: AgentStatus) -> str:
    return {"idle": "○", "running": "◉", "complete": "●", "failed": "✕", "skipped": "—"}.get(status.value, "?")


STAGE_LABELS = {
    Stage.GRILL: "1. Grill Requirements",
    Stage.PLAN: "2. Plan Scenes",
    Stage.TTS: "3. Generate Audio (TTS)",
    Stage.TIMING: "4. Compute Frame Timing",
    Stage.RENDER: "5. Render Scenes",
    Stage.CONCAT: "6. Concatenate Video",
    Stage.REVIEW: "7. Review Quality",
    Stage.DONE: "✓ Complete",
}

AGENTS = [
    ("grill-me", "Requirement Gatherer"),
    ("scene-planner", "Scene Planning Agent"),
    ("tts-agent", "Audio Generation Agent"),
    ("timing-agent", "Animation Timing Agent"),
    ("render-agent", "Video Rendering Agent"),
    ("concat-agent", "Video Assembly Agent"),
    ("review-agent", "Quality Review Agent"),
]


class MainScreen(Screen):
    """Main orchestrator screen with panels."""

    BINDINGS = [
        ("p", "start_pipeline", "Start"),
        ("c", "cancel_pipeline", "Cancel"),
        ("r", "refresh", "Refresh"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Container(
            Horizontal(
                VerticalScroll(id="pipeline-col", classes="panel"),
                VerticalScroll(id="agents-col", classes="panel"),
                id="top-row",
            ),
            RichLog(id="log-panel", highlight=True, markup=True, max_lines=1000),
            Input(placeholder="Press p to start pipeline, q to quit", id="cmd-input"),
            id="app-content",
        )

    def on_mount(self):
        self.runner = None
        self._log_widget = self.query_one("#log-panel", RichLog)
        self._cmd = self.query_one("#cmd-input", Input)
        self._render_pipeline()
        self._render_agents()
        self.title = "VideoForge Orchestrator v1.0"
        self._log("System", "Ready. Press p to start pipeline, q to quit.")

    def _log(self, agent: str, msg: str, level: str = "INFO"):
        ts = time.strftime("%H:%M:%S")
        colors = {"INFO": "green", "WARN": "yellow", "ERROR": "red"}
        c = colors.get(level, "white")
        self._log_widget.write(f"[dim]{ts}[/] [bold]{agent}[/] [{c}]{msg}[/]")

    def _render_pipeline(self):
        col = self.query_one("#pipeline-col", VerticalScroll)
        col.remove_children()
        col.mount(Static("[bold]Pipeline Stages[/]", classes="section-title"))
        for stage in Stage:
            icon = status_icon(AgentStatus.IDLE)
            label = STAGE_LABELS[stage]
            bar = ProgressBar(total=100, show_eta=False, id=f"bar-{stage.value}")
            col.mount(Container(Static(f"{icon} {label}", id=f"stage-{stage.value}"), bar, classes="stage-row"))

    def _render_agents(self):
        col = self.query_one("#agents-col", VerticalScroll)
        col.mount(Static("[bold]Subagents[/]", classes="section-title"))
        for name, role in AGENTS:
            col.mount(Container(
                Static(f"○ [bold]{name}[/]", id=f"agent-name-{name}"),
                Static(f"[dim]{role}[/]", id=f"agent-role-{name}"),
                Static("idle", id=f"agent-status-{name}"),
                id=f"agent-card-{name}", classes="agent-card",
            ))

    def _update_stage(self, stage: Stage, status: AgentStatus, progress: float = 0, msg: str = ""):
        w = self.query_one(f"#stage-{stage.value}", Static)
        w.update(f"{status_icon(status)} {STAGE_LABELS[stage]} [dim]{msg}[/]")
        w.styles.color = status_color(status)
        bar = self.query_one(f"#bar-{stage.value}", ProgressBar)
        bar.progress = int(progress * 100)

    def _update_agent(self, name: str, status: AgentStatus, msg: str = ""):
        w = self.query_one(f"#agent-status-{name}", Static)
        w.update(f"[{status_color(status)}]{status_icon(status)} {msg or status.value}[/]")
        card = self.query_one(f"#agent-card-{name}", Container)
        card.styles.border = ("solid", status_color(status))

    # ── Actions ──

    def action_start_pipeline(self):
        self._log("System", "Starting pipeline...")
        self._run_pipeline()

    action_cancel_pipeline = lambda self: self._log("System", "Cancelled", "WARN")
    action_refresh = lambda self: self._log("System", "Refreshed")
    action_quit = lambda self: self.app.exit()

    @work(thread=True, exit_on_error=False)
    def _run_pipeline(self):
        async def run():
            stages = list(Stage)
            agents_data = [
                ("grill-me", "Grilling requirements..."),
                ("scene-planner", "Planning scenes..."),
                ("tts-agent", "Generating audio..."),
                ("timing-agent", "Computing timing..."),
                ("render-agent", "Rendering video..."),
                ("concat-agent", "Concatenating..."),
                ("review-agent", "Reviewing quality..."),
            ]

            # Simulate: Grill
            self.call_from_thread(self._log, "grill-me", "Analyzing topic...")
            self.call_from_thread(self._update_stage, Stage.GRILL, AgentStatus.RUNNING, 0.5, "Working...")
            self.call_from_thread(self._update_agent, "grill-me", AgentStatus.RUNNING, "analyzing")
            await asyncio.sleep(1.5)
            self.call_from_thread(self._update_stage, Stage.GRILL, AgentStatus.COMPLETE, 1.0, "Done")
            self.call_from_thread(self._update_agent, "grill-me", AgentStatus.COMPLETE, "done")

            # Plan
            self.call_from_thread(self._log, "scene-planner", "Planning 5 scenes...")
            self.call_from_thread(self._update_stage, Stage.PLAN, AgentStatus.RUNNING, 0.5, "Creating scenes...")
            self.call_from_thread(self._update_agent, "scene-planner", AgentStatus.RUNNING, "creating")
            await asyncio.sleep(1.5)
            self.call_from_thread(self._update_stage, Stage.PLAN, AgentStatus.COMPLETE, 1.0, "5 scenes")
            self.call_from_thread(self._update_agent, "scene-planner", AgentStatus.COMPLETE, "done")

            # TTS per scene
            self.call_from_thread(self._update_stage, Stage.TTS, AgentStatus.RUNNING, 0.0, "Scene 1/5...")
            self.call_from_thread(self._update_agent, "tts-agent", AgentStatus.RUNNING, "scene 1/5")
            for i in range(5):
                self.call_from_thread(self._log, "tts-agent", f"Scene {i+1}/5 audio generated")
                self.call_from_thread(self._update_stage, Stage.TTS, AgentStatus.RUNNING, (i+1)/5, f"Scene {i+1}/5")
                await asyncio.sleep(0.8)
            self.call_from_thread(self._update_stage, Stage.TTS, AgentStatus.COMPLETE, 1.0, "5/5 done")
            self.call_from_thread(self._update_agent, "tts-agent", AgentStatus.COMPLETE, "done")

            # Timing
            self.call_from_thread(self._log, "timing-agent", "Computing audio-synced animation timing...")
            self.call_from_thread(self._update_stage, Stage.TIMING, AgentStatus.RUNNING, 0.5, "Computing...")
            self.call_from_thread(self._update_agent, "timing-agent", AgentStatus.RUNNING, "computing")
            await asyncio.sleep(1.5)
            self.call_from_thread(self._update_stage, Stage.TIMING, AgentStatus.COMPLETE, 1.0, "All synced")
            self.call_from_thread(self._update_agent, "timing-agent", AgentStatus.COMPLETE, "done")

            # Render per scene
            self.call_from_thread(self._update_stage, Stage.RENDER, AgentStatus.RUNNING, 0.0, "Scene 1/5...")
            self.call_from_thread(self._update_agent, "render-agent", AgentStatus.RUNNING, "rendering")
            for i in range(5):
                self.call_from_thread(self._log, "render-agent", f"Scene {i+1}/5 rendered")
                self.call_from_thread(self._update_stage, Stage.RENDER, AgentStatus.RUNNING, (i+1)/5, f"Scene {i+1}/5")
                await asyncio.sleep(2.0)
            self.call_from_thread(self._update_stage, Stage.RENDER, AgentStatus.COMPLETE, 1.0, "5/5 rendered")
            self.call_from_thread(self._update_agent, "render-agent", AgentStatus.COMPLETE, "done")

            # Concat
            self.call_from_thread(self._log, "concat-agent", "Concatenating 5 scenes with FFmpeg...")
            self.call_from_thread(self._update_stage, Stage.CONCAT, AgentStatus.RUNNING, 0.5, "Stitching...")
            self.call_from_thread(self._update_agent, "concat-agent", AgentStatus.RUNNING, "stitching")
            await asyncio.sleep(1)
            self.call_from_thread(self._update_stage, Stage.CONCAT, AgentStatus.COMPLETE, 1.0, "Assembled")
            self.call_from_thread(self._update_agent, "concat-agent", AgentStatus.COMPLETE, "done")

            # Review
            self.call_from_thread(self._log, "review-agent", "L1 Frame Review: 0 issues")
            self.call_from_thread(self._update_stage, Stage.REVIEW, AgentStatus.RUNNING, 0.5, "Checking...")
            self.call_from_thread(self._update_agent, "review-agent", AgentStatus.RUNNING, "checking")
            await asyncio.sleep(1)
            self.call_from_thread(self._update_stage, Stage.REVIEW, AgentStatus.COMPLETE, 1.0, "Passed ✓")
            self.call_from_thread(self._update_agent, "review-agent", AgentStatus.COMPLETE, "passed")

            # Done
            self.call_from_thread(self._update_stage, Stage.DONE, AgentStatus.COMPLETE, 1.0, "Video ready!")
            self.call_from_thread(self._log, "System", "Pipeline complete!")

        asyncio.run(run())


class VideoForgeTUI(App):
    TITLE = "VideoForge Orchestrator"
    CSS = """
    Screen {
        background: #1a1a2e;
    }
    #app-content {
        height: 100%;
    }
    #top-row {
        height: 40%;
        margin-bottom: 1;
    }
    .panel {
        width: 50%;
        border: solid #4a90d9;
        padding: 0 1;
        overflow-y: auto;
    }
    #agents-col {
        border: solid #7c5cbf;
    }
    .section-title {
        text-align: center;
        padding: 1 0;
        background: rgba(255,255,255,0.08);
        margin-bottom: 1;
        text-style: bold;
    }
    .stage-row {
        height: 3;
        margin-bottom: 1;
    }
    .stage-row Static {
        width: 50%;
    }
    ProgressBar {
        width: 50%;
    }
    .agent-card {
        height: 3;
        border: solid grey;
        padding: 0 1;
        margin-bottom: 1;
    }
    #log-panel {
        height: 50%;
        border: solid #2a2a4e;
    }
    #cmd-input {
        dock: bottom;
        height: 1;
    }
    Header { background: #0f0f23; }
    Footer { background: #0f0f23; }
    """

    def on_mount(self):
        self.push_screen(MainScreen())


def run():
    app = VideoForgeTUI()
    app.run()


if __name__ == "__main__":
    run()
