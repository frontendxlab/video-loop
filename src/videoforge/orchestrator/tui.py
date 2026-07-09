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
from typing import Any

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, ProgressBar, RichLog, Static

from videoforge.orchestrator.runner import AgentLog, AgentStatus, Stage, StageState

# Import review panel for integration into TUI screens
from videoforge.review.review_panel import ReviewPanel, make_review_panel_from_report


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
                VerticalScroll(id="review-col", classes="panel"),
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
        self._render_review_column()
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

    def _render_review_column(self):
        """Mount ReviewPanel in the review column (empty by default)."""
        col = self.query_one("#review-col", VerticalScroll)
        col.remove_children()
        col.mount(Static("[bold]Review Controls[/]", classes="section-title"))
        self._review_panel = ReviewPanel(
            id="review-controls",
            on_retry=self._on_review_retry,
            on_reroute=self._on_review_reroute,
            on_stop=self._on_review_stop,
            on_repair=self._on_review_repair,
        )
        col.mount(self._review_panel)

    def _update_review_panel(self, report_path: str | None = None, coherence_path: str | None = None):
        """Update ReviewPanel from report JSON files.

        Called during review stage — loads report artifact and refreshes
        the review panel widget tree.
        """
        if not report_path:
            self._review_panel.refresh_from(report={}, coherence={}, aggregate={})
            return

        from pathlib import Path

        rp = Path(report_path)
        if not rp.exists():
            self._log("review", f"Report not found: {report_path}", "WARN")
            return

        import json
        try:
            with open(rp) as f:
                report = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            self._log("review", f"Failed to load report: {exc}", "ERROR")
            return

        coherence: dict[str, Any] = {}
        if coherence_path:
            cp = Path(coherence_path)
            if cp.exists():
                try:
                    with open(cp) as f:
                        coherence = json.load(f)
                except (json.JSONDecodeError, OSError):
                    pass

        from videoforge.review.policy import aggregate as aggregate_verdict

        agg = aggregate_verdict(
            l0_result=report.get("l0_summary"),
            l1_result=report.get("l1_summary"),
            l2_result=report.get("l2_layout_overlap_summary"),
            coherence_result=coherence or None,
        )

        self._review_panel.refresh_from(report=report, coherence=coherence, aggregate=agg)

    # ── Review action callbacks ──

    def _on_review_retry(self, scene_id: str) -> None:
        self._log("review", f"Retry requested for scene {scene_id}", "WARN")

    def _on_review_reroute(self, scene_id: str, engine: str) -> None:
        self._log("review", f"Reroute scene {scene_id} to {engine}", "WARN")

    def _on_review_stop(self) -> None:
        self._log("review", "Stop requested", "ERROR")
        self.action_cancel_pipeline()

    def _on_review_repair(self, action: dict) -> None:
        self._log("review", f"Repair action: {action}", "WARN")

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
            self.call_from_thread(self._update_stage, Stage.REVIEW, AgentStatus.RUNNING, 0.3, "Loading report...")
            self.call_from_thread(self._update_agent, "review-agent", AgentStatus.RUNNING, "checking")

            # Load report into review panel
            report_path = str(Path("test.mp4.report.json").resolve())
            coherence_path = str(Path("videos/claude-architect-fundamentals.mp4.report.json").resolve())
            self.call_from_thread(self._update_review_panel, report_path, coherence_path)
            await asyncio.sleep(0.5)

            self.call_from_thread(self._log, "review-agent", "L0 Visual: 2 issues found")
            self.call_from_thread(self._update_stage, Stage.REVIEW, AgentStatus.RUNNING, 0.7, "Issues found")
            await asyncio.sleep(0.5)

            self.call_from_thread(self._log, "review-agent", "Repair plan built: rerender blank frames")
            self.call_from_thread(self._update_stage, Stage.REVIEW, AgentStatus.RUNNING, 0.9, "Repairing...")
            await asyncio.sleep(0.5)

            self.call_from_thread(self._update_stage, Stage.REVIEW, AgentStatus.COMPLETE, 1.0, "Review complete")
            self.call_from_thread(self._update_agent, "review-agent", AgentStatus.COMPLETE, "done")

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
        width: 33%;
        border: solid #4a90d9;
        padding: 0 1;
        overflow-y: auto;
    }
    #agents-col {
        border: solid #7c5cbf;
    }
    #review-col {
        border: solid #2d8a4e;
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

    /* ── Review panel styling ────────────────────────────── */
    #review-controls {
        height: 100%;
    }
    #verdict-banner {
        border: solid #4a90d9;
        padding: 1;
        margin-bottom: 1;
        text-align: center;
    }
    .verdict-text {
        text-style: bold;
        text-align: center;
    }
    .verdict-levels {
        text-align: center;
        margin-top: 1;
    }
    .verdict-extras {
        text-align: center;
        margin-top: 1;
    }
    .level-cards {
        margin-bottom: 1;
    }
    .level-card {
        border: solid #3a3a5e;
        padding: 0 1;
        margin-bottom: 1;
    }
    .card-header {
        height: 1;
    }
    .card-title {
        width: 70%;
    }
    .status-badge {
        width: 30%;
        text-align: right;
    }
    .severity-tag {
        width: 8;
    }
    .card-issue {
        height: 1;
        margin-left: 1;
    }
    .card-issue-text {
        width: 1fr;
    }
    .card-meta, .card-more, .card-severity {
        margin-left: 1;
    }
    .card-issues-label {
        margin-top: 1;
    }
    .repair-plan {
        margin-bottom: 1;
    }
    .repair-action-card {
        border: solid #5a3a3e;
        padding: 0 1;
        margin-bottom: 1;
    }
    .repair-action-desc {
        margin-bottom: 1;
    }
    .repair-btn {
        width: 100%;
    }
    .action-bar-buttons {
        height: 3;
        margin-bottom: 1;
    }
    .action-bar-buttons Button {
        width: 1fr;
        margin: 0 1;
    }
    .scene-artifacts {
        margin-bottom: 1;
    }
    .scene-ref {
        height: 1;
        margin-left: 1;
    }
    .scene-ref-status {
        width: 10;
        text-align: right;
    }
    .empty-state {
        text-align: center;
        color: #666;
        margin: 1 0;
    }
    .count-badge {
        margin-left: 1;
    }
    .artifact-count {
        margin-left: 1;
    }

    /* ── Responsive collapse for narrow terminals ────────── */
    @media (max-width: 120) {
        .panel {
            width: 50%;
        }
        #review-col {
            display: none;
        }
    }
    @media (max-width: 80) {
        .panel {
            width: 100%;
        }
        #agents-col {
            display: none;
        }
    }
    """

    def on_mount(self):
        self.push_screen(MainScreen())


def run():
    app = VideoForgeTUI()
    app.run()


if __name__ == "__main__":
    run()
