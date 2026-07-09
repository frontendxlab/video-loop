"""Tests for L0MixedEngineReview — deterministic frame-sampled visual gate."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from videoforge.review.l0_mixed_engine import (
    L0MixedEngineReview,
    _brightness,
    _color_distance,
    _mean_rgb,
    _mse,
)


# ── Unit tests for helper functions ────────────────────────────────────────


class TestHelpers:
    def test_mean_rgb_empty(self) -> None:
        assert _mean_rgb([]) == (0.0, 0.0, 0.0)

    def test_mean_rgb_single(self) -> None:
        assert _mean_rgb([(10, 20, 30)]) == (10.0, 20.0, 30.0)

    def test_mean_rgb_multiple(self) -> None:
        pixels = [(0, 0, 0), (10, 20, 30)]
        m = _mean_rgb(pixels)
        assert m == (5.0, 10.0, 15.0)

    def test_brightness(self) -> None:
        assert _brightness((0.0, 0.0, 0.0)) == 0.0
        assert _brightness((255.0, 255.0, 255.0)) == 255.0
        assert _brightness((10.0, 20.0, 30.0)) == 20.0

    def test_color_distance_identical(self) -> None:
        assert _color_distance((100.0, 100.0, 100.0), (100, 100, 100)) == 0.0

    def test_color_distance_different(self) -> None:
        assert _color_distance((0.0, 0.0, 0.0), (255, 255, 255)) == pytest.approx(441.67, rel=0.01)

    def test_mse_identical(self) -> None:
        a = [(10, 20, 30), (40, 50, 60)]
        assert _mse(a, a) == 0.0

    def test_mse_different(self) -> None:
        a = [(0, 0, 0)]
        b = [(10, 20, 30)]
        # sum((diff^2) per pixel) / n_pixels = (100 + 400 + 900) / 1 = 1400
        assert _mse(a, b) == 1400.0

    def test_mse_mismatched_length(self) -> None:
        assert _mse([(1, 2, 3)], [(1, 2, 3), (4, 5, 6)]) == float("inf")

    def test_mse_empty(self) -> None:
        assert _mse([], []) == float("inf")

    def test_parse_rgb_line_valid(self) -> None:
        from videoforge.review.l0_mixed_engine import _parse_rgb_line
        assert _parse_rgb_line("10 20 30") == (10, 20, 30)

    def test_parse_rgb_line_invalid(self) -> None:
        from videoforge.review.l0_mixed_engine import _parse_rgb_line
        assert _parse_rgb_line("not numbers") is None

    def test_parse_rgb_line_short(self) -> None:
        from videoforge.review.l0_mixed_engine import _parse_rgb_line
        assert _parse_rgb_line("10 20") is None


# ── L0MixedEngineReview unit tests ─────────────────────────────────────────


@pytest.fixture
def reviewer() -> L0MixedEngineReview:
    return L0MixedEngineReview(sample_count=6)


class TestStreamProbing:
    def test_extract_total_frames_from_nb(self) -> None:
        streams = [{"codec_type": "video", "nb_frames": "300"}]
        assert L0MixedEngineReview._extract_total_frames(streams) == 300

    def test_extract_total_frames_fallback(self) -> None:
        streams = [{"codec_type": "video", "duration": "10.0", "avg_frame_rate": "30/1"}]
        assert L0MixedEngineReview._extract_total_frames(streams) == 300

    def test_extract_total_frames_no_video(self) -> None:
        assert L0MixedEngineReview._extract_total_frames([]) == 0

    def test_extract_total_frames_malformed_rate(self) -> None:
        streams = [{"codec_type": "video", "duration": "10.0", "avg_frame_rate": "bogus"}]
        assert L0MixedEngineReview._extract_total_frames(streams) == 0

    def test_extract_duration(self) -> None:
        streams = [{"codec_type": "video", "duration": "15.5"}]
        assert L0MixedEngineReview._extract_duration(streams) == 15.5

    def test_extract_duration_no_video(self) -> None:
        assert L0MixedEngineReview._extract_duration([]) == 0.0


class TestFrameSampling:
    def test_sample_frames_count(self, reviewer: L0MixedEngineReview) -> None:
        frames = reviewer._sample_frames("dummy.mp4", 300, 10.0)
        assert len(frames) == 6  # sample_count
        assert frames[0]["index"] == 0
        # step = (300-1) // (6-1) = 299//5 = 59 → indices: 0,59,118,177,236,295
        assert frames[-1]["index"] == 295

    def test_sample_frames_single_frame(self, reviewer: L0MixedEngineReview) -> None:
        frames = reviewer._sample_frames("dummy.mp4", 1, 0.033)
        assert len(frames) == 1
        assert frames[0]["index"] == 0

    def test_sample_frames_no_frames(self, reviewer: L0MixedEngineReview) -> None:
        frames = reviewer._sample_frames("dummy.mp4", 0, 0.0)
        assert frames == []

    def test_sample_frames_timestamps(self, reviewer: L0MixedEngineReview) -> None:
        frames = reviewer._sample_frames("dummy.mp4", 300, 10.0)
        assert frames[0]["pts"] == 0.0
        # last frame index 295 → pts = 295 / (300/10) = 9.833
        assert frames[-1]["pts"] == pytest.approx(9.833, rel=0.01)


class TestResolutionChecks:
    def test_single_stream_no_issues(self) -> None:
        streams = [
            {"index": 0, "codec_type": "video", "width": 1920, "height": 1080, "codec_name": "h264"},
        ]
        reviewer = L0MixedEngineReview()
        issues = reviewer._check_resolution_consistency(streams)
        assert issues == []

    def test_mismatched_resolution(self) -> None:
        streams = [
            {"index": 0, "codec_type": "video", "width": 1920, "height": 1080, "codec_name": "h264"},
            {"index": 1, "codec_type": "video", "width": 1280, "height": 720, "codec_name": "h264"},
        ]
        reviewer = L0MixedEngineReview()
        issues = reviewer._check_resolution_consistency(streams)
        assert len(issues) == 1
        assert issues[0]["type"] == "resolution_mismatch"
        assert issues[0]["expected"] == "1920x1080"
        assert issues[0]["actual"] == "1280x720"

    def test_codec_mismatch(self) -> None:
        streams = [
            {"index": 0, "codec_type": "video", "width": 1920, "height": 1080, "codec_name": "h264"},
            {"index": 1, "codec_type": "video", "width": 1920, "height": 1080, "codec_name": "vp9"},
        ]
        reviewer = L0MixedEngineReview()
        issues = reviewer._check_resolution_consistency(streams)
        assert len(issues) == 1
        assert issues[0]["type"] == "codec_mismatch"


class TestBlankFrameDetection:
    def test_blank_frame_detected(self, reviewer: L0MixedEngineReview) -> None:
        all_black = [(0, 0, 0)] * 100
        frame = {"index": 0, "pts": 0.0, "pixels": {"data": all_black, "width": 10, "height": 10}}
        issues = reviewer._check_blank_frames([frame], 300, 10.0)
        assert len(issues) == 1
        assert issues[0]["type"] == "blank_frame"
        assert issues[0]["frame_index"] == 0

    def test_clean_frame_passes(self, reviewer: L0MixedEngineReview) -> None:
        bright_pixels = [(100, 150, 200)] * 100
        frame = {"index": 0, "pts": 0.0, "pixels": {"data": bright_pixels, "width": 10, "height": 10}}
        issues = reviewer._check_blank_frames([frame], 300, 10.0)
        assert issues == []

    def test_no_pixels_skips(self, reviewer: L0MixedEngineReview) -> None:
        frame = {"index": 0, "pts": 0.0}
        issues = reviewer._check_blank_frames([frame], 300, 10.0)
        assert issues == []


class TestPaletteCoherence:
    def test_palette_ok(self, reviewer: L0MixedEngineReview) -> None:
        # Pixels close to default bg (#0F172A ~= (15, 23, 42))
        close_to_bg = [(20, 30, 50)] * 100
        frame = {"index": 0, "pts": 0.0, "pixels": {"data": close_to_bg, "width": 10, "height": 10}}
        issues = reviewer._check_palette_coherence([frame], 300, 10.0)
        assert issues == []

    def test_palette_drift(self, reviewer: L0MixedEngineReview) -> None:
        # White — far from dark bg
        white = [(255, 255, 255)] * 100
        frame = {"index": 0, "pts": 0.0, "pixels": {"data": white, "width": 10, "height": 10}}
        issues = reviewer._check_palette_coherence([frame], 300, 10.0)
        assert len(issues) == 1
        assert issues[0]["type"] == "palette_drift"

    def test_no_pixels_skips(self, reviewer: L0MixedEngineReview) -> None:
        frame = {"index": 0, "pts": 0.0}
        issues = reviewer._check_palette_coherence([frame], 300, 10.0)
        assert issues == []


class TestFreezeDetection:
    def test_freeze_detected(self, reviewer: L0MixedEngineReview) -> None:
        pixels = [(10, 20, 30)] * 100
        frames = [
            {"index": 0, "pts": 0.0, "pixels": {"data": pixels, "width": 10, "height": 10}},
            {"index": 10, "pts": 0.5, "pixels": {"data": pixels, "width": 10, "height": 10}},  # same pixels
        ]
        issues = reviewer._check_freeze(frames, 300, 10.0)
        assert len(issues) == 1
        assert issues[0]["type"] == "suspected_freeze"
        assert issues[0]["frame_a"] == 0
        assert issues[0]["frame_b"] == 10
        assert issues[0]["mse"] == 0.0

    def test_no_freeze_when_different(self, reviewer: L0MixedEngineReview) -> None:
        frames = [
            {"index": 0, "pts": 0.0, "pixels": {"data": [(10, 20, 30)] * 100, "width": 10, "height": 10}},
            {"index": 10, "pts": 0.5, "pixels": {"data": [(200, 100, 50)] * 100, "width": 10, "height": 10}},
        ]
        issues = reviewer._check_freeze(frames, 300, 10.0)
        assert issues == []

    def test_no_pixels_skips(self, reviewer: L0MixedEngineReview) -> None:
        frames = [
            {"index": 0, "pts": 0.0},
            {"index": 10, "pts": 0.5},
        ]
        issues = reviewer._check_freeze(frames, 300, 10.0)
        assert issues == []

    def test_different_resolution_skips(self, reviewer: L0MixedEngineReview) -> None:
        frames = [
            {"index": 0, "pts": 0.0, "pixels": {"data": [(10, 20, 30)] * 100, "width": 10, "height": 10}},
            {"index": 10, "pts": 0.5, "pixels": {"data": [(10, 20, 30)] * 200, "width": 20, "height": 10}},
        ]
        issues = reviewer._check_freeze(frames, 300, 10.0)
        assert issues == []


class TestAllBlankSummary:
    def test_all_blank_reported(self, reviewer: L0MixedEngineReview) -> None:
        """When all sampled frames are blank, summary issue added."""
        black_pixels = [(0, 0, 0)] * 100
        frames = [
            {"index": 0, "pts": 0.0, "pixels": {"data": black_pixels, "width": 10, "height": 10}},
            {"index": 15, "pts": 1.0, "pixels": {"data": black_pixels, "width": 10, "height": 10}},
        ]
        blank_issues = reviewer._check_blank_frames(frames, 300, 10.0)
        # Verify 2 blank issues found
        assert len(blank_issues) == 2


class TestRunMethod:
    def test_run_no_video_stream(self, reviewer: L0MixedEngineReview) -> None:
        result = reviewer.run("dummy.mp4", streams_info=[])
        assert result["passed"] is False
        assert any(i["type"] == "no_video_stream" for i in result["issues"])

    def test_run_clean_video(self, reviewer: L0MixedEngineReview) -> None:
        """Mock probe returns a clean single-stream video. No pixels = no pixel-based issues."""
        streams = [
            {"codec_type": "video", "width": 1920, "height": 1080, "codec_name": "h264", "nb_frames": "300", "duration": "10.0", "index": 0},
        ]
        result = reviewer.run("dummy.mp4", streams_info=streams)
        # No pixel data available (mock not extracting) so only stream-level checks pass
        assert result["passed"] is True
        assert result["sampled_frames"] == 6
        assert result["total_frames"] == 300
        assert result["duration_seconds"] == 10.0

    def test_run_resolution_mismatch(self, reviewer: L0MixedEngineReview) -> None:
        streams = [
            {"codec_type": "video", "width": 1920, "height": 1080, "codec_name": "h264", "nb_frames": "300", "index": 0},
            {"codec_type": "video", "width": 1280, "height": 720, "codec_name": "h264", "nb_frames": "150", "index": 1},
        ]
        result = reviewer.run("dummy.mp4", streams_info=streams)
        assert result["passed"] is False
        assert any(i["type"] == "resolution_mismatch" for i in result["issues"])


# ── Integration: L0 called via FrameReviewer.check_mixed_engine ─────────────


class TestFrameReviewerIntegration:
    def test_check_mixed_engine_delegates(self) -> None:
        from videoforge.review.frame_reviewer import FrameReviewer
        fr = FrameReviewer()
        with patch.object(fr._l0, "run") as mock_run:
            mock_run.return_value = {"passed": True, "issues": [], "sampled_frames": 6}
            result = fr.check_mixed_engine("test.mp4")
            assert result["passed"] is True
            mock_run.assert_called_once_with("test.mp4")

    def test_aggregate_review_includes_l0(self) -> None:
        from videoforge.review.frame_reviewer import FrameReviewer
        fr = FrameReviewer()
        with patch.object(fr._l0, "run") as mock_l0, \
             patch.object(fr, "check_integrity") as mock_l1:

            mock_l0.return_value = {"passed": True, "issues": [], "sampled_frames": 6}
            mock_l1.return_value = {"passed": True, "issues": [], "total_frames": 300}

            result = fr.aggregate_review("test.mp4")
            assert "l0_mixed_engine" in result["levels"]
            assert result["levels"]["l0_mixed_engine"]["passed"] is True

    def test_retry_on_exception_then_succeed(self) -> None:
        """Retry on exception, second attempt succeeds."""
        from videoforge.review.frame_reviewer import FrameReviewer
        fr = FrameReviewer(max_retries=2)
        with patch.object(fr._l0, "run") as mock_run:
            mock_run.side_effect = [
                RuntimeError("transient failure"),
                {"passed": True, "issues": [], "sampled_frames": 6, "total_frames": 300},
            ]
            result = fr.check_mixed_engine("test.mp4")
            assert result["passed"] is True
            assert result["retry_attempts"] == 1
            assert result["retry_limit"] == 2
            assert mock_run.call_count == 2

    def test_retry_on_infrastructure_failure(self) -> None:
        """Retry on infrastructure failure (sampled_frames=0, total_frames>0)."""
        from videoforge.review.frame_reviewer import FrameReviewer
        fr = FrameReviewer(max_retries=2)
        with patch.object(fr._l0, "run") as mock_run:
            mock_run.side_effect = [
                {"passed": False, "issues": [], "sampled_frames": 0, "total_frames": 300},
                {"passed": True, "issues": [], "sampled_frames": 6, "total_frames": 300},
            ]
            result = fr.check_mixed_engine("test.mp4")
            assert result["passed"] is True
            assert result["retry_attempts"] == 1
            assert result["retry_limit"] == 2
            assert mock_run.call_count == 2

    def test_exhaust_retries_on_exception(self) -> None:
        """Exhaust all retries on persistent exception."""
        from videoforge.review.frame_reviewer import FrameReviewer
        fr = FrameReviewer(max_retries=2)
        with patch.object(fr._l0, "run") as mock_run:
            mock_run.side_effect = RuntimeError("persistent failure")
            with pytest.raises(RuntimeError, match="persistent failure"):
                fr.check_mixed_engine("test.mp4")
            assert mock_run.call_count == 3  # 1 initial + 2 retries

    def test_no_retry_on_genuine_quality_issues(self) -> None:
        """Genuine quality issues (sampled_frames > 0) do NOT trigger retry."""
        from videoforge.review.frame_reviewer import FrameReviewer
        fr = FrameReviewer(max_retries=2)
        with patch.object(fr._l0, "run") as mock_run:
            mock_run.return_value = {
                "passed": False,
                "issues": [{"type": "blank_frame", "severity": "high"}],
                "sampled_frames": 6,
                "total_frames": 300,
            }
            result = fr.check_mixed_engine("test.mp4")
            assert result["passed"] is False
            assert "retry_attempts" not in result
            assert "retry_limit" not in result
            mock_run.assert_called_once_with("test.mp4")

    def test_no_retry_metadata_on_first_attempt_success(self) -> None:
        """No retry metadata when first attempt succeeds."""
        from videoforge.review.frame_reviewer import FrameReviewer
        fr = FrameReviewer(max_retries=2)
        with patch.object(fr._l0, "run") as mock_run:
            mock_run.return_value = {"passed": True, "issues": [], "sampled_frames": 6, "total_frames": 300}
            result = fr.check_mixed_engine("test.mp4")
            assert result["passed"] is True
            assert "retry_attempts" not in result
            assert "retry_limit" not in result
            mock_run.assert_called_once_with("test.mp4")

    def test_retry_metadata_shape(self) -> None:
        """Retry metadata has correct types."""
        from videoforge.review.frame_reviewer import FrameReviewer
        fr = FrameReviewer(max_retries=3)
        with patch.object(fr._l0, "run") as mock_run:
            mock_run.side_effect = [
                RuntimeError("transient"),
                {"passed": True, "issues": [], "sampled_frames": 6, "total_frames": 300},
            ]
            result = fr.check_mixed_engine("test.mp4")
            assert isinstance(result["retry_attempts"], int)
            assert isinstance(result["retry_limit"], int)
            assert result["retry_attempts"] == 1
            assert result["retry_limit"] == 3

    def test_aggregate_review_benefits_from_retry(self) -> None:
        """aggregate_review also gets retry via check_mixed_engine."""
        from videoforge.review.frame_reviewer import FrameReviewer
        fr = FrameReviewer(max_retries=2)
        with patch.object(fr._l0, "run") as mock_l0, \
             patch.object(fr, "check_integrity") as mock_l1:
            mock_l0.side_effect = [
                RuntimeError("transient"),
                {"passed": True, "issues": [], "sampled_frames": 6, "total_frames": 300},
            ]
            mock_l1.return_value = {"passed": True, "issues": [], "total_frames": 300}
            result = fr.aggregate_review("test.mp4")
            assert result["levels"]["l0_mixed_engine"]["passed"] is True
            assert result["levels"]["l0_mixed_engine"]["retry_attempts"] == 1
            assert mock_l0.call_count == 2


# ── L0 configurable thresholds ────────────────────────────────────────────


def test_custom_sample_count() -> None:
    r = L0MixedEngineReview(sample_count=3)
    frames = r._sample_frames("test.mp4", 300, 10.0)
    assert len(frames) == 3
    assert frames[0]["index"] == 0
    # step = (300-1) // 2 = 149 → indices: 0, 149, 298
    assert frames[-1]["index"] == 298