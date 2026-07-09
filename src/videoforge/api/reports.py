"""Reports API — discover and serve video report / provenance / scene artifacts.

Endpoints:
  GET  /api/reports                  — list all discovered reports
  GET  /api/reports/{name}           — full video report JSON
  GET  /api/reports/{name}/provenance — provenance graph JSON
  GET  /api/reports/{name}/scenes    — per-scene report artifacts

Artifacts live on disk as:
  <video>.mp4.report.json           — video-level report
  <video>.provenance.json           — provenance graph
  <scene>.mp4.scene.report.json     — per-scene report
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/reports", tags=["reports"])

def _reports_dir() -> Path:
    """Scan directory for report artifacts.

    Override via ``VIDEOFORGE_REPORTS_DIR`` env var.
    Eval'd on each call so tests can ``monkeypatch``.
    """
    return Path(os.environ.get("VIDEOFORGE_REPORTS_DIR", Path.cwd()))

# Safe name pattern — only allow alphanumeric, hyphens, underscores, dots
_SAFE_NAME = re.compile(r"^[a-zA-Z0-9._-]+$")

# ─── Helpers ─────────────────────────────────────────────────────────────


def _list_report_files() -> list[Path]:
    """Discover ``*.mp4.report.json`` files under reports dir."""
    return sorted(_reports_dir().rglob("*.mp4.report.json"))


def _report_name(path: Path) -> str:
    """Derive URL-safe name from report file path.

    ``test.mp4.report.json`` → ``test``
    ``builds/demo.mp4.report.json`` → ``demo``
    """
    return path.name.removesuffix(".mp4.report.json")


def _resolve_report_path(name: str) -> Path:
    """Find report file matching *name*.

    Raises 404 if not found.
    """
    if not _SAFE_NAME.match(name):
        raise HTTPException(400, f"Invalid report name: {name!r}")
    for p in _list_report_files():
        if _report_name(p) == name:
            return p
    raise HTTPException(404, f"Report not found: {name!r}")


def _read_json(path: Path) -> dict[str, Any]:
    """Read and parse JSON file, raising 404 on failure."""
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        raise HTTPException(404, f"Cannot read {path.name}: {exc}")


def _build_summary(report_path: Path) -> dict[str, Any]:
    """Build summary dict from report file without loading full content."""
    name = _report_name(report_path)
    video_path = report_path.with_name(f"{name}.mp4")
    provenance_path = report_path.with_name(f"{name}.provenance.json")
    try:
        report = json.loads(report_path.read_text())
    except (json.JSONDecodeError, OSError):
        return {
            "name": name,
            "error": "unreadable",
        }

    return {
        "name": name,
        "artifact": report.get("artifact"),
        "report_timestamp": report.get("report_timestamp"),
        "content_hash": report.get("content_hash", ""),
        "engine_mix": report.get("engine_mix", []),
        "scenes_count": report.get("scenes_summary", {}).get("count", 0),
        "total_duration_frames": report.get("scenes_summary", {}).get(
            "total_duration_frames", 0
        ),
        "l0_status": report.get("l0_summary", {}).get("status", "?"),
        "l1_passed": report.get("l1_summary", {}).get("passed", None),
        "policy_verdict": report.get("policy_verdict", "?"),
        "video_path": str(video_path.resolve()) if video_path.exists() else None,
        "has_provenance": provenance_path.exists(),
    }


# ─── Routes ──────────────────────────────────────────────────────────────


@router.get("")
async def list_reports() -> list[dict[str, Any]]:
    """List all discovered report artifacts with summary metadata."""
    return [_build_summary(p) for p in _list_report_files()]


@router.get("/{name}")
async def get_report(name: str) -> dict[str, Any]:
    """Return full video report JSON."""
    path = _resolve_report_path(name)
    data = _read_json(path)
    return data


@router.get("/{name}/provenance")
async def get_provenance(name: str) -> dict[str, Any]:
    """Return provenance graph JSON (if exists)."""
    report_path = _resolve_report_path(name)
    provenance_path = report_path.with_name(f"{name}.provenance.json")
    if not provenance_path.exists():
        raise HTTPException(
            404, f"Provenance graph not found for {name!r}"
        )
    return _read_json(provenance_path)


@router.get("/{name}/scenes")
async def get_scenes(name: str) -> list[dict[str, Any]]:
    """Return per-scene report artifacts for this video."""
    report_path = _resolve_report_path(name)
    video_dir = report_path.parent
    # Scan for scene reports matching this video name
    pattern = f"{name}.scene_*.mp4.scene.report.json"
    scene_reports: list[dict[str, Any]] = []
    for p in sorted(video_dir.glob(pattern)):
        try:
            scene_reports.append(json.loads(p.read_text()))
        except (json.JSONDecodeError, OSError):
            continue
    return scene_reports
