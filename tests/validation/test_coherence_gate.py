"""Tests for deterministic coherence gate."""

from __future__ import annotations

import pytest


@pytest.fixture
def gate():
    from videoforge.validation.coherence_gate import CoherenceGate
    return CoherenceGate()


@pytest.fixture
def complete_plan():
    """Full arc: context -> problem -> solution -> impact."""
    return {
        "version": 1,
        "scenes": [
            {"id": 1, "type": "title", "duration_seconds": 4,
             "title": "Auth Overhaul", "transition_out": "fade"},
            {"id": 2, "type": "bullet", "duration_seconds": 5,
             "title": "The Problem", "text": "Auth was slow",
             "transition_out": "slide-left"},
            {"id": 3, "type": "code", "duration_seconds": 8,
             "code": "def auth(): pass", "transition_out": "fade"},
            {"id": 4, "type": "outro", "duration_seconds": 4,
             "title": "Results", "transition_out": "none"},
        ],
    }


class TestNarrativeArc:
    def test_complete_arc_passes(self, gate, complete_plan):
        report = gate.check_narrative_arc(complete_plan)
        assert report["has_complete_arc"] is True
        assert report["missing_phases"] == []
        assert report["duplicate_phases"] == []
        assert report["phase_order_valid"] is True

    def test_missing_phases_flagged(self, gate):
        plan = {"scenes": [{"type": "title"}, {"type": "code"}]}
        report = gate.check_narrative_arc(plan)
        assert report["has_complete_arc"] is False
        assert "problem" in report["missing_phases"]
        assert "impact" in report["missing_phases"]

    def test_empty_plan_returns_all_missing(self, gate):
        report = gate.check_narrative_arc({"scenes": []})
        assert report["has_complete_arc"] is False
        assert set(report["missing_phases"]) == {"context", "problem", "solution", "impact"}

    def test_missing_scenes_key(self, gate):
        report = gate.check_narrative_arc({})
        assert report["has_complete_arc"] is False

    def test_unknown_scene_type_ignored(self, gate):
        plan = {"scenes": [
            {"type": "title"},
            {"type": "unknown_thing"},
            {"type": "code"},
            {"type": "bullet"},
            {"type": "outro"},
        ]}
        report = gate.check_narrative_arc(plan)
        assert report["has_complete_arc"] is True


class TestDuplicateSections:
    def test_duplicate_phase_detected(self, gate):
        """Context appears, then solution, then context again = duplicate."""
        plan = {"scenes": [
            {"type": "title"},     # context
            {"type": "code"},      # solution
            {"type": "image"},     # context — duplicate, non-contiguous
        ]}
        report = gate.check_narrative_arc(plan)
        assert "context" in report["duplicate_phases"]

    def test_adjacent_same_phase_not_duplicate(self, gate):
        """Two code scenes adjacent = same phase, not a duplicate."""
        plan = {"scenes": [
            {"type": "title"},      # context
            {"type": "code"},       # solution
            {"type": "diff"},       # solution (adjacent, not duplicate)
            {"type": "outro"},      # impact
        ]}
        report = gate.check_narrative_arc(plan)
        assert report["duplicate_phases"] == []

    def test_multiple_duplicates_detected(self, gate):
        plan = {"scenes": [
            {"type": "title"},       # context
            {"type": "bullet"},      # problem
            {"type": "title"},       # context — duplicate
            {"type": "code"},        # solution
            {"type": "bullet"},      # problem — duplicate
        ]}
        report = gate.check_narrative_arc(plan)
        assert "context" in report["duplicate_phases"]
        assert "problem" in report["duplicate_phases"]

    def test_no_duplicates_in_single_pass(self, gate):
        plan = {"scenes": [
            {"type": "title"},       # context
            {"type": "bullet"},      # problem
            {"type": "code"},        # solution
            {"type": "diff"},        # solution
            {"type": "outro"},       # impact
        ]}
        report = gate.check_narrative_arc(plan)
        assert report["duplicate_phases"] == []


class TestPhaseOrder:
    def test_out_of_order_flagged(self, gate):
        """Impact before context = invalid."""
        plan = {"scenes": [
            {"type": "outro"},       # impact — appears first, out of order
            {"type": "title"},       # context
            {"type": "code"},
        ]}
        report = gate.check_narrative_arc(plan)
        assert report["phase_order_valid"] is False
        assert len(report["phase_order_issues"]) > 0

    def test_partial_order_valid(self, gate):
        """context -> problem is valid even without solution/impact."""
        plan = {"scenes": [
            {"type": "title"},       # context
            {"type": "bullet"},      # problem
        ]}
        report = gate.check_narrative_arc(plan)
        assert report["phase_order_valid"] is True

    def test_completely_reversed_order(self, gate):
        plan = {"scenes": [
            {"type": "outro"},       # impact
            {"type": "code"},        # solution
            {"type": "bullet"},      # problem
            {"type": "title"},       # context
        ]}
        report = gate.check_narrative_arc(plan)
        assert report["phase_order_valid"] is False


class TestWeakTransitions:
    def test_no_transition_at_arc_boundary_flagged(self, gate):
        plan = {"scenes": [
            {"type": "title", "transition_out": "none"},
            {"type": "code", "transition_out": "fade"},
            {"type": "outro", "transition_out": "none"},
        ]}
        report = gate.check_weak_transitions(plan)
        assert len(report["weak_transitions"]) > 0

    def test_strong_transitions_pass(self, gate):
        plan = {"scenes": [
            {"type": "title", "transition_out": "fade"},
            {"type": "bullet", "transition_out": "slide-left"},
            {"type": "code", "transition_out": "dissolve"},
            {"type": "outro", "transition_out": "fade"},
        ]}
        report = gate.check_weak_transitions(plan)
        assert report["weak_transitions"] == []

    def test_empty_plan_no_transitions(self, gate):
        report = gate.check_weak_transitions({"scenes": []})
        assert report["weak_transitions"] == []
        assert report["max_possible"] == 0

    def test_transition_score_computed(self, gate):
        plan = {"scenes": [
            {"type": "title", "transition_out": "fade"},       # 2
            {"type": "bullet", "transition_out": "slide-left"},  # 2
            {"type": "code", "transition_out": "fade"},         # 2
        ]}
        report = gate.check_weak_transitions(plan)
        assert report["transition_score"] == 4

    def test_single_scene_no_boundaries(self, gate):
        plan = {"scenes": [{"type": "title"}]}
        report = gate.check_weak_transitions(plan)
        assert report["weak_transitions"] == []
        assert report["max_possible"] == 0


class TestScriptCoherence:
    def test_script_covers_all_phases(self, gate):
        script = (
            "We introduce the current auth system. "
            "The main issue is slow token validation. "
            "We implement a caching layer to fix it. "
            "The result is improved performance."
        )
        plan = {"scenes": [{"type": "title"}, {"type": "code"}]}
        report = gate.check_script_coherence(script, plan)
        assert report["uncovered_phases"] == []

    def test_empty_script_no_coverage(self, gate):
        report = gate.check_script_coherence("", {"scenes": []})
        assert set(report["uncovered_phases"]) == {"context", "problem", "solution", "impact"}

    def test_script_missing_problem_keywords(self, gate):
        script = "We introduce the system. We implement a fix."
        plan = {"scenes": []}
        report = gate.check_script_coherence(script, plan)
        assert "problem" in report["uncovered_phases"]

    def test_phase_content_without_keywords_still_passes(self, gate):
        """Scene has title/text content even if script lacks keywords."""
        script = "Something unrelated."
        plan = {"scenes": [
            {"type": "title", "title": "Intro"},
            {"type": "bullet", "text": "Broken feature"},
            {"type": "code", "code": "def f(): pass"},
            {"type": "outro", "title": "Done"},
        ]}
        report = gate.check_script_coherence(script, plan)
        assert report["phase_content_issues"] == []

    def test_no_content_and_no_keywords_flagged(self, gate):
        script = "Something unrelated."
        plan = {"scenes": [
            {"type": "title"},  # no title/text
        ]}
        report = gate.check_script_coherence(script, plan)
        assert len(report["phase_content_issues"]) > 0


class TestFullReport:
    def test_report_contains_all_sections(self, gate, complete_plan):
        report = gate.check_scenes("test script", complete_plan)
        assert "narrative_arc" in report
        assert "transitions" in report
        assert "script_coherence" in report
        assert "issues" in report
        assert "coherent" in report

    def test_coherent_plan_passes(self, gate, complete_plan):
        script = (
            "We introduce the auth background. "
            "The problem is slow validation. "
            "We implement a fix with caching. "
            "The result is better performance."
        )
        report = gate.check_scenes(script, complete_plan)
        assert report["coherent"] is True
        assert report["issues"] == []

    def test_incoherent_plan_flagged(self, gate):
        script = "Something."
        plan = {"scenes": [
            {"type": "outro", "transition_out": "none"},
            {"type": "title", "transition_out": "none"},
        ]}
        report = gate.check_scenes(script, plan)
        assert report["coherent"] is False
        assert len(report["issues"]) > 0

    def test_missing_and_duplicate_and_order_issues(self, gate):
        script = ""
        plan = {"scenes": [
            {"type": "outro"},        # impact (out of order)
            {"type": "code"},         # solution
            {"type": "bullet"},       # problem
            {"type": "title"},        # context (duplicate after outro)
            {"type": "code"},         # solution (duplicate)
        ]}
        report = gate.check_scenes(script, plan)
        assert report["coherent"] is False
        issues_str = " ".join(report["issues"])
        assert "Duplicate" in issues_str or "duplicate" in issues_str
        assert "order" in issues_str
