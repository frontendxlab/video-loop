"""Tests for artifact generator — thumbnail/frame extraction from rendered scenes.

Covers:
- extract_frame success + failure cases
- generate_scene_thumbnail outputs correct path/size
- generate_sampled_frame outputs correct path/size
- generate_scene_artifacts produces all artifact types
- generate_batch_scene_artifacts handles multiple scenes
- Best-effort on missing/corrupt video
- Deterministic paths
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from videoforge.artifacts.generator import (
    _probe_duration_frames,
    extract_frame,
    generate_batch_scene_artifacts,
    generate_scene_artifacts,
    generate_scene_thumbnail,
    generate_sampled_frame,
)


# ─── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture
def sample_video(tmp_path: Path) -> Path:
    """Create a minimal valid MP4 using ffmpeg."""
    out = tmp_path / "scene_0000.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "testsrc2=s=320x240:d=2,format=yuv420p",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-r", "30",
        str(out),
    ]
    subprocess.run(cmd, capture_output=True, timeout=30, check=True)
    assert out.is_file() and out.stat().st_size > 0
    return out


@pytest.fixture
def artifacts_dir(tmp_path: Path) -> Path:
    return tmp_path / "artifacts"


# ─── Unit: extract_frame ───────────────────────────────────────────────────


class TestExtractFrame:
    def test_extracts_frame_from_valid_video(self, sample_video: Path) -> None:
        out = sample_video.parent / "frame.jpg"
        assert extract_frame(sample_video, out, position_sec=0.0, scale="320:-1")
        assert out.is_file()
        assert out.stat().st_size > 0

    def test_extracts_at_mid_point(self, sample_video: Path) -> None:
        out = sample_video.parent / "frame_mid.jpg"
        assert extract_frame(sample_video, out, position_sec=1.0, scale="640:-1")
        assert out.is_file() and out.stat().st_size > 0

    def test_missing_video_returns_false(self, tmp_path: Path) -> None:
        assert not extract_frame(
            tmp_path / "nonexistent.mp4",
            tmp_path / "out.jpg",
        )

    def test_corrupt_video_returns_false(self, tmp_path: Path) -> None:
        corrupt = tmp_path / "corrupt.mp4"
        corrupt.write_bytes(b"not a video file")
        assert not extract_frame(corrupt, tmp_path / "out.jpg")

    def test_creates_parent_dirs(self, sample_video: Path, tmp_path: Path) -> None:
        out = tmp_path / "deep" / "nested" / "frame.jpg"
        assert extract_frame(sample_video, out)
        assert out.is_file()

    def test_deterministic_output(self, sample_video: Path, tmp_path: Path) -> None:
        """Same input + same position = identical bytes."""
        a = tmp_path / "a.jpg"
        b = tmp_path / "b.jpg"
        assert extract_frame(sample_video, a, position_sec=0.5, scale="320:-1")
        assert extract_frame(sample_video, b, position_sec=0.5, scale="320:-1")
        assert a.read_bytes() == b.read_bytes()

    def test_different_positions_different_bytes(self, sample_video: Path, tmp_path: Path) -> None:
        """Different position should produce different frame bytes."""
        a = tmp_path / "a.jpg"
        b = tmp_path / "b.jpg"
        assert extract_frame(sample_video, a, position_sec=0.0, scale="320:-1")
        assert extract_frame(sample_video, b, position_sec=0.5, scale="320:-1")
        assert a.read_bytes() != b.read_bytes()

    def test_no_scale_uses_native_resolution(self, sample_video: Path) -> None:
        out = sample_video.parent / "native.jpg"
        assert extract_frame(sample_video, out, position_sec=0.0, scale=None)
        assert out.is_file() and out.stat().st_size > 0


# ─── Unit: generate_scene_thumbnail ──────────────────────────────────────


class TestGenerateSceneThumbnail:
    def test_generates_jpg_at_320px(self, sample_video: Path, artifacts_dir: Path) -> None:
        scene_id = "scene_0000"
        assert generate_scene_thumbnail(sample_video, artifacts_dir, scene_id)
        path = artifacts_dir / "thumbnails" / f"{scene_id}.jpg"
        assert path.is_file() and path.stat().st_size > 0

    def test_creates_thumbnails_subdir(self, sample_video: Path, tmp_path: Path) -> None:
        d = tmp_path / "custom_artifacts"
        assert generate_scene_thumbnail(sample_video, d, "s1")
        assert (d / "thumbnails" / "s1.jpg").is_file()

    def test_failure_on_empty_video(self, tmp_path: Path) -> None:
        empty = tmp_path / "empty.mp4"
        empty.write_bytes(b"")
        assert not generate_scene_thumbnail(empty, tmp_path, "s1")

    def test_deterministic_thumbnail(self, sample_video: Path, tmp_path: Path) -> None:
        """Thumbnails from same source at same position are identical."""
        d1 = tmp_path / "d1"
        d2 = tmp_path / "d2"
        assert generate_scene_thumbnail(sample_video, d1, "s1")
        assert generate_scene_thumbnail(sample_video, d2, "s1")
        a = (d1 / "thumbnails" / "s1.jpg").read_bytes()
        b = (d2 / "thumbnails" / "s1.jpg").read_bytes()
        assert a == b


# ─── Unit: generate_sampled_frame ──────────────────────────────────────────


class TestGenerateSampledFrame:
    def test_generates_jpg_at_640px(self, sample_video: Path, artifacts_dir: Path) -> None:
        scene_id = "scene_0000"
        assert generate_sampled_frame(sample_video, artifacts_dir, scene_id)
        path = artifacts_dir / "frames" / f"{scene_id}.jpg"
        assert path.is_file() and path.stat().st_size > 0

    def test_creates_frames_subdir(self, sample_video: Path, tmp_path: Path) -> None:
        d = tmp_path / "custom"
        assert generate_sampled_frame(sample_video, d, "s1")
        assert (d / "frames" / "s1.jpg").is_file()

    def test_thumbnail_and_frame_independent(self, sample_video: Path, artifacts_dir: Path) -> None:
        """Thumbnail and frame are different files with different sizes."""
        assert generate_scene_thumbnail(sample_video, artifacts_dir, "s1")
        assert generate_sampled_frame(sample_video, artifacts_dir, "s1")
        thumb = artifacts_dir / "thumbnails" / "s1.jpg"
        frame = artifacts_dir / "frames" / "s1.jpg"
        assert thumb.is_file() and frame.is_file()
        # Frame should be larger than thumbnail (640px vs 320px)
        assert frame.stat().st_size > thumb.stat().st_size


# ─── Unit: generate_scene_artifacts ───────────────────────────────────────


class TestGenerateSceneArtifacts:
    def test_returns_all_artifact_paths(self, sample_video: Path, artifacts_dir: Path) -> None:
        result = generate_scene_artifacts(sample_video, artifacts_dir, "scene_0000")
        assert result["thumbnail"], "thumbnail should exist"
        assert result["frame"], "frame should exist"
        assert Path(result["thumbnail"]).is_file()
        assert Path(result["frame"]).is_file()

    def test_mid_frame_when_duration_provided(self, sample_video: Path, artifacts_dir: Path) -> None:
        result = generate_scene_artifacts(
            sample_video, artifacts_dir, "scene_long",
            duration_frames=60, fps=30,
        )
        assert len(result["frames_mid"]) == 1
        assert Path(result["frames_mid"][0]).is_file()

    def test_no_mid_frame_when_duration_zero(self, sample_video: Path, artifacts_dir: Path) -> None:
        result = generate_scene_artifacts(
            sample_video, artifacts_dir, "scene_short",
            duration_frames=0, fps=30,
        )
        assert result["frames_mid"] == []

    def test_missing_video_returns_empty_paths(self, tmp_path: Path) -> None:
        result = generate_scene_artifacts(
            tmp_path / "missing.mp4", tmp_path / "arts", "s1",
        )
        assert result["thumbnail"] == ""
        assert result["frame"] == ""
        assert result["frames_mid"] == []

    def test_result_has_expected_keys(self, sample_video: Path, artifacts_dir: Path) -> None:
        result = generate_scene_artifacts(sample_video, artifacts_dir, "s1")
        assert set(result.keys()) == {"thumbnail", "frame", "frames_mid"}


# ─── Unit: generate_batch_scene_artifacts ─────────────────────────────────


class TestGenerateBatch:
    def test_generates_for_all_scenes(self, tmp_path: Path) -> None:
        """Create 2 scenes via ffmpeg, batch-generate artifacts."""
        arts = tmp_path / "arts"
        scenes = []
        for i in range(2):
            v = tmp_path / f"scene_{i:04d}.mp4"
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "testsrc2=s=320x240:d=1,format=yuv420p",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-r", "30",
                str(v),
            ]
            subprocess.run(cmd, capture_output=True, timeout=30, check=True)
            scenes.append(str(v))

        results = generate_batch_scene_artifacts(
            artifacts_dir=arts,
            scene_paths=scenes,
            scene_ids=["scene_0000", "scene_0001"],
            fps=30,
        )

        assert len(results) == 2
        for i, r in enumerate(results):
            assert r["thumbnail"], f"scene {i} thumbnail missing"
            assert r["frame"], f"scene {i} frame missing"
            assert Path(r["thumbnail"]).is_file()
            assert Path(r["frame"]).is_file()

    def test_missing_paths_skipped(self, tmp_path: Path) -> None:
        arts = tmp_path / "arts"
        results = generate_batch_scene_artifacts(
            artifacts_dir=arts,
            scene_paths=[str(tmp_path / "nonexistent.mp4")],
            scene_ids=["s1"],
            fps=30,
        )
        # Should not crash; returns empty paths
        assert len(results) == 1
        assert results[0]["thumbnail"] == ""

    def test_scene_ids_fallback(self, tmp_path: Path) -> None:
        """When scene_ids is shorter, falls back to index-based IDs."""
        v = tmp_path / "scene_0000.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "testsrc2=s=320x240:d=1,format=yuv420p",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-r", "30",
            str(v),
        ]
        subprocess.run(cmd, capture_output=True, timeout=30, check=True)

        arts = tmp_path / "arts"
        results = generate_batch_scene_artifacts(
            artifacts_dir=arts,
            scene_paths=[str(v)],
            scene_ids=[],  # empty — uses fallback
            fps=30,
        )
        assert len(results) == 1
        assert results[0]["thumbnail"]


# ─── Unit: _probe_duration_frames ──────────────────────────────────────────


class TestProbeDuration:
    def test_returns_frames_from_nb_frames(self, sample_video: Path) -> None:
        frames = _probe_duration_frames(sample_video)
        assert frames > 0

    def test_missing_file_returns_zero(self, tmp_path: Path) -> None:
        assert _probe_duration_frames(tmp_path / "nope.mp4") == 0

    def test_corrupt_file_returns_zero(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.mp4"
        bad.write_bytes(b"garbage")
        assert _probe_duration_frames(bad) == 0


# ─── Integration: Artifact dir structure matches API expectations ─────────


class TestArtifactDirStructure:
    """Generated artifact layout must match what the Artifacts API expects.

    API expects:
      {ARTIFACTS_DIR}/{job_id}/thumbnails/{scene_id}.jpg
      {ARTIFACTS_DIR}/{job_id}/frames/{scene_id}.jpg
    """

    def test_structure_matches_api_contract(self, sample_video: Path, tmp_path: Path) -> None:
        job_dir = tmp_path / "job_test_001"
        result = generate_scene_artifacts(sample_video, job_dir, "scene_alpha")
        assert (job_dir / "thumbnails" / "scene_alpha.jpg").is_file()
        assert (job_dir / "frames" / "scene_alpha.jpg").is_file()
        # Verify via path from result
        assert result["thumbnail"] == str((job_dir / "thumbnails" / "scene_alpha.jpg").resolve())
        assert result["frame"] == str((job_dir / "frames" / "scene_alpha.jpg").resolve())

    def test_multiple_scenes_no_collision(self, tmp_path: Path) -> None:
        """Two scenes produce two independent artifact sets."""
        arts = tmp_path / "arts"
        scenes = []
        for i, color in enumerate(["red", "blue"]):
            v = tmp_path / f"scene_{i:04d}.mp4"
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "testsrc2=s=320x240:d=1,format=yuv420p",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-r", "30",
                str(v),
            ]
            subprocess.run(cmd, capture_output=True, timeout=30, check=True)
            scenes.append(str(v))

        generate_batch_scene_artifacts(arts, scenes, ["s1", "s2"])
        assert (arts / "thumbnails" / "s1.jpg").is_file()
        assert (arts / "thumbnails" / "s2.jpg").is_file()
        assert (arts / "frames" / "s1.jpg").is_file()
        assert (arts / "frames" / "s2.jpg").is_file()
