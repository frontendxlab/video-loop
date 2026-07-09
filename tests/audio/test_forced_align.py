"""Tests for forced alignment quality scoring and metadata propagation."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# AlignmentResult / AlignmentMetadata shape
# ---------------------------------------------------------------------------

class TestAlignmentResult:
    def test_is_list_and_carries_metadata(self):
        from videoforge.audio.forced_align import AlignmentMetadata, AlignmentResult
        meta = AlignmentMetadata(source="aeneas", confidence=0.95, fallback_used=False)
        result = AlignmentResult(
            [{"text": "hi", "startMs": 0.0, "endMs": 100.0}], metadata=meta,
        )
        assert len(result) == 1
        assert result[0]["text"] == "hi"
        assert result.metadata is meta

    def test_default_metadata_none(self):
        from videoforge.audio.forced_align import AlignmentResult
        result = AlignmentResult()
        assert result.metadata is None

    def test_iteration_backwards_compatible(self):
        from videoforge.audio.forced_align import AlignmentResult
        items = [{"text": "a", "startMs": 0.0, "endMs": 1.0}]
        result = AlignmentResult(items)
        assert list(result) == items


# ---------------------------------------------------------------------------
# forced_align — edge cases
# ---------------------------------------------------------------------------

class TestForcedAlignEdgeCases:
    def test_empty_text(self):
        from videoforge.audio.forced_align import forced_align
        result = forced_align("", "/fake.wav")
        assert len(result) == 0
        assert result.metadata.source == "none"
        assert result.metadata.confidence == 1.0
        assert result.metadata.fallback_used is False

    def test_missing_wav_returns_estimate_with_low_confidence(self):
        from videoforge.audio.forced_align import forced_align
        result = forced_align("Hello world", "/nonexistent.wav")
        assert len(result) == 2
        assert result.metadata.source == "punctuation_estimate"
        assert result.metadata.confidence == 0.4
        assert result.metadata.fallback_used is True


# ---------------------------------------------------------------------------
# forced_align — backend-specific paths
# ---------------------------------------------------------------------------

class TestForcedAlignBackends:
    def test_aeneas_success(self, tmp_path: Path):
        wav = tmp_path / "test.wav"
        wav.write_bytes(b"\x00" * 1000)

        from videoforge.audio.forced_align import forced_align
        with patch("videoforge.audio.forced_align._align_aeneas") as mock:
            mock.return_value = [
                {"text": "Hello", "startMs": 0.0, "endMs": 500.0},
                {"text": "world", "startMs": 500.0, "endMs": 1000.0},
            ]
            result = forced_align("Hello world", str(wav))

        assert len(result) == 2
        assert result.metadata.source == "aeneas"
        assert result.metadata.confidence == 0.95
        assert result.metadata.fallback_used is False
        assert result.metadata.attempted_backends == ("aeneas",)

    def test_aeneas_fails_whisper_succeeds(self, tmp_path: Path):
        wav = tmp_path / "test.wav"
        wav.write_bytes(b"\x00" * 1000)

        from videoforge.audio.forced_align import forced_align
        with (
            patch("videoforge.audio.forced_align._align_aeneas", return_value=None),
            patch("videoforge.audio.forced_align._align_whisper") as mock_w,
        ):
            mock_w.return_value = [
                {"text": "Hello", "startMs": 0.0, "endMs": 500.0},
                {"text": "world", "startMs": 500.0, "endMs": 1000.0},
            ]
            result = forced_align("Hello world", str(wav))

        assert result.metadata.source == "whisper"
        assert result.metadata.confidence == 0.85
        assert result.metadata.fallback_used is True
        assert result.metadata.attempted_backends == ("aeneas", "whisper")

    def test_aeneas_whisper_fail_espeak_succeeds(self, tmp_path: Path):
        wav = tmp_path / "test.wav"
        wav.write_bytes(b"\x00" * 1000)

        from videoforge.audio.forced_align import forced_align
        with (
            patch("videoforge.audio.forced_align._align_aeneas", return_value=None),
            patch("videoforge.audio.forced_align._align_whisper", return_value=None),
            patch("videoforge.audio.forced_align._align_espeak") as mock_e,
        ):
            mock_e.return_value = [
                {"text": "Hello", "startMs": 0.0, "endMs": 500.0},
                {"text": "world", "startMs": 500.0, "endMs": 1000.0},
            ]
            result = forced_align("Hello world", str(wav))

        assert result.metadata.source == "espeak"
        assert result.metadata.confidence == 0.60
        assert result.metadata.fallback_used is True
        assert result.metadata.attempted_backends == ("aeneas", "whisper", "espeak")

    def test_all_backends_fail_punctuation_fallback(self, tmp_path: Path):
        wav = tmp_path / "test.wav"
        wav.write_bytes(b"\x00" * 1000)

        from videoforge.audio.forced_align import forced_align
        with (
            patch("videoforge.audio.forced_align._align_aeneas", return_value=None),
            patch("videoforge.audio.forced_align._align_whisper", return_value=None),
            patch("videoforge.audio.forced_align._align_espeak", return_value=None),
        ):
            result = forced_align("Hello world", str(wav))

        assert len(result) == 2
        assert result.metadata.source == "punctuation_estimate"
        assert result.metadata.confidence == 0.4
        assert result.metadata.fallback_used is True
        assert result.metadata.attempted_backends == ("aeneas", "whisper", "espeak")

    def test_backend_raises_exception(self, tmp_path: Path):
        """Exception from backend is caught, next backend tried."""
        wav = tmp_path / "test.wav"
        wav.write_bytes(b"\x00" * 1000)

        from videoforge.audio.forced_align import forced_align
        with (
            patch("videoforge.audio.forced_align._align_aeneas", side_effect=RuntimeError("boom")) as mock_a,
            patch("videoforge.audio.forced_align._align_whisper") as mock_w,
        ):
            mock_a.side_effect = RuntimeError("boom")
            mock_w.return_value = [
                {"text": "Hello", "startMs": 0.0, "endMs": 500.0},
            ]
            result = forced_align("Hello world", str(wav))

        assert result.metadata.source == "whisper"
        assert mock_a.call_count == 1
        assert mock_w.call_count == 1


# ---------------------------------------------------------------------------
# Integration: generate_audio includes alignment_metadata
# ---------------------------------------------------------------------------

class TestGenerateAudioMetadata:
    def test_alignment_metadata_in_return_dict(self, tmp_path: Path):
        wav = tmp_path / "audio.wav"
        from videoforge.audio.forced_align import AlignmentMetadata, AlignmentResult
        from videoforge.engine.tts import generate_audio

        fake_timings = [
            {"text": "Hello", "startMs": 0.0, "endMs": 100.0},
            {"text": "world", "startMs": 100.0, "endMs": 200.0},
        ]
        fake_meta = AlignmentMetadata(
            source="whisper", confidence=0.85, fallback_used=True,
            attempted_backends=("aeneas", "whisper"),
        )

        with (
            patch("videoforge.engine.tts.requests.post") as mock_post,
            patch("videoforge.engine.tts._wav_duration", return_value=0.5),
            patch("videoforge.audio.forced_align.forced_align") as mock_fa,
        ):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.headers = {"content-type": "audio/wav"}
            mock_resp.content = b"\x00" * 1000
            mock_post.return_value = mock_resp

            mock_fa.return_value = AlignmentResult(fake_timings, metadata=fake_meta)

            result = generate_audio("Hello world", str(wav))

        assert "alignment_metadata" in result
        meta = result["alignment_metadata"]
        assert meta["source"] == "whisper"
        assert meta["confidence"] == 0.85
        assert meta["fallback_used"] is True
        assert meta["attempted_backends"] == ["aeneas", "whisper"]

    def test_alignment_metadata_fallback_when_forced_align_raises(self, tmp_path: Path):
        """When forced_align raises, metadata shows estimated."""
        wav = tmp_path / "audio.wav"
        from videoforge.engine.tts import generate_audio

        with (
            patch("videoforge.engine.tts.requests.post") as mock_post,
            patch("videoforge.engine.tts._wav_duration", return_value=0.5),
            patch("videoforge.audio.forced_align.forced_align", side_effect=RuntimeError("align failed")),
        ):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.headers = {"content-type": "audio/wav"}
            mock_resp.content = b"\x00" * 1000
            mock_post.return_value = mock_resp

            result = generate_audio("Hello world", str(wav))

        assert "alignment_metadata" in result
        assert result["alignment_metadata"]["source"] == "estimated"
        assert result["alignment_metadata"]["confidence"] == 0.2
        assert result["alignment_metadata"]["fallback_used"] is True
