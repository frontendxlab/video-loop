"""Tests for Remotion render executor."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from videoforge.exceptions import RenderError


@pytest.fixture
def executor():
    from videoforge.render.executor import RenderExecutor
    return RenderExecutor()


class TestRenderExecution:
    def test_render_produces_output_path(self, executor, temp_dir):
        output = temp_dir / "output.mp4"
        with patch("subprocess.run") as mock:
            mock.return_value = MagicMock(returncode=0, stdout="", stderr="")
            Path(output).write_text("mock video")
            result = executor.render("TestComp", {}, str(output))
        assert result["output_path"].endswith(".mp4")

    def test_raises_on_render_failure(self, executor):
        with patch("subprocess.run") as mock:
            mock.side_effect = FileNotFoundError("npx not found")
            with pytest.raises(RenderError):
                executor.render("TestComp", {}, "/tmp/out.mp4")

    def test_render_timeout_kills_process(self, executor):
        import subprocess
        with patch("subprocess.run") as mock:
            mock.side_effect = subprocess.TimeoutExpired("remotion", 600)
            with pytest.raises(RenderError):
                executor.render("TestComp", {}, "/tmp/out.mp4")

    def test_progress_reported_during_render(self, executor, temp_dir):
        output = temp_dir / "output.mp4"
        progress_log = []

        def capture_progress(line):
            progress_log.append(line)

        with patch("subprocess.Popen") as mock_popen:
            process = MagicMock()
            process.returncode = 0
            process.stdout = iter(["Frame: 10/100", "Frame: 50/100", "Frame: 100/100\n"])
            process.stderr = ""
            mock_popen.return_value = process
            Path(output).write_text("mock")
            executor.render("TestComp", {}, str(output), progress_callback=capture_progress)

        assert len(progress_log) > 0
