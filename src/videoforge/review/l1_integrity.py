from __future__ import annotations

import json
import subprocess


class L1Integrity:
    def run(self, video_path: str) -> dict:
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_streams",
            video_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)

        total_frames = 0
        streams = data.get("streams", [])
        if streams:
            nb_frames = streams[0].get("nb_frames")
            if nb_frames is not None:
                total_frames = int(nb_frames)

        detect_cmd = [
            "ffmpeg", "-i", video_path,
            "-vf", "blackdetect=d=2:pic_th=0.98,freezedetect=d=2:n=0.001",
            "-f", "null", "-",
        ]
        detect_result = subprocess.run(detect_cmd, capture_output=True, text=True)
        detect_text = detect_result.stderr

        issues: list[dict] = []
        lines = detect_text.splitlines()
        for line in lines:
            if "blackdetect" in line and "black_start" in line:
                pass

        import re
        black_starts = re.findall(r"black_start:([\d.]+)", detect_text)
        black_ends = re.findall(r"black_end:([\d.]+)", detect_text)
        for s, e in zip(black_starts, black_ends):
            issues.append({
                "type": "black",
                "start": int(float(s)),
                "end": int(float(e)),
            })

        frozen_starts = re.findall(r"freeze_start:([\d.]+)", detect_text)
        frozen_ends = re.findall(r"freeze_end:([\d.]+)", detect_text)
        for s, e in zip(frozen_starts, frozen_ends):
            issues.append({
                "type": "frozen",
                "start": int(float(s)),
                "end": int(float(e)),
            })

        return {
            "total_frames": total_frames,
            "issues": issues,
            "passed": len(issues) == 0,
        }
