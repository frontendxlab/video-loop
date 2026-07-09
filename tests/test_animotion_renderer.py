"""Tests for animotion adapter + renderer.

Tests adapter HTML generation and renderer frame capture (mocked).
"""

from __future__ import annotations

import base64
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from videoforge.design_tokens import animotion_theme_stub
from videoforge.engine.animotion_adapter import get_animotion_render_config, scene_to_html
from videoforge.engine.animotion_renderer import capture_frames, frames_to_video
from videoforge.engine.models import SceneDefinition, SceneType


class TestAnimotionAdapter:
    def test_render_config_returns_animotion(self):
        config = get_animotion_render_config()
        assert config["renderer"] == "animotion"
        assert config["theme"]["accentColor"] == "#4A90D9"
        assert config["theme"]["tokenSource"] == "config/design-tokens.json"

    def test_scene_to_html_returns_string(self):
        html = scene_to_html(
            title="Hello",
            kind="title",
            payload={"subtitle": "World"},
            duration_frames=90,
            fps=30,
        )
        assert isinstance(html, str)
        assert len(html) > 200
        assert "window.setFrame" in html
        assert "Hello" in html
        assert "World" in html

    def test_scene_to_html_contains_set_frame(self):
        html = scene_to_html(
            title="Test",
            kind="bullets",
            payload={"points": ["A", "B", "C"]},
            duration_frames=150,
        )
        assert "window.setFrame" in html
        assert "A" in html
        assert "B" in html
        assert "data-start" in html
        assert "data-anim" in html

    def test_scene_to_html_code_scene(self):
        html = scene_to_html(
            title="Code",
            kind="code",
            payload={"code": "def hello():\n  return 42", "lang": "python"},
            duration_frames=120,
        )
        assert "def hello()" in html
        assert "JetBrains Mono" in html
        assert ".anim-element" in html

    def test_scene_to_html_uses_shared_tokens(self):
        tokens = animotion_theme_stub()
        html = scene_to_html(
            title="Token Test", kind="title", payload={},
            duration_frames=60,
        )
        # Font from tokens should appear in HTML
        font = tokens.get("bodyFont", "Inter")
        assert font in html
        assert tokens.get("deckBackground", "") in html

    def test_scene_to_html_different_kinds(self):
        kinds = ["title", "outro", "bullets", "code", "diff", "diagram"]
        for kind in kinds:
            html = scene_to_html(
                title=f"Test {kind}",
                kind=kind,
                payload={"text": "content"},
                duration_frames=60,
            )
            assert f"Test {kind}" in html
            assert "window.setFrame" in html

    def test_html_exposes_set_frame_function(self):
        html = scene_to_html(
            title="Frame Test", kind="title", payload={},
            duration_frames=30,
        )
        # Browser would find window.setFrame
        assert "window.setFrame = function(f)" in html
        # Animation logic for element visibility
        assert "data-start" in html
        assert "el.style.display" in html


class TestAnimotionRenderer:
    def test_frames_to_video(self, tmp_path: Path):
        """FFmpeg assembly from frame PNGs — includes silent audio track."""
        frame_dir = tmp_path / "frames"
        frame_dir.mkdir()
        output = tmp_path / "output.mp4"

        # Create dummy frame (small valid PNG)
        for i in range(3):
            _make_dummy_png(frame_dir / f"frame_{i:03d}.png")

        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            # Create output file so ffmpeg "succeeds"
            output.write_text("dummy")

            result = frames_to_video(
                frame_dir, output, fps=30, frame_count=3,
            )
            assert result.endswith(".mp4")
            assert mock_run.called
            # Verify silent audio track is muxed
            args = mock_run.call_args[0][0]
            args_str = " ".join(args)
            assert "anullsrc" in args_str, "Missing anullsrc silent audio source"
            assert "-c:a" in args, "Missing audio codec flag"
            aac_idx = args.index("-c:a")
            assert args[aac_idx + 1] == "aac", "Audio codec should be aac"
            assert "-shortest" in args, "Missing -shortest flag"
            assert "-ac" in args, "Missing audio channels flag"
            assert "-ar" in args, "Missing audio sample rate flag"

    def test_capture_frames_no_chrome(self):
        """Should raise RuntimeError when Chrome not found."""
        with patch("videoforge.engine.animotion_renderer.CHROME_BINARY", ""):
            with pytest.raises(RuntimeError, match="No Chrome"):
                capture_frames(
                    "<html></html>",
                    "/tmp/animotion_test",
                    fps=30,
                    duration_frames=2,
                )

    def test_capture_frames_with_mocked_cdp(self, tmp_path: Path):
        """Mock CDP websocket to verify frame capture pipeline."""
        from unittest.mock import patch as u_patch

        fake_png = _make_png_bytes()

        with (
            u_patch("videoforge.engine.animotion_renderer.CHROME_BINARY", "/fake/chrome"),
            u_patch("subprocess.Popen") as mock_popen,
            u_patch("urllib.request.urlopen") as mock_urlopen,
            u_patch("videoforge.engine.animotion_renderer.connect") as mock_connect,
        ):
            # Mock Chrome process
            mock_popen.return_value = MagicMock()

            # Mock CDP WS URL fetch
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps({
                "webSocketDebuggerUrl": "ws://localhost:0/devtools/page/1",
            }).encode()
            mock_urlopen.return_value.__enter__.return_value = mock_resp

            # Mock websocket connection
            mock_ws = MagicMock()

            # Build CDP response sequence to match _send_cdp calls
            # Phase 1: domain enables (Page, DOM, Runtime) — each gets {}
            responses = []
            # Page.enable, DOM.enable, Runtime.enable — consume 3 recv's for id=1..3
            # But _send_cdp sends and then recv-loops, so extra events may arrive
            # We generate many generic responses in order; _send_cdp discards non-matching
            msg_id = 1
            for _ in range(3):
                responses.append(json.dumps({"id": msg_id, "result": {}}))
                msg_id += 1
            # Page.navigate
            responses.append(json.dumps({"id": msg_id, "result": {"frameId": "f1"}}))
            msg_id += 1
            # readyState evaluate: first returns False, next 2 also False to be safe
            for _ in range(3):
                responses.append(json.dumps({
                    "id": msg_id,
                    "result": {"result": {"type": "boolean", "value": False}},
                }))
                msg_id += 1
            # readyState evaluate returns True
            responses.append(json.dumps({
                "id": msg_id,
                "result": {"result": {"type": "boolean", "value": True}},
            }))
            msg_id += 1
            # Emulation.setDeviceMetricsOverride
            responses.append(json.dumps({"id": msg_id, "result": {}}))
            msg_id += 1
            # 3 frames: each has Runtime.evaluate (setFrame) + Page.captureScreenshot
            b64 = base64.b64encode(fake_png).decode()
            for _frame_idx in range(3):
                responses.append(json.dumps({"id": msg_id, "result": {"result": {"value": None}}}))
                msg_id += 1
                responses.append(json.dumps({"id": msg_id, "result": {"data": b64}}))
                msg_id += 1
            # Extra padding responses to prevent StopIteration if readyState loop runs more
            for _ in range(20):
                responses.append(json.dumps({"id": msg_id, "result": {"result": {"value": True}}}))
                msg_id += 1

            mock_ws.recv.side_effect = responses
            mock_connect.return_value.__enter__.return_value = mock_ws

            result = capture_frames(
                "<html><body><div id='scene'></div></body></html>",
                tmp_path,
                fps=30,
                duration_frames=3,
            )
            assert len(result) == 3


def _make_dummy_png(path: Path):
    """Create minimal valid PNG for testing."""
    path.write_bytes(_make_png_bytes())


def _make_png_bytes() -> bytes:
    """Return minimal valid PNG bytes (1x1 pixel)."""
    import struct
    import zlib

    # Minimal PNG: 1x1 RGB pixel
    def _chunk(chunk_type: bytes, data: bytes) -> bytes:
        c = chunk_type + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = _chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    raw = zlib.compress(b"\x00\x80\x80\x80")  # gray pixel
    idat = _chunk(b"IDAT", raw)
    iend = _chunk(b"IEND", b"")
    return sig + ihdr + idat + iend
