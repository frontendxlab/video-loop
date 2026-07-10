from __future__ import annotations

from typing import Any

from videoforge.orchestrator.recipe_payload import build_recipe_payload

TRANSITIONS = [
    "fade",
    "slide-left",
    "slide-right",
    "zoom",
    "wipe",
    "dissolve",
    "flip",
    "scale",
    "rotate",
    "blur",
    "morph",
    "glitch",
    "warp",
]

# Showcase scene types get bespoke entrance transitions by rule.
SHOWCASE_ENTRANCE: dict[str, str] = {
    "svg-morph": "morph",
    "kinetic-text": "scale",
    "canvas-composite": "glitch",
    "real-estate": "slide-right",
    "promo": "zoom",
    "three-scene": "flip",
    "hero-intro": "zoom",
    "screenflow": "slide-right",
    "trajectory-timeline": "wipe",
}


class ScenePlanner:
    def plan_scenes(self, script: dict[str, Any], audio_metadata: list[dict[str, Any]]) -> dict[str, Any]:
        script_scenes = script.get("scenes", [])
        fps = 30
        resolution = [1920, 1080]
        video_type = script.get("video_type", "PR_WALKTHROUGH")

        planned_scenes: list[dict[str, Any]] = []
        current_frame = 0

        for i, scene in enumerate(script_scenes):
            duration_seconds = scene.get("estimated_duration_seconds", 4.0)
            duration_frames = int(duration_seconds * fps)

            # Recipe-enriched scenes carry entrance/exit from recipe registry.
            # Prefer recipe entrance over SHOWCASE_ENTRANCE lookup.
            entrance_override = scene.get("entrance")
            exit_override = scene.get("exit_")
            transition_type = self._select_transition(
                i, scene.get("scene_type", ""),
                entrance_override=entrance_override,
            )
            transit_out = exit_override or self._select_next_transition(i, script_scenes)

            base: dict[str, Any] = {
                "id": i + 1,
                "type": scene.get("scene_type", "title"),
                "duration_seconds": duration_seconds,
                "duration_frames": duration_frames,
                "start_frame": current_frame,
                "title": scene.get("title", ""),
                "text": scene.get("text", ""),
                "transition_in": transition_type,
                "transition_out": transit_out,
            }

            # Carry recipe enrichment through so downstream (compose_props,
            # ir_adapter) can build recipe-aware SceneNode payloads.
            if scene.get("recipe_id"):
                base["recipe_id"] = scene["recipe_id"]
                base["engine_hint"] = scene.get("engine_hint", "remotion")
                base["recipe_payload"] = scene.get("recipe_payload", {})
                # Use recipe-provided entrance (already applied above) and exit
                base["transition_in"] = transition_type
                base["transition_out"] = transit_out

            planned_scenes.append(base)

            current_frame += duration_frames

        if not planned_scenes:
            planned_scenes.append({
                "id": 1,
                "type": "title",
                "duration_seconds": 4.0,
                "duration_frames": 4 * fps,
                "start_frame": 0,
                "title": script.get("title", "Video"),
                "text": "",
                "transition_in": "fade",
                "transition_out": "none",
            })

        return {
            "version": 1,
            "video_type": video_type,
            "fps": fps,
            "resolution": resolution,
            "scenes": planned_scenes,
        }

    # ── Template-based scene graph generation ─────────────────────

    def plan_from_template(
        self,
        template_id: str,
        content: dict[str, Any],
        audio_metadata: list[dict[str, Any]] | None = None,
        **overrides: Any,
    ) -> dict[str, Any]:
        """Generate scene graph directly from a template.

        Unlike plan_scenes() which consumes script-writer output, this
        method works directly with a template from the registry —
        expanding multi-scene plans, assigning durations, transitions,
        and engine hints from the template definition.

        Args:
            template_id: Template identifier from template_registry.
            content: User content dict (showcase fields, body, etc).
            audio_metadata: Optional audio timing data (unused, for API compat).
            **overrides: Override template defaults:
                fps, resolution, duration_seconds, entrance, exit_.

        Returns:
            Planned scene dict with scenes[], fps, resolution.
        """
        from videoforge.orchestrator.template_registry import get_template

        template = get_template(template_id)
        if template is None:
            raise ValueError(f"Unknown template: {template_id}")

        enrichment = build_recipe_payload(content, template_id)

        plan = template.expand(content)

        fps = overrides.get("fps", 30)
        resolution = overrides.get("resolution", [1920, 1080])

        planned_scenes: list[dict[str, Any]] = []
        current_frame = 0

        if plan is not None:
            # ── Multi-scene expansion ──────────────────────────────
            for i, ps in enumerate(plan):
                duration_seconds = ps.get("estimated_duration_seconds", 4.0)
                duration_frames = int(duration_seconds * fps)
                scene_entry: dict[str, Any] = {
                    "id": len(planned_scenes) + 1,
                    "type": ps["scene_type"],
                    "duration_seconds": duration_seconds,
                    "duration_frames": duration_frames,
                    "start_frame": current_frame,
                    "title": ps["title"],
                    "text": ps["text"],
                    "transition_in": (
                        ps.get("entrance")
                        or enrichment.get("entrance")
                        or "fade"
                    ),
                    "transition_out": (
                        ps.get("exit_")
                        or enrichment.get("exit_")
                        or "none"
                    ),
                    "template_id": template_id,
                    "engine_hint": enrichment.get(
                        "engine_hint", template.preferred_engine
                    ),
                    "recipe_payload": enrichment.get("recipe_payload", {}),
                    "scene_index": i,
                    "total_scenes": len(plan),
                }
                planned_scenes.append(scene_entry)
                current_frame += duration_frames
        else:
            # ── Single-scene fallback ──────────────────────────────
            duration_seconds = overrides.get("duration_seconds", 6.0)
            duration_frames = int(duration_seconds * fps)
            scene_entry: dict[str, Any] = {
                "id": 1,
                "type": template.scene_kind,
                "duration_seconds": duration_seconds,
                "duration_frames": duration_frames,
                "start_frame": 0,
                "title": template.name,
                "text": (
                    content.get("body", "")[:200]
                    or f"Showcasing {template.name}"
                ),
                "transition_in": (
                    overrides.get("entrance")
                    or enrichment.get("entrance")
                    or template.entrance
                ),
                "transition_out": (
                    overrides.get("exit_")
                    or enrichment.get("exit_")
                    or template.exit
                ),
                "template_id": template_id,
                "engine_hint": enrichment.get(
                    "engine_hint", template.preferred_engine
                ),
                "recipe_payload": enrichment.get("recipe_payload", {}),
            }
            planned_scenes.append(scene_entry)

        return {
            "version": 1,
            "video_type": "TEMPLATE",
            "fps": fps,
            "resolution": resolution,
            "scenes": planned_scenes,
        }

    def plan_from_templates(
        self,
        template_map: dict[str, str],
        content: dict[str, Any],
        audio_metadata: list[dict[str, Any]] | None = None,
        **overrides: Any,
    ) -> dict[str, Any]:
        """Combine multiple templates into a single cohesive video plan.

        Each template in the map generates its scene graph. All scenes
        are concatenated with contiguous frame numbering and section
        labels for downstream assembly.

        Args:
            template_map: Dict mapping section names to template ids.
                Example: {"intro": "hero-intro", "body": "screenflow",
                          "outro": "overlay-cta"}.
            content: User content dict (shared across all templates).
            audio_metadata: Optional audio timing data.
            **overrides: Global overrides (fps, resolution) or
                per-section overrides nested by section name:
                plan_from_templates({...}, content,
                                    fps=30,
                                    body={"duration_seconds": 8.0})

        Returns:
            Planned scene dict with combined scenes[] from all templates.
        """
        all_scenes: list[dict[str, Any]] = []
        fps = overrides.get("fps", 30)
        resolution = overrides.get("resolution", [1920, 1080])
        current_frame = 0

        for section_name, template_id in template_map.items():
            section_overrides = overrides.get(section_name, {})
            section = self.plan_from_template(
                template_id,
                content,
                audio_metadata,
                fps=fps,
                resolution=resolution,
                **section_overrides,
            )
            for s in section["scenes"]:
                s["section"] = section_name
                s["start_frame"] = current_frame
                s["id"] = len(all_scenes) + 1
                current_frame += s["duration_frames"]
                all_scenes.append(s)

        return {
            "version": 1,
            "video_type": "MULTI_TEMPLATE",
            "fps": fps,
            "resolution": resolution,
            "scenes": all_scenes,
        }

    def _select_transition(self, index: int, scene_type: str,
                           entrance_override: str | None = None) -> str:
        # Recipe-driven entrance takes highest priority
        if index > 0 and entrance_override:
            return entrance_override if entrance_override in TRANSITIONS or entrance_override in (
                "slide_out_left", "fade_out", "blur_out", "count_up",
                "device_rise_in", "device_fall_out", "axes_draw",
                "stars_fade_in", "zoom_out_deep",
                "fade_in_3d", "fade_out_3d", "slide_in_right",
                "morph_out", "path_draw",
            ) else "fade"
        # Showcase types get a bespoke entrance transition second
        if index > 0 and scene_type in SHOWCASE_ENTRANCE:
            return SHOWCASE_ENTRANCE[scene_type]
        return TRANSITIONS[index % (len(TRANSITIONS) - 2) + 1] if index > 0 else "fade"

    def _select_next_transition(self, index: int, scenes: list[dict[str, Any]]) -> str:
        next_idx = index + 1
        if next_idx >= len(scenes):
            return "none"
        t = TRANSITIONS[(next_idx) % (len(TRANSITIONS) - 2) + 1]
        return t
