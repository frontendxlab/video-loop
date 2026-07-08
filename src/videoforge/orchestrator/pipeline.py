from __future__ import annotations

import datetime
from typing import Any

from videoforge.orchestrator.errors import handle_phase_error
from videoforge.orchestrator.state_machine import (
    STATUS_COMPLETE,
    STATUS_FAILED,
    STATUS_IN_PROGRESS,
    STATUS_QUEUED,
    StateMachine,
)


class Pipeline:
    PHASES = [
        "INGEST",
        "RESEARCH",
        "SCRIPT",
        "FACT_CHECK",
        "SCENE_PLAN",
        "LOGIC_CHECK",
        "AUDIO",
        "ASSETS",
        "COMPOSE",
        "RENDER",
        "REVIEW",
        "PUBLISH",
    ]

    def __init__(self, state_machine: StateMachine | None = None) -> None:
        self.state = state_machine or StateMachine()

    def run(self, job_id: str, content_type: str, params: dict[str, Any]) -> dict[str, Any]:
        completed_phases: list[str] = []
        output_path: str | None = None

        self.state.transition(job_id, self.PHASES[0], STATUS_QUEUED)

        for phase in self.PHASES:
            self.state.transition(job_id, phase, STATUS_IN_PROGRESS)
            try:
                result = self._run_phase(phase, job_id)
                self.state.transition(job_id, phase, STATUS_COMPLETE)
                completed_phases.append(phase)
                if phase == "RENDER":
                    output_path = result.get("output_path", f"/tmp/{job_id}/output.mp4")
            except Exception as exc:
                self.state.transition(job_id, phase, STATUS_FAILED)
                handle_phase_error(phase, exc)

        return {
            "job_id": job_id,
            "completed_phases": completed_phases,
            "output_path": output_path,
        }

    def _run_phase(self, phase: str, job_id: str) -> dict[str, Any]:
        return {
            "phase": phase,
            "job_id": job_id,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "status": "passed",
        }
