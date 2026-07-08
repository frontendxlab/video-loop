"""Tests for 5-Level Frame Reviewer — L1 Frame Integrity."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


@pytest.fixture
def reviewer():
    from videoforge.review.frame_reviewer import FrameReviewer
    return FrameReviewer()


class TestL1FrameIntegrity:
    def test_detects_black_frames(self, reviewer, temp_dir):
        video = temp_dir / "test.mp4"
        video.write_text("mock")
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = '{"black_frames": [{"start": 0, "end": 30}]}'
            mock_run.return_value = mock_result
            result = reviewer.check_integrity(str(video))
        assert "issues" in result

    def test_detects_frozen_frames(self, reviewer, temp_dir):
        video = temp_dir / "test.mp4"
        video.write_text("mock")
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = '{"frozen_frames": [{"start": 60, "end": 90}]}'
            mock_run.return_value = mock_result
            result = reviewer.check_integrity(str(video))
        assert "issues" in result

    def test_passes_clean_video(self, reviewer, temp_dir):
        video = temp_dir / "test.mp4"
        video.write_text("mock")
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = '{"black_frames": [], "frozen_frames": []}'
            mock_run.return_value = mock_result
            result = reviewer.check_integrity(str(video))
        assert len(result.get("issues", [])) == 0

    def test_reports_frame_count(self, reviewer, temp_dir):
        video = temp_dir / "test.mp4"
        video.write_text("mock")
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = '{"streams": [{"nb_frames": "300"}]}'
            mock_run.return_value = mock_result
            result = reviewer.check_integrity(str(video))
        assert "total_frames" in result
