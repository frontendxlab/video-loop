#!/usr/bin/env python3
"""
End-to-end video generation pipeline.

Usage:
  python3 scripts/generate_video.py --topic "Claude Certified Architect exam Domain 1"

Flow:
  1. Define script and scenes
  2. Generate TTS audio via Pocket TTS HTTP server
  3. Build Remotion inputProps with proper timing
  4. Render MP4 via npx remotion render
  5. Verify with Frame Reviewer (L1-L5)
  6. Output final video

Known Pocket TTS quirks (handled here):
  - tts_model = None: The `pocket-tts serve` CLI doesn't pass model to uvicorn.
    Use scripts/run_tts_server.py instead, or start with:
      python3 scripts/run_tts_server.py
  - WAV setnframes(1B): Pocket TTS WAV writer uses setnframes(1_000_000_000) as
    streaming placeholder. Never use wave.open().getnframes().
    Always compute: (filesize - 44) / (sampwidth * channels) / framerate
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import wave
from pathlib import Path
from typing import Any

import requests

from videoforge.design_tokens import remotion_style_defaults

TTS_URL = os.environ.get("POCKET_TTS_URL", "http://localhost:8000")
STYLE_DEFAULTS = remotion_style_defaults()


def wav_actual_duration(path: str | Path) -> float:
    """Get real WAV duration from file size, not the streaming placeholder header."""
    p = Path(path)
    with wave.open(str(p), "rb") as wf:
        framerate = wf.getframerate()
        sampwidth = wf.getsampwidth()
        channels = wf.getnchannels()
    data_bytes = p.stat().st_size - 44  # WAV header is 44 bytes
    if data_bytes <= 0:
        return 0.0
    return data_bytes / (sampwidth * channels) / framerate


def generate_tts(text: str, output_path: str | Path, voice: str = "alba") -> float:
    """Generate TTS audio via Pocket TTS. Returns actual duration in seconds."""
    resp = requests.post(
        f"{TTS_URL}/tts",
        data={"text": text, "voice": voice},
        timeout=120,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"TTS failed: {resp.status_code} {resp.text[:200]}")

    Path(output_path).write_bytes(resp.content)
    return wav_actual_duration(output_path)


def build_video(
    scenes: list[dict[str, Any]],
    texts: list[str],
    output_path: str = "/tmp/videoforge/output.mp4",
    voice: str = "alba",
    remotion_dir: str | None = None,
) -> str:
    """Full pipeline: TTS -> compose -> render -> return MP4 path."""
    if remotion_dir is None:
        remotion_dir = str(Path(__file__).parent.parent / "remotion-project")

    remo = Path(remotion_dir)
    public_audio = remo / "public" / "audio"
    public_audio.mkdir(parents=True, exist_ok=True)
    out_dir = Path(output_path).parent
    out_dir.mkdir(parents=True, exist_ok=True)

    scene_list: list[dict[str, Any]] = []
    all_captions: list[dict[str, Any]] = []
    frame_offset = 0

    for i, (text, cfg) in enumerate(zip(texts, scenes)):
        print(f"[{i+1}/{len(texts)}] TTS...", end=" ", flush=True)
        wav_path = out_dir / f"scene_{i:03d}.wav"
        try:
            secs = generate_tts(text, wav_path, voice)
        except RuntimeError as e:
            print(f"FAILED: {e}")
            secs = max(2.0, len(text.split()) * 0.3)
            wav_path = None

        if wav_path and wav_path.exists():
            import shutil
            shutil.copy2(wav_path, public_audio / wav_path.name)

        dur_frames = max(1, int(secs * 30))
        print(f"{secs:.1f}s -> {dur_frames}f", flush=True)

        scene = dict(cfg)
        scene["duration"] = dur_frames
        scene_list.append(scene)

        words = text.split()
        per_word_ms = (dur_frames / 30.0 * 1000.0) / max(len(words), 1)
        for j, w in enumerate(words):
            all_captions.append({
                "text": w,
                "startMs": round(j * per_word_ms),
                "endMs": round((j + 1) * per_word_ms),
            })
        frame_offset += dur_frames

    audio_tracks = []
    off = 0
    for i, s in enumerate(scene_list):
        audio_tracks.append({
            "src": f"audio/scene_{i:03d}.wav",
            "startFrame": off,
            "durationFrames": s["duration"],
        })
        off += s["duration"]

    input_props = {
        "title": "Generated Video",
        "scenes": scene_list,
        "audioTracks": audio_tracks,
        "captions": all_captions,
        "voice": voice,
        "style": STYLE_DEFAULTS,
    }

    props_path = out_dir / "input_props.json"
    with open(props_path, "w") as f:
        json.dump(input_props, f, indent=2)

    total_secs = frame_offset / 30.0
    print(f"\nTotal: {frame_offset}f ({total_secs:.1f}s), {len(scene_list)} scenes", flush=True)

    os.chdir(remo)
    out = Path(output_path)
    result = subprocess.run(
        [
            "npx", "remotion", "render", "src/index.ts", "VideoComposition",
            str(out), "--props", str(props_path),
            "--concurrency", "2", "--log", "error",
        ],
        capture_output=True, text=True, timeout=600,
    )

    if result.returncode != 0:
        err = (result.stderr or "")[-1000:]
        raise RuntimeError(f"Render failed:\n{err}")

    if not out.exists():
        raise RuntimeError("Render completed but no output file found")

    # Run L0 Mixed-Engine + L1 Frame Review
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from videoforge.review.frame_reviewer import FrameReviewer
        fr = FrameReviewer()
        l0 = fr.check_mixed_engine(str(out))
        l0_st = fr.evaluate_l0_policy(l0)
        print(f"L0 Mixed-Engine: status={l0_st}, {len(l0.get('issues',[]))} issues, "
              f"{l0.get('sampled_frames',0)} frames sampled")
        if l0.get("issues"):
            for iss in l0["issues"]:
                print(f"  [{iss.get('severity','?')}] {iss.get('type','?')}: {iss.get('detail','')}")
        review = fr.check_integrity(str(out))
        if not review.get("passed", False):
            print(f"WARNING: L1 Frame Review failed: {review.get('issues', [])}")
        else:
            print(f"L1 Frame Review: {review.get('total_frames')} frames, passed")
    except ImportError:
        pass  # Frame reviewer not available

    return str(out.resolve())


if __name__ == "__main__":
    # Example: Claude Certified Architect exam — Domain 1
    scenes = [
        {"type": "title", "title": "Claude Certified Architect", "subtitle": "Domain 1: Fundamentals"},
        {"type": "bullet", "points": ["Understand Claude architecture and capabilities", "Master prompt engineering fundamentals", "Learn context window management", "Implement safety and reliability patterns"]},
        {"type": "code", "code": "System: You are a helpful assistant.\nUser: What is the capital of France?\nAssistant: The capital of France is Paris.", "lang": "text"},
        {"type": "bullet", "points": ["Messages API with three roles", "Streaming responses for real-time apps", "Token counting and cost estimation", "Retry logic and error handling"]},
        {"type": "code", "code": "import anthropic\n\nclient = anthropic.Anthropic()\nresponse = client.messages.create(\n    model=\"claude-sonnet-4-20250514\",\n    max_tokens=1024,\n    messages=[{\"role\": \"user\", \"content\": \"Hello\"}]\n)\nprint(response.content[0].text)", "lang": "python"},
        {"type": "bullet", "points": ["Extended thinking for reasoning", "Vision capabilities for images", "Tool use for function calling", "Context caching for savings"]},
        {"type": "outro", "title": "Master the Fundamentals", "cta": "Continue learning"},
    ]
    texts = [
        "Welcome to the Claude Certified Architect exam preparation. This video covers Domain 1: Fundamentals.",
        "Domain 1 covers four key areas: understanding Claude architecture, mastering prompt engineering, learning context window management, and implementing safety patterns.",
        "The fundamentals start with understanding the message structure. Claude uses System, User, and Assistant messages.",
        "Key API concepts include the Messages API with three roles, streaming responses, token counting, and retry logic.",
        "Here is the Python SDK call. Create a client and call messages dot create.",
        "Advanced features include extended thinking, vision capabilities, tool use, and context caching.",
        "Master these fundamentals. Good luck with your certification journey.",
    ]
    out = build_video(scenes, texts, "/tmp/videoforge/output.mp4")
    print(f"\nVideo generated: {out}")
