"""Tests for videoforge.paths — shared path/build/review/report utilities."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from videoforge.paths import (
    DEFAULT_BUILD_DIR,
    ensure_dir,
    ensure_parent,
    merge_coherence_to_report,
    run_coherence_on_scenes,
)


class TestEnsureParent:
    def test_creates_parent_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "sub" / "file.txt"
            result = ensure_parent(p)
            assert result == p
            assert p.parent.exists()

    def test_existing_parent_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "file.txt"
            result = ensure_parent(p)
            assert result == p
            assert p.parent.exists()


class TestEnsureDir:
    def test_creates_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "newdir"
            result = ensure_dir(d)
            assert result == d
            assert d.exists()
            assert d.is_dir()

    def test_existing_dir_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = ensure_dir(tmp)
            assert result == Path(tmp)
            assert Path(tmp).exists()

    def test_nested_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "a" / "b" / "c"
            result = ensure_dir(d)
            assert result == d
            assert d.exists()

    def test_default_constant_is_valid(self):
        assert isinstance(DEFAULT_BUILD_DIR, str)
        assert DEFAULT_BUILD_DIR == "/tmp/vfx-build"


class TestRunCoherenceOnScenes:
    def test_coherence_on_valid_scenes(self):
        scenes = [
            {"type": "title", "title": "Intro", "text": "Welcome."},
            {"type": "bullet", "title": "Problem", "text": "The issue."},
            {"type": "code", "title": "Fix", "text": "The solution."},
            {"type": "outro", "title": "Impact", "text": "Results."},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "plan.json"
            result = run_coherence_on_scenes(scenes, plan_path, fallback_script="Test")

            assert "coherent" in result
            assert "issues" in result
            assert "narrative_arc" in result
            assert "transitions" in result
            assert "script_coherence" in result

            # Coherence report file next to plan_path
            report = plan_path.with_stem(plan_path.stem + ".coherence")
            assert report.exists()

    def test_empty_scenes(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "plan.json"
            result = run_coherence_on_scenes([], plan_path)
            assert result["coherent"] is False


class TestMergeCoherenceToReport:
    def test_merges_coherence(self):
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "report.json"
            report_path.write_text(json.dumps({"video_path": "test.mp4"}))

            coherence = {
                "coherent": True,
                "issues": [{"type": "test", "detail": "sample"}],
            }
            merge_coherence_to_report(report_path, coherence)

            data = json.loads(report_path.read_text())
            assert data["coherence"]["coherent"] is True
            assert data["coherence"]["total_issues"] == 1
            assert data["video_path"] == "test.mp4"

    def test_skip_missing_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Should not raise
            merge_coherence_to_report(
                Path(tmp) / "nonexistent.json",
                {"coherent": True, "issues": []},
            )

    def test_merge_empty_issues(self):
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "report.json"
            report_path.write_text(json.dumps({"video_path": "test.mp4"}))

            merge_coherence_to_report(report_path, {"coherent": True, "issues": []})

            data = json.loads(report_path.read_text())
            assert data["coherence"]["total_issues"] == 0
