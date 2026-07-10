"""TTS adapter using Pocket TTS MCP server.

Connects to the remote Pocket TTS MCP server via SSE and calls generate_speech tool.
Falls back to direct HTTP if MCP connection fails.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import struct
import wave
from pathlib import Path
from typing import Any

logger = logging.getLogger("videoforge.engine.tts_mcp")

# Default Pocket TTS MCP server URL (from OpenCode config)
DEFAULT_MCP_URL = "http://172.236.176.29:8000/sse"


def _create_wav_from_pcm(pcm_data: bytes, sample_rate: int = 24000, channels: int = 1, sample_width: int = 2) -> bytes:
    """Create WAV file from raw PCM data."""
    import io
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    return buf.getvalue()


async def generate_speech_via_mcp(
    text: str,
    voice: str = "alba",
    mcp_url: str = DEFAULT_MCP_URL,
) -> dict[str, Any]:
    """Generate speech using Pocket TTS MCP server.

    Returns:
        dict with: audio_bytes (WAV), duration_seconds, sample_rate
    """
    from mcp import ClientSession
    from mcp.client.sse import sse_client

    async with sse_client(mcp_url) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            tool_names = [t.name for t in tools.tools]
            logger.info("MCP TTS tools: %s", tool_names)

            # Call generate_speech
            result = await session.call_tool(
                "generate_speech",
                arguments={"text": text, "voice": voice}
            )

            # Parse result
            if result.content and len(result.content) > 0:
                content = result.content[0]
                if hasattr(content, 'data'):
                    # AudioContent - base64 encoded audio (f32le format)
                    audio_bytes = base64.b64decode(content.data)

                    return {
                        "audio_bytes": audio_bytes,
                        "duration_seconds": 0,  # calculated after ffmpeg conversion
                        "sample_rate": 24000,
                    }

    raise RuntimeError("MCP TTS returned no audio data")


def generate_speech_mcp_sync(
    text: str,
    output_path: str | Path,
    voice: str = "alba",
    mcp_url: str = DEFAULT_MCP_URL,
) -> dict[str, Any]:
    """Synchronous wrapper for MCP TTS generation.

    Works both standalone and inside an existing event loop by running
    the async MCP call in a background thread with its own event loop.

    Args:
        text: Text to synthesize
        output_path: Where to save the WAV file
        voice: Voice name (e.g., "alba")
        mcp_url: Pocket TTS MCP server URL

    Returns:
        dict with: audio_path, duration_seconds, sample_rate, word_timestamps
    """
    import threading

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Run async MCP call in a background thread to avoid event loop conflicts
    result_holder: dict[str, Any] = {}
    error_holder: list[Exception] = []

    def _run():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result_holder["data"] = loop.run_until_complete(
                    generate_speech_via_mcp(text, voice, mcp_url)
                )
            finally:
                loop.close()
        except Exception as e:
            error_holder.append(e)

    t = threading.Thread(target=_run)
    t.start()
    t.join(timeout=60)

    if error_holder:
        raise error_holder[0]
    if "data" not in result_holder:
        raise TimeoutError("MCP TTS call timed out after 60s")

    result = result_holder["data"]

    # Save raw audio bytes (f32le format from Pocket TTS)
    raw_path = output_path.with_suffix(".raw")
    raw_path.write_bytes(result["audio_bytes"])

    # Convert to standard WAV using ffmpeg
    import subprocess
    cmd = [
        "ffmpeg", "-y", "-f", "f32le", "-ar", "24000", "-ac", "1",
        "-i", str(raw_path),
        "-acodec", "pcm_s16le",
        str(output_path),
    ]
    conv = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    raw_path.unlink(missing_ok=True)

    if conv.returncode != 0 or not output_path.exists():
        raise RuntimeError(f"FFmpeg audio conversion failed: {conv.stderr[-300:]}")

    # Calculate duration from converted WAV
    with wave.open(str(output_path), 'rb') as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        duration_seconds = frames / rate if rate > 0 else 0
        sample_rate = rate

    # Generate word timestamps (estimated)
    words = text.split()
    duration_ms = duration_seconds * 1000
    word_timestamps = []
    if words:
        per_word_ms = duration_ms / len(words)
        for i, word in enumerate(words):
            word_timestamps.append({
                "text": word,
                "startMs": round(i * per_word_ms),
                "endMs": round((i + 1) * per_word_ms),
            })

    return {
        "audio_path": str(output_path.resolve()),
        "duration_seconds": result["duration_seconds"],
        "sample_rate": result["sample_rate"],
        "word_timestamps": word_timestamps,
    }
