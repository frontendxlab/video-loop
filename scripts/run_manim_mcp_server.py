#!/usr/bin/env python3
"""Start the Manim MCP server for animation generation.

Usage:
    python3 scripts/run_manim_mcp_server.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from videoforge.engine.manim_renderer import MANIM_MCP_SCRIPT

if MANIM_MCP_SCRIPT:
    print(f"Starting Manim MCP server from: {MANIM_MCP_SCRIPT}")
    import subprocess
    subprocess.run([sys.executable, MANIM_MCP_SCRIPT])
else:
    # Fallback: start direct manim server from cloned repo
    mcp_path = Path(__file__).resolve().parent.parent / "manim-mcp-server" / "src" / "manim_server.py"
    if mcp_path.exists():
        print(f"Starting Manim MCP server from: {mcp_path}")
        import subprocess
        subprocess.run([sys.executable, str(mcp_path)])
    else:
        print("Manim MCP server not found. Install with:")
        print("  git clone https://github.com/abhiemj/manim-mcp-server.git")
        sys.exit(1)
