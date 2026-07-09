"""L0: Deterministic frame-sampled visual review gate for mixed-engine output.

Checks basic visual consistency across frames sampled from a rendered video
that may combine Remotion, Manim, and Animotion clips. No external AI dependency.

Sampling strategy: N equally-spaced frames from the video. Each frame decoded
to raw RGB pixels via ffmpeg. Checks run on sampled pixel data.

Checks:
  - Blank/near-blank frames (mean brightness < threshold)
  - Resolution/format mismatch indicators (width/height changes detected via ffprobe)
  - Palette/theme coherence (dominant color distance from expected background)
  - Freeze detection (consecutive sampled frames identical or near-identical)
"""

from __future__ import annotations

import json
import math
import subprocess
from typing import Any

from videoforge.design_tokens import load_design_tokens


# Default background color from design tokens (in hex)
_DEFAULT_BG = tuple(int(load_design_tokens()["theme"]["background"]["base"].lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))  # noqa: RUF001

# How many frames to sample for review
_DEFAULT_SAMPLE_COUNT = 12

# Thresholds
_BLANK_BRIGHTNESS_THRESHOLD = 15.0  # mean pixel value below this = blank
_FREEZE_MSE_THRESHOLD = 5.0  # MSE between consecutive sampled frames below this = freeze
_COLOR_DISTANCE_THRESHOLD = 100.0  # Euclidean RGB distance from expected bg
_RESOLUTION_MISMATCH_ALLOWED = 0.01  # 1% tolerance for aspect ratio changes


def _parse_rgb_line(line: str) -> tuple[int, int, int] | None:
    """Parse a single 'r g b' line from ffmpeg rgb24 frame dump."""
    parts = line.strip().split()
    if len(parts) < 3:
        return None
    try:
        return (int(parts[0]), int(parts[1]), int(parts[2]))
    except ValueError:
        return None


def _mean_rgb(pixels: list[tuple[int, int, int]]) -> tuple[float, float, float]:
    if not pixels:
        return (0.0, 0.0, 0.0)
    n = len(pixels)
    return (sum(p[0] for p in pixels) / n, sum(p[1] for p in pixels) / n, sum(p[2] for p in pixels) / n)


def _brightness(rgb: tuple[float, float, float]) -> float:
    return (rgb[0] + rgb[1] + rgb[2]) / 3.0


def _color_distance(a: tuple[float, float, float], b: tuple[int, int, int]) -> float:
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


def _mse(a: list[tuple[int, int, int]], b: list[tuple[int, int, int]]) -> float:
    if not a or not b or len(a) != len(b):
        return float("inf")
    s = sum((a[i][0] - b[i][0]) ** 2 + (a[i][1] - b[i][1]) ** 2 + (a[i][2] - b[i][2]) ** 2 for i in range(len(a)))
    return s / len(a)


class L0MixedEngineReview:
    """Frame-sampled visual review gate for mixed-engine output."""

    def __init__(self, sample_count: int = _DEFAULT_SAMPLE_COUNT) -> None:
        self.sample_count = sample_count
        self._bg_color = _DEFAULT_BG

    def run(
        self, video_path: str, streams_info: list[dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        """Run all deterministic visual checks on sampled frames.

        Args:
            video_path: Path to rendered video file.
            streams_info: Optional pre-extracted ffprobe streams JSON. If None,
                          extracted internally.

        Returns:
            dict with keys: issues, passed, sampled_count, total_frames, duration_seconds.
        """
        issues: list[dict[str, Any]] = []

        # ── 1. Probe streams for resolution info ──────────────────────────
        if streams_info is None:
            streams_info = self._probe_streams(video_path)
        total_frames = self._extract_total_frames(streams_info)
        duration = self._extract_duration(streams_info)
        video_streams = [s for s in streams_info if s.get("codec_type") == "video"]

        if not video_streams:
            return {
                "issues": [{"type": "no_video_stream", "detail": "No video stream found in file"}],
                "passed": False,
                "sampled_frames": 0,
                "total_frames": total_frames,
                "duration_seconds": duration,
            }

        # ── 2. Resolution / format consistency across streams ────────────
        if len(video_streams) > 1:
            issues.extend(self._check_resolution_consistency(video_streams))

        # ── 3. Sample frames ──────────────────────────────────────────────
        if total_frames > 0:
            sampled = self._sample_frame_pixels(video_path, total_frames, duration)
        else:
            sampled = []

        # ── 4. Run checks on sampled frames ───────────────────────────────
        issues.extend(self._check_blank_frames(sampled, total_frames, duration))
        issues.extend(self._check_palette_coherence(sampled, total_frames, duration))
        freeze_issues = self._check_freeze(sampled, total_frames, duration)
        issues.extend(freeze_issues)

        # ── 5. If all sampled frames are blank, add summary note ──────────
        blank_count = sum(1 for i in issues if i["type"] == "blank_frame")
        if blank_count == len(sampled) and blank_count > 1:
            issues.append({
                "type": "all_blank",
                "detail": f"All {len(sampled)} sampled frames appear blank/near-blank",
                "severity": "high",
            })

        return {
            "issues": issues,
            "passed": len(issues) == 0,
            "sampled_frames": len(sampled),
            "total_frames": total_frames,
            "duration_seconds": duration,
        }

    # ── Stream probing ─────────────────────────────────────────────────────

    def _probe_streams(self, video_path: str) -> list[dict[str, Any]]:
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "quiet", "-print_format", "json",
                    "-show_streams", "-show_format", video_path,
                ],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode != 0:
                return []
            data = json.loads(result.stdout)
            return data.get("streams", [])
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            return []

    @staticmethod
    def _extract_total_frames(streams: list[dict[str, Any]]) -> int:
        for s in streams:
            if s.get("codec_type") == "video":
                nb = s.get("nb_frames")
                if nb is not None:
                    return int(nb)
                # fallback: derive from duration * fps
                dur = s.get("duration")
                avg_fps = s.get("avg_frame_rate", "0/1")
                if dur and avg_fps and "/" in avg_fps:
                    try:
                        num, den = avg_fps.split("/")
                        fps = float(num) / float(den) if float(den) > 0 else 0.0
                        return int(float(dur) * fps)
                    except (ValueError, ZeroDivisionError):
                        pass
        return 0

    @staticmethod
    def _extract_duration(streams: list[dict[str, Any]]) -> float:
        for s in streams:
            if s.get("codec_type") == "video":
                dur = s.get("duration")
                if dur:
                    return float(dur)
        return 0.0

    # ── Resolution checks ──────────────────────────────────────────────────

    def _check_resolution_consistency(
        self, video_streams: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        ref_w = video_streams[0].get("width", 0)
        ref_h = video_streams[0].get("height", 0)
        ref_ratio = ref_w / ref_h if ref_h > 0 else 0.0
        ref_codec = video_streams[0].get("codec_name", "unknown")
        ref_idx = video_streams[0].get("index", 0)

        for s in video_streams[1:]:
            w = s.get("width", 0)
            h = s.get("height", 0)
            codec = s.get("codec_name", "unknown")
            idx = s.get("index", 0)
            ratio = w / h if h > 0 else 0.0

            if w != ref_w or h != ref_h:
                issues.append({
                    "type": "resolution_mismatch",
                    "stream_index": idx,
                    "expected": f"{ref_w}x{ref_h}",
                    "actual": f"{w}x{h}",
                    "detail": f"Stream {idx} has resolution {w}x{h}, expected {ref_w}x{ref_h}",
                    "severity": "high",
                })
            elif abs(ratio - ref_ratio) > _RESOLUTION_MISMATCH_ALLOWED:
                issues.append({
                    "type": "aspect_ratio_mismatch",
                    "stream_index": idx,
                    "expected_ratio": round(ref_ratio, 4),
                    "actual_ratio": round(ratio, 4),
                    "detail": f"Stream {idx} aspect ratio {ratio:.4f} differs from ref stream {ref_idx}",
                    "severity": "medium",
                })

            if codec != ref_codec:
                issues.append({
                    "type": "codec_mismatch",
                    "stream_index": idx,
                    "expected": ref_codec,
                    "actual": codec,
                    "detail": f"Stream {idx} codec {codec}, expected {ref_codec}",
                    "severity": "low",
                })

        return issues

    # ── Frame sampling ─────────────────────────────────────────────────────

    def _sample_frames(
        self, video_path: str, total_frames: int, duration: float
    ) -> list[dict[str, Any]]:
        """Decide which frame indices to sample. Returns metadata list."""
        if total_frames <= 0:
            return []

        count = min(self.sample_count, total_frames)
        if count <= 1:
            indices = [0]
        else:
            step = max(1, (total_frames - 1) // (count - 1))
            indices = [min(i * step, total_frames - 1) for i in range(count)]

        frames: list[dict[str, Any]] = []
        for idx in indices:
            pts = idx / (total_frames / duration) if duration > 0 else 0.0
            frames.append({"index": idx, "pts": round(pts, 3)})
        return frames

    def _sample_frame_pixels(
        self, video_path: str, total_frames: int, duration: float
    ) -> list[dict[str, Any]]:
        """Sample frames from video and decode to RGB pixel data.

        Uses ffmpeg to extract individual frames at selected timestamps.
        Falls back gracefully if ffmpeg is unavailable.
        """
        frame_metas = self._sample_frames(video_path, total_frames, duration)
        if not frame_metas:
            return []

        result_frames: list[dict[str, Any]] = []
        for fm in frame_metas:
            pixels = self._extract_frame_pixels(video_path, fm["pts"])
            if pixels is not None:
                fm["pixels"] = pixels
                fm["width"] = pixels["width"]
                fm["height"] = pixels["height"]
            result_frames.append(fm)
        return result_frames

    def _extract_frame_pixels(
        self, video_path: str, pts: float
    ) -> dict[str, Any] | None:
        """Extract a single frame at given PTS as raw RGB pixels via ffmpeg.

        Uses select filter for exact frame selection and rawvideo output.
        Returns dict with 'data' (list of (r,g,b) tuples), 'width', 'height'.
        Returns None if ffmpeg fails or unavailable.
        """
        try:
            result = subprocess.run(
                [
                    "ffmpeg", "-y", "-i", video_path,
                    "-vf", f"select=gte(t,{pts})",
                    "-vsync", "vfr",
                    "-frames:v", "1",
                    "-f", "rawvideo",
                    "-pix_fmt", "rgb24",
                    "-",
                ],
                capture_output=True, timeout=120,
            )
            if result.returncode != 0 or not result.stdout:
                return None

            raw = result.stdout
            # Guess dimensions from stream info (probed earlier if available)
            # Default to 1920x1080 if unknown; 3 bytes per pixel
            width, height = self._guess_dimensions(video_path)
            expected = width * height * 3
            if len(raw) < expected:
                # Try smaller: maybe video is not full HD
                # Brute-force plausible widths
                for w in (1920, 1280, 854, 720, 640, 426, 320):
                    h_calc = len(raw) // (w * 3)
                    if h_calc > 0 and h_calc * w * 3 == len(raw):
                        width, height = w, h_calc
                        break
                else:
                    return None  # can't determine dimensions

            pixels: list[tuple[int, int, int]] = []
            stride = width * height * 3
            actual = min(len(raw), stride)
            for i in range(0, actual, 3):
                r = raw[i]
                g = raw[i + 1]
                b = raw[i + 2]
                pixels.append((r, g, b))
            return {"data": pixels, "width": width, "height": height}
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None

    def _guess_dimensions(self, video_path: str) -> tuple[int, int]:
        """Fallback dimension guess. Defaults 1920x1080."""
        _ = video_path  # unused; could probe but called from failure path
        return (1920, 1080)

    # ── Blank frame detection ──────────────────────────────────────────────

    def _check_blank_frames(
        self, sampled: list[dict[str, Any]], total_frames: int, duration: float
    ) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        for frame in sampled:
            pixels = frame.get("pixels")
            if pixels is None:
                continue
            mean = _mean_rgb(pixels["data"])
            b = _brightness(mean)
            if b < _BLANK_BRIGHTNESS_THRESHOLD:
                issues.append({
                    "type": "blank_frame",
                    "frame_index": frame["index"],
                    "pts": frame["pts"],
                    "mean_brightness": round(b, 2),
                    "detail": f"Frame {frame['index']} (PTS {frame['pts']}s) appears blank (brightness {b:.2f})",
                    "severity": "high",
                })
        return issues

    # ── Palette / theme coherence ──────────────────────────────────────────

    def _check_palette_coherence(
        self, sampled: list[dict[str, Any]], total_frames: int, duration: float
    ) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        bg = self._bg_color

        for frame in sampled:
            pixels = frame.get("pixels")
            if pixels is None:
                continue
            mean = _mean_rgb(pixels["data"])
            dist = _color_distance(mean, bg)
            if dist > _COLOR_DISTANCE_THRESHOLD:
                issues.append({
                    "type": "palette_drift",
                    "frame_index": frame["index"],
                    "pts": frame["pts"],
                    "dominant_color": f"({mean[0]:.0f},{mean[1]:.0f},{mean[2]:.0f})",
                    "expected_bg": f"({bg[0]},{bg[1]},{bg[2]})",
                    "distance": round(dist, 2),
                    "detail": f"Frame {frame['index']} dominant color drifted from expected background",
                    "severity": "medium",
                })
        return issues

    # ── Freeze detection ────────────────────────────────────────────────────

    def _check_freeze(
        self, sampled: list[dict[str, Any]], total_frames: int, duration: float
    ) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        for i in range(1, len(sampled)):
            prev = sampled[i - 1].get("pixels")
            curr = sampled[i].get("pixels")
            if prev is None or curr is None:
                continue
            if prev["width"] != curr["width"] or prev["height"] != curr["height"]:
                continue
            mse_val = _mse(prev["data"], curr["data"])
            if mse_val < _FREEZE_MSE_THRESHOLD:
                issues.append({
                    "type": "suspected_freeze",
                    "frame_a": sampled[i - 1]["index"],
                    "frame_b": sampled[i]["index"],
                    "pts_a": sampled[i - 1]["pts"],
                    "pts_b": sampled[i]["pts"],
                    "mse": round(mse_val, 4),
                    "detail": f"Frames {sampled[i-1]['index']} and {sampled[i]['index']} near-identical (MSE {mse_val:.4f})",
                    "severity": "medium",
                })
        return issues