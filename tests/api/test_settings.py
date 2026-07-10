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
import requests

from videoforge.providers import discover_9router_models
from videoforge.providers.router9 import clear_cache as clear_9router_cache


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


DEFAULT_PROVIDER_COUNT = 7

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
        assert data["activeProvider"] == "9router"
        assert data["activeModel"] == "ocg/deepseek-v4-flash"
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
        assert data["activeProvider"] == "9router"
        assert len(data["providers"]) == DEFAULT_PROVIDER_COUNT


class Test9RouterDefaults:
    """9router provider appears correctly in default settings."""

    def test_9router_in_default_providers(self, client):
        resp = client.get("/api/settings")
        providers = resp.json()["providers"]
        router = next((p for p in providers if p["provider"] == "9router"), None)
        assert router is not None
        assert router["defaultModel"] == "ocg/deepseek-v4-flash"
        assert len(router["models"]) == 2

    def test_9router_has_expected_models(self, client):
        resp = client.get("/api/settings")
        providers = resp.json()["providers"]
        router = next(p for p in providers if p["provider"] == "9router")
        model_ids = {m["id"] for m in router["models"]}
        assert "ocg/deepseek-v4-flash" in model_ids
        assert "ocg/deepseek-v4-flash:free" in model_ids

    def test_9router_is_active_provider_by_default(self, client):
        resp = client.get("/api/settings")
        data = resp.json()
        assert data["activeProvider"] == "9router"
        assert data["activeModel"] == "ocg/deepseek-v4-flash"


class TestProviderStatus:
    """GET /api/settings/provider-status exposes provider/model state."""

    def test_provider_status_returns_200(self, client):
        resp = client.get("/api/settings/provider-status")
        assert resp.status_code == 200

    def test_provider_status_has_active_provider(self, client):
        resp = client.get("/api/settings/provider-status")
        data = resp.json()
        assert data["activeProvider"] == "9router"
        assert data["activeModel"] == "ocg/deepseek-v4-flash"

    def test_provider_status_lists_all_providers(self, client):
        resp = client.get("/api/settings/provider-status")
        providers = resp.json()["providers"]
        assert len(providers) == DEFAULT_PROVIDER_COUNT
        ids = {p["provider"] for p in providers}
        assert "9router" in ids
        assert "openai" in ids
        assert "custom" in ids

    def test_provider_status_availability_flags(self, client):
        resp = client.get("/api/settings/provider-status")
        data = resp.json()
        # Default settings have no apiKey for any provider
        assert data["available"] is True  # 9router is in providers list
        assert data["configured"] is False  # no apiKey

    def test_provider_status_after_put(self, client):
        payload = {
            "activeProvider": "openai",
            "activeModel": "gpt-4o",
            "providers": [{
                "provider": "openai", "label": "OpenAI",
                "apiKey": "sk-configured",
                "baseUrl": "", "defaultModel": "gpt-4o",
                "models": [{"id": "gpt-4o", "label": "GPT-4o", "maxTokens": 16384}],
            }],
            "queue": {"maxConcurrency": 1, "maxQueueSize": 10},
            "retry": {"maxRetries": 1, "retryDelayMs": 1000, "exponentialBackoff": False},
            "review": {"l0MinScore": 0.5, "l1MinScore": 0.5, "coherenceGateEnabled": False},
        }
        client.put("/api/settings", json=payload)
        resp = client.get("/api/settings/provider-status")
        data = resp.json()
        assert data["activeProvider"] == "openai"
        assert data["activeModel"] == "gpt-4o"
        assert data["available"] is True
        assert data["configured"] is True  # apiKey set

    def test_provider_status_unknown_active_falls_back(self, client):
        """Unknown activeProvider still returns gracefully."""
        payload = {
            "activeProvider": "nonexistent",
            "activeModel": "foo",
            "providers": [],
            "queue": {"maxConcurrency": 1, "maxQueueSize": 10},
            "retry": {"maxRetries": 1, "retryDelayMs": 1000, "exponentialBackoff": False},
            "review": {"l0MinScore": 0.5, "l1MinScore": 0.5, "coherenceGateEnabled": False},
        }
        client.put("/api/settings", json=payload)
        resp = client.get("/api/settings/provider-status")
        data = resp.json()
        assert data["available"] is False
        assert data["configured"] is False
        assert data["activeProvider"] == "nonexistent"


class Test9RouterDiscovery:
    """9router dynamic model discovery — adapter + endpoint integration."""

    def test_discovery_fallback_when_no_api_key(self):
        """Without 9ROUTER_API_KEY and without settings, discovery returns fallback models."""
        clear_9router_cache()
        import os
        old_key = os.environ.pop("9ROUTER_API_KEY", None)
        old_url = os.environ.pop("9ROUTER_API_URL", None)
        try:
            from unittest.mock import patch
            with patch("videoforge.api.settings.load_settings", return_value={"providers": []}):
                result = discover_9router_models(force=True)
                assert result["discovered"] is False
                assert result["source"] == "fallback"
                assert "9ROUTER_API_KEY" in (result.get("error") or "")
                assert len(result["models"]) >= 2
        finally:
            if old_key: os.environ["9ROUTER_API_KEY"] = old_key
            if old_url: os.environ["9ROUTER_API_URL"] = old_url

    def test_discovery_fallback_model_ids(self):
        """Fallback models have expected IDs when no key available."""
        clear_9router_cache()
        import os
        old_key = os.environ.pop("9ROUTER_API_KEY", None)
        old_url = os.environ.pop("9ROUTER_API_URL", None)
        try:
            from unittest.mock import patch
            with patch("videoforge.api.settings.load_settings", return_value={"providers": []}):
                result = discover_9router_models(force=True)
                ids = {m["id"] for m in result["models"]}
                assert "ocg/deepseek-v4-flash" in ids
                assert "ocg/deepseek-v4-flash:free" in ids
        finally:
            if old_key: os.environ["9ROUTER_API_KEY"] = old_key
            if old_url: os.environ["9ROUTER_API_URL"] = old_url

    def test_discovery_succeeds_with_settings_key(self):
        """Discovery succeeds when settings file has 9router API key."""
        clear_9router_cache()
        result = discover_9router_models(force=True)
        assert result["discovered"] is True
        assert result["source"] == "api"
        assert len(result["models"]) > 2

    def test_provider_status_includes_discovery_meta(self, client):
        """provider-status response includes discovered/discoverySource/
        discoveryError fields for 9router provider.
        """
        clear_9router_cache()
        resp = client.get("/api/settings/provider-status")
        providers = resp.json()["providers"]
        router = next(p for p in providers if p["provider"] == "9router")
        assert "discovered" in router
        assert router["discovered"] is False  # no API key in test env
        assert router["discoverySource"] == "fallback"
        assert router["discoveryError"] is not None

    def test_provider_status_other_providers_no_discovery_meta(self, client):
        """Non-9router providers omit discovery fields."""
        resp = client.get("/api/settings/provider-status")
        providers = resp.json()["providers"]
        for p in providers:
            if p["provider"] == "9router":
                continue
            assert "discovered" not in p, f"{p['provider']} has discovered"
            assert "discoverySource" not in p, f"{p['provider']} has discoverySource"

    def test_discovery_with_mocked_api(self, monkeypatch):
        """Mocked successful API response returns discovered models."""
        import json

        clear_9router_cache()

        class _MockResponse:
            def __init__(self):
                self.status_code = 200

            def json(self):
                return {
                    "data": [
                        {"id": "ocg/deepseek-v4-flash", "owned_by": "deepseek"},
                        {"id": "ocg/deepseek-v4-flash:free", "owned_by": "deepseek"},
                        {"id": "ocg/qwen-72b", "owned_by": "alibaba"},
                    ]
                }

            def raise_for_status(self):
                pass

        monkeypatch.setattr("videoforge.providers.router9.requests.get", lambda *a, **kw: _MockResponse())
        monkeypatch.setenv("9ROUTER_API_KEY", "sk-test-key")

        result = discover_9router_models(force=True)
        assert result["discovered"] is True
        assert result["source"] == "api"
        assert result["error"] is None
        assert len(result["models"]) == 3
        ids = {m["id"] for m in result["models"]}
        assert "ocg/qwen-72b" in ids

    def test_discovery_network_error_falls_back(self, monkeypatch):
        """Network error during discovery falls back gracefully."""
        clear_9router_cache()

        def _fail(*a, **kw):
            raise requests.ConnectionError("Network unreachable")

        monkeypatch.setattr("videoforge.providers.router9.requests.get", _fail)
        monkeypatch.setenv("9ROUTER_API_KEY", "sk-test-key")

        result = discover_9router_models(force=True)
        assert result["discovered"] is False
        assert result["source"] == "fallback"
        assert "Network unreachable" in (result.get("error") or "")
        assert len(result["models"]) == 2  # fallback models

    def test_default_settings_uses_enriched_9router(self, client):
        """GET /api/settings returns 9router entry with models (fallback
        or discovered). Provider count reflects all configured providers.
        """
        clear_9router_cache()
        resp = client.get("/api/settings")
        providers = resp.json()["providers"]
        assert len(providers) == 7
        router = next(p for p in providers if p["provider"] == "9router")
        assert len(router["models"]) >= 2  # at least fallback models
        assert router["defaultModel"] == "ocg/deepseek-v4-flash"
