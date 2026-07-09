from __future__ import annotations

import json
import subprocess
from typing import Any

from videoforge.review.l0_mixed_engine import L0MixedEngineReview
from videoforge.review.l3_smoothness import L3Smoothness
from videoforge.review.l4_transitions import L4Transitions
from videoforge.review.l5_consistency import L5Consistency


class FrameReviewer:
    def __init__(self) -> None:
        self._l0 = L0MixedEngineReview()
        self._l3 = L3Smoothness()
        self._l4 = L4Transitions()
        self._l5 = L5Consistency()

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
        """Run L0 mixed-engine review gate standalone.

        Convenience method for pipeline callers that only need the frame-sampled
        visual consistency check without running the full L1-L5 gauntlet.
        """
        return self._l0.run(video_path)

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

        l0_result = self._l0.run(video_path)
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
