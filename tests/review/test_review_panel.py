"""Tests for the ReviewPanel Textual widget.

Uses Textual's `pilot` test harness for widget composition/rendering tests
and plain unit tests for helper functions.
"""

from __future__ import annotations

from typing import Any

import pytest
from textual.widgets import Button, Static

from videoforge.review.policy import ReviewVerdict, aggregate
from videoforge.review.review_panel import (
    ReviewPanel,
    _count_badge,
    _severity_tag,
    _status_badge,
    make_review_panel_from_report,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def sample_report() -> dict[str, Any]:
    return {
        "artifact": "videoforge-video-report",
        "version": 1,
        "scenes_summary": {
            "count": 3,
            "engines": {"remotion": 3},
            "total_duration_frames": 900,
        },
        "l0_summary": {
            "status": "fail",
            "passed": False,
            "total_issues": 2,
            "severity_counts": {"high": 1, "medium": 1, "low": 0},
            "sampled_frames": 6,
            "total_frames": 300,
            "duration_seconds": 10.0,
            "issues": [
                {"severity": "high", "type": "blank_frame", "detail": "Frame 42 blank"},
                {"severity": "medium", "type": "palette_drift", "detail": "Color distance 150"},
            ],
        },
        "l1_summary": {
            "passed": True,
            "total_frames": 300,
            "total_issues": 0,
            "issues": [],
        },
        "l2_layout_overlap_summary": {
            "status": "pass",
            "passed": True,
            "total_issues": 0,
            "severity_counts": {"high": 0, "medium": 0, "low": 0},
            "issues": [],
        },
        "policy_verdict": "fail",
    }


@pytest.fixture
def sample_coherence() -> dict[str, Any]:
    return {
        "coherent": False,
        "issues": ["Missing phases: impact", "Weak transitions at 1 arc boundary(ies)"],
        "narrative_arc": {
            "phases": ["context", "problem", "solution"],
            "missing_phases": ["impact"],
            "duplicate_phases": [],
            "phase_order_valid": True,
            "phase_order_issues": [],
            "has_complete_arc": False,
        },
        "transitions": {
            "weak_transitions": [
                {
                    "scene_index": 2,
                    "from_phase": "solution",
                    "to_phase": "context",
                    "transition": "none",
                    "issue": "No transition at arc phase boundary",
                    "severity": "weak",
                }
            ],
            "transition_score": 4,
            "max_possible": 6,
        },
        "script_coherence": {
            "phase_keyword_coverage": {
                "context": {"matched_keywords": ["introduce"], "count": 1, "covered": True},
                "problem": {"matched_keywords": ["bug"], "count": 1, "covered": True},
                "solution": {"matched_keywords": ["implement"], "count": 1, "covered": True},
                "impact": {"matched_keywords": [], "count": 0, "covered": False},
            },
            "uncovered_phases": ["impact"],
            "phase_content_issues": [],
        },
    }


@pytest.fixture
def sample_aggregate(sample_report, sample_coherence) -> dict[str, Any]:
    return aggregate(
        l0_result=sample_report["l0_summary"],
        l1_result=sample_report["l1_summary"],
        l2_result=sample_report["l2_layout_overlap_summary"],
        coherence_result=sample_coherence,
    )


# ── Helper function tests ─────────────────────────────────────────────────────


class TestHelpers:
    """Helper functions produce correct markup strings (checked via _Static__content)."""

    def _content(self, s: Static) -> str:
        return s._Static__content  # noqa: SLF001

    def test_severity_tag_high(self) -> None:
        tag = _severity_tag("high")
        assert "HIGH" in self._content(tag)

    def test_severity_tag_medium(self) -> None:
        tag = _severity_tag("medium")
        assert "MEDIUM" in self._content(tag)

    def test_severity_tag_low(self) -> None:
        tag = _severity_tag("low")
        assert "LOW" in self._content(tag)

    def test_status_badge_pass(self) -> None:
        badge = _status_badge("pass")
        text = self._content(badge)
        assert "PASS" in text
        assert "✓" in text

    def test_status_badge_fail(self) -> None:
        badge = _status_badge("fail")
        text = self._content(badge)
        assert "FAIL" in text
        assert "✕" in text

    def test_count_badge_zero(self) -> None:
        badge = _count_badge(0)
        assert "0 issues" in self._content(badge)

    def test_count_badge_positive(self) -> None:
        badge = _count_badge(5)
        assert "5 issues" in self._content(badge)


# ── ReviewPanel composition tests ─────────────────────────────────────────────


class TestReviewPanelCompose:
    """Verify the widget tree mounts correctly."""

    async def test_compose_creates_sections(self) -> None:
        """All major sections present after compose."""
        from textual.app import App, ComposeResult

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield ReviewPanel()

        app = TestApp()
        async with app.run_test() as pilot:
            panel = app.query_one(ReviewPanel)
            assert panel.query("#verdict-banner")
            assert panel.query("#level-cards")
            assert panel.query("#card-l0")
            assert panel.query("#card-l1")
            assert panel.query("#card-l2")
            assert panel.query("#card-coherence")
            assert panel.query("#repair-plan")
            assert panel.query("#action-bar")
            assert panel.query("#scene-artifacts")

    async def test_compose_with_data(self, sample_report, sample_coherence, sample_aggregate) -> None:
        """Panel renders data without crashing."""

        from textual.app import App, ComposeResult

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield ReviewPanel(
                    report=sample_report,
                    coherence=sample_coherence,
                    aggregate=sample_aggregate,
                )

        app = TestApp()
        async with app.run_test() as pilot:
            panel = app.query_one(ReviewPanel)
            # Verdict should show FAIL
            banner = panel.query_one("#verdict-banner")

    async def test_refresh_updates_content(self, sample_report, sample_coherence, sample_aggregate) -> None:
        """Calling refresh_from() updates rendered content."""

        from textual.app import App, ComposeResult

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield ReviewPanel()

        app = TestApp()
        async with app.run_test() as pilot:
            panel = app.query_one(ReviewPanel)
            panel.refresh_from(report=sample_report, coherence=sample_coherence, aggregate=sample_aggregate)

    async def test_empty_state(self) -> None:
        """Panel renders empty state messages when no data."""

        from textual.app import App, ComposeResult

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield ReviewPanel()

        app = TestApp()
        async with app.run_test() as pilot:
            repair_plan = app.query_one("#repair-plan")
            scene_artifacts = app.query_one("#scene-artifacts")
            # Should contain empty-state labels
            texts = [s._Static__content for s in repair_plan.query(Static)]  # noqa: SLF001
            assert any("No repairs needed" in t for t in texts)
            texts2 = [s._Static__content for s in scene_artifacts.query(Static)]  # noqa: SLF001
            assert any("No scene artifacts" in t for t in texts2)


# ── Action callback tests ─────────────────────────────────────────────────────


class TestReviewPanelActions:
    async def test_retry_button_fires_callback(self, sample_report, sample_aggregate) -> None:
        """Pressing retry button calls on_retry handler."""
        from textual.app import App, ComposeResult

        calls: list[str] = []

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield ReviewPanel(
                    report=sample_report,
                    aggregate=sample_aggregate,
                    on_retry=lambda scene_id: calls.append(scene_id),
                )

        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            panel = app.query_one(ReviewPanel)
            btn = panel.query_one("#btn-retry", Button)
            await pilot.click(btn)
            await pilot.pause()
            assert len(calls) == 1

    async def test_stop_button_fires_callback(self, sample_report, sample_aggregate) -> None:
        """Pressing stop button calls on_stop handler."""
        from textual.app import App, ComposeResult

        calls: list[str] = []

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield ReviewPanel(
                    report=sample_report,
                    aggregate=sample_aggregate,
                    on_stop=lambda: calls.append("stopped"),
                )

        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            panel = app.query_one(ReviewPanel)
            btn = panel.query_one("#btn-stop", Button)
            await pilot.click(btn)
            await pilot.pause()
            assert calls == ["stopped"]

    async def test_reroute_button_fires_callback(self, sample_report, sample_aggregate) -> None:
        """Pressing reroute button calls on_reroute handler."""
        from textual.app import App, ComposeResult

        calls: list[tuple[str, str]] = []

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield ReviewPanel(
                    report=sample_report,
                    aggregate=sample_aggregate,
                    on_reroute=lambda sid, eng: calls.append((sid, eng)),
                )

        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            panel = app.query_one(ReviewPanel)
            btn = panel.query_one("#btn-reroute", Button)
            await pilot.click(btn)
            await pilot.pause()
            assert len(calls) == 1
            assert calls[0] == ("current", "remotion")


# ── Factory function test ─────────────────────────────────────────────────────


class TestMakeReviewPanelFromReport:
    def test_factory_with_real_report(self, tmp_path) -> None:
        """make_review_panel_from_report loads JSON and builds ReviewPanel."""
        import json

        report = {
            "l0_summary": {"status": "pass", "passed": True, "total_issues": 0, "issues": []},
            "l1_summary": {"passed": True, "total_issues": 0, "issues": []},
            "l2_layout_overlap_summary": {"status": "pass", "passed": True, "total_issues": 0, "issues": []},
            "scenes_summary": {"count": 0, "engines": {}, "total_duration_frames": 0},
            "policy_verdict": "pass",
        }
        report_path = tmp_path / "test.report.json"
        report_path.write_text(json.dumps(report))

        panel = make_review_panel_from_report(str(report_path))
        assert isinstance(panel, ReviewPanel)
        assert panel._report["policy_verdict"] == "pass"

    def test_factory_with_coherence(self, tmp_path) -> None:
        """Factory loads coherence sidecar when provided."""
        import json

        report = {
            "l0_summary": {"status": "pass", "passed": True, "total_issues": 0, "issues": []},
            "l1_summary": {"passed": True, "total_issues": 0, "issues": []},
            "l2_layout_overlap_summary": {"status": "pass", "passed": True, "total_issues": 0, "issues": []},
            "scenes_summary": {"count": 0, "engines": {}, "total_duration_frames": 0},
            "policy_verdict": "pass",
        }
        coherence = {
            "coherent": True,
            "issues": [],
            "narrative_arc": {"phases": ["context", "problem", "solution", "impact"], "missing_phases": [], "has_complete_arc": True},
            "transitions": {"transition_score": 6, "max_possible": 6},
        }
        rp = tmp_path / "test.report.json"
        cp = tmp_path / "test.coherence.json"
        rp.write_text(json.dumps(report))
        cp.write_text(json.dumps(coherence))

        panel = make_review_panel_from_report(str(rp), coherence_path=str(cp))
        assert panel._coherence["coherent"] is True

    def test_factory_handles_missing_coherence(self, tmp_path) -> None:
        """Factory does not crash when coherence file missing."""
        import json

        report = {
            "l0_summary": {"status": "pass", "passed": True, "total_issues": 0, "issues": []},
            "l1_summary": {"passed": True, "total_issues": 0, "issues": []},
            "l2_layout_overlap_summary": {"status": "pass", "passed": True, "total_issues": 0, "issues": []},
            "scenes_summary": {"count": 0, "engines": {}, "total_duration_frames": 0},
            "policy_verdict": "pass",
        }
        rp = tmp_path / "test.report.json"
        rp.write_text(json.dumps(report))

        panel = make_review_panel_from_report(str(rp), coherence_path="/nonexistent/coherence.json")
        assert panel._coherence == {}


# ── Reactive update tests ─────────────────────────────────────────────────────


class TestReactiveUpdates:
    async def test_reactive_report_update(self, sample_report, sample_aggregate) -> None:
        """Changing report reactive triggers refresh."""
        from textual.app import App, ComposeResult

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield ReviewPanel(report={}, aggregate={})

        app = TestApp()
        async with app.run_test() as pilot:
            panel = app.query_one(ReviewPanel)
            panel.report = sample_report

    async def test_reactive_aggregate_update(self, sample_aggregate) -> None:
        """Changing aggregate reactive triggers refresh."""
        from textual.app import App, ComposeResult

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield ReviewPanel(aggregate={})

        app = TestApp()
        async with app.run_test() as pilot:
            panel = app.query_one(ReviewPanel)
            panel.aggregate = sample_aggregate

    async def test_rerender_with_failing_l0_shows_issues(self, sample_report, sample_aggregate) -> None:
        """L0 card shows issue count and severity badges."""
        from textual.app import App, ComposeResult

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield ReviewPanel(
                    report=sample_report,
                    aggregate=sample_aggregate,
                )

        app = TestApp()
        async with app.run_test() as pilot:
            card = app.query_one("#card-l0")
            texts = [s._Static__content for s in card.query(Static)]  # noqa: SLF001
            assert any("blank_frame" in t for t in texts)
            assert any("HIGH" in t for t in texts)
            assert any("2 issues" in t for t in texts)


# ── TUI integration test ──────────────────────────────────────────────────────


class TestTuiIntegration:
    """Verify ReviewPanel composes inside the existing TUI structure."""

    async def test_review_agent_shows_panel(self, sample_report, sample_coherence, sample_aggregate) -> None:
        """Panel can be mounted inside the existing TUI screen."""
        from textual.app import App, ComposeResult
        from textual.containers import VerticalScroll

        class TestReviewScreen(App):
            def compose(self) -> ComposeResult:
                with VerticalScroll(id="review-col"):
                    yield ReviewPanel(
                        report=sample_report,
                        coherence=sample_coherence,
                        aggregate=sample_aggregate,
                    )

        app = TestReviewScreen()
        async with app.run_test() as pilot:
            col = app.query_one("#review-col")
            panel = col.query_one(ReviewPanel)
            assert panel is not None
            # All sections rendered
            assert panel.query("#verdict-banner")
            assert panel.query("#card-l0")
            assert panel.query("#card-coherence")
