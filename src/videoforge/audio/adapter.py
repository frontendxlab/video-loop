from __future__ import annotations

import concurrent.futures
import time
from pathlib import Path

import requests

from videoforge.exceptions import TTSConnectionError, TTSTimeoutError

POCKET_TTS_VOICES = [
    "alba", "alessio", "angela", "anna", "aria", "brian",
    "catherine", "chiara", "davis", "derek", "emma", "eva",
    "fred", "giada", "giorgio", "henry", "jane", "lisa",
    "maria", "mark", "michele", "olivia", "paul", "sara",
    "steve", "susan",
]


class TTSAdapter:
    def __init__(
        self,
        server_url: str = "http://localhost:8000",
        voice: str = "alba",
        max_retries: int = 3,
        timeout_seconds: int = 60,
    ):
        self.server_url = server_url
        self.voice = voice
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds

    def generate(self, text: str, output_path: Path) -> str:
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                return self._run_with_timeout(text, output_path)
            except TTSTimeoutError:
                raise
            except TTSConnectionError as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
        raise TTSConnectionError(
            f"All {self.max_retries} retries exhausted"
        ) from last_exception

    def _run_with_timeout(self, text: str, output_path: Path) -> str:
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        try:
            future = executor.submit(self._call_pocket_tts, text, output_path)
            return future.result(timeout=self.timeout_seconds)
        except concurrent.futures.TimeoutError:
            raise TTSTimeoutError(
                f"TTS request timed out after {self.timeout_seconds}s"
            )
        finally:
            executor.shutdown(wait=False)

    def _call_pocket_tts(self, text: str, output_path: Path) -> str:
        try:
            resp = requests.post(
                f"{self.server_url}/tts",
                data={"text": text, "voice": self.voice},
                timeout=self.timeout_seconds,
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            raise TTSConnectionError(str(e)) from e
        output_path.write_bytes(resp.content)
        return str(output_path)

    @staticmethod
    def get_voice_list() -> list[str]:
        return list(POCKET_TTS_VOICES)

    @staticmethod
    def clone_voice(audio_path: str, name: str) -> str:
        return ""

    @staticmethod
    def list_saved_voices() -> list[str]:
        voices_dir = Path.home() / ".cache" / "videoforge" / "voices"
        if not voices_dir.exists():
            return []
        return sorted(
            str(p) for p in voices_dir.iterdir() if p.suffix == ".safetensors"
        )
