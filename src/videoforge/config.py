from __future__ import annotations

import os
from typing import Any

import yaml

from videoforge.exceptions import ConfigError


def load_config(path: str | None = None) -> dict[str, Any]:
    config_path = path or "config.yaml"
    try:
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML syntax: {e}") from e


class Config:
    def __init__(self, path: str | None = None) -> None:
        self._data = load_config(path)

    @property
    def server(self) -> dict[str, Any]:
        return self._data.get("server", {})

    @property
    def server_name(self) -> str:
        return self.server.get("name", "VideoForge")

    @property
    def server_host(self) -> str:
        return self.server.get("host", "127.0.0.1")

    @property
    def server_port(self) -> int:
        return self.server.get("port", 8080)

    @property
    def server_log_level(self) -> str:
        return self.server.get("log_level", "INFO")

    @property
    def pocket_tts(self) -> dict[str, Any]:
        return self._data.get("pocket_tts", {})

    @property
    def pocket_tts_server_url(self) -> str:
        return self.pocket_tts.get("server_url", "http://127.0.0.1:8120")

    @property
    def pocket_tts_default_voice(self) -> str:
        return self.pocket_tts.get("default_voice", "en_US-amy-medium")

    @property
    def pocket_tts_language(self) -> str:
        return self.pocket_tts.get("language", "en")

    @property
    def pocket_tts_max_retries(self) -> int:
        return self.pocket_tts.get("max_retries", 3)

    @property
    def pocket_tts_timeout_seconds(self) -> int:
        return self.pocket_tts.get("timeout_seconds", 60)

    @property
    def pipeline(self) -> dict[str, Any]:
        return self._data.get("pipeline", {})

    @property
    def pipeline_max_video_duration_seconds(self) -> int:
        return self.pipeline.get("max_video_duration_seconds", 180)

    @property
    def pipeline_default_fps(self) -> int:
        return self.pipeline.get("default_fps", 30)

    @property
    def pipeline_default_resolution(self) -> tuple[int, int]:
        res = self.pipeline.get("default_resolution", [1920, 1080])
        return (res[0], res[1])

    @property
    def pipeline_default_codec(self) -> str:
        return self.pipeline.get("default_codec", "h264")

    @property
    def pipeline_max_caption_tokens_per_chunk(self) -> int:
        return self.pipeline.get("max_caption_tokens_per_chunk", 50)

    @property
    def assets(self) -> dict[str, Any]:
        return self._data.get("assets", {})

    @property
    def assets_ai_generation(self) -> dict[str, Any]:
        return self.assets.get("ai_generation", {})

    @property
    def assets_ai_generation_enabled(self) -> bool:
        return self.assets_ai_generation.get("enabled", False)

    @property
    def assets_ai_generation_provider(self) -> str:
        return self.assets_ai_generation.get("provider", "")

    @property
    def assets_stock_photos(self) -> dict[str, Any]:
        return self.assets.get("stock_photos", {})

    @property
    def assets_stock_photos_enabled(self) -> bool:
        return self.assets_stock_photos.get("enabled", False)

    @property
    def assets_stock_photos_provider(self) -> str:
        return self.assets_stock_photos.get("provider", "")

    @property
    def github(self) -> dict[str, Any]:
        return self._data.get("github", {})

    @property
    def github_webhook_secret_env(self) -> str:
        return self.github.get("webhook_secret_env", "VIDEOFORGE_WEBHOOK_SECRET")

    @property
    def github_auto_post_pr_comments(self) -> bool:
        return self.github.get("auto_post_pr_comments", True)

    def check_kill_switch(self) -> bool:
        return bool(os.environ.get("VIDEOFORCE_KILL_SWITCH"))
