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

from videoforge.engine.models import SceneDefinition, SceneType

logger = logging.getLogger("videoforge.engine.manim")

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

    lines = []
    lines.append("from manim import *")
    lines.append("import numpy as np")
    lines.append(f"config.frame_rate = {fps}")
    lines.append("config.pixel_width = 1920")
    lines.append("config.pixel_height = 1080")
    lines.append('config.quality = "high_quality"')
    lines.append('config.background_color = "#1a1a2e"')
    lines.append("")

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

        lines.append(f"        title = Text('{title_esc}', color=WHITE, font_size=60)")
        lines.append(f"        subtitle = Text('{subtitle_esc}', color=GRAY, font_size=36)")
        lines.append("        subtitle.next_to(title, DOWN, buff=0.3)")
        lines.append("        self.play(Write(title), run_time=1.5)")
        lines.append("        self.wait(0.5)")
        if subtitle_esc and subtitle_esc != title_esc:
            lines.append("        self.play(Write(subtitle), run_time=1.0)")
        if text_esc:
            lines.append(f"        extra = Text('{text_esc}', color=BLUE, font_size=24)")
            lines.append("        extra.next_to(subtitle, DOWN, buff=0.3)")
            lines.append("        self.play(Write(extra), run_time=0.5)")
        lines.append(f"        self.wait({max(duration_sec - 3, 1):.1f})")

    elif scene.type == SceneType.BULLET:
        title_esc = scene.title.replace("'", "\\'")
        points_str = "\\n".join("• " + p[:80] for p in scene.points[:6])
        points_esc = points_str.replace("'", "\\'")
        lines.append(f"        title = Text('{title_esc}', color=WHITE, font_size=48)")
        lines.append("        title.to_edge(UP)")
        lines.append("        self.play(Write(title), run_time=0.8)")
        lines.append(f"        body = Text('{points_esc}', color=WHITE, font_size=28, line_spacing=0.5)")
        lines.append("        body.next_to(title, DOWN, buff=0.3, aligned_edge=LEFT)")
        lines.append("        self.play(Write(body), run_time=1.5)")
        lines.append(f"        self.wait({max(duration_sec - 2.5, 1):.1f})")
        lines.append(f"        self.wait({max(duration_sec - len(scene.points) * 0.7, 1):.1f})")

    elif scene.type in (SceneType.CODE, SceneType.CODE_WALKTHROUGH):
        title_esc = scene.title.replace("'", "\\'")
        code_lines = scene.code.split("\\n")[:15]
        code_display = "\\n".join(code_lines)[:1500]
        code_esc = code_display.replace("'", "\\'")

        lines.append(f"        title = Text('{title_esc}', color=WHITE, font_size=36)")
        lines.append("        title.to_edge(UP)")
        lines.append("        self.play(Write(title), run_time=0.5)")
        lines.append(f"        code_text = Text('{code_esc}', color=GREEN, font_size=14, font='Courier', line_spacing=0.5)")
        lines.append("        code_text.next_to(title, DOWN, buff=0.3, aligned_edge=LEFT)")
        lines.append("        bg = Rectangle(width=code_text.width + 1, height=code_text.height + 0.5, fill_opacity=0.3, color=DARK_GRAY)")
        lines.append("        bg.move_to(code_text)")
        lines.append("        self.add(bg)")
        lines.append("        self.play(Write(code_text), run_time=1.5)")
        lines.append(f"        self.wait({max(duration_sec - 2.5, 1):.1f})")

    elif scene.type == SceneType.MINDMAP:
        title_esc = scene.title.replace("'", "\\'")
        text_esc = scene.text[:300].replace("'", "\\'")

        lines.append(f"        title = Text('{title_esc}', color=WHITE, font_size=42)")
        lines.append("        title.to_edge(UP)")
        lines.append("        self.play(Write(title), run_time=0.5)")
        lines.append(f"        body = Text('{text_esc}', font_size=22, color=LIGHT_GRAY, line_spacing=0.5)")
        lines.append("        body.next_to(title, DOWN, buff=0.3)")
        lines.append("        self.play(Write(body), run_time=1.5)")
        lines.append(f"        self.wait({max(duration_sec - 2.5, 1):.1f})")

    else:
        title_esc = scene.title.replace("'", "\\'")
        text_esc = scene.text[:200].replace("'", "\\'")

        lines.append(f"        text = Text('{title_esc or 'Manim Scene'}', color=WHITE, font_size=48)")
        lines.append("        self.play(Write(text), run_time=1.0)")
        if text_esc:
            lines.append(f"        body = Text('{text_esc}', color=GRAY, font_size=28)")
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
