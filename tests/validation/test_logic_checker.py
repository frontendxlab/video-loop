"""Tests for Logic Checker."""

from __future__ import annotations

import pytest


@pytest.fixture
def logic_checker():
    from videoforge.validation.logic_checker import LogicChecker
    return LogicChecker()


class TestNarrativeArc:
    def test_detects_complete_arc(self, logic_checker, sample_scene_plan):
        report = logic_checker.check_narrative_arc(sample_scene_plan)
        assert "phases" in report

    def test_missing_phases_flagged(self, logic_checker):
        plan = {"version": 1, "scenes": [{"type": "outro"}]}
        report = logic_checker.check_narrative_arc(plan)
        assert len(report.get("missing_phases", [])) > 0

    def test_empty_plan_returns_all_phases_missing(self, logic_checker):
        plan = {"version": 1, "scenes": []}
        report = logic_checker.check_narrative_arc(plan)
        assert "missing_phases" in report


class TestCauseEffect:
    def test_detects_unsupported_cause_effect(self, logic_checker, sample_scene_plan):
        script = "Because caching was added, latency decreased."
        report = logic_checker.check_cause_effect(script, sample_scene_plan)
        assert "issues" in report


class TestSceneOrdering:
    def test_detects_reversed_order(self, logic_checker):
        plan = {
            "version": 1,
            "scenes": [
                {"type": "outro", "id": 1},
                {"type": "title", "id": 2},
            ],
        }
        report = logic_checker.check_scene_ordering(plan)
        assert len(report.get("issues", [])) > 0

    def test_correct_order_passes(self, logic_checker):
        plan = {
            "version": 1,
            "scenes": [
                {"type": "title", "id": 1},
                {"type": "code", "id": 2},
                {"type": "outro", "id": 3},
            ],
        }
        report = logic_checker.check_scene_ordering(plan)
        assert len(report.get("issues", [])) == 0


class TestPacing:
    def test_short_scene_flagged(self, logic_checker):
        plan = {
            "version": 1,
            "scenes": [{"type": "code", "duration_seconds": 0.5}],
        }
        report = logic_checker.check_pacing(plan)
        assert len(report.get("issues", [])) > 0

    def test_normal_duration_passes(self, logic_checker):
        plan = {
            "version": 1,
            "scenes": [{"type": "code", "duration_seconds": 8}],
        }
        report = logic_checker.check_pacing(plan)
        assert len(report.get("issues", [])) == 0


class TestLogicCheckReport:
    def test_full_report_all_checks(self, logic_checker, sample_scene_plan):
        report = logic_checker.check_scenes(
            "This is a test script about the authenticate function.",
            sample_scene_plan,
            "mock diff"
        )
        assert "narrative_arc" in report
        assert "cause_effect" in report
        assert "scene_ordering" in report
        assert "pacing" in report

    def test_l1_mode_advisory(self, logic_checker, sample_scene_plan):
        report = logic_checker.check_scenes(
            "", sample_scene_plan, "", mode="advisory"
        )
        assert "blocked" in report
        assert report["blocked"] is False
