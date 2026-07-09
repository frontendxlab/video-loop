"""Advanced review controls panel — L0/L1/L2/coherence summaries, repair plans, actions.

Textual widget that consumes the same dict shapes from
:mod:`videoforge.review.policy` and :mod:`videoforge.review.repair_actions`.
Emits action callbacks; caller wires them to actual rerender/retry logic.

Usage::

    from videoforge.review.review_panel import ReviewPanel

    # In a Textual Screen.compose():
    yield ReviewPanel(
        report=report_dict,
        coherence=coherence_dict,
        aggregate=aggregate_dict,
        on_retry=lambda scene_id: ...,
        on_reroute=lambda scene_id, engine: ...,
        on_stop=lambda: ...,
    )
"""

from __future__ import annotations

from typing import Any, Callable

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, Label, Static

# ── Severity/status helpers ───────────────────────────────────────────────────

_SEVERITY_COLORS: dict[str, str] = {
    "high": "red",
    "medium": "yellow",
    "low": "dim",
}

_STATUS_COLORS: dict[str, str] = {
    "pass": "green",
    "fail": "red",
    "warn": "yellow",
    "retry": "blue",
    "repair": "magenta",
}

_STATUS_ICONS: dict[str, str] = {
    "pass": "✓",
    "fail": "✕",
    "warn": "⚠",
    "retry": "⟳",
    "repair": "🔧",
}

_ACTION_LABELS: dict[str, str] = {
    "rerender": "Rerender",
    "rerender_with_token_reset": "Reset Tokens + Rerender",
}


def _severity_tag(severity: str) -> Static:
    """Return coloured severity badge."""
    color = _SEVERITY_COLORS.get(severity, "white")
    return Static(f"[{color}]{severity.upper()}[/]", classes="severity-tag")


def _status_badge(status: str) -> Static:
    """Return coloured status badge with icon."""
    color = _STATUS_COLORS.get(status, "white")
    icon = _STATUS_ICONS.get(status, "?")
    return Static(f"[{color}]{icon} {status.upper()}[/]", classes="status-badge")


def _count_badge(count: int, label: str = "issues") -> Static:
    color = "green" if count == 0 else "yellow" if count < 3 else "red"
    return Static(f"[{color}]{count} {label}[/]", classes="count-badge")


# ── ReviewPanel widget ────────────────────────────────────────────────────────


class ReviewPanel(Widget):
    """Advanced review controls surface.

    Shows:
      - Aggregate verdict banner
      - Per-level summary cards (L0, L1, L2, coherence)
      - Issue lists with severity tags
      - Repair plan with action buttons
      - Retry / reroute / stop action bar
      - Per-scene artifact references (from scenes_summary)
    """

    report: dict[str, Any] = reactive({})
    coherence: dict[str, Any] = reactive({})
    aggregate: dict[str, Any] = reactive({})

    def __init__(
        self,
        report: dict[str, Any] | None = None,
        coherence: dict[str, Any] | None = None,
        aggregate: dict[str, Any] | None = None,
        on_retry: Callable[[str], None] | None = None,
        on_reroute: Callable[[str, str], None] | None = None,
        on_stop: Callable[[], None] | None = None,
        on_repair: Callable[[dict[str, Any]], None] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._report = report or {}
        self._coherence = coherence or {}
        self._aggregate = aggregate or {}
        self._on_retry = on_retry
        self._on_reroute = on_reroute
        self._on_stop = on_stop
        self._on_repair = on_repair

    def on_mount(self) -> None:
        """After compose, render initial data from constructor args."""
        self._refresh_all()

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="review-panel", classes="review-panel"):
            # ── Verdict banner ──
            yield Container(id="verdict-banner", classes="verdict-banner")
            # ── Level summary cards ──
            yield Label("[bold]Review Levels[/]", classes="section-title")
            with Container(id="level-cards", classes="level-cards"):
                yield Container(id="card-l0", classes="level-card")
                yield Container(id="card-l1", classes="level-card")
                yield Container(id="card-l2", classes="level-card")
                yield Container(id="card-coherence", classes="level-card")
            # ── Repair plan ──
            yield Label("[bold]Repair Plan[/]", classes="section-title")
            yield Container(Static("[dim]No repairs needed[/]", classes="empty-state"), id="repair-plan", classes="repair-plan")
            # ── Action bar ──
            yield Label("[bold]Actions[/]", classes="section-title")
            yield Container(id="action-bar", classes="action-bar")
            # ── Scene artifacts ──
            yield Label("[bold]Scene Artifacts[/]", classes="section-title")
            yield Container(Static("[dim]No scene artifacts[/]", classes="empty-state"), id="scene-artifacts", classes="scene-artifacts")

    def _watch_report(self, val: dict[str, Any]) -> None:
        self._report = val
        if self.is_mounted:
            self._refresh_all()

    def _watch_coherence(self, val: dict[str, Any]) -> None:
        self._coherence = val
        if self.is_mounted:
            self._refresh_all()

    def _watch_aggregate(self, val: dict[str, Any]) -> None:
        self._aggregate = val
        if self.is_mounted:
            self._refresh_all()

    def refresh_from(
        self,
        report: dict[str, Any] | None = None,
        coherence: dict[str, Any] | None = None,
        aggregate: dict[str, Any] | None = None,
    ) -> None:
        """Update all data and re-render."""
        if report is not None:
            self._report = report
        if coherence is not None:
            self._coherence = coherence
        if aggregate is not None:
            self._aggregate = aggregate
        self._refresh_all()

    def _refresh_all(self) -> None:
        try:
            self._render_verdict()
            self._render_level_cards()
            self._render_repair_plan()
            self._render_action_bar()
            self._render_scene_artifacts()
        except NoMatches:
            pass  # Not yet mounted

    # ── Verdict banner ─────────────────────────────────────────────────────────

    def _render_verdict(self) -> None:
        banner = self.query_one("#verdict-banner", Container)
        banner.remove_children()

        agg = self._aggregate
        verdict = agg.get("verdict", "pass")
        color = _STATUS_COLORS.get(verdict, "white")
        icon = _STATUS_ICONS.get(verdict, "?")

        # Main verdict
        banner.mount(
            Static(f"[bold {color}]{icon} Verdict: {verdict.upper()}[/]", classes="verdict-text")
        )

        # Per-level verdicts
        levels = agg.get("levels", {})
        parts: list[str] = []
        for level in ("l0", "l1", "l2", "coherence"):
            if level in levels:
                lv = levels[level]
                lc = _STATUS_COLORS.get(lv, "white")
                parts.append(f"[{lc}]{level}:{lv}[/]")
        if parts:
            banner.mount(Static(" | ".join(parts), classes="verdict-levels"))

        # Retry / repair suggestion
        extras: list[str] = []
        if agg.get("retry_suggested"):
            extras.append("[blue]⟳ Retry suggested[/]")
        if agg.get("repair_suggested"):
            extras.append("[magenta]🔧 Repair suggested[/]")
        if extras:
            banner.mount(Static(" ".join(extras), classes="verdict-extras"))

    # ── Level cards ────────────────────────────────────────────────────────────

    def _render_level_cards(self) -> None:
        cards = self.query_one("#level-cards", Container)

        self._render_level_card(cards, "#card-l0", "L0 — Visual Quality",
                                self._report.get("l0_summary", {}))
        self._render_level_card(cards, "#card-l1", "L1 — Frame Integrity",
                                self._report.get("l1_summary", {}))
        self._render_level_card(cards, "#card-l2", "L2 — Layout Overlap",
                                self._report.get("l2_layout_overlap_summary", {}))
        self._render_coherence_card(cards, "#card-coherence")

    def _render_level_card(
        self, parent: Container, selector: str, title: str, summary: dict[str, Any]
    ) -> None:
        try:
            card = parent.query_one(selector, Container)
        except NoMatches:
            return
        card.remove_children()

        status = summary.get("status", summary.get("passed", True) and "pass" or "fail")
        if isinstance(status, bool):
            status = "pass" if status else "fail"

        card.mount(
            Horizontal(
                Static(f"[bold]{title}[/]", classes="card-title"),
                _status_badge(str(status)),
                classes="card-header",
            )
        )

        issues = summary.get("issues", [])
        card.mount(_count_badge(len(issues)))

        sev = summary.get("severity_counts", {})
        if sev:
            sev_parts = [f"{k}={v}" for k, v in sev.items() if v > 0]
            if sev_parts:
                card.mount(Static(f"[dim]{', '.join(sev_parts)}[/]", classes="card-severity"))

        # If L0 has duration info
        dur = summary.get("duration_seconds", 0)
        if dur:
            card.mount(Static(f"[dim]{dur:.1f}s | {summary.get('total_frames', 0)} frames[/]",
                              classes="card-meta"))

        # Issue list (collapsed to first 3)
        if issues:
            card.mount(Label("[dim]Issues:[/]", classes="card-issues-label"))
            for i, issue in enumerate(issues[:3]):
                sev = issue.get("severity", "low")
                itype = issue.get("type", "unknown")
                detail = issue.get("detail", "")
                card.mount(
                    Horizontal(
                        _severity_tag(sev),
                        Static(f"[bold]{itype}[/]" + (f" — {detail}" if detail else ""),
                               classes="card-issue-text"),
                        classes="card-issue",
                    )
                )
            if len(issues) > 3:
                card.mount(Static(f"[dim]… and {len(issues) - 3} more[/]", classes="card-more"))

    def _render_coherence_card(self, parent: Container, selector: str) -> None:
        try:
            card = parent.query_one(selector, Container)
        except NoMatches:
            return
        card.remove_children()

        coherent = self._coherence.get("coherent", True)
        issues = self._coherence.get("issues", [])
        status = "pass" if coherent else "warn" if issues else "pass"

        card.mount(
            Horizontal(
                Static("[bold]Coherence — Narrative Arc[/]", classes="card-title"),
                _status_badge(status),
                classes="card-header",
            )
        )
        card.mount(_count_badge(len(issues)))

        arc = self._coherence.get("narrative_arc", {})
        phases = arc.get("phases", [])
        if phases:
            card.mount(Static(f"[dim]Phases: {', '.join(phases)}[/]", classes="card-meta"))

        missing = arc.get("missing_phases", [])
        if missing:
            card.mount(Static(f"[yellow]Missing: {', '.join(missing)}[/]", classes="card-meta"))

        t = self._coherence.get("transitions", {})
        ts = t.get("transition_score", 0)
        tm = t.get("max_possible", 1)
        pct = (ts / tm * 100) if tm else 0
        card.mount(Static(f"[dim]Transition score: {ts}/{tm} ({pct:.0f}%)[/]", classes="card-meta"))

        for issue in issues[:3]:
            card.mount(Static(f"[yellow]• {issue}[/]", classes="card-issue-text"))
        if len(issues) > 3:
            card.mount(Static(f"[dim]… and {len(issues) - 3} more[/]", classes="card-more"))

    # ── Repair plan ────────────────────────────────────────────────────────────

    def _render_repair_plan(self) -> None:
        container = self.query_one("#repair-plan", Container)
        container.remove_children()

        plan = self._aggregate.get("repair_plan", [])
        if not plan:
            container.mount(Static("[dim]No repairs needed[/]", classes="empty-state"))
            return

        for action in plan:
            # RepairAction dataclass or dict
            if hasattr(action, "action"):
                action_type = action.action
                issue_type = action.issue_type
                desc = action.description
            else:
                action_type = action.get("action", "?")
                issue_type = action.get("issue_type", "?")
                desc = action.get("description", "")
            label = _ACTION_LABELS.get(str(action_type), str(action_type))

            label_text = f"[bold]{label}[/] — [dim]{issue_type}[/]"
            if desc:
                label_text += f"\n[dim]{desc}[/]"

            children = [Static(label_text, classes="repair-action-desc")]
            if self._on_repair:
                unique = str(hash(str(action_type) + str(issue_type) + str(id(action))))
                children.append(
                    Button(f"Apply {label}", id=f"repair-{issue_type}-{unique[-8:]}", classes="repair-btn")
                )
            container.mount(Container(*children, classes="repair-action-card"))

    # ── Action bar ─────────────────────────────────────────────────────────────

    def _render_action_bar(self) -> None:
        container = self.query_one("#action-bar", Container)
        container.remove_children()

        buttons: list[Button] = []
        if self._on_retry:
            buttons.append(Button("⟳ Retry Scene", id="btn-retry", variant="primary"))
        if self._on_reroute:
            buttons.append(Button("↻ Reroute Engine", id="btn-reroute", variant="default"))
        if self._on_repair:
            buttons.append(Button("🔧 Repair All", id="btn-repair-all", variant="warning"))
        if self._on_stop:
            buttons.append(Button("■ Stop", id="btn-stop", variant="error"))
        container.mount(Horizontal(*buttons, classes="action-bar-buttons"))

    # ── Scene artifacts ────────────────────────────────────────────────────────

    def _render_scene_artifacts(self) -> None:
        container = self.query_one("#scene-artifacts", Container)
        container.remove_children()

        scenes = self._report.get("scenes_summary", {})
        count = scenes.get("count", 0)
        engines = scenes.get("engines", {})

        if count == 0 and not engines:
            container.mount(Static("[dim]No scene artifacts[/]", classes="empty-state"))
            return

        container.mount(Static(f"[bold]{count} scene(s)[/]", classes="artifact-count"))
        if engines:
            engine_parts = [f"{eng}:{cnt}" for eng, cnt in engines.items() if cnt]
            if engine_parts:
                container.mount(Static(f"[dim]Engines: {', '.join(engine_parts)}[/]"))

        # Per-scene references from scenes.json or scenes_summary
        scene_refs = scenes.get("references", [])
        if scene_refs:
            for ref in scene_refs[:5]:
                sid = ref.get("id", ref.get("scene_id", "?"))
                stype = ref.get("type", ref.get("scene_type", "?"))
                status = ref.get("status", "rendered")
                sc = _STATUS_COLORS.get(status, "white")
                container.mount(
                    Horizontal(
                        Static(f"[dim]{sid}[/]  [bold]{stype}[/]"),
                        Static(f"[{sc}]{status}[/]", classes="scene-ref-status"),
                        classes="scene-ref",
                    )
                )
            if len(scene_refs) > 5:
                container.mount(Static(f"[dim]… and {len(scene_refs) - 5} more[/]"))

    # ── Event handlers ─────────────────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        if btn_id == "btn-retry" and self._on_retry:
            agg = self._aggregate
            scene_id = agg.get("details", {}).get("l0", {}).get("scene_id", "current")
            self._on_retry(str(scene_id))
        elif btn_id == "btn-reroute" and self._on_reroute:
            self._on_reroute("current", "remotion")
        elif btn_id == "btn-repair-all" and self._on_repair:
            self._on_repair({"action": "repair_all"})
        elif btn_id == "btn-stop" and self._on_stop:
            self._on_stop()
        elif btn_id and btn_id.startswith("repair-") and self._on_repair:
            self._on_repair({"action": btn_id})


# ── Convenience factory ───────────────────────────────────────────────────────


def make_review_panel_from_report(
    report_path: str,
    coherence_path: str | None = None,
    **action_handlers: Any,
) -> ReviewPanel:
    """Build a ReviewPanel by loading report JSON files.

    Args:
        report_path: Path to ``.report.json`` file.
        coherence_path: Optional path to ``.coherence.json`` file.
        **action_handlers: Passed as ``on_retry``, ``on_reroute``, etc.

    Returns:
        Configured ReviewPanel instance (caller must mount it).
    """
    import json

    with open(report_path) as f:
        report = json.load(f)

    coherence: dict[str, Any] = {}
    if coherence_path:
        try:
            with open(coherence_path) as f:
                coherence = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    from videoforge.review.policy import aggregate

    agg = aggregate(
        l0_result=report.get("l0_summary"),
        l1_result=report.get("l1_summary"),
        l2_result=report.get("l2_layout_overlap_summary"),
        coherence_result=coherence or None,
    )

    return ReviewPanel(
        report=report,
        coherence=coherence,
        aggregate=agg,
        **action_handlers,
    )
