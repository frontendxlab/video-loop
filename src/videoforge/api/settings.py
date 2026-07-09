"""Settings API — read/update persisted config for provider/model/queue/retry/review."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/settings", tags=["settings"])


def _settings_path() -> Path:
    """Resolve settings path from env or default."""
    return Path(os.environ.get("VIDEOFORGE_SETTINGS_PATH", "config/settings.json"))

# ─── Pydantic models ─────────────────────────────────────────────────────────


class ModelConfig(BaseModel):
    id: str
    label: str
    maxTokens: int = 4096


class ProviderConfig(BaseModel):
    provider: str
    label: str
    apiKey: str = ""
    baseUrl: str = ""
    defaultModel: str
    models: list[ModelConfig] = []


class QueueSettings(BaseModel):
    maxConcurrency: int = Field(default=4, ge=1, le=32)
    maxQueueSize: int = Field(default=100, ge=1, le=500)


class RetrySettings(BaseModel):
    maxRetries: int = Field(default=3, ge=0, le=10)
    retryDelayMs: int = Field(default=2000, ge=0, le=60_000)
    exponentialBackoff: bool = True


class ReviewThresholds(BaseModel):
    l0MinScore: float = Field(default=0.9, ge=0, le=1)
    l1MinScore: float = Field(default=0.85, ge=0, le=1)
    coherenceGateEnabled: bool = True


class SettingsPayload(BaseModel):
    activeProvider: str = "openai"
    activeModel: str = "gpt-4o"
    providers: list[ProviderConfig] = []
    queue: QueueSettings = QueueSettings()
    retry: RetrySettings = RetrySettings()
    review: ReviewThresholds = ReviewThresholds()


# ─── Defaults ────────────────────────────────────────────────────────────────


def _default_settings() -> dict[str, Any]:
    """Default settings matching frontend DEFAULT_SETTINGS."""
    return {
        "activeProvider": "openai",
        "activeModel": "gpt-4o",
        "providers": [
            {
                "provider": "openai",
                "label": "OpenAI",
                "apiKey": "",
                "baseUrl": "",
                "defaultModel": "gpt-4o",
                "models": [
                    {"id": "gpt-4o", "label": "GPT-4o", "maxTokens": 16384},
                    {"id": "gpt-4o-mini", "label": "GPT-4o Mini", "maxTokens": 16384},
                    {"id": "o1", "label": "o1", "maxTokens": 32768},
                ],
            },
            {
                "provider": "anthropic",
                "label": "Anthropic",
                "apiKey": "",
                "baseUrl": "",
                "defaultModel": "claude-sonnet-4-20250514",
                "models": [
                    {"id": "claude-sonnet-4-20250514", "label": "Claude Sonnet 4", "maxTokens": 8192},
                    {"id": "claude-opus-4-20250514", "label": "Claude Opus 4", "maxTokens": 8192},
                ],
            },
            {
                "provider": "google",
                "label": "Google",
                "apiKey": "",
                "baseUrl": "",
                "defaultModel": "gemini-2.0-flash",
                "models": [
                    {"id": "gemini-2.0-flash", "label": "Gemini 2.0 Flash", "maxTokens": 8192},
                    {"id": "gemini-2.0-pro", "label": "Gemini 2.0 Pro", "maxTokens": 8192},
                ],
            },
            {
                "provider": "groq",
                "label": "Groq",
                "apiKey": "",
                "baseUrl": "",
                "defaultModel": "llama-3.3-70b",
                "models": [
                    {"id": "llama-3.3-70b", "label": "Llama 3.3 70B", "maxTokens": 8192},
                    {"id": "mixtral-8x7b", "label": "Mixtral 8x7B", "maxTokens": 8192},
                ],
            },
            {
                "provider": "custom",
                "label": "Custom",
                "apiKey": "",
                "baseUrl": "",
                "defaultModel": "custom-model",
                "models": [{"id": "custom-model", "label": "Custom Model", "maxTokens": 4096}],
            },
        ],
        "queue": {"maxConcurrency": 4, "maxQueueSize": 100},
        "retry": {"maxRetries": 3, "retryDelayMs": 2000, "exponentialBackoff": True},
        "review": {"l0MinScore": 0.9, "l1MinScore": 0.85, "coherenceGateEnabled": True},
    }


# ─── Persistence helpers ─────────────────────────────────────────────────────


def load_settings() -> dict[str, Any]:
    """Load settings from disk or return defaults."""
    path = _settings_path()
    if path.exists():
        try:
            with open(path) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return _default_settings()


def save_settings(data: dict[str, Any]) -> None:
    """Persist settings to disk."""
    path = _settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)


# ─── Routes ──────────────────────────────────────────────────────────────────


@router.get("")
async def get_settings() -> dict[str, Any]:
    """Read current persisted settings."""
    return load_settings()


@router.put("")
async def update_settings(payload: SettingsPayload) -> dict[str, Any]:
    """Update persisted settings. Validates via Pydantic before write."""
    data = payload.model_dump()
    save_settings(data)
    return {"status": "ok"}
