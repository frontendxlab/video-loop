"""Artifacts API — serve scene thumbnails, sampled frames, and per-scene reports.

Endpoints:
  GET /api/artifacts/{job_id}/scenes              — list scene artifacts for job
  GET /api/artifacts/{job_id}/scenes/{scene_id}/thumbnail  — scene thumbnail image
  GET /api/artifacts/{job_id}/scenes/{scene_id}/frame      — sampled frame image
  GET /api/artifacts/{job_id}/scenes/{scene_id}/report     — per-scene report JSON

Artifact directory layout:
  {ARTIFACTS_DIR}/{job_id}/thumbnails/{scene_id}.jpg
  {ARTIFACTS_DIR}/{job_id}/frames/{scene_id}.jpg
  {ARTIFACTS_DIR}/{job_id}/reports/{scene_id}.json

ARTIFACTS_DIR defaults to ``/tmp/vfx-artifacts``, overridable via
``VIDEOFORGE_ARTIFACTS_DIR`` env var.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse

router = APIRouter(prefix="/api/artifacts", tags=["artifacts"])

ARTIFACTS_DIR = Path(os.environ.get("VIDEOFORGE_ARTIFACTS_DIR", "/tmp/vfx-artifacts"))

_SAFE_NAME = re.compile(r"^[a-zA-Z0-9._-]+$")


def _safe_job_path(job_id: str) -> Path:
    """Resolve job artifact directory, raising 400 for unsafe names."""
    if not _SAFE_NAME.match(job_id):
        raise HTTPException(400, f"Invalid job_id: {job_id!r}")
    return ARTIFACTS_DIR / job_id


def _safe_scene_path(job_id: str, scene_id: str) -> Path:
    """Resolve scene artifact path."""
    if not _SAFE_NAME.match(scene_id):
        raise HTTPException(400, f"Invalid scene_id: {scene_id!r}")
    if ".." in scene_id:
        raise HTTPException(400, f"Invalid scene_id: {scene_id!r}")
    return _safe_job_path(job_id)


def _file_or_404(path: Path) -> Path:
    """Return path if file exists, else raise 404."""
    if not path.is_file():
        raise HTTPException(404, f"Artifact not found: {path.name}")
    return path


def _read_json_or_404(path: Path) -> dict[str, Any]:
    """Read and parse JSON, raising 404 on failure."""
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        raise HTTPException(404, f"Cannot read {path.name}: {exc}")


def _collect_scene_artifacts(job_id: str) -> list[dict[str, Any]]:
    """Enumerate scene artifacts available for a job."""
    job_dir = _safe_job_path(job_id)
    if not job_dir.is_dir():
        return []

    thumb_dir = job_dir / "thumbnails"
    frame_dir = job_dir / "frames"
    report_dir = job_dir / "reports"

    # Collect scene IDs from any artifact directory
    seen: set[str] = set()
    for d in (thumb_dir, frame_dir, report_dir):
        if d.is_dir():
            for p in d.iterdir():
                scene_id = p.stem
                if _SAFE_NAME.match(scene_id):
                    seen.add(scene_id)

    artifacts: list[dict[str, Any]] = []
    for scene_id in sorted(seen):
        # Check thumbnail (try common extensions)
        has_thumbnail = False
        if thumb_dir.is_dir():
            for ext in (".jpg", ".jpeg", ".png", ".webp"):
                if (thumb_dir / f"{scene_id}{ext}").is_file():
                    has_thumbnail = True
                    break
        # Check frame (try common extensions)
        has_frame = False
        if frame_dir.is_dir():
            for ext in (".jpg", ".jpeg", ".png", ".webp"):
                if (frame_dir / f"{scene_id}{ext}").is_file():
                    has_frame = True
                    break
        has_report = (report_dir / f"{scene_id}.json").is_file() if report_dir.is_dir() else False

        artifacts.append({
            "sceneId": scene_id,
            "hasThumbnail": has_thumbnail,
            "hasFrame": has_frame,
            "hasReport": has_report,
        })

    return artifacts


@router.get("/{job_id}/scenes")
async def list_scene_artifacts(job_id: str) -> list[dict[str, Any]]:
    """List scene artifacts available for a job."""
    return _collect_scene_artifacts(job_id)


@router.get("/{job_id}/scenes/{scene_id}/thumbnail")
async def get_scene_thumbnail(job_id: str, scene_id: str):
    """Serve scene thumbnail image. Returns 404 if not found."""
    job_dir = _safe_scene_path(job_id, scene_id)
    # Try .jpg, .png, .webp
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        path = job_dir / "thumbnails" / f"{scene_id}{ext}"
        if path.is_file():
            return FileResponse(path)
    raise HTTPException(404, f"Thumbnail not found for scene {scene_id!r}")


@router.get("/{job_id}/scenes/{scene_id}/frame")
async def get_scene_frame(job_id: str, scene_id: str):
    """Serve sampled frame image. Returns 404 if not found."""
    job_dir = _safe_scene_path(job_id, scene_id)
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        path = job_dir / "frames" / f"{scene_id}{ext}"
        if path.is_file():
            return FileResponse(path)
    raise HTTPException(404, f"Sampled frame not found for scene {scene_id!r}")


@router.get("/{job_id}/scenes/{scene_id}/report")
async def get_scene_report(job_id: str, scene_id: str) -> dict[str, Any]:
    """Return per-scene report JSON. Returns 404 if not found."""
    job_dir = _safe_scene_path(job_id, scene_id)
    path = job_dir / "reports" / f"{scene_id}.json"
    return _read_json_or_404(path)
