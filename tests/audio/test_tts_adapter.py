"""Tests for TTS adapter (wraps Pocket TTS HTTP)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from videoforge.exceptions import TTSConnectionError, TTSTimeoutError


@pytest.fixture
def adapter():
    from videoforge.audio.adapter import TTSAdapter
    return TTSAdapter(server_url="http://localhost:8000", voice="alba")


class TestAdapterInit:
    def test_default_server_url(self):
        from videoforge.audio.adapter import TTSAdapter
        a = TTSAdapter()
        assert a.server_url == "http://localhost:8000"

    def test_default_voice(self):
        from videoforge.audio.adapter import TTSAdapter
        a = TTSAdapter()
        assert a.voice is not None


class TestAdapterGenerate:
    def test_generate_returns_wav_path(self, adapter, temp_dir):
        output = temp_dir / "test.wav"
        with patch.object(adapter, "_call_pocket_tts") as mock:
            mock.return_value = str(output)
            output.write_bytes(b"RIFF")
            result = adapter.generate("Hello world.", output)
        assert result.endswith(".wav")

    def test_retries_on_connection_error(self, adapter):
        adapter.max_retries = 3
        call_count = 0

        def _fail_then_succeed(text, path):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TTSConnectionError("mock fail")
            return str(path)

        with patch.object(adapter, "_call_pocket_tts", side_effect=_fail_then_succeed):
            result = adapter.generate("Hello", Path("/tmp/t.wav"))
            assert call_count == 3
            assert result is not None

    def test_raises_after_max_retries(self, adapter):
        adapter.max_retries = 2
        with patch.object(adapter, "_call_pocket_tts") as mock:
            mock.side_effect = TTSConnectionError("persistent fail")
            with pytest.raises(TTSConnectionError):
                adapter.generate("Hello", Path("/tmp/t.wav"))
            assert mock.call_count == 2

    def test_timeout_raises_tts_timeout(self, adapter):
        import time

        def _slow(text, path):
            time.sleep(0.1)
            return str(path)

        adapter.timeout_seconds = 0.01
        with patch.object(adapter, "_call_pocket_tts", side_effect=_slow):
            with pytest.raises(TTSTimeoutError):
                adapter.generate("Hello", Path("/tmp/t.wav"))
