"""SSE event payload schemas for job lifecycle.

All event types defined in STUDY-ui-showcase-next.md §5.
Deterministic payload schemas — no web framework dependency.
"""

from __future__ import annotations

import json
import time
import uuid
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """All event types from STUDY-ui-showcase-next.md §5."""

    JOB_STARTED = "job.started"
    JOB_STAGE = "job.stage"
    JOB_TODO = "job.todo"
    PROMPT_GRILLED = "prompt.grilled"
    DIRECTOR_SCENE_PLANNED = "director.scene_planned"
    DIRECTOR_SCENE_ROUTED = "director.scene_routed"
    SUBAGENT_STARTED = "subagent.started"
    SUBAGENT_TOKEN = "subagent.token"
    SUBAGENT_COMPLETED = "subagent.completed"
    SUBAGENT_FAILED = "subagent.failed"
    RENDER_SCENE_STARTED = "render.scene_started"
    RENDER_SCENE_COMPLETED = "render.scene_completed"
    REVIEW_ISSUE = "review.issue"
    REPAIR_PLAN = "repair.plan"
    RETRY_STARTED = "retry.started"
    ARTIFACT_READY = "artifact.ready"
    JOB_COMPLETED = "job.completed"
    JOB_FAILED = "job.failed"


SSE_EVENT_TYPES: list[str] = [e.value for e in EventType]
"""Canonical list of all SSE event types. Single source of truth."""


class JobEvent(BaseModel):
    """Base envelope for all SSE events.

    Every event has: id, type, jobId, timestamp, payload.
    """

    id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    type: str = ""
    jobId: str
    timestamp: float = Field(default_factory=time.time)
    payload: dict[str, Any] = Field(default_factory=dict)

    def serialize(self) -> str:
        """Serialize to SSE text/event-stream format.

        Returns multi-line string with event: type, data: JSON, id: eventId.
        Blank line trailing for consumer parsing.
        """
        data = self.model_dump()
        lines = [
            f"event: {self.type}",
            f"id: {self.id}",
            f"data: {json.dumps(data, separators=(',', ':'))}",
            "",
            "",
        ]
        return "\n".join(lines)


# ─── Concrete event helpers ──────────────────────────────────────────────


class JobStarted(JobEvent):
    type: Literal["job.started"] = "job.started"
    payload: dict[str, Any]  # recipeId, input, runId


class JobStage(JobEvent):
    type: Literal["job.stage"] = "job.stage"
    payload: dict[str, Any]  # stage, progress (0-100), label


class JobTodo(JobEvent):
    type: Literal["job.todo"] = "job.todo"
    payload: dict[str, Any]  # itemId, description, status


class PromptGrilled(JobEvent):
    type: Literal["prompt.grilled"] = "prompt.grilled"
    payload: dict[str, Any]  # grills, chosen


class DirectorScenePlanned(JobEvent):
    type: Literal["director.scene_planned"] = "director.scene_planned"
    payload: dict[str, Any]  # sceneCount, kinds


class DirectorSceneRouted(JobEvent):
    type: Literal["director.scene_routed"] = "director.scene_routed"
    payload: dict[str, Any]  # sceneId, kind, engine


class SubagentStarted(JobEvent):
    type: Literal["subagent.started"] = "subagent.started"
    payload: dict[str, Any]  # subagentId, role, model


class SubagentToken(JobEvent):
    type: Literal["subagent.token"] = "subagent.token"
    payload: dict[str, Any]  # subagentId, tokens, progressPct


class SubagentCompleted(JobEvent):
    type: Literal["subagent.completed"] = "subagent.completed"
    payload: dict[str, Any]  # subagentId, result


class SubagentFailed(JobEvent):
    type: Literal["subagent.failed"] = "subagent.failed"
    payload: dict[str, Any]  # subagentId, error


class RenderSceneStarted(JobEvent):
    type: Literal["render.scene_started"] = "render.scene_started"
    payload: dict[str, Any]  # sceneId, engine


class RenderSceneCompleted(JobEvent):
    type: Literal["render.scene_completed"] = "render.scene_completed"
    payload: dict[str, Any]  # sceneId, outputPath, duration


class ReviewIssue(JobEvent):
    type: Literal["review.issue"] = "review.issue"
    payload: dict[str, Any]  # sceneId, gate, verdict, detail


class RepairPlan(JobEvent):
    type: Literal["repair.plan"] = "repair.plan"
    payload: dict[str, Any]  # issue, strategy, retryCount


class RetryStarted(JobEvent):
    type: Literal["retry.started"] = "retry.started"
    payload: dict[str, Any]  # itemType, itemId, attempt, maxRetries


class ArtifactReady(JobEvent):
    type: Literal["artifact.ready"] = "artifact.ready"
    payload: dict[str, Any]  # artifactType, path, sceneId (optional)


class JobCompleted(JobEvent):
    type: Literal["job.completed"] = "job.completed"
    payload: dict[str, Any]  # finalVideo, duration, artifactCount


class JobFailed(JobEvent):
    type: Literal["job.failed"] = "job.failed"
    payload: dict[str, Any]  # error, stage, retryCount


# ─── Factory / dispatch ───────────────────────────────────────────────────


_EVENT_BY_TYPE: dict[str, type[JobEvent]] = {
    "job.started": JobStarted,
    "job.stage": JobStage,
    "job.todo": JobTodo,
    "prompt.grilled": PromptGrilled,
    "director.scene_planned": DirectorScenePlanned,
    "director.scene_routed": DirectorSceneRouted,
    "subagent.started": SubagentStarted,
    "subagent.token": SubagentToken,
    "subagent.completed": SubagentCompleted,
    "subagent.failed": SubagentFailed,
    "render.scene_started": RenderSceneStarted,
    "render.scene_completed": RenderSceneCompleted,
    "review.issue": ReviewIssue,
    "repair.plan": RepairPlan,
    "retry.started": RetryStarted,
    "artifact.ready": ArtifactReady,
    "job.completed": JobCompleted,
    "job.failed": JobFailed,
}


def parse_event(raw: str) -> JobEvent:
    """Parse SSE data line into typed JobEvent.

    Args:
        raw: JSON string from SSE ``data:`` field.

    Returns:
        Concrete JobEvent subclass based on ``type`` field.
    """
    data = json.loads(raw)
    event_type = data.get("type", "")
    cls = _EVENT_BY_TYPE.get(event_type, JobEvent)
    return cls(**data)


def serialize_event(event: JobEvent) -> str:
    """Serialize JobEvent to SSE text/event-stream format."""
    return event.serialize()
