"""Manim renderer — generate animated scenes via Manim or Manim MCP server.

Three modes:
1. Direct: calls manim CLI directly (fastest, most reliable)
2. MCP stdio: launches manim-mcp-server as subprocess, communicates via MCP
3. MCP connect: connects to an already-running MCP server
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import tempfile
import textwrap
from pathlib import Path
from typing import Any

from videoforge.design_tokens import manim_theme
from videoforge.engine.models import SceneDefinition, SceneType

logger = logging.getLogger("videoforge.engine.manim")
MANIM_THEME = manim_theme()

MANIM_MCP_SCRIPT = None
try:
    import importlib.util
    spec = importlib.util.find_spec("manim_server")
    if spec:
        MANIM_MCP_SCRIPT = spec.origin
except ImportError:
    pass

MANIM_OUTPUT_PATTERNS = [
    re.compile(r"File\s+(/.*?\.mp4)\s+has"),
    re.compile(r"Successfully rendered at\s+(/.*?\.mp4)"),
]


def _manim_prelude(fps: int) -> list[str]:
    return [
        "from manim import *",
        "import numpy as np",
        f"config.frame_rate = {fps}",
        "config.pixel_width = 1920",
        "config.pixel_height = 1080",
        'config.quality = "high_quality"',
        f'config.background_color = "{MANIM_THEME["backgroundColor"]}"',
        f'THEME_TEXT = "{MANIM_THEME["textColor"]}"',
        f'THEME_MUTED = "{MANIM_THEME["mutedTextColor"]}"',
        f'THEME_PRIMARY = "{MANIM_THEME["primaryColor"]}"',
        f'THEME_SECONDARY = "{MANIM_THEME["secondaryColor"]}"',
        f'THEME_SUCCESS = "{MANIM_THEME["successColor"]}"',
        f'THEME_ERROR = "{MANIM_THEME["errorColor"]}"',
        f'THEME_CODE_BG = "{MANIM_THEME["codeBackground"]}"',
        f'THEME_CODE_TEXT = "{MANIM_THEME["codeTextColor"]}"',
        f'THEME_HEADING_FONT = "{MANIM_THEME["headingFont"]}"',
        f'THEME_BODY_FONT = "{MANIM_THEME["bodyFont"]}"',
        f'THEME_MONO_FONT = "{MANIM_THEME["monoFont"]}"',
        "",
    ]


def find_manim_output(log: str, workdir: str) -> str | None:
    """Extract video path from manim CLI output."""
    for pat in MANIM_OUTPUT_PATTERNS:
        m = pat.search(log)
        if m:
            p = m.group(1)
            if os.path.isabs(p):
                return p
            return os.path.join(workdir, p)
    return None


def find_manim_output_in_dir(directory: str | Path) -> str | None:
    """Find the most recent mp4 in manim's media output structure."""
    d = Path(directory)
    media_root = d / "media"
    if media_root.exists():
        mp4s = sorted(media_root.rglob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
        if mp4s:
            return str(mp4s[0])
    mp4s = sorted(Path(d).rglob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    return str(mp4s[0]) if mp4s else None


def scene_to_manim_code(scene: SceneDefinition, fps: int = 30) -> str:
    """Generate a complete Manim Python script from a SceneDefinition."""

    duration_sec = scene.duration / fps if scene.duration > 0 else 5

    lines = _manim_prelude(fps)

    scene_class_name = re.sub(r"[^a-zA-Z0-9]", "", scene.title.replace(" ", "_")) or "ManimScene"
    lines.append(f"class {scene_class_name}(Scene):")
    lines.append("    def construct(self):")

    # Background
    lines.append("        bg = Rectangle(")
    lines.append("            width=config.frame_width, height=config.frame_height,")
    lines.append('            fill_opacity=1, color=config.background_color')
    lines.append("        )")
    lines.append("        self.add(bg)")
    lines.append("")

    if scene.type in (SceneType.TITLE, SceneType.OUTRO):
        title_esc = scene.title.replace("'", "\\'")
        subtitle_esc = scene.subtitle.replace("'", "\\'")
        text_esc = scene.text[:150].replace("'", "\\'") if scene.text else ""

        lines.append(f"        title = Text('{title_esc}', color=THEME_TEXT, font=THEME_HEADING_FONT, font_size=60)")
        lines.append(f"        subtitle = Text('{subtitle_esc}', color=THEME_MUTED, font=THEME_BODY_FONT, font_size=36)")
        lines.append("        subtitle.next_to(title, DOWN, buff=0.3)")
        lines.append("        self.play(Write(title), run_time=1.5)")
        lines.append("        self.wait(0.5)")
        if subtitle_esc and subtitle_esc != title_esc:
            lines.append("        self.play(Write(subtitle), run_time=1.0)")
        if text_esc:
            lines.append(f"        extra = Text('{text_esc}', color=THEME_PRIMARY, font=THEME_BODY_FONT, font_size=24)")
            lines.append("        extra.next_to(subtitle, DOWN, buff=0.3)")
            lines.append("        self.play(Write(extra), run_time=0.5)")
        lines.append(f"        self.wait({max(duration_sec - 3, 1):.1f})")

    elif scene.type == SceneType.BULLET:
        title_esc = scene.title.replace("'", "\\'")
        points_str = "\\n".join("• " + p[:80] for p in scene.points[:6])
        points_esc = points_str.replace("'", "\\'")
        lines.append(f"        title = Text('{title_esc}', color=THEME_TEXT, font=THEME_HEADING_FONT, font_size=48)")
        lines.append("        title.to_edge(UP)")
        lines.append("        self.play(Write(title), run_time=0.8)")
        lines.append(f"        body = Text('{points_esc}', color=THEME_TEXT, font=THEME_BODY_FONT, font_size=28, line_spacing=0.5)")
        lines.append("        body.next_to(title, DOWN, buff=0.3, aligned_edge=LEFT)")
        lines.append("        self.play(Write(body), run_time=1.5)")
        lines.append(f"        self.wait({max(duration_sec - 2.5, 1):.1f})")
        lines.append(f"        self.wait({max(duration_sec - len(scene.points) * 0.7, 1):.1f})")

    elif scene.type in (SceneType.CODE, SceneType.CODE_WALKTHROUGH):
        title_esc = scene.title.replace("'", "\\'")
        code_lines = scene.code.split("\\n")[:15]
        code_display = "\\n".join(code_lines)[:1500]
        code_esc = code_display.replace("'", "\\'")

        lines.append(f"        title = Text('{title_esc}', color=THEME_TEXT, font=THEME_HEADING_FONT, font_size=36)")
        lines.append("        title.to_edge(UP)")
        lines.append("        self.play(Write(title), run_time=0.5)")
        lines.append(f"        code_text = Text('{code_esc}', color=THEME_CODE_TEXT, font_size=14, font=THEME_MONO_FONT, line_spacing=0.5)")
        lines.append("        code_text.next_to(title, DOWN, buff=0.3, aligned_edge=LEFT)")
        lines.append("        bg = Rectangle(width=code_text.width + 1, height=code_text.height + 0.5, fill_opacity=0.3, color=THEME_CODE_BG)")
        lines.append("        bg.move_to(code_text)")
        lines.append("        self.add(bg)")
        lines.append("        self.play(Write(code_text), run_time=1.5)")
        lines.append(f"        self.wait({max(duration_sec - 2.5, 1):.1f})")

    elif scene.type == SceneType.MINDMAP:
        title_esc = scene.title.replace("'", "\\'")
        text_esc = scene.text[:300].replace("'", "\\'")

        lines.append(f"        title = Text('{title_esc}', color=THEME_TEXT, font=THEME_HEADING_FONT, font_size=42)")
        lines.append("        title.to_edge(UP)")
        lines.append("        self.play(Write(title), run_time=0.5)")
        lines.append(f"        body = Text('{text_esc}', font=THEME_BODY_FONT, font_size=22, color=THEME_MUTED, line_spacing=0.5)")
        lines.append("        body.next_to(title, DOWN, buff=0.3)")
        lines.append("        self.play(Write(body), run_time=1.5)")
        lines.append(f"        self.wait({max(duration_sec - 2.5, 1):.1f})")

    else:
        title_esc = scene.title.replace("'", "\\'")
        text_esc = scene.text[:200].replace("'", "\\'")

        lines.append(f"        text = Text('{title_esc or 'Manim Scene'}', color=THEME_TEXT, font=THEME_HEADING_FONT, font_size=48)")
        lines.append("        self.play(Write(text), run_time=1.0)")
        if text_esc:
            lines.append(f"        body = Text('{text_esc}', color=THEME_MUTED, font=THEME_BODY_FONT, font_size=28)")
            lines.append("        body.next_to(text, DOWN)")
            lines.append("        self.play(Write(body), run_time=0.5)")
        lines.append(f"        self.wait({max(duration_sec - 2, 1):.1f})")

    return "\n".join(lines)


def render_direct(code: str, output_dir: str | Path, quality: str = "high_quality") -> dict[str, Any]:
    """Render Manim code directly via manim CLI. Returns {success, video_path, log}."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    script_path = output_dir / "scene.py"
    script_path.write_text(code)

    qflag = "-qh" if quality == "high_quality" else "-ql"
    cmd = ["manim", qflag, str(script_path)]

    logger.info("Running manim: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=str(output_dir))
    log = (result.stdout or "") + (result.stderr or "")

    video_path = find_manim_output(log, str(output_dir))
    if not video_path or not Path(video_path).exists():
        video_path = find_manim_output_in_dir(output_dir)

    if video_path and Path(video_path).exists():
        p = Path(video_path)
        dest = output_dir / p.name
        if p != dest:
            import shutil
            shutil.copy2(str(p), str(dest))
            video_path = str(dest)
        return {"success": True, "video_path": video_path, "log": log[:500]}

    return {"success": False, "video_path": None, "log": log[-1000:]}


async def render_via_mcp(code: str, mcp_server_cmd: list[str] | None = None) -> dict[str, Any]:
    """Render Manim code via the manim-mcp-server using stdio transport.

    Args:
        code: Complete Manim Python script
        mcp_server_cmd: Command to launch the MCP server.
                         Default: ['python3', '-m', 'manim_server']
    """
    if mcp_server_cmd is None:
        mcp_server_cmd = ["python3", "-m", "manim_server"]

    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    server_params = StdioServerParameters(command=mcp_server_cmd[0], args=mcp_server_cmd[1:])

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            tool_names = [t.name for t in tools.tools]
            logger.info("MCP server tools: %s", tool_names)

            result = await session.call_tool("execute_manim_code", arguments={"manim_code": code})
            content = result.content[0].text if result.content else ""
            logger.info("MCP response: %s", content[:200])

            media_dir = Path(os.path.dirname(os.path.abspath(__file__))) / ".." / ".." / ".." / "media"
            video_path = find_manim_output_in_dir(str(media_dir))

            return {
                "success": "successful" in content.lower(),
                "video_path": video_path,
                "log": content[:500],
            }


def render_scene(scene: SceneDefinition, output_dir: str | Path, fps: int = 30, mode: str = "direct") -> dict[str, Any]:
    """Render a single scene using Manim.

    Args:
        scene: Scene definition with type=MANIM or any type
        output_dir: Where to write output files
        fps: Frames per second
        mode: 'direct' (manim CLI), 'mcp' (MCP server)
    """
    code = scene_to_manim_code(scene, fps)

    import asyncio
    if mode == "mcp":
        return asyncio.run(render_via_mcp(code))

    return render_direct(code, output_dir)


def _escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace("'", "\\'")


def generate_graph_scene(
    nodes: list[dict[str, Any]],
    edges: list[tuple[str, str]] | list[list[str]],
    layout: str = "dot",
    fps: int = 30,
    duration_sec: float = 8.0,
) -> str:
    """Generate Manim code for a graph/diagram scene using manim.Graph.

    Args:
        nodes: [{"id": "a", "label": "Node A"}, ...]
        edges: [["a", "b"], ...] or list of tuples
        layout: "dot" | "spring" | "circular" | "random" | "partite"
        fps: frame rate pin
        duration_sec: total scene duration in seconds
    """
    node_ids = [str(n["id"]) for n in nodes]
    labels = {str(n["id"]): _escape(str(n.get("label", n["id"]))) for n in nodes}
    edge_pairs = [(str(a), str(b)) for a, b in edges]

    lines = _manim_prelude(fps) + [
        "class GraphScene(Scene):",
        "    def construct(self):",
        "        bg = Rectangle(width=config.frame_width, height=config.frame_height,",
        "                       fill_opacity=1, color=config.background_color)",
        "        self.add(bg)",
        f"        vertices = {node_ids!r}",
        f"        edges = {edge_pairs!r}",
        '        g = Graph(vertices, edges, layout="' + layout + '", labels=False,',
        "                  vertex_config={'radius': 0.35, 'color': THEME_PRIMARY, 'fill_opacity': 0.9},",
        "                  edge_config={'color': THEME_SECONDARY, 'stroke_width': 3})",
        "        self.play(Create(g), run_time=2.0)",
    ]
    for vid in node_ids:
        lines.append(f"        g.add_labels({{{vid!r}: Text({labels[vid]!r}, font=THEME_BODY_FONT, color=THEME_TEXT, font_size=24)}})")
    lines.append("        self.play(g.animate.scale(0.9).move_to(ORIGIN), run_time=0.5)")
    lines.append(f"        self.wait({max(duration_sec - 3.0, 1.0):.1f})")
    return "\n".join(lines) + "\n"


def generate_chart_scene(
    data: list[dict[str, Any]],
    chart_type: str = "bar",
    fps: int = 30,
    duration_sec: float = 8.0,
    title: str = "",
) -> str:
    """Generate Manim code for bar/line charts using BarChart / NumberLine.

    Args:
        data: [{"label": "A", "value": 10}, ...]
        chart_type: "bar" | "line"
        fps: frame rate pin
        duration_sec: total scene duration
        title: optional chart title
    """
    labels = [_escape(str(d.get("label", ""))) for d in data]
    values = [float(d.get("value", 0)) for d in data]
    title_esc = _escape(title)

    if chart_type == "line":
        return "\n".join(_manim_prelude(fps)) + textwrap.dedent(f"""\
        class LineChartScene(Scene):
            def construct(self):
                bg = Rectangle(width=config.frame_width, height=config.frame_height,
                               fill_opacity=1, color=config.background_color)
                self.add(bg)
                values = {values!r}
                max_val = max(values) if values else 1
                axis = NumberLine(x_range=[0, len(values) + 1, 1], length=10,
                                  color=THEME_TEXT, include_numbers=True).shift(DOWN * 0.5)
                y_axis = NumberLine(x_range=[0, max_val * 1.1, max_val / 5], length=5,
                                    rotation=PI / 2, color=THEME_TEXT).shift(LEFT * 5)
                self.play(Create(axis), Create(y_axis), run_time=1.0)
                dots = VGroup()
                for i, v in enumerate(values):
                    p = Dot(color=THEME_SECONDARY).move_to(axis.n2p(i + 1) + UP * (v / max_val) * 4)
                    dots.add(p)
                self.play(Create(dots), run_time=1.5)
                if len(dots) > 1:
                    lines = VGroup(*[
                        Line(dots[i].get_center(), dots[i + 1].get_center(), color=THEME_PRIMARY)
                        for i in range(len(dots) - 1)
                    ])
                    self.play(Create(lines), run_time=1.0)
                self.wait({max(duration_sec - 3.5, 1.0):.1f})
        """)

    return "\n".join(_manim_prelude(fps)) + textwrap.dedent(f"""\
    class BarChartScene(Scene):
        def construct(self):
            bg = Rectangle(width=config.frame_width, height=config.frame_height,
                           fill_opacity=1, color=config.background_color)
            self.add(bg)
            values = {values!r}
            labels = {labels!r}
            max_val = max(values) if values else 1
            chart = BarChart(values=values, y_range=[0, max_val * 1.1, max_val / 5],
                             bar_colors=[THEME_PRIMARY, THEME_SECONDARY, THEME_SUCCESS, '#EAB308', THEME_ERROR],
                             x_labels=[Text(l, font=THEME_BODY_FONT, color=THEME_TEXT, font_size=24) for l in labels],
                             bar_width=0.6).scale(0.8)
            self.play(Create(chart), run_time=2.0)
            {f"title = Text('{title_esc}', color=THEME_TEXT, font=THEME_HEADING_FONT, font_size=36).to_edge(UP); self.play(Write(title), run_time=0.5)" if title_esc else "pass"}
            self.wait({max(duration_sec - 3.0, 1.0):.1f})
    """)


def generate_timeline_scene(
    events: list[dict[str, Any]],
    fps: int = 30,
    duration_sec: float = 8.0,
    title: str = "",
) -> str:
    """Generate Manim code for a timeline using NumberLine + MoveAlongPath.

    Args:
        events: [{"label": "Start", "date": "2020"}, ...]
        fps: frame rate pin
        duration_sec: total scene duration
        title: optional title
    """
    labels = [_escape(str(e.get("label", ""))) for e in events]
    dates = [_escape(str(e.get("date", ""))) for e in events]
    title_esc = _escape(title)
    n = len(events)

    return "\n".join(_manim_prelude(fps)) + textwrap.dedent(f"""\
    class TimelineScene(Scene):
        def construct(self):
            bg = Rectangle(width=config.frame_width, height=config.frame_height,
                           fill_opacity=1, color=config.background_color)
            self.add(bg)
            labels = {labels!r}
            dates = {dates!r}
            n = {n}
            axis = NumberLine(x_range=[0, max(n, 1), 1], length=12, color=THEME_TEXT,
                              include_numbers=False).shift(DOWN * 0.3)
            self.play(Create(axis), run_time=1.0)
            {f"title_t = Text('{title_esc}', color=THEME_TEXT, font=THEME_HEADING_FONT, font_size=36).to_edge(UP); self.play(Write(title_t), run_time=0.5)" if title_esc else "pass"}
            for i in range(n):
                pos = axis.n2p(i + 1)
                dot = Dot(point=pos, radius=0.12, color=THEME_SECONDARY)
                lbl = Text(labels[i], color=THEME_TEXT, font=THEME_BODY_FONT, font_size=24).next_to(dot, UP if i % 2 == 0 else DOWN, buff=0.4)
                self.play(FadeIn(dot), Write(lbl), run_time=0.6)
                if dates[i]:
                    d = Text(dates[i], font=THEME_BODY_FONT, font_size=18, color=THEME_MUTED).next_to(lbl, UP if i % 2 == 0 else DOWN, buff=0.2)
                    self.play(Write(d), run_time=0.3)
            marker = Dot(radius=0.18, color=THEME_PRIMARY)
            marker.move_to(axis.n2p(0))
            self.add(marker)
            self.play(MoveAlongPath(marker, axis), run_time={max(duration_sec - 2.0, 1.0):.1f})
    """)
