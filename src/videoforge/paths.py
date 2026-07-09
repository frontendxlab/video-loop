"""Shared path utilities for build/review/report workflows.

Reduces duplicated legacy-path drift between scripts/orchestrator.py and
src/videoforge/app.py.  Smallest safe extraction — directory helpers,
coherence gate runner, and report-merge utility.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_BUILD_DIR = "/tmp/vfx-build"


def ensure_parent(path: str | Path) -> Path:
    """Ensure parent directory of *path* exists, return Path."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def ensure_dir(path: str | Path) -> Path:
    """Ensure directory *path* exists, return Path."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def run_coherence_on_scenes(
    scene_data: list[dict],
    plan_path: str | Path,
    fallback_script: str = "",
) -> dict[str, Any]:
    """Run coherence gate on scenes with logging + written report.

    Wraps the common 4-step: extract_script → run_coherence_gate →
    log_coherence_results → write_coherence_report.

    Returns the coherence result dict.
    """
    from videoforge.validation.coherence_gate import (  # noqa: PLC0415
        extract_script_from_scenes,
        log_coherence_results,
        run_coherence_gate,
        write_coherence_report,
    )

    plan_dict: dict[str, Any] = {"scenes": scene_data}
    script = extract_script_from_scenes(scene_data) or fallback_script
    coherence = run_coherence_gate(script, plan_dict, plan_path=str(plan_path))
    log_coherence_results(coherence)
    write_coherence_report(coherence, plan_path)
    return coherence


def merge_coherence_to_report(
    report_path: str | Path,
    coherence: dict[str, Any],
) -> None:
    """Append coherence results into an existing review report JSON."""
    rp = Path(report_path)
    if not rp.exists():
        return
    report_data = json.loads(rp.read_text())
    report_data["coherence"] = {
        "coherent": coherence.get("coherent", False),
        "total_issues": len(coherence.get("issues", [])),
        "issues": coherence.get("issues", []),
    }
    rp.write_text(json.dumps(report_data, indent=2, default=str))
