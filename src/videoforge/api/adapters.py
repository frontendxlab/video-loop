"""Lightweight event feed adapters for SSE stream.

Provides read source for job/report/provenance artifacts.
Placeholder feed for dev/test when real queue integration not ready.
"""

from __future__ import annotations

import json
import os
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import AsyncIterator, Callable

from videoforge.api.events import (
    EventType,
    JobEvent,
    JobStarted,
    JobStage,
    JobCompleted,
    serialize_event,
)


class EventFeed(ABC):
    """Abstract event feed — yields SSE-formatted strings for a job."""

    @abstractmethod
    async def stream(self, job_id: str, after_id: str | None = None) -> AsyncIterator[str]:
        """Yield SSE-formatted event strings for *job_id*.

        If *after_id* is set, only yield events after that event ID.
        """
        ...

    @abstractmethod
    async def append(self, event: JobEvent) -> None:
        """Persist an event to the feed."""
        ...

    @abstractmethod
    async def replay(self, job_id: str) -> list[JobEvent]:
        """Return all persisted events for *job_id* (for replay)."""
        ...


class MemoryEventFeed(EventFeed):
    """In-memory event store. Events discarded on restart."""

    def __init__(self) -> None:
        self._events: dict[str, list[JobEvent]] = {}

    async def stream(self, job_id: str, after_id: str | None = None) -> AsyncIterator[str]:
        events = self._events.get(job_id, [])
        if after_id:
            idx = self._find_index(events, after_id)
            events = events[idx + 1:] if idx is not None else []
        for ev in events:
            yield serialize_event(ev)

    async def append(self, event: JobEvent) -> None:
        self._events.setdefault(event.jobId, []).append(event)

    async def replay(self, job_id: str) -> list[JobEvent]:
        return list(self._events.get(job_id, []))

    @staticmethod
    def _find_index(events: list[JobEvent], event_id: str) -> int | None:
        for i, ev in enumerate(events):
            if ev.id == event_id:
                return i
        return None


class FileEventFeed(EventFeed):
    """File-backed event store. One JSONL file per job.

    Path: ``{base_dir}/{job_id}.jsonl``
    """

    def __init__(self, base_dir: str | Path) -> None:
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, job_id: str) -> Path:
        safe = job_id.replace("/", "_").replace("..", "_")
        return self._base_dir / f"{safe}.jsonl"

    async def stream(self, job_id: str, after_id: str | None = None) -> AsyncIterator[str]:
        path = self._path_for(job_id)
        if not path.exists():
            return
        after_found = after_id is None
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                event = JobEvent(**json.loads(line))
                if not after_found:
                    if event.id == after_id:
                        after_found = True
                    continue
                yield serialize_event(event)

    async def append(self, event: JobEvent) -> None:
        path = self._path_for(event.jobId)
        with open(path, "a") as f:
            f.write(event.model_dump_json() + "\n")

    async def replay(self, job_id: str) -> list[JobEvent]:
        path = self._path_for(job_id)
        if not path.exists():
            return []
        events: list[JobEvent] = []
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(JobEvent(**json.loads(line)))
        return events


class PlaceholderEventFeed(EventFeed):
    """Generates synthetic event sequence for dev/test.

    Yields deterministic event stream for any job_id without real queue.
    Useful for UI development until queue integration is ready.
    """

    def __init__(self, delay: float = 0.05) -> None:
        self._delay = delay
        self._appended: list[JobEvent] = []

    async def stream(self, job_id: str, after_id: str | None = None) -> AsyncIterator[str]:
        events = self._build_placeholder_events(job_id)
        if after_id:
            idx = next((i for i, e in enumerate(events) if e.id == after_id), None)
            events = events[idx + 1:] if idx is not None else events
        for ev in events:
            yield serialize_event(ev)

    async def append(self, event: JobEvent) -> None:
        self._appended.append(event)

    async def replay(self, job_id: str) -> list[JobEvent]:
        return [e for e in self._appended if e.jobId == job_id]

    def _build_placeholder_events(self, job_id: str) -> list[JobEvent]:
        t0 = time.time()
        return [
            JobStarted(jobId=job_id, payload={"recipeId": "default", "input": "placeholder", "runId": job_id}),
            JobStage(jobId=job_id, payload={"stage": "grill", "progress": 10, "label": "Grilling prompt"}),
            JobStage(jobId=job_id, payload={"stage": "direct", "progress": 25, "label": "Planning scenes"}),
            JobStage(jobId=job_id, payload={"stage": "render", "progress": 50, "label": "Rendering scenes"}),
            JobStage(jobId=job_id, payload={"stage": "review", "progress": 75, "label": "Reviewing output"}),
            JobStage(jobId=job_id, payload={"stage": "assemble", "progress": 90, "label": "Assembling final"}),
            JobCompleted(jobId=job_id, payload={"finalVideo": f"/artifacts/{job_id}/final.mp4", "duration": 30, "artifactCount": 5}),
        ]


# ─── Factory ──────────────────────────────────────────────────────────────


def create_feed(kind: str = "memory", **kwargs) -> EventFeed:
    """Create event feed by kind name.

    Args:
        kind: ``"memory"``, ``"file"``, or ``"placeholder"``.
        **kwargs: passed to feed constructor.

    Returns:
        Configured EventFeed instance.
    """
    feeds = {
        "memory": MemoryEventFeed,
        "file": FileEventFeed,
        "placeholder": PlaceholderEventFeed,
    }
    cls = feeds.get(kind)
    if cls is None:
        raise ValueError(f"Unknown feed kind: {kind!r}. Choose from: {list(feeds)}")
    return cls(**kwargs)
