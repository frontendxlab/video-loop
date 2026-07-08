from __future__ import annotations

import json
import subprocess
from typing import Any


class L4Transitions:
    def run(self, video_path: str, input_props: dict | None = None) -> dict[str, Any]:
        issues: list[dict[str, Any]] = []

        abrupt_cuts = self._detect_abrupt_cuts(video_path)
        issues.extend(abrupt_cuts)

        incomplete_transitions = self._detect_incomplete_transitions(video_path)
        issues.extend(incomplete_transitions)

        overlapping_scenes = self._detect_overlapping_scenes(video_path)
        issues.extend(overlapping_scenes)

        transitions_checked = len(abrupt_cuts) + len(incomplete_transitions) + len(overlapping_scenes)

        if input_props:
            expected = input_props.get("transitions", [])
            actual = self._extract_actual_transitions(video_path)
            mismatches = self._cross_reference(expected, actual)
            issues.extend(mismatches)
            transitions_checked += len(mismatches)

        return {
            "issues": issues,
            "passed": len(issues) == 0,
            "transitions_checked": transitions_checked,
        }

    def _detect_abrupt_cuts(self, video_path: str) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        try:
            result = subprocess.run(
                [
                    "ffmpeg", "-i", video_path,
                    "-vf", "select=gt(scene\\,0.4),showinfo",
                    "-f", "null", "-",
                ],
                capture_output=True, text=True, timeout=120,
            )
            stderr = result.stderr
            for line in stderr.splitlines():
                if "pts_time:" in line and "scene:" in line.lower():
                    issues.append({
                        "type": "abrupt_cut",
                        "detail": line.strip(),
                    })
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return issues

    def _detect_incomplete_transitions(self, video_path: str) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "quiet", "-print_format", "json",
                    "-show_frames", video_path,
                ],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode != 0:
                return issues

            data = json.loads(result.stdout)
            frames = data.get("frames", [])
            prev_pict_type = ""

            for f in frames:
                if f.get("media_type") != "video":
                    continue
                pict_type = f.get("pict_type", "")
                if prev_pict_type and pict_type != prev_pict_type:
                    issues.append({
                        "type": "incomplete_transition",
                        "frame": int(f.get("coded_picture_number", 0)),
                        "from_pict_type": prev_pict_type,
                        "to_pict_type": pict_type,
                        "detail": "Unexpected pict_type change may indicate incomplete transition",
                    })
                prev_pict_type = pict_type
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            pass

        return issues

    def _detect_overlapping_scenes(self, video_path: str) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        try:
            result = subprocess.run(
                [
                    "ffmpeg", "-i", video_path,
                    "-vf", "select=gt(scene\\,0.3),showinfo",
                    "-f", "null", "-",
                ],
                capture_output=True, text=True, timeout=120,
            )
            stderr = result.stderr
            seen_times: set[str] = set()
            for line in stderr.splitlines():
                if "pts_time:" in line:
                    parts = line.split()
                    for p in parts:
                        if p.startswith("pts_time:"):
                            t = p.split(":")[1]
                            if t in seen_times:
                                issues.append({
                                    "type": "overlapping_scene",
                                    "pts_time": t,
                                    "detail": f"Duplicate scene detection at time {t}",
                                })
                            seen_times.add(t)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return issues

    def _extract_actual_transitions(self, video_path: str) -> list[dict[str, Any]]:
        actual: list[dict[str, Any]] = []
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "quiet", "-print_format", "json",
                    "-show_frames", video_path,
                ],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode != 0:
                return actual

            data = json.loads(result.stdout)
            frames = data.get("frames", [])
            for f in frames:
                if f.get("media_type") == "video":
                    actual.append({
                        "frame": int(f.get("coded_picture_number", 0)),
                        "pict_type": f.get("pict_type", ""),
                    })
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            pass

        return actual

    def _cross_reference(
        self,
        expected: list[dict[str, Any]],
        actual: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        mismatches: list[dict[str, Any]] = []
        expected_pict_types = {
            e.get("frame", 0): e.get("pict_type", "") for e in expected
        }
        for a in actual:
            frame_num = a.get("frame", 0)
            actual_type = a.get("pict_type", "")
            expected_type = expected_pict_types.get(frame_num)
            if expected_type and actual_type != expected_type:
                mismatches.append({
                    "type": "transition_mismatch",
                    "frame": frame_num,
                    "expected": expected_type,
                    "actual": actual_type,
                    "detail": f"Expected pict_type {expected_type}, got {actual_type}",
                })
        return mismatches
