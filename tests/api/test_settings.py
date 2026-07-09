"""Tests for Settings API — GET/PUT /api/settings.

Covers:
- GET returns defaults when no file exists
- GET returns persisted values after PUT
- PUT validates payload (rejects out-of-range values → 422)
- Persisted file is valid JSON
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from videoforge.api.app import create_app


@pytest.fixture
def settings_path(tmp_path: Path) -> Path:
    """Point settings to temp path so tests don't clobber real config."""
    p = tmp_path / "settings.json"
    os.environ["VIDEOFORGE_SETTINGS_PATH"] = str(p)
    yield p
    os.environ.pop("VIDEOFORGE_SETTINGS_PATH", None)


@pytest.fixture
def client(settings_path: Path):
    app = create_app()
    return TestClient(app)


DEFAULT_PROVIDER_COUNT = 5

VALID_PAYLOAD = {
    "activeProvider": "openai",
    "activeModel": "gpt-4o",
    "providers": [
        {
            "provider": "openai",
            "label": "OpenAI",
            "apiKey": "sk-test",
            "baseUrl": "",
            "defaultModel": "gpt-4o",
            "models": [{"id": "gpt-4o", "label": "GPT-4o", "maxTokens": 16384}],
        },
    ],
    "queue": {"maxConcurrency": 8, "maxQueueSize": 200},
    "retry": {"maxRetries": 5, "retryDelayMs": 3000, "exponentialBackoff": False},
    "review": {"l0MinScore": 0.95, "l1MinScore": 0.9, "coherenceGateEnabled": False},
}


class TestGetSettings:
    """GET /api/settings behaves correctly."""

    def test_returns_defaults_when_no_file(self, client):
        resp = client.get("/api/settings")
        assert resp.status_code == 200
        data = resp.json()
        assert data["activeProvider"] == "openai"
        assert data["activeModel"] == "gpt-4o"
        assert len(data["providers"]) == DEFAULT_PROVIDER_COUNT
        assert data["queue"] == {"maxConcurrency": 4, "maxQueueSize": 100}
        assert data["retry"] == {"maxRetries": 3, "retryDelayMs": 2000, "exponentialBackoff": True}
        assert data["review"] == {"l0MinScore": 0.9, "l1MinScore": 0.85, "coherenceGateEnabled": True}

    def test_returns_persisted_values_after_put(self, client):
        # Persist via PUT
        client.put("/api/settings", json=VALID_PAYLOAD)

        # Read back via GET
        resp = client.get("/api/settings")
        assert resp.status_code == 200
        data = resp.json()
        assert data["activeProvider"] == "openai"
        assert data["activeModel"] == "gpt-4o"
        assert len(data["providers"]) == 1
        assert data["providers"][0]["apiKey"] == "sk-test"
        assert data["queue"]["maxConcurrency"] == 8
        assert data["retry"]["maxRetries"] == 5
        assert data["retry"]["exponentialBackoff"] is False

    def test_returns_updated_defaults_after_partial_put(self, client):
        """PUT replaces entire config; GET returns exactly what was PUT."""
        payload = {
            "activeProvider": "anthropic",
            "activeModel": "claude-sonnet-4-20250514",
            "providers": [
                {
                    "provider": "anthropic",
                    "label": "Anthropic",
                    "apiKey": "",
                    "baseUrl": "",
                    "defaultModel": "claude-sonnet-4-20250514",
                    "models": [{"id": "claude-sonnet-4-20250514", "label": "Claude Sonnet 4", "maxTokens": 8192}],
                },
            ],
            "queue": {"maxConcurrency": 1, "maxQueueSize": 50},
            "retry": {"maxRetries": 0, "retryDelayMs": 0, "exponentialBackoff": False},
            "review": {"l0MinScore": 0.5, "l1MinScore": 0.5, "coherenceGateEnabled": False},
        }
        client.put("/api/settings", json=payload)
        resp = client.get("/api/settings")
        assert resp.status_code == 200
        assert resp.json() == payload


class TestPutSettings:
    """PUT /api/settings validates and persists."""

    def test_persists_valid_payload(self, client, settings_path):
        resp = client.put("/api/settings", json=VALID_PAYLOAD)
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

        # Verify file on disk
        assert settings_path.exists()
        with open(settings_path) as f:
            saved = json.load(f)
        assert saved["queue"]["maxConcurrency"] == 8

    def test_rejects_invalid_type(self, client):
        """activeProvider must be a string, not a number."""
        resp = client.put("/api/settings", json={"activeProvider": 42, "activeModel": "gpt-4o", "queue": {"maxConcurrency": 1, "maxQueueSize": 10}, "retry": {"maxRetries": 1, "retryDelayMs": 1000, "exponentialBackoff": False}, "review": {"l0MinScore": 0.5, "l1MinScore": 0.5, "coherenceGateEnabled": False}, "providers": []})
        assert resp.status_code == 422

    def test_rejects_queue_out_of_range(self, client):
        payload = dict(VALID_PAYLOAD)
        payload["queue"] = {"maxConcurrency": 99, "maxQueueSize": 100}
        resp = client.put("/api/settings", json=payload)
        assert resp.status_code == 422

    def test_rejects_retry_out_of_range(self, client):
        payload = dict(VALID_PAYLOAD)
        payload["retry"] = {"maxRetries": 99, "retryDelayMs": 2000, "exponentialBackoff": True}
        resp = client.put("/api/settings", json=payload)
        assert resp.status_code == 422

    def test_rejects_review_score_out_of_range(self, client):
        payload = dict(VALID_PAYLOAD)
        payload["review"] = {"l0MinScore": 1.5, "l1MinScore": 0.5, "coherenceGateEnabled": True}
        resp = client.put("/api/settings", json=payload)
        assert resp.status_code == 422

    def test_rejects_invalid_json(self, client):
        resp = client.put("/api/settings", data=b"not json", headers={"Content-Type": "application/json"})
        assert resp.status_code == 422


class TestPersistence:
    """Settings survive across app instances (file-backed)."""

    def test_survives_app_restart(self, client, settings_path):
        # Write via first app
        client.put("/api/settings", json=VALID_PAYLOAD)

        # Create new app instance
        app2 = create_app()
        client2 = TestClient(app2)
        resp = client2.get("/api/settings")
        assert resp.status_code == 200
        data = resp.json()
        assert data["queue"]["maxConcurrency"] == 8

    def test_corrupt_file_falls_back_to_defaults(self, settings_path):
        """If settings.json is invalid JSON, GET returns defaults."""
        settings_path.write_text("{{{corrupt")
        app = create_app()
        client = TestClient(app)
        resp = client.get("/api/settings")
        assert resp.status_code == 200
        data = resp.json()
        assert data["activeProvider"] == "openai"
        assert len(data["providers"]) == DEFAULT_PROVIDER_COUNT
