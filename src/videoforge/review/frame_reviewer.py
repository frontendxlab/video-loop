from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from videoforge.engine.models import VideoDefinition
from videoforge.engine.recipes import load_review_hints_for_recipe, review_hints_to_dicts
from videoforge.review.alpha_gate import AlphaGate
from videoforge.review.axis_gate import DualChartAxisGate
from videoforge.review.l0_mixed_engine import L0MixedEngineReview
from videoforge.review.l3_smoothness import L3Smoothness
from videoforge.review.l4_transitions import L4Transitions
from videoforge.review.l5_consistency import L5Consistency
from videoforge.review.overlap_gate import OverlapGate
from videoforge.review.repair_actions import RepairAction, RepairHook, build_repair_plan
from videoforge.review.rerender_orchestrator import run_orchestrated_review
from videoforge.review.policy import (
    ReviewVerdict,
    aggregate as aggregate_policy,
    evaluate_alpha as _policy_evaluate_alpha,
    evaluate_axis as _policy_evaluate_axis,
    evaluate_l0 as _policy_evaluate_l0,
    evaluate_l1 as _policy_evaluate_l1,
    evaluate_l2 as _policy_evaluate_l2,
    evaluate_substring as _policy_evaluate_substring,
    evaluate_visibility as _policy_evaluate_visibility,
)
from videoforge.review.substring_gate import HighlightSubstringGate
from videoforge.review.visibility_gate import VisibilityGate


class FrameReviewer:
    def __init__(self, max_retries: int = 2) -> None:
        self._l0 = L0MixedEngineReview()
        self._l3 = L3Smoothness()
        self._l4 = L4Transitions()
        self._l5 = L5Consistency()
        self._overlap_gate = OverlapGate()
        self._alpha_gate = AlphaGate()
        self._visibility_gate = VisibilityGate()
        self._axis_gate = DualChartAxisGate()
        self._substring_gate = HighlightSubstringGate()
        self.max_retries = max_retries

    def check_integrity(self, video_path: str) -> dict[str, Any]:
        issues: list[dict[str, Any]] = []
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "quiet", "-print_format", "json",
                    "-show_frames", "-show_streams", video_path,
                ],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode != 0:
                return {"issues": issues, "passed": False, "total_frames": 0}

            data = json.loads(result.stdout)

            black_frames = data.get("black_frames", [])
            for bf in black_frames:
                issues.append({
                    "type": "black_frame",
                    "start": bf.get("start", 0),
                    "end": bf.get("end", 0),
                })

            frozen_frames = data.get("frozen_frames", [])
            for ff in frozen_frames:
                issues.append({
                    "type": "frozen_frame",
                    "start": ff.get("start", 0),
                    "end": ff.get("end", 0),
                })

            total_frames = 0
            streams = data.get("streams", [])
            for stream in streams:
                if stream.get("codec_type") == "video":
                    nb = stream.get("nb_frames")
                    if nb is not None:
                        total_frames = int(nb)
                    break

            return {
                "issues": issues,
                "passed": len(issues) == 0,
                "total_frames": total_frames,
            }
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            return {"issues": [{"type": "error", "detail": "Failed to probe video"}], "passed": False, "total_frames": 0}

    def check_frames(self, video_path: str) -> dict[str, Any]:
        issues: list[dict[str, Any]] = []
        try:
            result = subprocess.run(
                [
                    "ffmpeg", "-i", video_path,
                    "-vf", "freezedetect=f=0.001:d=2,metadata=mode=print:key=lavfi.freezedetect.freezed_start",
                    "-f", "null", "-",
                ],
                capture_output=True, text=True, timeout=120,
            )
            stderr = result.stderr
            for line in stderr.splitlines():
                if "freeze_start" in line:
                    issues.append({
                        "type": "frame_freeze",
                        "detail": line.strip(),
                    })
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return {
            "issues": issues,
            "passed": len(issues) == 0,
        }

    def check_mixed_engine(self, video_path: str) -> dict[str, Any]:
        """Run L0 mixed-engine review with bounded retry on infrastructure failure.

        Retries on:
          - Exception raised by L0 engine (transient subprocess/IO errors)
          - Infrastructure failure: no frames sampled despite video having frames

        Does NOT retry on genuine quality issues (blank frames, palette drift, etc.).

        Exposes structured retry metadata in result dict when retries occurred.
        """
        for attempt in range(self.max_retries + 1):
            try:
                result = self._l0.run(video_path)
            except Exception:
                if attempt < self.max_retries:
                    continue
                raise

            # Retry on infrastructure failure only: frames exist but none sampled
            if (
                result.get("sampled_frames", 0) == 0
                and result.get("total_frames", 0) > 0
            ):
                if attempt < self.max_retries:
                    continue

            if attempt > 0:
                result["retry_attempts"] = attempt
                result["retry_limit"] = self.max_retries
            return result

        # Unreachable -- either returned above or raised
        raise RuntimeError("L0 mixed-engine review failed")  # pragma: no cover

    def check_layout_overlap(
        self,
        elements: list[dict[str, Any]],
        viewport: tuple[int, int] = (1920, 1080),
    ) -> dict[str, Any]:
        """Run L2 layout-overlap gate standalone.

        Args:
            elements: List of element dicts with ``x``, ``y``, ``width``, ``height``.
            viewport: ``(width, height)`` of canvas.

        Returns:
            Dict with ``issues`` and ``passed`` keys.
        """
        return self._overlap_gate.run(elements, viewport)

    def check_alpha(
        self,
        scene_payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Run alpha/overlay validation gate standalone.

        Args:
            scene_payload: Scene props dict with ``alpha``,
                ``include_transparent_bg``, ``background_opacity`` keys.

        Returns:
            Dict with ``issues`` and ``passed`` keys.
        """
        return self._alpha_gate.run(scene_payload)

    def check_visibility(
        self,
        scene_payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Run 3D/chart visibility gate standalone.

        Args:
            scene_payload: Scene props dict with data arrays
                (``objects``, ``data_points``, ``bar_values``, etc.).

        Returns:
            Dict with ``issues`` and ``passed`` keys.
        """
        return self._visibility_gate.run(scene_payload)

    def check_axis_sanity(
        self,
        scene_payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Run dual-chart axis-sanity gate standalone.

        Args:
            scene_payload: Scene props dict with ``x_labels``,
                ``bar_data``, ``line_data``, ``dual_axes`` keys.

        Returns:
            Dict with ``issues`` and ``passed`` keys.
        """
        return self._axis_gate.run(scene_payload)

    def check_highlight_substring(
        self,
        scene_payload: dict[str, Any],
        case_sensitive: bool = True,
    ) -> dict[str, Any]:
        """Run highlight substring-presence gate standalone.

        Args:
            scene_payload: Scene props dict with ``focus_phrase``
                and ``body_snippet`` keys.
            case_sensitive: Whether substring match is case-sensitive.

        Returns:
            Dict with ``issues`` and ``passed`` keys.
        """
        return self._substring_gate.run(scene_payload, case_sensitive=case_sensitive)

    @staticmethod
    def evaluate_l0_policy(result: dict[str, Any]) -> str:
        """Evaluate L0 issues against severity-based gate policy.

        Policy:
            - 0 issues                              → "pass"
            - only "low" severity issues             → "warn"
            - any "medium" severity issues           → "warn"
            - any "high" severity issues             → "fail"

        Returns:
            One of "pass", "warn", "fail".
        """
        return FrameReviewer._evaluate_by_severity(result)

    @staticmethod
    def evaluate_overlap_policy(result: dict[str, Any]) -> str:
        """Evaluate L2b overlap gate issues against severity-based policy.

        Same pass/warn/fail policy as L0.

        Returns:
            One of "pass", "warn", "fail".
        """
        return FrameReviewer._evaluate_by_severity(result)

    @staticmethod
    def evaluate_alpha_policy(result: dict[str, Any]) -> str:
        """Evaluate AlphaGate result against severity-based policy.

        Returns:
            One of "pass", "warn", "fail".
        """
        return _policy_evaluate_alpha(result).value

    @staticmethod
    def evaluate_visibility_policy(result: dict[str, Any]) -> str:
        """Evaluate VisibilityGate result against severity-based policy.

        Returns:
            One of "pass", "warn", "fail".
        """
        return _policy_evaluate_visibility(result).value

    @staticmethod
    def evaluate_axis_policy(result: dict[str, Any]) -> str:
        """Evaluate DualChartAxisGate result against severity-based policy.

        Returns:
            One of "pass", "warn", "fail".
        """
        return _policy_evaluate_axis(result).value

    @staticmethod
    def evaluate_substring_policy(result: dict[str, Any]) -> str:
        """Evaluate HighlightSubstringGate result against severity-based policy.

        Returns:
            One of "pass", "warn", "fail".
        """
        return _policy_evaluate_substring(result).value

    @staticmethod
    def _evaluate_by_severity(result: dict[str, Any]) -> str:
        """Shared severity-based gate policy.

        Delegates to :func:`policy.evaluate_l0` for single-source-of-truth.

        - 0 issues → pass
        - only low → warn
        - any medium → warn
        - any high → fail
        """
        return _policy_evaluate_l0(result).value

    @staticmethod
    def evaluate_l1_policy(result: dict[str, Any]) -> str:
        """Evaluate L1 integrity result against gate policy.

        Delegates to :func:`policy.evaluate_l1`.

        Returns:
            One of ``"pass"``, ``"fail"``, ``"retry"``.
        """
        return _policy_evaluate_l1(result).value

    @classmethod
    def evaluate(
        cls,
        l0_result: dict[str, Any] | None = None,
        l1_result: dict[str, Any] | None = None,
        l2_result: dict[str, Any] | None = None,
        coherence_result: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Convenience wrapper around :func:`policy.aggregate`.

        Single entry point for CLI/pipeline to evaluate all review levels
        and get a unified decision (pass/warn/fail/retry/repair).

        Returns:
            Dict with ``verdict``, ``levels``, ``retry_suggested``,
            ``repair_suggested``, and optionally ``repair_plan``.
        """
        return aggregate_policy(
            l0_result=l0_result,
            l1_result=l1_result,
            l2_result=l2_result,
            coherence_result=coherence_result,
        )

    def aggregate_review(
        self, video_path: str, input_props: dict | None = None
    ) -> dict[str, Any]:
        report: dict[str, Any] = {
            "video_path": video_path,
            "levels": {},
        }

        l0_result = self.check_mixed_engine(video_path)
        report["levels"]["l0_mixed_engine"] = l0_result

        l1_result = self.check_integrity(video_path)
        report["levels"]["l1_integrity"] = l1_result

        if _policy_evaluate_l1(l1_result) != ReviewVerdict.PASS:
            report["passed"] = False
            report["gate_blocked"] = "l1_integrity"
            report["levels"]["l2_frames"] = {"issues": [], "passed": False, "skipped": True}
            report["levels"]["l3_smoothness"] = {"issues": [], "passed": False, "skipped": True}
            report["levels"]["l4_transitions"] = {"issues": [], "passed": False, "skipped": True}
            report["levels"]["l5_consistency"] = {"issues": [], "passed": False, "skipped": True}
            return report

        l2_result = self.check_frames(video_path)
        report["levels"]["l2_frames"] = l2_result

        if _policy_evaluate_l2(l2_result) != ReviewVerdict.PASS:
            report["passed"] = False
            report["gate_blocked"] = "l2_frames"
            report["levels"]["l3_smoothness"] = {"issues": [], "passed": False, "skipped": True}
            report["levels"]["l4_transitions"] = {"issues": [], "passed": False, "skipped": True}
            report["levels"]["l5_consistency"] = {"issues": [], "passed": False, "skipped": True}
            return report

        # L2b: layout overlap gate (no-video-path gate; passes if no element metadata)
        elements = (input_props or {}).get("elements", [])
        layout_result = self._overlap_gate.run(elements)
        report["levels"]["l2_layout_overlap"] = layout_result

        l3_result = self._l3.run(video_path, input_props)
        report["levels"]["l3_smoothness"] = l3_result

        l4_result = self._l4.run(video_path, input_props)
        report["levels"]["l4_transitions"] = l4_result

        l5_result = self._l5.run(video_path, input_props)
        report["levels"]["l5_consistency"] = l5_result

        all_passed = all(
            level.get("passed", False)
            for level in report["levels"].values()
        )
        report["passed"] = all_passed

        return report


def generate_video_report(
    video_path: str,
    content_hash: str = "",
    engine_mix: list[str] | None = None,
    render_format: dict[str, Any] | None = None,
    l0_result: dict[str, Any] | None = None,
    l1_result: dict[str, Any] | None = None,
    l0_status: str = "pass",
    l2_result: dict[str, Any] | None = None,
    l2_status: str = "pass",
    scene_reports: list[dict[str, Any]] | None = None,
    coherence_result: dict[str, Any] | None = None,
    review_hints: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Build structured JSON artifact for final assembled video.

    Includes content hash, engine mix, render format, L0 summary, L1 summary,
    L2b layout-overlap summary, per-scene artifact summary, optional
    coherence summary, and optional recipe-driven review hints.

    Args:
        video_path: Path to final MP4.
        content_hash: sha256 hash of video definition (16-char hex).
        engine_mix: List of engines used (remotion, manim, animotion).
        render_format: Dict with fps, width, height, pixel_format, etc.
        l0_result: Raw L0 review result dict (issues, sampled_frames, ...).
        l1_result: Raw L1 integrity result dict (issues, total_frames, ...).
        l0_status: Pre-computed L0 policy status ("pass", "warn", "fail").
        l2_result: Raw L2b layout-overlap result dict (issues, passed).
        l2_status: Pre-computed L2b policy status ("pass", "warn", "fail").
        scene_reports: Optional list of per-scene report dicts. When provided,
            ``scenes_summary`` with count, engine breakdown, total duration,
            and compact scene references is included in report.
        coherence_result: Optional coherence gate result dict. When provided,
            ``coherence_summary`` with coherent bool, issues list, and
            narrative_arc summary is included in report.
        review_hints: Optional list of recipe review hint dicts
            (``{"check": str, "severity": str}``). When provided, included
            as ``review_hints`` in the report artifact.

    Returns:
        Report dict suitable for JSON serialization.
    """
    # ── Severity counts for L0 ────────────────────────────────────────────
    l0_issues = (l0_result or {}).get("issues", [])
    l0_severity_counts: dict[str, int] = {"high": 0, "medium": 0, "low": 0}
    for iss in l0_issues:
        sev = iss.get("severity", "low")
        l0_severity_counts[sev] = l0_severity_counts.get(sev, 0) + 1

    # ── L1 summary ────────────────────────────────────────────────────────
    l1_data = l1_result or {}
    l1_issues = l1_data.get("issues", [])

    # ── L2b layout-overlap summary ────────────────────────────────────────
    l2_data = l2_result or {"issues": [], "passed": True}
    l2_issues = l2_data.get("issues", [])
    l2_severity_counts: dict[str, int] = {"high": 0, "medium": 0, "low": 0}
    for iss in l2_issues:
        sev = iss.get("severity", "low")
        l2_severity_counts[sev] = l2_severity_counts.get(sev, 0) + 1

    # ── Scenes summary ────────────────────────────────────────────────────
    scene_engines: dict[str, int] = {}
    scene_duration = 0
    scene_refs: list[dict[str, Any]] = []
    for sr in scene_reports or []:
        eng = sr.get("engine", "?")
        scene_engines[eng] = scene_engines.get(eng, 0) + 1
        scene_duration += sr.get("duration_frames", 0)
        scene_refs.append({
            "index": sr.get("scene_index", 0),
            "engine": eng,
            "duration_frames": sr.get("duration_frames", 0),
        })

    scenes_summary: dict[str, Any] = {
        "count": len(scene_reports or []),
        "engines": scene_engines,
        "total_duration_frames": scene_duration,
    }
    if scene_refs:
        scenes_summary["scenes"] = scene_refs

    # ── Render format fallback ─────────────────────────────────────────────
    fmt = render_format or {
        "fps": 30,
        "width": 1920,
        "height": 1080,
        "pixel_format": "yuv420p",
        "video_codec": "h264",
        "audio_codec": "aac",
    }

    report: dict[str, Any] = {
        "artifact": "videoforge-video-report",
        "version": 1,
        "video_path": str(Path(video_path).resolve()),
        "report_timestamp": datetime.now(timezone.utc).isoformat(),
        "content_hash": content_hash,
        "engine_mix": sorted(set(engine_mix or ["remotion"])),
        "render_format": {
            "fps": fmt.get("fps", 30),
            "width": fmt.get("width", 1920),
            "height": fmt.get("height", 1080),
            "pixel_format": fmt.get("pixel_format", "yuv420p"),
            "video_codec": fmt.get("video_codec", "h264"),
            "audio_codec": fmt.get("audio_codec", "aac"),
        },
        "scenes_summary": scenes_summary,
        "l0_summary": {
            "status": l0_status,
            "passed": l0_status == "pass",
            "total_issues": len(l0_issues),
            "severity_counts": l0_severity_counts,
            "sampled_frames": (l0_result or {}).get("sampled_frames", 0),
            "total_frames": (l0_result or {}).get("total_frames", 0),
            "duration_seconds": (l0_result or {}).get("duration_seconds", 0.0),
            "issues": l0_issues,
        },
        "l1_summary": {
            "passed": l1_data.get("passed", False),
            "total_frames": l1_data.get("total_frames", 0),
            "total_issues": len(l1_issues),
            "issues": l1_issues,
        },
        "l2_layout_overlap_summary": {
            "status": l2_status,
            "passed": l2_status == "pass",
            "total_issues": len(l2_issues),
            "severity_counts": l2_severity_counts,
            "issues": l2_issues,
        },
    }

    # ── Review hints from recipe ────────────────────────────────────────────
    if review_hints:
        report["review_hints"] = review_hints

    # ── Coherence summary ───────────────────────────────────────────────────
    if coherence_result is not None:
        nar = coherence_result.get("narrative_arc", {})
        report["coherence_summary"] = {
            "coherent": coherence_result.get("coherent", False),
            "total_issues": len(coherence_result.get("issues", [])),
            "issues": coherence_result.get("issues", []),
            "has_complete_arc": nar.get("has_complete_arc", False),
            "missing_phases": nar.get("missing_phases", []),
            "duplicate_phases": nar.get("duplicate_phases", []),
            "phase_order_valid": nar.get("phase_order_valid", True),
        }

    return report


def write_video_report(
    report: dict[str, Any],
    video_path: str,
) -> str:
    """Write report JSON to <video_path>.report.json.

    Returns path to written report file.
    """
    report_path = Path(video_path).with_suffix(".mp4.report.json")
    report_path.write_text(json.dumps(report, indent=2, default=str))
    return str(report_path.resolve())


def _discover_scene_reports(video_path: str) -> list[dict[str, Any]]:
    """Discover per-scene report artifacts on disk next to video file.

    Scans for ``*.mp4.scene.report.json`` files in same directory as
    ``video_path`` and returns them sorted by ``scene_index``.

    Returns:
        List of scene report dicts (empty if none found).
    """
    video_dir = Path(video_path).parent
    reports: list[dict[str, Any]] = []
    for p in sorted(video_dir.glob("*.mp4.scene.report.json")):
        try:
            reports.append(json.loads(p.read_text()))
        except (json.JSONDecodeError, OSError):
            continue
    reports.sort(key=lambda r: r.get("scene_index", 0))
    return reports


def run_review(
    video_path: str,
    content_hash: str = "",
    engine_mix: list[str] | None = None,
    reviewer: FrameReviewer | None = None,
    elements: list[dict[str, Any]] | None = None,
    scene_reports: list[dict[str, Any]] | None = None,
    rerender: bool = False,
    rerender_hook: RepairHook | None = None,
    coherence_result: dict[str, Any] | None = None,
    recipe_id: str | None = None,
) -> dict[str, Any]:
    """Run L0 + L1 + L2b review + optional coherence, generate report artifact.

    Automatically discovers per-scene report artifacts from disk when
    ``scene_reports`` is not provided.

    When ``rerender=True``, L0-repairable issues trigger the rerender
    orchestrator loop (bounded retry via ``run_orchestrated_review``).
    The orchestrator's final review replaces ``l0_result``.

    When ``recipe_id`` is provided, loads the recipe's review hints from
    the registry and includes them in the report artifact, provenance,
    and scene reports (influences review context additively).

    Args:
        video_path: Path to video file to review.
        content_hash: Optional content hash for report.
        engine_mix: Optional list of render engines used.
        reviewer: Optional FrameReviewer instance (created fresh if omitted).
        elements: Optional element layout metadata for L2b overlap gate.
        scene_reports: Optional list of per-scene report dicts. Auto-discovered
            from disk when omitted.
        rerender: Enable rerender orchestration loop for L0-repairable issues.
        rerender_hook: Callback invoked per repair action. If omitted and
            ``rerender=True``, a default no-op hook (always returns True) is used.
        coherence_result: Optional coherence gate result dict. When provided,
            coherence is included in the unified policy decision and report.
        recipe_id: Optional recipe id for loading review hints. When provided,
            hints are propagated into report, provenance, and scene reports.

    Returns:
        Dict with keys: l0_result, l0_status, l1_result, l2_result, l2_status,
                        report, report_path, decision.
                        When ``rerender=True``, also includes
                        ``orchestration_result``.
                        When ``coherence_result`` is provided, also includes
                        ``coherence_result``.
                        When ``recipe_id`` is provided, also includes
                        ``review_hints`` and ``recipe_id``.
    """
    if reviewer is None:
        reviewer = FrameReviewer()

    # ── Load recipe review hints (additive deterministic context) ─────────
    _review_hints: list[dict[str, str]] | None = None
    if recipe_id:
        _review_hints = load_review_hints_for_recipe(recipe_id)

    l0_result = reviewer.check_mixed_engine(video_path)
    l0_status = reviewer.evaluate_l0_policy(l0_result)

    # ── Optional rerender orchestration ────────────────────────────────────
    orchestration_result: dict[str, Any] | None = None
    if rerender:
        plan = build_repair_plan(l0_result)
        if plan:
            hook = rerender_hook if rerender_hook is not None else _default_rerender_hook
            orc_result = run_orchestrated_review(
                video_path=video_path,
                review_fn=reviewer.check_mixed_engine,
                render_hook=hook,
                max_rounds=reviewer.max_retries + 1,
            )
            orchestration_result = orc_result
            l0_result = orc_result["final_review"]
            l0_status = reviewer.evaluate_l0_policy(l0_result)

    l1_result = reviewer.check_integrity(video_path)

    # L2b: Layout overlap (passes trivially when no elements provided)
    if elements:
        l2_result = reviewer.check_layout_overlap(elements)
        l2_status = reviewer.evaluate_overlap_policy(l2_result)
    else:
        l2_result = {"issues": [], "passed": True}
        l2_status = "pass"

    # Auto-discover scene reports from disk if not provided
    if scene_reports is None:
        scene_reports = _discover_scene_reports(video_path)

    # Unified policy decision across all levels
    decision = reviewer.evaluate(
        l0_result=l0_result,
        l1_result=l1_result,
        l2_result=l2_result,
        coherence_result=coherence_result,
    )

    report = generate_video_report(
        video_path=video_path,
        content_hash=content_hash,
        engine_mix=engine_mix,
        l0_result=l0_result,
        l1_result=l1_result,
        l0_status=l0_status,
        l2_result=l2_result,
        l2_status=l2_status,
        scene_reports=scene_reports,
        coherence_result=coherence_result,
        review_hints=_review_hints,
    )
    # Embed central policy verdict in report artifact
    report["policy_verdict"] = decision["verdict"]
    report_path = write_video_report(report, video_path)

    result: dict[str, Any] = {
        "l0_result": l0_result,
        "l0_status": l0_status,
        "l1_result": l1_result,
        "l2_result": l2_result,
        "l2_status": l2_status,
        "report": report,
        "report_path": report_path,
        "decision": decision,
    }
    if _review_hints is not None:
        result["review_hints"] = _review_hints
        result["recipe_id"] = recipe_id
    if orchestration_result is not None:
        result["orchestration_result"] = orchestration_result
        result["scene_reports"] = scene_reports
    if coherence_result is not None:
        result["coherence_result"] = coherence_result
    return result


def _default_rerender_hook(action: RepairAction) -> bool:
    """Default no-op rerender hook — always returns True.

    Callers that want actual rerender side effects should pass a custom
    ``rerender_hook`` to :func:`run_review`.
    """
    return True


def generate_scene_report(
    scene_index: int,
    engine: str,
    duration_frames: int,
    scene_path: str,
    render_format: dict[str, Any] | None = None,
    content_hash: str = "",
    review_hints: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Build per-scene JSON artifact next to rendered scene file.

    Includes engine, duration, render format, content hash, and optional
    recipe-driven review hints for traceability back to the parent recipe.

    Args:
        scene_index: 0-based scene index.
        engine: Rendering engine (``remotion``, ``manim``, ``animotion``).
        duration_frames: Scene duration in frames.
        scene_path: Path to rendered scene MP4.
        render_format: Dict with fps, width, height, pixel_format, etc.
        content_hash: Video-level content hash (16-char hex).
        review_hints: Optional list of recipe review hint dicts
            (``{"check": str, "severity": str}``).

    Returns:
        Scene report dict suitable for JSON serialization.
    """
    fmt = render_format or {
        "fps": 30,
        "width": 1920,
        "height": 1080,
        "pixel_format": "yuv420p",
        "video_codec": "h264",
        "audio_codec": "aac",
    }

    report: dict[str, Any] = {
        "artifact": "videoforge-scene-report",
        "version": 1,
        "scene_index": scene_index,
        "engine": engine,
        "duration_frames": duration_frames,
        "scene_path": str(Path(scene_path).resolve()),
        "report_timestamp": datetime.now(timezone.utc).isoformat(),
        "content_hash": content_hash,
        "render_format": {
            "fps": fmt.get("fps", 30),
            "width": fmt.get("width", 1920),
            "height": fmt.get("height", 1080),
            "pixel_format": fmt.get("pixel_format", "yuv420p"),
            "video_codec": fmt.get("video_codec", "h264"),
            "audio_codec": fmt.get("audio_codec", "aac"),
        },
    }
    if review_hints:
        report["review_hints"] = review_hints
    return report


def write_scene_report(
    report: dict[str, Any],
    scene_path: str,
) -> str:
    """Write scene report JSON to ``<scene_path>.scene.report.json``.

    Returns path to written report file.
    """
    report_path = Path(scene_path).with_suffix(".mp4.scene.report.json")
    report_path.write_text(json.dumps(report, indent=2, default=str))
    return str(report_path.resolve())


# ── Provenance Graph ────────────────────────────────────────────────────────


def _scene_content_hash(scene: object, index: int) -> str:
    """Deterministic sha256 for single scene definition (16-char hex).

    Uses dataclass fields, prefixed by index so identical content at
    different positions yields different hashes.
    """
    import hashlib
    from dataclasses import asdict

    try:
        data = json.dumps(asdict(scene), sort_keys=True, default=str)
    except (TypeError, ValueError):
        data = json.dumps(scene, sort_keys=True, default=str)
    return hashlib.sha256(f"{index}:{data}".encode()).hexdigest()[:16]


def generate_provenance_graph(
    video_path: str,
    content_hash: str = "",
    scenes: list[dict] | None = None,
    engine_mix: list[str] | None = None,
    review_hints: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Build deterministic provenance graph artifact.

    Traces render lineage: scene ids → engine choice → asset paths →
    report artifact paths → content hash references. Links video-level
    content hash down through per-scene hashes to individual assets.

    Args:
        video_path: Path to final assembled MP4.
        content_hash: Video-level content hash (16-char hex).
        scenes: List of scene provenance entries, each with:
            - id: Scene identifier.
            - engine: Engine used (``remotion``, ``manim``, ``animotion``).
            - kind: Scene type/kind.
            - content_hash: Per-scene content hash.
            - scene_path: Path to rendered scene MP4.
            - scene_report_path: Path to scene report JSON.
            - duration_frames: Scene duration in frames.
            - assets: Dict of asset paths (audio_src, props_path, …).
        engine_mix: List of all engines used.
        review_hints: Optional list of recipe review hint dicts
            (``{"check": str, "severity": str}``). Included in the
            provenance graph when provided.

    Returns:
        Provenance graph dict suitable for JSON serialization.
    """
    scenes = scenes or []
    video_resolved = str(Path(video_path).resolve())

    graph: dict[str, Any] = {
        "artifact": "videoforge-provenance-graph",
        "version": 1,
        "video_path": video_resolved,
        "report_timestamp": datetime.now(timezone.utc).isoformat(),
        "content_hash": content_hash,
        "engines": sorted(set(engine_mix or [])),
        "scenes": scenes,
        "reports": {
            "video_report": str(
                Path(video_resolved).with_suffix(".mp4.report.json")
            ),
            "provenance_graph": str(
                Path(video_resolved).with_suffix(".provenance.json")
            ),
        },
    }
    if review_hints:
        graph["review_hints"] = review_hints
    return graph


def write_provenance_graph(
    graph: dict[str, Any],
    video_path: str,
) -> str:
    """Write provenance graph JSON to ``<video_path>.provenance.json``.

    Returns path to written provenance file.
    """
    graph_path = Path(video_path).with_suffix(".provenance.json")
    graph_path.write_text(json.dumps(graph, indent=2, default=str))
    return str(graph_path.resolve())


def build_provenance_scenes(
    video_def: object,
    scene_paths: list[str],
    build_dir: str | Path = "",
    recipe_ids: list[str | None] | None = None,
) -> list[dict[str, Any]]:
    """Build scenes list for provenance graph from render result.

    Args:
        video_def: VideoDefinition (or any object with ``.scenes``,
            ``.audioTracks`` and ``.fps``).
        scene_paths: List of scene MP4 paths in render order.
        build_dir: Build directory (locates props JSON artifacts).
        recipe_ids: Optional per-scene recipe ids. When provided, loads
            each recipe's review hints and attaches them to the scene
            provenance entry.

    Returns:
        List of scene provenance entries.
    """
    build_dir = Path(build_dir) if build_dir else Path()
    scenes_data: list[dict[str, Any]] = []

    for i, sp in enumerate(scene_paths):
        scene = video_def.scenes[i]  # type: ignore[union-attr]
        sp_path = Path(sp)
        scene_report_path = sp_path.with_suffix(".mp4.scene.report.json")
        engine = getattr(scene, "renderer", "remotion")

        assets: dict[str, str] = {}
        tracks = getattr(video_def, "audioTracks", None) or getattr(
            video_def, "audio_tracks", ()
        )
        if i < len(tracks):
            src = getattr(tracks[i], "src", "")
            if src:
                assets["audio_src"] = src

        props_path = build_dir / f"props_{i:04d}.json"
        if props_path.exists():
            assets["props_path"] = str(props_path.resolve())

        entry: dict[str, Any] = {
            "id": f"scene_{i:04d}",
            "engine": engine,
            "kind": scene.type.value
            if hasattr(scene, "type")
            else getattr(scene, "kind", "").value,
            "content_hash": _scene_content_hash(scene, i),
            "scene_path": str(sp_path.resolve()),
            "scene_report_path": (
                str(scene_report_path.resolve())
                if scene_report_path.exists()
                else ""
            ),
            "duration_frames": getattr(scene, "duration", 0)
            or getattr(scene, "duration_frames", 0),
            "assets": assets,
        }

        # Attach recipe review hints per scene when recipe_ids provided
        if recipe_ids and i < len(recipe_ids):
            rid = recipe_ids[i]
            if rid:
                hints = load_review_hints_for_recipe(rid)
                if hints:
                    entry["review_hints"] = hints
                    entry["recipe_id"] = rid

        scenes_data.append(entry)

    return scenes_data
