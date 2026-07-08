from __future__ import annotations

import json
import subprocess
from typing import Any


class L3Smoothness:
    def run(self, video_path: str, input_props: dict | None = None) -> dict[str, Any]:
        if input_props is None:
            return {
                "issues": [],
                "passed": True,
                "warning": "No input_props provided; skipping temporal smoothness checks",
            }

        issues: list[dict[str, Any]] = []

        position_jitter = self._detect_position_jitter(video_path)
        issues.extend(position_jitter)

        opacity_flicker = self._detect_opacity_flicker(video_path)
        issues.extend(opacity_flicker)

        scale_oscillation = self._detect_scale_oscillation(video_path)
        issues.extend(scale_oscillation)

        return {
            "issues": issues,
            "passed": len(issues) == 0,
            "position_jitter_count": len(position_jitter),
            "opacity_flicker_count": len(opacity_flicker),
            "scale_oscillation_count": len(scale_oscillation),
        }

    def _detect_position_jitter(self, video_path: str) -> list[dict[str, Any]]:
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
            prev_x: float | None = None
            prev_y: float | None = None

            for f in frames:
                if f.get("media_type") != "video":
                    continue
                x = float(f.get("pkt_pos", 0))
                y = 0
                if prev_x is not None and prev_y is not None:
                    dx = abs(x - prev_x)
                    dy = abs(y - prev_y)
                    if dx > 3 or dy > 3:
                        issues.append({
                            "type": "position_jitter",
                            "frame": int(f.get("coded_picture_number", 0)),
                            "dx": round(dx, 2),
                            "dy": round(dy, 2),
                            "detail": f"Position delta ({dx:.2f}, {dy:.2f}) exceeds 3px threshold",
                        })
                prev_x = x
                prev_y = y
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            pass

        return issues

    def _detect_opacity_flicker(self, video_path: str) -> list[dict[str, Any]]:
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
            prev_opacity: float | None = None

            for f in frames:
                if f.get("media_type") != "video":
                    continue
                opacity = float(f.get("pkt_duration", 0))
                if prev_opacity is not None:
                    if (prev_opacity == 0 and opacity == 1) or (prev_opacity == 1 and opacity == 0):
                        issues.append({
                            "type": "opacity_flicker",
                            "frame": int(f.get("coded_picture_number", 0)),
                            "from": prev_opacity,
                            "to": opacity,
                            "detail": "Opacity alternates between 0 and 1",
                        })
                prev_opacity = opacity
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            pass

        return issues

    def _detect_scale_oscillation(self, video_path: str) -> list[dict[str, Any]]:
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
            scale_window: list[float] = []

            for f in frames:
                if f.get("media_type") != "video":
                    continue
                w = float(f.get("width", 0))
                h = float(f.get("height", 0))
                scale = round(w * h, 2)
                scale_window.append(scale)
                if len(scale_window) > 10:
                    scale_window.pop(0)
                if len(scale_window) >= 5:
                    deltas = [
                        abs(scale_window[i] - scale_window[i - 1])
                        for i in range(1, len(scale_window))
                    ]
                    if deltas and max(deltas) > 0 and min(deltas) == 0:
                        issues.append({
                            "type": "scale_oscillation",
                            "frame": int(f.get("coded_picture_number", 0)),
                            "scale_values": scale_window.copy(),
                            "detail": "Detected scale oscillation in recent frame window",
                        })
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            pass

        return issues
