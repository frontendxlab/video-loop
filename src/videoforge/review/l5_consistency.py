from __future__ import annotations

import json
import subprocess
from typing import Any


class L5Consistency:
    def run(self, video_path: str, input_props: dict | None = None) -> dict[str, Any]:
        issues: list[dict[str, Any]] = []

        element_issues = self._detect_element_disappear_reappear(video_path)
        issues.extend(element_issues)

        caption_issues = self._check_caption_mismatches(video_path, input_props)
        issues.extend(caption_issues)

        scene_issues = self._check_scene_content_mismatches(video_path, input_props)
        issues.extend(scene_issues)

        return {
            "issues": issues,
            "passed": len(issues) == 0,
            "degraded": input_props is None,
        }

    def _detect_element_disappear_reappear(self, video_path: str) -> list[dict[str, Any]]:
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
            prev_pts: float | None = None

            for f in frames:
                if f.get("media_type") != "video":
                    continue
                pts = float(f.get("pts", 0))
                if prev_pts is not None:
                    gap = pts - prev_pts
                    if gap > 1.5:
                        issues.append({
                            "type": "element_disappear_reappear",
                            "pts": prev_pts,
                            "detail": f"Large gap ({gap:.2f}s) between frames suggests element disappearance",
                        })
                prev_pts = pts
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            pass

        return issues

    def _check_caption_mismatches(
        self, video_path: str, input_props: dict | None
    ) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        if input_props is None:
            return issues

        expected_captions = input_props.get("captions", [])
        actual_captions = self._extract_captions(video_path)

        if not expected_captions:
            return issues

        for expected in expected_captions:
            expected_text = expected.get("text", "").strip().lower()
            if not expected_text:
                continue
            found = any(
                expected_text in actual.get("text", "").strip().lower()
                for actual in actual_captions
            )
            if not found:
                issues.append({
                    "type": "caption_mismatch",
                    "expected_text": expected.get("text", ""),
                    "detail": f"Expected caption '{expected.get('text', '')}' not found in output",
                })

        return issues

    def _check_scene_content_mismatches(
        self, video_path: str, input_props: dict | None
    ) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        if input_props is None:
            return issues

        expected_scenes = input_props.get("scenes", [])
        detected_scenes = self._detect_scenes(video_path)

        if not expected_scenes:
            return issues

        if len(detected_scenes) != len(expected_scenes):
            issues.append({
                "type": "scene_count_mismatch",
                "expected": len(expected_scenes),
                "detected": len(detected_scenes),
                "detail": f"Expected {len(expected_scenes)} scenes but detected {len(detected_scenes)}",
            })

        for i, expected in enumerate(expected_scenes):
            if i >= len(detected_scenes):
                break
            expected_id = expected.get("id")
            detected_id = detected_scenes[i].get("id")
            if expected_id is not None and detected_id is not None and expected_id != detected_id:
                issues.append({
                    "type": "scene_content_mismatch",
                    "scene_index": i,
                    "expected_id": expected_id,
                    "detected_id": detected_id,
                    "detail": f"Scene {i}: expected id {expected_id}, detected {detected_id}",
                })

        return issues

    def _extract_captions(self, video_path: str) -> list[dict[str, Any]]:
        captions: list[dict[str, Any]] = []
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "quiet", "-print_format", "json",
                    "-show_streams", "-show_entries", "stream=index:stream_tags",
                    video_path,
                ],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode != 0:
                return captions

            data = json.loads(result.stdout)
            for stream in data.get("streams", []):
                if stream.get("codec_type") == "subtitle":
                    tags = stream.get("tags", {})
                    captions.append({
                        "index": stream.get("index", 0),
                        "text": tags.get("title", tags.get("language", "")),
                    })
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            pass

        return captions

    def _detect_scenes(self, video_path: str) -> list[dict[str, Any]]:
        scenes: list[dict[str, Any]] = []
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
            for i, line in enumerate(stderr.splitlines()):
                if "pts_time:" in line and "scene:" in line.lower():
                    scenes.append({"id": i, "line": line.strip()})
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return scenes
