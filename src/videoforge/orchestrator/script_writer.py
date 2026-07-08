from __future__ import annotations

from typing import Any

SCENE_TYPES = ["title", "code", "diff", "bullet", "image", "comparison", "diagram", "outro"]


class ScriptWriter:
    def write_script(self, content: dict[str, Any], tone: str = "professional") -> dict[str, Any]:
        title = content.get("title", "Untitled")
        body = content.get("body", "")
        diff = content.get("diff", "")
        files = content.get("files", [])

        script_parts: list[str] = []
        scenes: list[dict[str, Any]] = []

        scene_idx = 0

        script_parts.append(f"Welcome to this walkthrough of {title}.")
        scenes.append({
            "title": "Introduction",
            "text": script_parts[-1],
            "scene_type": "title",
            "estimated_duration_seconds": 4.0,
        })
        scene_idx += 1

        if files:
            file_summary = ", ".join(f.get("path", f"file {i+1}") for i, f in enumerate(files[:3]))
            script_parts.append(
                f"This change touches {len(files)} file(s): {file_summary}."
            )
            scenes.append({
                "title": "Files Changed",
                "text": script_parts[-1],
                "scene_type": "bullet",
                "estimated_duration_seconds": 3.0,
            })
            scene_idx += 1

        if diff:
            script_parts.append("Let's look at the key code changes.")
            scenes.append({
                "title": "Code Changes",
                "text": script_parts[-1],
                "scene_type": "code",
                "estimated_duration_seconds": 6.0,
            })
            scene_idx += 1

        if body:
            sentences = [s.strip() for s in body.replace("\n", " ").split(".") if s.strip()]
            for sentence in sentences[:3]:
                script_parts.append(sentence + ".")
                scenes.append({
                    "title": f"Detail {scene_idx}",
                    "text": sentence + ".",
                    "scene_type": "bullet",
                    "estimated_duration_seconds": max(2.0, len(sentence.split()) / 2.8),
                })
                scene_idx += 1

        script_parts.append(
            f"That wraps up this review of {title}. Thanks for watching!"
        )
        scenes.append({
            "title": "Outro",
            "text": script_parts[-1],
            "scene_type": "outro",
            "estimated_duration_seconds": 4.0,
        })

        script_text = " ".join(script_parts)
        estimated_duration = sum(s["estimated_duration_seconds"] for s in scenes)

        return {
            "script_text": script_text,
            "scenes": scenes,
            "estimated_duration": int(estimated_duration),
        }
