"""Logic checker for validating scene plans and scripts."""

from __future__ import annotations

from typing import Any


class LogicChecker:
    """Validates the logical consistency of scene plans and scripts."""

    SCENE_ROLES: dict[str, str] = {
        "title": "context",
        "code": "solution",
        "diff": "solution",
        "bullet": "problem",
        "image": "context",
        "comparison": "problem",
        "diagram": "solution",
        "outro": "impact",
    }

    ALL_PHASES: list[str] = ["context", "problem", "solution", "impact"]

    def check_narrative_arc(self, scene_plan: dict) -> dict:
        """Check that the scene sequence has a complete narrative arc."""
        scenes = scene_plan.get("scenes", [])
        if not scenes:
            return {
                "phases": [],
                "missing_phases": list(self.ALL_PHASES),
                "has_complete_arc": False,
            }
        phases_found: list[str] = []
        for scene in scenes:
            role = self.SCENE_ROLES.get(scene.get("type", ""))
            if role and role not in phases_found:
                phases_found.append(role)
        missing = [p for p in self.ALL_PHASES if p not in phases_found]
        return {
            "phases": phases_found,
            "missing_phases": missing,
            "has_complete_arc": len(missing) == 0,
        }

    def check_cause_effect(self, script: str, scene_plan: dict) -> dict:
        """Check that cause/effect claims in the script are supported by scene content."""
        issues: list[str] = []
        scenes = scene_plan.get("scenes", [])

        if "because" in script.lower():
            scene_text = " ".join(
                str(scene.get(k, "") or "")
                for scene in scenes
                for k in ("code", "title", "text", "diff")
            ).lower()

            idx = script.lower().find("because")
            after = script[idx:]
            terms = [
                w.strip(".,!?;:()'\"")
                for w in after.split()
                if len(w.strip(".,!?;:()'\"")) > 3
            ]

            matches = sum(term in scene_text for term in terms)
            if matches < 1:
                issues.append("Cause/effect claim lacks supporting scene content")
            return {"issues": issues, "total_claims_checked": 1}

        return {"issues": issues, "total_claims_checked": 0}

    def check_scene_ordering(self, scene_plan: dict) -> dict:
        """Verify scenes are in logical order."""
        issues: list[str] = []
        scenes = scene_plan.get("scenes", [])

        title_idx = None
        code_idx = None
        diff_idx = None
        outro_idx = None

        for i, scene in enumerate(scenes):
            t = scene.get("type", "")
            if t == "title" and title_idx is None:
                title_idx = i
            elif t == "code" and code_idx is None:
                code_idx = i
            elif t == "diff" and diff_idx is None:
                diff_idx = i
            elif t == "outro" and outro_idx is None:
                outro_idx = i

        if outro_idx is not None and title_idx is not None and outro_idx < title_idx:
            issues.append(
                f"Outro appears before title"
            )

        if code_idx is not None and diff_idx is not None and diff_idx < code_idx:
            issues.append(
                f"Diff appears before code"
            )

        return {"issues": issues, "ordered_correctly": len(issues) == 0}

    def check_pacing(self, scene_plan: dict) -> dict:
        """Check scene durations for pacing issues."""
        issues: list[str] = []
        scenes = scene_plan.get("scenes", [])
        for i, scene in enumerate(scenes):
            dur = scene.get("duration_seconds", 0)
            if dur < 2:
                issues.append(
                    f"Scene {i + 1} ({scene.get('type', 'unknown')}) is too short ({dur}s)"
                )
            elif dur > 30:
                issues.append(
                    f"Scene {i + 1} ({scene.get('type', 'unknown')}) is too long ({dur}s)"
                )
        return {"issues": issues, "pacing_ok": len(issues) == 0}

    def check_scenes(
        self,
        script: str,
        scene_plan: dict,
        source_diff: str,
        mode: str = "advisory",
    ) -> dict[str, Any]:
        """Run all checks and return a comprehensive report."""
        return {
            "narrative_arc": self.check_narrative_arc(scene_plan),
            "cause_effect": self.check_cause_effect(script, scene_plan),
            "scene_ordering": self.check_scene_ordering(scene_plan),
            "pacing": self.check_pacing(scene_plan),
            "blocked": mode not in ("advisory",),
        }
