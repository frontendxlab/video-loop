"""Deterministic script coherence gate — rule-based 4-arc structure checker.

Validates scene/narration sequences against context -> problem -> solution -> impact arc.
No LLM. Deterministic only.
"""

from __future__ import annotations

from typing import Any


class CoherenceGate:
    """Rule-based 4-arc structure coherence gate for script/scene plans."""

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

    PHASE_KEYWORDS: dict[str, list[str]] = {
        "context": [
            "introduce", "background", "overview", "current",
            "existing", "before", "initially", "setup",
        ],
        "problem": [
            "issue", "problem", "bug", "error", "broken",
            "fail", "limit", "challenge", "pain", "difficult",
        ],
        "solution": [
            "implement", "add", "fix", "change", "update",
            "refactor", "solution", "resolve", "patch", "feature",
        ],
        "impact": [
            "result", "outcome", "improve", "reduce", "increase",
            "benefit", "conclusion", "impact", "effect", "performance",
        ],
    }

    TRANSITION_STRENGTH: dict[str, int] = {
        "fade": 2,
        "slide-left": 2,
        "slide-right": 2,
        "slide-up": 2,
        "slide-down": 2,
        "push": 2,
        "wipe": 2,
        "zoom": 2,
        "dissolve": 2,
        "flip": 1,
        "none": 1,
    }

    def check_narrative_arc(self, scene_plan: dict) -> dict:
        """Check scene sequence for complete narrative arc.

        Detects missing phases, duplicate non-contiguous sections,
        and phase ordering violations.
        """
        scenes = scene_plan.get("scenes", [])
        if not scenes:
            return {
                "phases": [],
                "missing_phases": list(self.ALL_PHASES),
                "duplicate_phases": [],
                "phase_order_valid": True,
                "phase_order_issues": [],
                "has_complete_arc": False,
            }

        phase_sequence: list[str] = []
        for scene in scenes:
            role = self.SCENE_ROLES.get(scene.get("type", ""))
            if role:
                phase_sequence.append(role)

        phases_found: list[str] = []
        for p in phase_sequence:
            if p not in phases_found:
                phases_found.append(p)

        missing = [p for p in self.ALL_PHASES if p not in phases_found]
        duplicate_phases = self._find_duplicate_sections(phase_sequence)

        order_issues: list[str] = []
        order_valid = True
        expected_order = {p: i for i, p in enumerate(self.ALL_PHASES)}
        prev_idx = -1
        for phase in phases_found:
            curr_idx = expected_order.get(phase, -1)
            if curr_idx < prev_idx:
                order_issues.append(
                    f"Phase '{phase}' appears out of order"
                )
                order_valid = False
            prev_idx = curr_idx

        return {
            "phases": phases_found,
            "missing_phases": missing,
            "duplicate_phases": duplicate_phases,
            "phase_order_valid": order_valid,
            "phase_order_issues": order_issues,
            "has_complete_arc": len(missing) == 0,
        }

    def _find_duplicate_sections(self, phase_sequence: list[str]) -> list[str]:
        """Detect phases that appear non-contiguously (duplicate sections).

        A phase is duplicated when it appears, another phase or phase sequence
        appears, and then the original phase reappears — creating a
        broken narrative flow.
        """
        if not phase_sequence:
            return []

        seen: dict[str, int] = {}
        duplicates: set[str] = set()

        for i, phase in enumerate(phase_sequence):
            if phase in seen:
                if i - seen[phase] > 1:
                    duplicates.add(phase)
            seen[phase] = i

        return sorted(duplicates)

    def check_weak_transitions(self, scene_plan: dict) -> dict:
        """Check transition strength at arc phase boundaries.

        Higher confidence transitions (fade, slide, dissolve) between
        different arc phases indicate better narrative flow.  A 'none'
        transition at an arc boundary is flagged as weak.
        """
        scenes = scene_plan.get("scenes", [])
        if not scenes:
            return {
                "weak_transitions": [],
                "transition_score": 0,
                "max_possible": 0,
            }

        issues: list[dict] = []
        score = 0
        max_possible = max(len(scenes) - 1, 0) * 2

        for i in range(len(scenes) - 1):
            scene = scenes[i]
            next_scene = scenes[i + 1]
            curr_role = self.SCENE_ROLES.get(scene.get("type", ""), "unknown")
            next_role = self.SCENE_ROLES.get(next_scene.get("type", ""), "unknown")

            transition_out = scene.get("transition_out", "").lower()
            strength = self.TRANSITION_STRENGTH.get(transition_out, 0)
            score += strength

            if curr_role != next_role and curr_role != "unknown" and next_role != "unknown":
                if not transition_out or transition_out == "none":
                    issues.append({
                        "scene_index": i,
                        "from_phase": curr_role,
                        "to_phase": next_role,
                        "transition": transition_out or "none",
                        "issue": "No transition at arc phase boundary",
                        "severity": "weak",
                    })

        return {
            "weak_transitions": issues,
            "transition_score": score,
            "max_possible": max_possible,
        }

    def check_script_coherence(self, script: str, scene_plan: dict) -> dict:
        """Check narration script for arc phase keyword coverage.

        Matches phase-specific keywords against the script to identify
        which narrative arcs are linguistically supported.
        """
        if not script:
            return {
                "phase_keyword_coverage": {},
                "uncovered_phases": list(self.ALL_PHASES),
                "phase_content_issues": [],
            }

        script_lower = script.lower()
        coverage: dict[str, dict] = {}

        for phase, keywords in self.PHASE_KEYWORDS.items():
            matched = [kw for kw in keywords if kw in script_lower]
            coverage[phase] = {
                "matched_keywords": matched,
                "count": len(matched),
                "covered": len(matched) > 0,
            }

        phase_scenes: dict[str, list[dict]] = {p: [] for p in self.ALL_PHASES}
        for scene in scene_plan.get("scenes", []):
            role = self.SCENE_ROLES.get(scene.get("type", ""))
            if role:
                phase_scenes[role].append(scene)

        phase_content_issues: list[str] = []
        for phase in self.ALL_PHASES:
            scenes_in_phase = phase_scenes.get(phase, [])
            if not scenes_in_phase:
                continue
            has_content = any(
                scene.get("title") or scene.get("text") or scene.get("code")
                or scene.get("points")
                for scene in scenes_in_phase
            )
            if not has_content and not coverage[phase]["covered"]:
                phase_content_issues.append(
                    f"Phase '{phase}' lacks both keyword coverage and scene content"
                )

        uncovered = [p for p in self.ALL_PHASES if not coverage[p]["covered"]]

        return {
            "phase_keyword_coverage": coverage,
            "uncovered_phases": uncovered,
            "phase_content_issues": phase_content_issues,
        }

    def check_scenes(
        self, script: str, scene_plan: dict, **kwargs: Any
    ) -> dict[str, Any]:
        """Run all coherence checks and return structured report."""
        arc = self.check_narrative_arc(scene_plan)
        transitions = self.check_weak_transitions(scene_plan)
        script_coherence = self.check_script_coherence(script, scene_plan)

        issues: list[str] = []
        if not arc["has_complete_arc"]:
            issues.append(
                f"Missing phases: {', '.join(arc['missing_phases'])}"
            )
        if arc["duplicate_phases"]:
            issues.append(
                f"Duplicate sections: {', '.join(arc['duplicate_phases'])}"
            )
        if arc["phase_order_issues"]:
            issues.extend(arc["phase_order_issues"])
        if transitions["weak_transitions"]:
            issues.append(
                f"Weak transitions at {len(transitions['weak_transitions'])} arc boundary(ies)"
            )
        if script_coherence["phase_content_issues"]:
            issues.extend(script_coherence["phase_content_issues"])

        return {
            "narrative_arc": arc,
            "transitions": transitions,
            "script_coherence": script_coherence,
            "issues": issues,
            "coherent": len(issues) == 0,
        }
