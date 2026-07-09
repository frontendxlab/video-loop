from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from videoforge.review.l0_mixed_engine import L0MixedEngineReview
from videoforge.review.l3_smoothness import L3Smoothness
from videoforge.review.l4_transitions import L4Transitions
from videoforge.review.l5_consistency import L5Consistency
from videoforge.review.overlap_gate import OverlapGate


class FrameReviewer:
    def __init__(self, max_retries: int = 2) -> None:
        self._l0 = L0MixedEngineReview()
        self._l3 = L3Smoothness()
        self._l4 = L4Transitions()
        self._l5 = L5Consistency()
        self._overlap_gate = OverlapGate()
        self.max_retries = max_retries

    def check_integrity(self, video_path: str) -> dict[str, Any]:
        issues: list[dict[str, Any]] = []
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "quiet", "-print_format", "json",
                    "-show_frames", "-show_streams", video_path,
                ],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode != 0:
                return {"issues": issues, "passed": False, "total_frames": 0}

            data = json.loads(result.stdout)

            black_frames = data.get("black_frames", [])
            for bf in black_frames:
                issues.append({
                    "type": "black_frame",
                    "start": bf.get("start", 0),
                    "end": bf.get("end", 0),
                })

            frozen_frames = data.get("frozen_frames", [])
            for ff in frozen_frames:
                issues.append({
                    "type": "frozen_frame",
                    "start": ff.get("start", 0),
                    "end": ff.get("end", 0),
                })

            total_frames = 0
            streams = data.get("streams", [])
            for stream in streams:
                if stream.get("codec_type") == "video":
                    nb = stream.get("nb_frames")
                    if nb is not None:
                        total_frames = int(nb)
                    break

            return {
                "issues": issues,
                "passed": len(issues) == 0,
                "total_frames": total_frames,
            }
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            return {"issues": [{"type": "error", "detail": "Failed to probe video"}], "passed": False, "total_frames": 0}

    def check_frames(self, video_path: str) -> dict[str, Any]:
        issues: list[dict[str, Any]] = []
        try:
            result = subprocess.run(
                [
                    "ffmpeg", "-i", video_path,
                    "-vf", "freezedetect=f=0.001:d=2,metadata=mode=print:key=lavfi.freezedetect.freezed_start",
                    "-f", "null", "-",
                ],
                capture_output=True, text=True, timeout=120,
            )
            stderr = result.stderr
            for line in stderr.splitlines():
                if "freeze_start" in line:
                    issues.append({
                        "type": "frame_freeze",
                        "detail": line.strip(),
                    })
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return {
            "issues": issues,
            "passed": len(issues) == 0,
        }

    def check_mixed_engine(self, video_path: str) -> dict[str, Any]:
        """Run L0 mixed-engine review with bounded retry on infrastructure failure.

        Retries on:
          - Exception raised by L0 engine (transient subprocess/IO errors)
          - Infrastructure failure: no frames sampled despite video having frames

        Does NOT retry on genuine quality issues (blank frames, palette drift, etc.).

        Exposes structured retry metadata in result dict when retries occurred.
        """
        for attempt in range(self.max_retries + 1):
            try:
                result = self._l0.run(video_path)
            except Exception:
                if attempt < self.max_retries:
                    continue
                raise

            # Retry on infrastructure failure only: frames exist but none sampled
            if (
                result.get("sampled_frames", 0) == 0
                and result.get("total_frames", 0) > 0
            ):
                if attempt < self.max_retries:
                    continue

            if attempt > 0:
                result["retry_attempts"] = attempt
                result["retry_limit"] = self.max_retries
            return result

        # Unreachable -- either returned above or raised
        raise RuntimeError("L0 mixed-engine review failed")  # pragma: no cover

    def check_layout_overlap(
        self,
        elements: list[dict[str, Any]],
        viewport: tuple[int, int] = (1920, 1080),
    ) -> dict[str, Any]:
        """Run L2 layout-overlap gate standalone.

        Args:
            elements: List of element dicts with ``x``, ``y``, ``width``, ``height``.
            viewport: ``(width, height)`` of canvas.

        Returns:
            Dict with ``issues`` and ``passed`` keys.
        """
        return self._overlap_gate.run(elements, viewport)

    @staticmethod
    def evaluate_l0_policy(result: dict[str, Any]) -> str:
        """Evaluate L0 issues against severity-based gate policy.

        Policy:
            - 0 issues                              → "pass"
            - only "low" severity issues             → "warn"
            - any "medium" severity issues           → "warn"
            - any "high" severity issues             → "fail"

        Returns:
            One of "pass", "warn", "fail".
        """
        issues = result.get("issues", [])
        if not issues:
            return "pass"
        severities = {i.get("severity", "low") for i in issues}
        if "high" in severities:
            return "fail"
        if "medium" in severities:
            return "warn"
        return "warn"  # low only

    def aggregate_review(
        self, video_path: str, input_props: dict | None = None
    ) -> dict[str, Any]:
        report: dict[str, Any] = {
            "video_path": video_path,
            "levels": {},
        }

        l0_result = self.check_mixed_engine(video_path)
        report["levels"]["l0_mixed_engine"] = l0_result

        l1_result = self.check_integrity(video_path)
        report["levels"]["l1_integrity"] = l1_result

        if not l1_result.get("passed", False):
            report["passed"] = False
            report["gate_blocked"] = "l1_integrity"
            report["levels"]["l2_frames"] = {"issues": [], "passed": False, "skipped": True}
            report["levels"]["l3_smoothness"] = {"issues": [], "passed": False, "skipped": True}
            report["levels"]["l4_transitions"] = {"issues": [], "passed": False, "skipped": True}
            report["levels"]["l5_consistency"] = {"issues": [], "passed": False, "skipped": True}
            return report

        l2_result = self.check_frames(video_path)
        report["levels"]["l2_frames"] = l2_result

        if not l2_result.get("passed", False):
            report["passed"] = False
            report["gate_blocked"] = "l2_frames"
            report["levels"]["l3_smoothness"] = {"issues": [], "passed": False, "skipped": True}
            report["levels"]["l4_transitions"] = {"issues": [], "passed": False, "skipped": True}
            report["levels"]["l5_consistency"] = {"issues": [], "passed": False, "skipped": True}
            return report

        # L2b: layout overlap gate (no-video-path gate; passes if no element metadata)
        elements = (input_props or {}).get("elements", [])
        layout_result = self._overlap_gate.run(elements)
        report["levels"]["l2_layout_overlap"] = layout_result

        l3_result = self._l3.run(video_path, input_props)
        report["levels"]["l3_smoothness"] = l3_result

        l4_result = self._l4.run(video_path, input_props)
        report["levels"]["l4_transitions"] = l4_result

        l5_result = self._l5.run(video_path, input_props)
        report["levels"]["l5_consistency"] = l5_result

        all_passed = all(
            level.get("passed", False)
            for level in report["levels"].values()
        )
        report["passed"] = all_passed

        return report


def generate_video_report(
    video_path: str,
    content_hash: str = "",
    engine_mix: list[str] | None = None,
    render_format: dict[str, Any] | None = None,
    l0_result: dict[str, Any] | None = None,
    l1_result: dict[str, Any] | None = None,
    l0_status: str = "pass",
) -> dict[str, Any]:
    """Build structured JSON artifact for final assembled video.

    Includes content hash, engine mix, render format, L0 summary, L1 summary.
    Deterministic output path derived from video_path (<video>.report.json).

    Args:
        video_path: Path to final MP4.
        content_hash: sha256 hash of video definition (16-char hex).
        engine_mix: List of engines used (remotion, manim, animotion).
        render_format: Dict with fps, width, height, pixel_format, etc.
        l0_result: Raw L0 review result dict (issues, sampled_frames, ...).
        l1_result: Raw L1 integrity result dict (issues, total_frames, ...).
        l0_status: Pre-computed L0 policy status ("pass", "warn", "fail").

    Returns:
        Report dict suitable for JSON serialization.
    """
    # ── Severity counts for L0 ────────────────────────────────────────────
    l0_issues = (l0_result or {}).get("issues", [])
    l0_severity_counts: dict[str, int] = {"high": 0, "medium": 0, "low": 0}
    for iss in l0_issues:
        sev = iss.get("severity", "low")
        l0_severity_counts[sev] = l0_severity_counts.get(sev, 0) + 1

    # ── L1 summary ────────────────────────────────────────────────────────
    l1_data = l1_result or {}
    l1_issues = l1_data.get("issues", [])

    # ── Render format fallback ─────────────────────────────────────────────
    fmt = render_format or {
        "fps": 30,
        "width": 1920,
        "height": 1080,
        "pixel_format": "yuv420p",
        "video_codec": "h264",
        "audio_codec": "aac",
    }

    report: dict[str, Any] = {
        "artifact": "videoforge-video-report",
        "version": 1,
        "video_path": str(Path(video_path).resolve()),
        "report_timestamp": datetime.now(timezone.utc).isoformat(),
        "content_hash": content_hash,
        "engine_mix": sorted(set(engine_mix or ["remotion"])),
        "render_format": {
            "fps": fmt.get("fps", 30),
            "width": fmt.get("width", 1920),
            "height": fmt.get("height", 1080),
            "pixel_format": fmt.get("pixel_format", "yuv420p"),
            "video_codec": fmt.get("video_codec", "h264"),
            "audio_codec": fmt.get("audio_codec", "aac"),
        },
        "l0_summary": {
            "status": l0_status,
            "passed": l0_status == "pass",
            "total_issues": len(l0_issues),
            "severity_counts": l0_severity_counts,
            "sampled_frames": (l0_result or {}).get("sampled_frames", 0),
            "total_frames": (l0_result or {}).get("total_frames", 0),
            "duration_seconds": (l0_result or {}).get("duration_seconds", 0.0),
            "issues": l0_issues,
        },
        "l1_summary": {
            "passed": l1_data.get("passed", False),
            "total_frames": l1_data.get("total_frames", 0),
            "total_issues": len(l1_issues),
            "issues": l1_issues,
        },
    }

    return report


def write_video_report(
    report: dict[str, Any],
    video_path: str,
) -> str:
    """Write report JSON to <video_path>.report.json.

    Returns path to written report file.
    """
    report_path = Path(video_path).with_suffix(".mp4.report.json")
    report_path.write_text(json.dumps(report, indent=2, default=str))
    return str(report_path.resolve())
