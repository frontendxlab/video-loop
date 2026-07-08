from __future__ import annotations

import uuid

_jobs: dict[str, dict[str, str]] = {}


def _enqueue_job(content_type: str, url: str) -> str:
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"content_type": content_type, "url": url}
    return job_id


def handle_webhook(payload: dict, event_type: str) -> dict | None:
    action = payload.get("action")

    if event_type == "pull_request" and action == "opened":
        url = payload["pull_request"]["html_url"]
        job_id = _enqueue_job(event_type, url)
        return {"job_id": job_id}

    if event_type == "issues" and action == "opened":
        url = payload["issue"]["html_url"]
        job_id = _enqueue_job(event_type, url)
        return {"job_id": job_id}

    return None
