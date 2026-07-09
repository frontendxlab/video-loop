"""FastAPI endpoint for director preview — exposes IR scene graph with engine routing.

GET /api/director/preview → VideoProject JSON with per-scene routing.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder

from videoforge.engine.director import pick_engine
from videoforge.engine.ir import (
    AudioTrackIR,
    Engine,
    NarrationSpec,
    SceneKind,
    SceneNode,
    VideoProject,
    WordTiming,
)

router = APIRouter(prefix="/api/director", tags=["director"])


def _build_sample_preview() -> VideoProject:
    """Deterministic sample VideoProject for director preview."""
    scenes = (
        SceneNode(
            id="scene_0",
            kind=SceneKind.TITLE,
            payload='{"title":"Quantum Computing","subtitle":"A New Paradigm"}',
            engine_hint=Engine.REMOTION,
            duration_frames=90,
            narration=NarrationSpec(
                text="Quantum computing represents a fundamental shift.",
                words=(),
                source="estimated",
            ),
        ),
        SceneNode(
            id="scene_1",
            kind=SceneKind.CODE,
            payload=(
                '{"code":"from qiskit import QuantumCircuit\\n'
                'qc = QuantumCircuit(2,2)\\nqc.h(0)\\nqc.cx(0,1)",'
                '"lang":"python","title":"Bell State Circuit"}'
            ),
            engine_hint=Engine.REMOTION,
            duration_frames=150,
            narration=NarrationSpec(
                text="A simple Bell state circuit in Qiskit.",
                words=(),
                source="estimated",
            ),
        ),
        SceneNode(
            id="scene_2",
            kind=SceneKind.DIAGRAM,
            payload=(
                '{"layout":"math_graph",'
                '"nodes":[{"id":"|0>","label":"|0⟩"},{"id":"|1>","label":"|1⟩"}]}'
            ),
            engine_hint=Engine.MANIM,
            duration_frames=120,
            narration=NarrationSpec(
                text="Qubits in superposition states.",
                words=(),
                source="estimated",
            ),
        ),
        SceneNode(
            id="scene_3",
            kind=SceneKind.CHART,
            payload=(
                '{"chartType":"bar","title":"Quantum Volume",'
                '"data":[{"label":"2019","value":8},{"label":"2020","value":32},'
                '{"label":"2021","value":64},{"label":"2022","value":128},'
                '{"label":"2023","value":256}]}'
            ),
            engine_hint=Engine.MANIM,
            duration_frames=120,
            narration=NarrationSpec(
                text="Quantum volume doubled each year.",
                words=(),
                source="estimated",
            ),
        ),
        SceneNode(
            id="scene_4",
            kind=SceneKind.OUTRO,
            payload='{"title":"Thank You","cta":"Learn more"}',
            engine_hint=Engine.REMOTION,
            duration_frames=60,
            narration=NarrationSpec(
                text="Thank you for watching.",
                words=(),
                source="estimated",
            ),
        ),
    )
    return VideoProject(
        title="Introduction to Quantum Computing",
        scenes=scenes,
        fps=30,
        width=1920,
        height=1080,
        audio_tracks=(
            AudioTrackIR(src="tts/output.wav", startFrame=0, durationFrames=540),
        ),
    )


def _scene_to_dict(s: SceneNode) -> dict:
    """Serialize SceneNode to JSON-safe dict with routing info."""
    return {
        "id": s.id,
        "kind": s.kind.value,
        "payload": s.payload,
        "engine_hint": s.engine_hint.value,
        "duration_frames": s.duration_frames,
        "narration": {
            "text": s.narration.text,
            "words": [
                {"text": w.text, "startMs": w.startMs, "endMs": w.endMs}
                for w in s.narration.words
            ],
            "source": s.narration.source,
        },
        "contentHash": s.content_hash(),
        "routedEngine": pick_engine(s).value,
    }


def _serialize_project(project: VideoProject) -> dict:
    """Serialize VideoProject to JSON-safe dict with computed fields."""
    return jsonable_encoder(
        {
            "title": project.title,
            "fps": project.fps,
            "width": project.width,
            "height": project.height,
            "audio_tracks": [
                {"src": a.src, "startFrame": a.startFrame, "durationFrames": a.durationFrames}
                for a in project.audio_tracks
            ],
            "scenes": [_scene_to_dict(s) for s in project.scenes],
            "contentHash": project.content_hash(),
        }
    )


@router.get("/preview")
async def director_preview():
    """Return director preview payload: IR scene graph with engine routing."""
    project = _build_sample_preview()
    return _serialize_project(project)
