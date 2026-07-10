from __future__ import annotations

from typing import Any

from videoforge.orchestrator.recipe_payload import build_recipe_payload
from videoforge.orchestrator.recipe_scene_plan import get_recipe_scene_plan

SCENE_TYPES = ["title", "code", "diff", "bullet", "image", "comparison", "diagram", "outro"]

# Deterministic rules: (trigger_path, match_value) → showcase scene kind.
# Each rule checks content field at dot-path for exact match or truthiness.
# The recipe_id column (index 5) links to config/recipe_registry.json for
# entrance/exit/engine_hint/recipe_payload enrichment.
SHOWCASE_RULES: list[tuple[str, Any, str, str, float, str]] = [
    # (dot_path, expected_value, scene_type, label, duration_seconds, recipe_id)
    ("showcase.kind", "hero-intro", "title", "Hero Intro", 6.0, "hero-intro"),
    ("showcase.kind", "screenflow", "comparison", "Screenflow Demo", 8.0, "screenflow"),
    ("showcase.kind", "svg-morph", "svg-morph", "SVG Morph", 5.0, "svg-morph"),
    ("showcase.kind", "kinetic-text", "kinetic-text", "Kinetic Typography", 5.0, "kinetic-text"),
    ("showcase.kind", "canvas-composite", "canvas-composite", "Canvas Composite", 5.0, "canvas-composite"),
    ("showcase.kind", "real-estate", "real-estate", "Real Estate Showcase", 7.0, "real-estate"),
    ("showcase.kind", "promo", "promo", "Promo", 6.0, "launch-promo"),
    ("showcase.kind", "three-scene", "three-scene", "3D Scene", 7.0, "three-scene"),
    ("showcase.kind", "trajectory-timeline", "timeline", "Trajectory Timeline", 7.0, "trajectory-timeline"),
    ("showcase.kind", "3d-ranking", "chart", "3D Ranking", 6.0, "3d-ranking"),
    ("showcase.kind", "audio-reactive", "title", "Audio Reactive", 6.0, "audio-reactive"),
    ("showcase.kind", "audio-spectrum", "audio-reactive", "Audio Spectrum", 6.0, "audio-spectrum"),
    ("showcase.kind", "dual-chart", "chart", "Dual Chart", 7.0, "dual-chart"),
    ("showcase.kind", "document-highlight", "title", "Document Highlight", 5.0, "document-highlight"),
    ("showcase.kind", "overlay-cta", "outro", "Overlay CTA", 4.0, "overlay-cta"),
    ("showcase.kind", "device-rise", "three-scene", "Device Rise", 7.0, "device-rise"),
]


def _get_nested(content: dict[str, Any], path: str) -> Any:
    """Resolve a dot-separated path into a nested dict."""
    parts = path.split(".")
    val: Any = content
    for p in parts:
        if isinstance(val, dict):
            val = val.get(p)
        else:
            return None
    return val


def _detect_showcase_pattern(content: dict[str, Any]) -> dict[str, Any] | None:
    """Deterministic rule-based detection of showcase patterns in content.

    Returns scene dict with scene_type, title, text, duration, and recipe
    enrichment (entrance, exit, engine_hint, recipe_payload) if match found.
    Enrichment comes from config/recipe_registry.json via build_recipe_payload.
    """
    for path, expected, scene_type, label, duration, recipe_id in SHOWCASE_RULES:
        val = _get_nested(content, path)
        if val is not None and val == expected:
            scene: dict[str, Any] = {
                "title": label,
                "text": content.get("body", "")[:200] or f"Showcasing {label}",
                "scene_type": scene_type,
                "estimated_duration_seconds": duration,
                "recipe_id": recipe_id,
            }
            # Enrich with recipe metadata from registry (entrance, exit, engine_hint, payload)
            enrichment = build_recipe_payload(content, recipe_id)
            scene.update(enrichment)
            return scene
    return None


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

        # ── Showcase scene insertion (rule-based, deterministic) ──────
        #   Multi-scene recipes expand into 3-4 scenes (intro, body, outro).
        #   Single-scene recipes follow the existing pattern.
        #   Both paths carry recipe enrichment (engine_hint, entrance/exit_,
        #   recipe_payload, recipe_id) for downstream routing.
        showcase_scene = _detect_showcase_pattern(content)
        if showcase_scene is not None:
            recipe_id = showcase_scene.get("recipe_id")
            plan = get_recipe_scene_plan(recipe_id, content) if recipe_id else None

            if plan is not None:
                # ── Multi-scene expansion ─────────────────────────────
                recipe_enrichment = build_recipe_payload(content, recipe_id)
                for i, ps in enumerate(plan):
                    script_parts.append(
                        f"Next, {ps['scene_type'].replace('-', ' ')} "
                        f"highlight: {ps['text']}."
                    )
                    scene_entry: dict[str, Any] = {
                        "title": ps["title"],
                        "text": script_parts[-1],
                        "scene_type": ps["scene_type"],
                        "estimated_duration_seconds": ps["estimated_duration_seconds"],
                        "recipe_id": recipe_id,
                        "engine_hint": recipe_enrichment.get("engine_hint"),
                        "entrance": ps.get("entrance"),
                        "exit_": ps.get("exit_"),
                        "recipe_payload": recipe_enrichment.get("recipe_payload", {}),
                        "scene_index": i,
                        "total_scenes": len(plan),
                    }
                    scenes.append(
                        {k: v for k, v in scene_entry.items() if v is not None}
                    )
                    scene_idx += 1
            else:
                # ── Single-scene fallback (existing behavior) ─────────
                script_parts.append(
                    f"Next, {showcase_scene['scene_type'].replace('-', ' ')} "
                    f"highlight: {showcase_scene['text'][:80]}."
                )
                scene_entry = {
                    "title": showcase_scene["title"],
                    "text": script_parts[-1],
                    "scene_type": showcase_scene["scene_type"],
                    "estimated_duration_seconds": showcase_scene["estimated_duration_seconds"],
                    "recipe_id": showcase_scene.get("recipe_id"),
                    "engine_hint": showcase_scene.get("engine_hint"),
                    "entrance": showcase_scene.get("entrance"),
                    "exit_": showcase_scene.get("exit_"),
                    "recipe_payload": showcase_scene.get("recipe_payload", {}),
                }
                scenes.append(
                    {k: v for k, v in scene_entry.items() if v is not None}
                )
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
