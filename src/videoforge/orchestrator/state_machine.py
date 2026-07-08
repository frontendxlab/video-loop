from __future__ import annotations

import datetime
from typing import Any

STATUS_QUEUED = "QUEUED"
STATUS_IN_PROGRESS = "IN_PROGRESS"
STATUS_COMPLETE = "COMPLETE"
STATUS_FAILED = "FAILED"

VALID_STATUSES = {STATUS_QUEUED, STATUS_IN_PROGRESS, STATUS_COMPLETE, STATUS_FAILED}


class StateMachine:
    def __init__(self) -> None:
        self._jobs: dict[str, dict[str, Any]] = {}

    def transition(self, job_id: str, phase: str, status: str) -> None:
        if status not in VALID_STATUSES:
            raise ValueError(f"Invalid status: {status}. Must be one of {VALID_STATUSES}")

        now = datetime.datetime.utcnow().isoformat() + "Z"

        if job_id not in self._jobs:
            self._jobs[job_id] = {
                "phase": phase,
                "progress_pct": 0,
                "started_at": None,
                "error": None,
                "phases": {},
            }

        job = self._jobs[job_id]
        job["phase"] = phase
        job["phases"][phase] = {
            "status": status,
            "updated_at": now,
        }

        if status == STATUS_IN_PROGRESS and job["started_at"] is None:
            job["started_at"] = now

        if status == STATUS_FAILED:
            job["error"] = f"Phase {phase} failed"

        total = len(job["phases"])
        completed = sum(
            1 for s in job["phases"].values() if s["status"] == STATUS_COMPLETE
        )
        job["progress_pct"] = int(completed / total * 100) if total else 0

    def get_status(self, job_id: str) -> dict[str, Any]:
        job = self._jobs.get(job_id)
        if job is None:
            return {
                "phase": "UNKNOWN",
                "progress_pct": 0,
                "started_at": None,
                "error": f"Job {job_id} not found",
            }
        return {
            "phase": job["phase"],
            "progress_pct": job["progress_pct"],
            "started_at": job["started_at"],
            "error": job.get("error"),
        }
