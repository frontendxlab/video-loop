from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class PipelinePhaseError(Exception):
    def __init__(self, phase: str, message: str, context: dict[str, Any] | None = None) -> None:
        self.phase = phase
        self.context = context or {}
        super().__init__(f"[{phase}] {message}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase": self.phase,
            "error": str(self),
            "context": self.context,
        }


def handle_phase_error(phase: str, error: Exception) -> dict[str, Any]:
    logger.exception("Phase %s failed: %s", phase, error)
    if isinstance(error, PipelinePhaseError):
        return error.to_dict()
    return {
        "phase": phase,
        "error": str(error),
        "context": {},
    }
