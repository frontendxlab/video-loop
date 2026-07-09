"""TTS engine — deterministic audio generation with word timing.

This module deterministically generates TTS audio from text and computes
word-level timestamps. It wraps the Pocket TTS HTTP server.
"""

from __future__ import annotations

import json
import logging
import wave
from pathlib import Path
from typing import Any

import requests

from videoforge.engine.models import WordTiming

logger = logging.getLogger("videoforge.engine.tts")


def generate_audio(
    text: str,
    output_path: str | Path,
    voice: str = "alba",
    tts_url: str = "http://localhost:8000",
) -> dict[str, Any]:
    """Generate TTS audio and return metadata.

    Args:
        text: Text to synthesize.
        output_path: Where to save the WAV file.
        voice: TTS voice name.
        tts_url: Pocket TTS server URL.

    Returns:
        dict with: audio_path, duration_seconds, sample_rate, word_timestamps
    """
    resp = requests.post(
        f"{tts_url}/tts",
        data={"text": text, "voice": voice},
        timeout=120,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"TTS failed: {resp.status_code} {resp.text[:200]}")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    ct = resp.headers.get("content-type", "")
    if "audio" in ct:
        path.write_bytes(resp.content)
    elif resp.text.strip().startswith("{"):
        body = resp.json()
        if "audio" in body:
            import base64
            path.write_bytes(base64.b64decode(body["audio"]))
        else:
            raise RuntimeError(f"TTS returned JSON without audio: {list(body.keys())}")
    else:
        path.write_bytes(resp.content)

    # Get actual duration from WAV file size
    duration = _wav_duration(path)

    # Prefer forced alignment (real word boundaries) when module available
    words = text.split()
    word_timestamps: list[WordTiming]
    try:
        from videoforge.audio.forced_align import forced_align
        aligned = forced_align(text, str(path))
        word_timestamps = [
            WordTiming(text=w["text"], startMs=float(w["startMs"]), endMs=float(w["endMs"]))
            for w in aligned
        ]
    except Exception:
        word_timestamps = _estimate_word_timestamps(words, duration)

    return {
        "audio_path": str(path.resolve()),
        "duration_seconds": duration,
        "sample_rate": 24000,
        "word_timestamps": [{"text": w.text, "startMs": w.startMs, "endMs": w.endMs} for w in word_timestamps],
    }


def _wav_duration(path: Path) -> float:
    """Get actual WAV duration from file size, not header (which is wrong for streamed WAVs)."""
    with wave.open(str(path), "rb") as wf:
        framerate = wf.getframerate()
        sampwidth = wf.getsampwidth()
        channels = wf.getnchannels()
    data_bytes = path.stat().st_size - 44
    return data_bytes / (sampwidth * channels) / framerate if data_bytes > 0 else 0.0


def _estimate_word_timestamps(words: list[str], total_duration: float) -> list[WordTiming]:
    """Distribute total duration evenly across words."""
    if not words:
        return []
    per_word_ms = (total_duration * 1000) / len(words)
    result = []
    for i, w in enumerate(words):
        result.append(WordTiming(
            text=w,
            startMs=round(i * per_word_ms),
            endMs=round((i + 1) * per_word_ms),
        ))
    return result


def build_scene_timing(
    scene_duration_frames: int,
    fps: int,
    word_timestamps: list[dict[str, Any]],
) -> list[WordTiming]:
    """Convert raw word timestamps to scene-relative WordTiming objects."""
    return [
        WordTiming(text=w["text"], startMs=w["startMs"], endMs=w["endMs"])
        for w in word_timestamps
    ]
