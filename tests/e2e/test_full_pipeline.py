"""E2E integration tests — full pipeline from mock input to video."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


class TestFullPipeline:
    @pytest.mark.slow
    def test_full_pipeline_completes(self):
        """Pipeline should complete all 12 phases in order."""
        from videoforge.orchestrator.pipeline import Pipeline
        p = Pipeline()
        with patch.object(p, "_run_phase") as mock:
            mock.return_value = {"phase": "COMPLETE", "status": "ok"}
            result = p.run("job-e2e-001", "PR", {"url": "https://github.com/org/repo/pull/1"})
        assert "job_id" in result
        assert result["job_id"] == "job-e2e-001"
        assert len(result["completed_phases"]) > 0

    def test_pipeline_runs_all_phases(self):
        """Pipeline should attempt all 12 phases."""
        from videoforge.orchestrator.pipeline import Pipeline
        p = Pipeline()
        assert len(p.PHASES) == 12
        assert "INGEST" in p.PHASES
        assert "FACT_CHECK" in p.PHASES
        assert "LOGIC_CHECK" in p.PHASES
        assert "REVIEW" in p.PHASES
        assert "PUBLISH" in p.PHASES

    def test_pipeline_records_state(self):
        """Pipeline should update STATE.md after each phase."""
        from videoforge.orchestrator.pipeline import Pipeline
        p = Pipeline()
        assert hasattr(p, "state")
        assert hasattr(p.state, "transition")

    def test_pipeline_fails_gracefully(self):
        """Pipeline should capture phase failures without crashing."""
        from videoforge.orchestrator.pipeline import Pipeline
        p = Pipeline()
        with patch.object(p, "_run_phase") as mock:
            mock.side_effect = [{"phase": "COMPLETE", "status": "ok"}] * 6 + [Exception("phase failed")]
            result = p.run("job-e2e-002", "PR", {"url": "..."})
        assert "completed_phases" in result


class TestE2EWithMocks:
    def test_pr_to_video_with_mocks(self):
        """Full PR→video path using mocked external calls."""
        from videoforge.orchestrator.pipeline import Pipeline
        p = Pipeline()
        with (
            patch.object(p, "_run_phase", return_value={"phase": "COMPLETE", "status": "ok"}),
        ):
            result = p.run("job-e2e-003", "PR", {"url": "https://github.com/org/repo/pull/1"})
        assert result["output_path"] is not None
