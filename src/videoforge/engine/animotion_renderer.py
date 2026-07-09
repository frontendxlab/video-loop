"""Animotion renderer — render HTML/CSS/JS scenes to MP4 via Chrome CDP + FFmpeg.

Flow:
1. Start Chrome headless with remote debugging
2. Connect via CDP (Chrome DevTools Protocol) over websockets
3. Navigate to generated HTML
4. For each frame: evaluate setFrame(i), capture screenshot via Page.captureScreenshot
5. FFmpeg frame sequence → MP4

Deterministic: same HTML + same Chrome version → byte-identical frames.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import socket
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import Any

from websockets.sync.client import connect

from videoforge.engine.animotion_adapter import scene_to_html
from videoforge.engine.models import SceneDefinition

logger = logging.getLogger("videoforge.engine.animotion")

CHROME_BINARY: str = ""
for _bin in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
    if subprocess.run(["which", _bin], capture_output=True, text=True).returncode == 0:
        CHROME_BINARY = _bin
        break

CLIP_FORMAT: dict[str, Any] = {
    "fps": 30,
    "width": 1920,
    "height": 1080,
    "pixel_format": "yuv420p",
    "video_codec": "h264",
    "audio_codec": "aac",
}


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _get_debug_ws_url(port: int) -> str | None:
    """Fetch the WebSocket debugger URL from Chrome DevTools endpoint."""
    url = f"http://localhost:{port}/json/version"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        return data.get("webSocketDebuggerUrl")
    except Exception as exc:
        logger.warning("Failed to get CDP WS URL: %s", exc)
        return None


def _send_cdp(ws: Any, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Send CDP command and receive response."""
    msg_id = _send_cdp._counter = getattr(_send_cdp, "_counter", 0) + 1
    ws.send(json.dumps({"id": msg_id, "method": method, "params": params or {}}))
    while True:
        resp = json.loads(ws.recv())
        if resp.get("id") == msg_id:
            return resp.get("result", {})
        # Ignore events (no id or different id)


def capture_frames(
    html_content: str,
    output_dir: str | Path,
    *,
    fps: int = 30,
    duration_frames: int = 90,
    width: int = 1920,
    height: int = 1080,
    chrome_binary: str | None = None,
) -> list[str]:
    """Capture frames from animated HTML via Chrome CDP.

    Returns list of PNG paths, one per frame.
    Raises RuntimeError if browser capture fails.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write HTML to temp file
    html_path = output_dir / "scene.html"
    html_path.write_text(html_content, encoding="utf-8")

    binary = chrome_binary or CHROME_BINARY
    if not binary:
        raise RuntimeError("No Chrome/Chromium binary found for Animotion renderer")

    port = _find_free_port()
    user_data = output_dir / "chrome_user_data"
    user_data.mkdir(exist_ok=True)

    chrome_proc = subprocess.Popen(
        [
            binary,
            f"--remote-debugging-port={port}",
            f"--user-data-dir={user_data}",
            "--headless=new",
            "--no-sandbox",
            "--disable-gpu",
            "--disable-software-rasterizer",
            f"--window-size={width},{height}",
            "--hide-scrollbars",
            f"file://{html_path.resolve()}",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        # Wait for Chrome to start
        ws_url = None
        for _attempt in range(20):
            time.sleep(0.3)
            ws_url = _get_debug_ws_url(port)
            if ws_url:
                break

        if not ws_url:
            raise RuntimeError("Chrome didn't start CDP in time")

        # Connect via websockets
        with connect(ws_url, open_timeout=10) as ws:
            # Enable domains
            _send_cdp(ws, "Page.enable")
            _send_cdp(ws, "DOM.enable")
            _send_cdp(ws, "Runtime.enable")

            # Navigate to HTML
            result = _send_cdp(ws, "Page.navigate", {"url": f"file://{html_path.resolve()}"})
            nav_id = result.get("frameId", "")

            # Wait for page load
            for _ in range(50):
                time.sleep(0.1)
                expr = "document.readyState === 'complete' && typeof window.setFrame === 'function'"
                r = _send_cdp(ws, "Runtime.evaluate", {"expression": expr, "returnByValue": True})
                if r.get("result", {}).get("value"):
                    break

            # Set viewport to exact size
            _send_cdp(ws, "Emulation.setDeviceMetricsOverride", {
                "width": width, "height": height,
                "deviceScaleFactor": 1, "mobile": False,
            })

            frame_paths: list[str] = []
            pad = len(str(duration_frames))

            for i in range(duration_frames):
                # Set animation frame
                _send_cdp(ws, "Runtime.evaluate", {
                    "expression": f"window.setFrame({i})",
                    "returnByValue": True,
                })

                # Small delay for render completion
                if duration_frames <= 180:
                    time.sleep(0.005)  # ~5ms for short clips

                # Capture screenshot
                result = _send_cdp(ws, "Page.captureScreenshot", {
                    "format": "png",
                    "fromSurface": True,
                })
                png_data = base64.b64decode(result.get("data", ""))

                frame_path = output_dir / f"frame_{i:0{pad}d}.png"
                frame_path.write_bytes(png_data)
                frame_paths.append(str(frame_path.resolve()))

            return frame_paths

    finally:
        chrome_proc.terminate()
        try:
            chrome_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            chrome_proc.kill()


def frames_to_video(
    frame_dir: str | Path,
    output_path: str | Path,
    fps: int = 30,
    frame_count: int | None = None,
) -> str:
    """Assemble frame PNG sequence into MP4 via FFmpeg.

    Returns output path string.
    """
    frame_dir = Path(frame_dir)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    pad = len(str(frame_count or 90))
    pattern = str(frame_dir / f"frame_%0{pad}d.png")

    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", pattern,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        "-crf", "18",
        "-vf", f"scale={CLIP_FORMAT['width']}:{CLIP_FORMAT['height']}:force_original_aspect_ratio=disable",
        "-frames:v", str(frame_count) if frame_count else "",
        str(output_path),
    ]
    # Remove empty strings from list
    cmd = [c for c in cmd if c]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0 or not output_path.exists():
        raise RuntimeError(f"FFmpeg frame assembly failed: {(result.stderr or '')[-500:]}")

    return str(output_path.resolve())


def render_scene(
    scene: SceneDefinition,
    output_dir: str | Path,
    *,
    fps: int = 30,
    width: int = 1920,
    height: int = 1080,
    chrome_binary: str | None = None,
) -> dict[str, Any]:
    """Render a single scene via Animotion (HTML → Chrome CDP → MP4).

    Args:
        scene: SceneDefinition with text/title/points/code payload
        output_dir: Where to write output files
        fps: Frames per second
        width/height: Output resolution
        chrome_binary: Path to Chrome/Chromium binary

    Returns: {"success": bool, "video_path": str|None, "log": str}
    """
    # Build payload dict from scene
    payload: dict[str, Any] = {
        "title": scene.title,
        "subtitle": scene.subtitle,
        "text": scene.text,
        "code": scene.code,
        "lang": scene.lang,
        "points": scene.points,
        "caption": scene.caption,
        "cta": scene.cta,
        "src": scene.src,
    }
    # Remove empty values
    payload = {k: v for k, v in payload.items() if v}

    html = scene_to_html(
        title=scene.title or "Animotion",
        kind=scene.type.value,
        payload=payload,
        duration_frames=scene.duration,
        fps=fps,
        width=width,
        height=height,
    )

    with tempfile.TemporaryDirectory(prefix="animotion_") as tmpdir:
        tmp_path = Path(tmpdir)

        try:
            frame_paths = capture_frames(
                html,
                tmp_path / "frames",
                fps=fps,
                duration_frames=scene.duration,
                width=width,
                height=height,
                chrome_binary=chrome_binary,
            )
        except RuntimeError as exc:
            return {"success": False, "video_path": None, "log": str(exc)[:500]}

        if not frame_paths:
            return {"success": False, "video_path": None, "log": "No frames captured"}

        try:
            video_path = frames_to_video(
                tmp_path / "frames",
                output_dir / f"scene_animotion.mp4",
                fps=fps,
                frame_count=scene.duration,
            )
        except RuntimeError as exc:
            return {"success": False, "video_path": None, "log": str(exc)[:500]}

        return {
            "success": True,
            "video_path": video_path,
            "log": f"Rendered {scene.duration}f via Animotion",
        }
