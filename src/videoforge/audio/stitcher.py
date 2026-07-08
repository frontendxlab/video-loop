from __future__ import annotations

from pathlib import Path


class Stitcher:
    def stitch_wavs(self, wav_paths: list[Path], output_path: Path) -> str:
        import subprocess

        inputs = []
        filter_parts = []
        for i, wav_path in enumerate(wav_paths):
            inputs.extend(["-i", str(wav_path)])
            filter_parts.append(f"[{i}:0]")
        filter_expr = "".join(
            filter_parts
        ) + f"concat={len(wav_paths)}:v=0:a=1[out]"
        cmd = [
            "ffmpeg",
            "-y",
            *inputs,
            "-filter_complex", filter_expr,
            "-map", "[out]",
            str(output_path),
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return str(output_path)
