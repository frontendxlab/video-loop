"""Integration tests: coherence gate hooks in CLI commands."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from videoforge.app import app


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def tmp_plan(tmp_path: Path) -> str:
    return str(tmp_path / "plan.json")


class TestPlanCommand:
    def test_plan_runs_coherence_gate(self, runner: CliRunner, tmp_plan: str):
        result = runner.invoke(app, ["plan", "--topic", "Auth refactor", "--output", tmp_plan])
        assert result.exit_code == 0
        # Coherence report file written alongside plan
        coherence_file = Path(tmp_plan).with_stem(Path(tmp_plan).stem + ".coherence")
        assert coherence_file.exists(), f"Missing {coherence_file}"
        report = json.loads(coherence_file.read_text())
        assert "narrative_arc" in report
        assert "coherent" in report

    def test_plan_writes_plan_and_coherence(self, runner: CliRunner, tmp_plan: str):
        result = runner.invoke(app, ["plan", "--topic", "Test", "--output", tmp_plan])
        assert result.exit_code == 0
        assert Path(tmp_plan).exists()
        coherence_file = Path(tmp_plan).with_stem(Path(tmp_plan).stem + ".coherence")
        report = json.loads(coherence_file.read_text())
        assert "timestamp" in report
        assert "plan_path" in report



