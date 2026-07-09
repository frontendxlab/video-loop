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

    def test_scene_to_html_comparison_basic(self):
        """Comparison scene produces split-pane layout with headings + body."""
        html = scene_to_html(
            title="VS Code vs Neovim",
            kind="comparison",
            payload={
                "left_heading": "VS Code",
                "right_heading": "Neovim",
                "left_body": "Full IDE with GUI and extensions.",
                "right_body": "Terminal editor with fast startup.",
            },
            duration_frames=120,
        )
        assert "VS Code vs Neovim" in html
        assert "VS Code" in html
        assert "Neovim" in html
        assert "Full IDE with GUI and extensions." in html
        assert "Terminal editor with fast startup." in html
        assert "display:inline-block" in html
        assert "44%" in html  # each pane width
        assert "window.setFrame" in html

    def test_scene_to_html_comparison_empty_fields(self):
        """Comparison with empty left heading/body handles gracefully."""
        html = scene_to_html(
            title="Comparison",
            kind="comparison",
            payload={
                "left_heading": "",
                "right_heading": "Right Only",
                "left_body": "",
                "right_body": "Some content here.",
            },
            duration_frames=60,
        )
        assert "Comparison" in html
        assert "Right Only" in html
        assert "Some content here." in html

    def test_scene_to_html_comparison_uses_shared_tokens(self):
        """Comparison scene references theme tokens (fonts, colors)."""
        tokens = animotion_theme_stub()
        html = scene_to_html(
            title="Token Test",
            kind="comparison",
            payload={
                "left_heading": "Left",
                "right_heading": "Right",
                "left_body": "Body A",
                "right_body": "Body B",
            },
            duration_frames=90,
        )
        assert tokens.get("headingFont", "Inter") in html
        assert tokens.get("panelBackground", "#1E293B") in html

    def test_scene_to_html_comparison_frame_visibility(self):
        """Comparison elements have data-start/data-end for frame-driven visibility."""
        html = scene_to_html(
            title="Frame Test",
            kind="comparison",
            payload={
                "left_heading": "L",
                "right_heading": "R",
                "left_body": "LB",
                "right_body": "RB",
            },
            duration_frames=100,
        )
        count_start = html.count("data-start")
        assert count_start >= 3, f"Expected >=3 anim elements, got {count_start}"
        assert html.count("data-anim") == count_start

    def test_scene_to_html_comparison_kind_routes_correctly(self):
        """'comparison' kind routes to split-pane layout, not generic fallback."""
        generic = scene_to_html(
            title="Same", kind="generic",
            payload={"text": "plain"},
            duration_frames=60,
        )
        comp = scene_to_html(
            title="Same", kind="comparison",
            payload={
                "left_heading": "A",
                "right_heading": "B",
                "left_body": "X",
                "right_body": "Y",
            },
            duration_frames=60,
        )
        assert "44%" in comp
        assert "44%" not in generic

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
        kinds = ["title", "outro", "bullets", "code", "diff", "diagram", "chart", "bar-chart", "comparison", "timeline"]
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

    # --- Chart / bar-chart scene tests ---

    def test_bar_chart_html_structure(self):
        html = scene_to_html(
            title="Sales",
            kind="bar-chart",
            payload={"labels": ["Q1", "Q2", "Q3"], "values": [100, 200, 150]},
            duration_frames=90,
        )
        assert "Sales" in html
        assert "Q1" in html
        assert "Q2" in html
        assert "Q3" in html
        assert "100" in html
        assert "200" in html
        assert "150" in html
        assert "scaleY" in html
        assert "data-anim=\"grow-up\"" in html

    def test_bar_chart_uses_shared_tokens(self):
        tokens = animotion_theme_stub()
        html = scene_to_html(
            title="Chart",
            kind="chart",
            payload={"labels": ["A", "B"], "values": [10, 20]},
            duration_frames=60,
        )
        assert tokens.get("accentColor", "") in html
        assert tokens.get("bodyFont", "Inter") in html

    def test_bar_chart_anim_element_count(self):
        html = scene_to_html(
            title="Bars",
            kind="bar-chart",
            payload={"labels": ["X", "Y", "Z"], "values": [5, 15, 10]},
            duration_frames=120,
        )
        # Each bar + title = 4 anim-elements
        assert html.count("anim-element") >= 3
        assert "grow-up" in html
        assert "transform-origin:bottom center" in html

    def test_bar_chart_empty_payload_falls_back(self):
        html = scene_to_html(
            title="Empty Chart",
            kind="chart",
            payload={},
            duration_frames=60,
        )
        assert "Empty Chart" in html
        # No element with data-anim="grow-up" (only in shared JS)
        assert 'data-anim="grow-up"' not in html

    def test_bar_chart_uneven_zipped(self):
        html = scene_to_html(
            title="Uneven",
            kind="chart",
            payload={"labels": ["A", "B", "C", "D"], "values": [10, 20]},
            duration_frames=60,
        )
        assert "A" in html
        assert "B" in html
        # Only 2 bars rendered (values zipped to shortest).
        # Count grow-up in element attrs only (CSS selector also matches).
        body = html.split("<body")[1].split("</body")[0]
        assert body.count("data-anim=\"grow-up\"") == 2

    def test_bar_chart_window_set_frame_compatible(self):
        html = scene_to_html(
            title="Chart Frame",
            kind="chart",
            payload={"labels": ["Apples", "Oranges"], "values": [30, 50]},
            duration_frames=90,
        )
        assert "window.setFrame" in html
        assert "data-anim=\"grow-up\"" in html
        # JS must handle grow-up animation
        assert "grow-up" in html


class TestTimelineScene:
    """Timeline scene — horizontal milestone track with frame-progress reveal."""

    def test_timeline_html_structure(self):
        """Timeline produces expected HTML skeleton with track + milestones."""
        html = scene_to_html(
            title="Roadmap",
            kind="timeline",
            payload={
                "milestones": [
                    {"date": "Q1 2024", "title": "Alpha", "description": "Internal build"},
                    {"date": "Q2 2024", "title": "Beta", "description": "Feature complete"},
                    {"date": "Q3 2024", "title": "RC", "description": "Stabilization"},
                ],
            },
            duration_frames=120,
        )
        assert "Roadmap" in html
        assert "Q1 2024" in html
        assert "Alpha" in html
        assert "Beta" in html
        assert "RC" in html
        assert "window.setFrame" in html
        assert 'data-anim="expand"' in html
        assert 'data-anim="progress"' in html

    def test_timeline_milestones_rendered(self):
        """All milestone entries (date, title, description) appear in output."""
        milestones = [
            {"date": "Jan", "title": "Start", "description": "Kick off"},
            {"date": "Feb", "title": "Dev", "description": "Development"},
            {"date": "Mar", "title": "Ship", "description": "Launch"},
        ]
        html = scene_to_html(
            title="Milestones",
            kind="timeline",
            payload={"milestones": milestones},
            duration_frames=90,
        )
        for ms in milestones:
            assert ms["date"] in html
            assert ms["title"] in html
            assert ms["description"] in html

    def test_timeline_token_usage(self):
        """Timeline uses shared theme tokens (fonts, colors)."""
        tokens = animotion_theme_stub()
        html = scene_to_html(
            title="Token Check",
            kind="timeline",
            payload={"milestones": [{"date": "V1", "title": "Launch"}]},
            duration_frames=60,
        )
        assert tokens.get("bodyFont", "Inter") in html
        assert tokens.get("monoFont", "JetBrains Mono") in html
        assert tokens.get("accentColor", "#4A90D9") in html

    def test_timeline_frame_attributes(self):
        """Timeline elements have data-start/data-end for frame-driven visibility."""
        html = scene_to_html(
            title="Frames",
            kind="timeline",
            payload={
                "milestones": [
                    {"date": "A", "title": "One"},
                    {"date": "B", "title": "Two"},
                    {"date": "C", "title": "Three"},
                ],
            },
            duration_frames=100,
        )
        count_start = html.count("data-start")
        assert count_start >= 5, f"Expected >=5 anim-elements, got {count_start}"
        assert html.count("data-anim") == count_start

    def test_timeline_empty_milestones(self):
        """Timeline with no milestones renders gracefully."""
        html = scene_to_html(
            title="Empty Timeline",
            kind="timeline",
            payload={},
            duration_frames=60,
        )
        assert "Empty Timeline" in html
        assert "window.setFrame" in html
        assert "No timeline data" in html

    def test_timeline_max_milestones(self):
        """Timeline caps at 10 milestones; excess ignored."""
        many = [{"date": f"M{i}", "title": f"Milestone {i}"} for i in range(15)]
        html = scene_to_html(
            title="Many",
            kind="timeline",
            payload={"milestones": many},
            duration_frames=120,
        )
        for i in range(10):
            assert f"M{i}" in html
        assert "M10" not in html

    def test_timeline_recognized_kind(self):
        """Timeline is a recognized kind that does not fall back to generic."""
        html = scene_to_html(
            title="Route Check",
            kind="timeline",
            payload={"milestones": [{"date": "D1", "title": "T1"}]},
            duration_frames=60,
        )
        assert 'data-anim="expand"' in html
        assert "D1" in html
        assert "T1" in html


class TestDiagramScene:
    """Interactive diagram scene — positioned nodes + SVG edges."""

    def test_diagram_html_structure(self):
        """Diagram with basic nodes/edges produces correct HTML skeleton."""
        html = scene_to_html(
            title="Flow",
            kind="diagram",
            payload={
                "nodes": [
                    {"id": "n1", "label": "Start", "x": 200, "y": 400},
                    {"id": "n2", "label": "End", "x": 600, "y": 400},
                ],
                "edges": [
                    {"source": "n1", "target": "n2"},
                ],
            },
            duration_frames=90,
        )
        assert "Flow" in html
        assert "Start" in html
        assert "End" in html
        assert "<line " in html  # SVG edge line
        assert '<svg ' in html
        assert "window.setFrame" in html
        assert 'data-anim="fade-up"' in html

    def test_diagram_auto_layout(self):
        """Diagram auto-places nodes when x/y omitted — horizontal row."""
        html = scene_to_html(
            title="Auto",
            kind="diagram",
            payload={
                "nodes": [
                    {"id": "a", "label": "A"},
                    {"id": "b", "label": "B"},
                    {"id": "c", "label": "C"},
                ],
            },
            duration_frames=60,
        )
        assert "Auto" in html
        assert "A" in html
        assert "B" in html
        assert "C" in html
        assert "window.setFrame" in html

    def test_diagram_edges_rendered(self):
        """Edges rendered as SVG line elements with arrow marker."""
        html = scene_to_html(
            title="Edges",
            kind="diagram",
            payload={
                "nodes": [
                    {"id": "a", "label": "Src", "x": 100, "y": 300},
                    {"id": "b", "label": "Dst", "x": 500, "y": 300},
                ],
                "edges": [
                    {"source": "a", "target": "b", "label": "connects"},
                ],
            },
            duration_frames=60,
        )
        assert "<line " in html
        assert "marker-end" in html
        assert 'class="diagram-edge"' in html
        assert 'x1="' in html
        assert 'x2="' in html

    def test_diagram_shared_tokens(self):
        """Diagram uses shared theme tokens (fonts, colors)."""
        tokens = animotion_theme_stub()
        html = scene_to_html(
            title="Token Test",
            kind="diagram",
            payload={
                "nodes": [
                    {"id": "n", "label": "Node", "x": 300, "y": 300},
                ],
            },
            duration_frames=60,
        )
        assert tokens.get("bodyFont", "Inter") in html
        assert tokens.get("accentColor", "#4A90D9") in html

    def test_diagram_frame_attributes(self):
        """Diagram elements have data-start/data-end for frame-driven visibility."""
        html = scene_to_html(
            title="Frame Test",
            kind="diagram",
            payload={
                "nodes": [
                    {"id": "a", "label": "A", "x": 100, "y": 300},
                    {"id": "b", "label": "B", "x": 500, "y": 300},
                ],
                "edges": [
                    {"source": "a", "target": "b"},
                ],
            },
            duration_frames=100,
        )
        count_start = html.count("data-start")
        assert count_start >= 3, f"Expected >=3 anim-elements, got {count_start}"
        assert html.count("data-anim") == count_start

    def test_diagram_empty_nodes_falls_back(self):
        """Diagram with no nodes falls back to generic output."""
        html = scene_to_html(
            title="Empty Diagram",
            kind="diagram",
            payload={},
            duration_frames=60,
        )
        assert "Empty Diagram" in html
        assert "window.setFrame" in html
        # No SVG line elements
        assert "<line " not in html

    def test_diagram_interactive_hover(self):
        """Diagram nodes include hover interaction attributes."""
        html = scene_to_html(
            title="Hover Test",
            kind="diagram",
            payload={
                "nodes": [
                    {"id": "n1", "label": "Hover", "x": 400, "y": 300},
                ],
            },
            duration_frames=60,
        )
        assert "onmouseenter" in html
        assert "onmouseleave" in html
        assert "scale(1.08)" in html
        assert "cursor:pointer" in html

    def test_diagram_set_frame_compatible(self):
        """Diagram scene works with window.setFrame frame-by-frame capture."""
        html = scene_to_html(
            title="Diagram Frame",
            kind="diagram",
            payload={
                "nodes": [
                    {"id": "n1", "label": "X", "x": 200, "y": 300},
                    {"id": "n2", "label": "Y", "x": 600, "y": 300},
                ],
                "edges": [
                    {"source": "n1", "target": "n2"},
                ],
            },
            duration_frames=90,
        )
        assert "window.setFrame" in html
        assert "data-start" in html
        assert "data-anim" in html

    def test_diagram_color_per_node(self):
        """Each node can have its own color, falls back to palette."""
        html = scene_to_html(
            title="Colors",
            kind="diagram",
            payload={
                "nodes": [
                    {"id": "a", "label": "Red", "x": 100, "y": 300, "color": "#FF0000"},
                    {"id": "b", "label": "Blue", "x": 400, "y": 300, "color": "#0000FF"},
                    {"id": "c", "label": "Default", "x": 700, "y": 300},
                ],
            },
            duration_frames=60,
        )
        assert "#FF0000" in html
        assert "#0000FF" in html

    def test_diagram_recognized_kind(self):
        """Diagram is a recognized kind routed to specific handler."""
        generic = scene_to_html(
            title="Same", kind="generic",
            payload={"text": "plain"},
            duration_frames=60,
        )
        diag = scene_to_html(
            title="Same", kind="diagram",
            payload={"nodes": [{"id": "n", "label": "N", "x": 300, "y": 300}]},
            duration_frames=60,
        )
        # Diagram has positioned nodes, generic does not
        assert "position:absolute" in diag
        assert "position:absolute" not in generic


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
