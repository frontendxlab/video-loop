"""Remotion render executor."""

from __future__ import annotations

import json
import subprocess
import time
from typing import Callable, Optional

from videoforge.exceptions import RenderError
from videoforge.render.progress import ProgressParser


class RenderExecutor:
    """Orchestrates a Remotion render subprocess."""

    def __init__(
        self,
        remotion_entry: str = "remotion-project",
        composition_id: str = "TestComp",
    ) -> None:
        self.remotion_entry = remotion_entry
        self.composition_id = composition_id

    def render(
        self,
        composition_id: str,
        input_props: dict,
        output_path: str,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> dict:
        cmd = self._build_command(composition_id, input_props, output_path)
        start = time.monotonic()

        try:
            if progress_callback is not None:
                self._run_with_progress(cmd, progress_callback)
            else:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=600,
                )
                if result.returncode != 0:
                    raise RenderError(f"Render failed: {result.stderr}")
        except FileNotFoundError:
            raise RenderError("npx not found")
        except subprocess.TimeoutExpired as exc:
            raise RenderError(f"Render timed out: {exc}")

        duration_ms = int((time.monotonic() - start) * 1000)

        return {
            "output_path": output_path,
            "frames_rendered": 0,
            "duration_ms": duration_ms,
        }

    def _build_command(
        self, composition_id: str, input_props: dict, output_path: str
    ) -> list[str]:
        props_json = json.dumps(input_props)
        return [
            "npx",
            "remotion",
            "render",
            self.remotion_entry,
            composition_id,
            output_path,
            "--props",
            props_json,
        ]

    def _run_with_progress(
        self,
        cmd: list[str],
        progress_callback: Callable[[str], None],
    ) -> None:
        parser = ProgressParser()
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        for line in proc.stdout:
            line = line.rstrip("\n")
            parsed = parser.parse_line(line)
            if parsed is not None:
                progress_callback(line)

        proc.wait()

        if proc.returncode != 0:
            stderr = proc.stderr.read() if proc.stderr else ""
            raise RenderError(f"Render failed: {stderr}")
