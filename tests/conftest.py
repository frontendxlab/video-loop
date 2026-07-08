"""Shared fixtures for all test modules."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Generator
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    with tempfile.TemporaryDirectory() as tmp:
        old = os.getcwd()
        os.chdir(tmp)
        yield Path(tmp)
        os.chdir(old)


@pytest.fixture
def sample_script() -> str:
    return (
        "Hello world. This is a test script for video generation. "
        "It has multiple sentences of varying lengths. "
        "Each chunk must be under fifty tokens."
    )


@pytest.fixture
def sample_wav_bytes() -> bytes:
    import struct, wave, io
    buf = io.BytesIO()
    sr = 24000
    n = sr // 2
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(struct.pack(f"<{n}h", *([0] * n)))
    return buf.getvalue()


@pytest.fixture
def sample_pr_diff() -> str:
    return (
        "diff --git a/src/auth.py b/src/auth.py\n"
        "new file mode 100644\n"
        "--- /dev/null\n"
        "+++ b/src/auth.py\n"
        "@@ -0,0 +1,12 @@\n"
        "+def authenticate(token: str) -> bool:\n"
        "+    return len(token) > 0\n"
        "+\n"
        "+def validate_session(session_id: str) -> dict | None:\n"
        "+    return {'user': 'test'} if session_id else None\n"
    )


@pytest.fixture
def sample_scene_plan() -> dict[str, Any]:
    return {
        "version": 1,
        "video_type": "PR_WALKTHROUGH",
        "fps": 30,
        "resolution": [1920, 1080],
        "scenes": [
            {"id": 1, "type": "title", "duration_seconds": 4, "title": "Test Video", "transition_in": "fade", "transition_out": "slide-left"},
            {"id": 2, "type": "code", "duration_seconds": 6, "code": "def hello():\n  return 'world'", "lang": "python", "transition_in": "slide-right", "transition_out": "fade"},
            {"id": 3, "type": "outro", "duration_seconds": 5, "title": "The End", "transition_in": "fade", "transition_out": "none"},
        ],
    }


@pytest.fixture
def mock_subprocess_run() -> Generator[MagicMock, None, None]:
    with patch("subprocess.run") as mock:
        result = MagicMock()
        result.returncode = 0
        result.stdout = json.dumps({"title": "Mock PR", "number": 1})
        result.stderr = ""
        mock.return_value = result
        yield mock
