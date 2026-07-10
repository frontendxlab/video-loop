"""9router provider adapter — dynamic model discovery with fallback.

Tries to fetch models from 9router API (OpenAI-compatible ``/v1/models``).
Falls back to hardcoded defaults if discovery fails (no API key, network
error, parse error). Results cached for 60 seconds to avoid hammering
the API on repeated calls.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

import requests

logger = logging.getLogger(__name__)

# ─── Fallback defaults ────────────────────────────────────────────────────────

_FALLBACK_MODELS: list[dict[str, Any]] = [
    {"id": "ocg/deepseek-v4-flash", "label": "DeepSeek V4 Flash", "maxTokens": 32768},
    {"id": "ocg/deepseek-v4-flash:free", "label": "DeepSeek V4 Flash Free", "maxTokens": 8192},
]

_DEFAULT_BASE_URL = "https://api.9router.com/v1"
_CACHE_TTL = 60  # seconds

# ─── Module-level cache ───────────────────────────────────────────────────────

_cache: dict[str, Any] | None = None
_cache_ts: float = 0


def _make_label(model_id: str) -> str:
    """Convert model ID to human-readable label."""
    parts = model_id.replace("/", " ").replace("-", " ").replace(":", " ").split()
    return " ".join(p.capitalize() for p in parts)


def _infer_max_tokens(model_id: str) -> int:
    """Infer sensible maxTokens heuristic from model ID."""
    m = model_id.lower()
    if "free" in m:
        return 8192
    if any(kw in m for kw in ("flash", "tiny", "mini", "small", "light")):
        return 16384
    return 32768


def _parse_models(api_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse OpenAI-compatible ``/v1/models`` response into model configs."""
    models: list[dict[str, Any]] = []
    for item in api_data.get("data", []):
        model_id: str = item.get("id", "")
        if not model_id:
            continue
        # Skip embedding / image / audio models — keep only LLM-ish ids
        if not any(c in model_id for c in ("/", ":")) and "." not in model_id:
            continue
        models.append({
            "id": model_id,
            "label": item.get("label") or item.get("description") or item.get("owned_by") or _make_label(model_id),
            "maxTokens": _infer_max_tokens(model_id),
        })
    return models


def _fallback_result(error: str) -> dict[str, Any]:
    """Return fallback result with hardcoded models."""
    return {
        "models": list(_FALLBACK_MODELS),
        "discovered": False,
        "source": "fallback",
        "error": error,
    }


def discover_models(*, force: bool = False) -> dict[str, Any]:
    """Discover 9router models from API or return fallback defaults.

    Uses ``9ROUTER_API_KEY`` and ``9ROUTER_API_URL`` env vars. Results
    cached for 60 s to avoid repeated API calls on rapid endpoint hits.

    Parameters
    ----------
    force : bool
        Bypass cache and force a fresh API call.

    Returns
    -------
    dict
        ``models`` — parsed model config list.
        ``discovered`` — ``True`` when models came from live API.
        ``source`` — ``"api"`` or ``"fallback"``.
        ``error`` — error string on fallback, ``None`` on success.
    """
    global _cache, _cache_ts  # noqa: PLW0603

    now = time.time()
    if not force and _cache is not None and (now - _cache_ts) < _CACHE_TTL:
        return _cache

    api_url = os.environ.get("9ROUTER_API_URL", "")
    api_key = os.environ.get("9ROUTER_API_KEY", "")

    # If env vars not set, try to read from persisted settings
    if not api_key or not api_url:
        try:
            from videoforge.api.settings import load_settings
            settings = load_settings()
            for p in settings.get("providers", []):
                if p.get("provider") == "9router":
                    if not api_key:
                        api_key = p.get("apiKey", "")
                    if not api_url:
                        api_url = p.get("baseUrl", "")
                    break
        except Exception:
            pass

    if not api_url:
        api_url = _DEFAULT_BASE_URL

    if not api_key:
        result = _fallback_result("9ROUTER_API_KEY not set")
        _cache, _cache_ts = result, now
        return result

    try:
        resp = requests.get(
            f"{api_url.rstrip('/')}/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=5,
        )
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()
        models = _parse_models(data)
        if not models:
            msg = "API returned no parseable models"
            result = _fallback_result(msg)
        else:
            result = {"models": models, "discovered": True, "source": "api", "error": None}
    except requests.RequestException as exc:
        logger.warning("9router discovery failed: %s", exc)
        result = _fallback_result(str(exc))
    except (ValueError, TypeError, KeyError) as exc:
        logger.warning("9router discovery parse error: %s", exc)
        result = _fallback_result(f"Parse error: {exc}")

    _cache, _cache_ts = result, now
    return result


def clear_cache() -> None:
    """Drop cached discovery result (helpful in tests)."""
    global _cache, _cache_ts  # noqa: PLW0603
    _cache = None
    _cache_ts = 0
