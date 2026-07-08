from __future__ import annotations

from typing import Any

_jobs: dict[str, dict[str, Any]] = {}


def status(job_id: str) -> dict[str, Any]:
    return _jobs.get(job_id, {"phase": "UNKNOWN", "progress_pct": 0})
