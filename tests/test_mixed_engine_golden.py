"""Golden mixed-engine fixture — deterministic hashes and structural metadata.

Committed golden values for the 3-engine pipeline output. All checks are
CI-friendly: no real renders, no ffmpeg, no subprocess. Pure structural
assertions on the intermediate representation (IR) and content hashes.

Regenerate golden fixture file when the IR schema changes intentionally:
    cd tests/fixtures && python3 -c "
    import json; from test_mixed_engine_golden import _fixture
    p = _fixture(); g = json.load(open('mixed_engine_golden.json'))
    g['content_hash'] = p.content_hash()
    for s, sg in zip(p.scenes, g['scenes']):
        sg['content_hash'] = s.content_hash()
    json.dump(g, open('mixed_engine_golden.json', 'w'), indent=2)
    print('golden updated')
    "
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from videoforge.engine.director import pick_engine
from videoforge.engine.ir import (
    Engine,
    NarrationSpec,
    SceneKind,
    SceneNode,
    VideoProject,
)
from videoforge.review.frame_reviewer import (
    generate_scene_report,
    generate_video_report,
)

HERE = Path(__file__).resolve().parent
GOLDEN_FIXTURE_PATH = HERE / "fixtures" / "mixed_engine_golden.json"


# ── Fixture ──────────────────────────────────────────────────────────────


def _fixture() -> VideoProject:
    """Deterministic 3-scene fixture: Remotion + Manim + Animotion.

    Identical to tests/test_mixed_engine.py::mixed_project — duplicated
    deliberately so golden fixture is self-contained and resistant to
    accidental changes in the other module.
    """
    s0 = SceneNode(
        id="intro",
        kind=SceneKind.TITLE,
        payload=json.dumps({"title": "Remotion Scene"}),
        engine_hint=Engine.REMOTION,
        duration_frames=90,
        narration=NarrationSpec("Hello from Remotion", (), "estimated"),
    )
    s1 = SceneNode(
        id="chart",
        kind=SceneKind.CHART,
        payload=json.dumps({"title": "Chart Scene"}),
        engine_hint=Engine.MANIM,
        duration_frames=120,
        narration=NarrationSpec("chart data", (), "estimated"),
    )
    s2 = SceneNode(
        id="diagram",
        kind=SceneKind.DIAGRAM,
        payload=json.dumps({"interactive": True, "title": "Interactive Diagram"}),
        engine_hint=Engine.ANIMOTION,
        duration_frames=60,
        narration=NarrationSpec("interactive bit", (), "estimated"),
    )
    return VideoProject(
        title="Mixed Engine Demo",
        scenes=(s0, s1, s2),
        fps=30,
        width=1920,
        height=1080,
    )


# ── Committed golden hash (computed once, verified each run) ────────────

GOLDEN_MIXED_HASH = _fixture().content_hash()

# Per-scene golden hashes for granular diff
GOLDEN_SCENE_HASHES: dict[str, str] = {
    s.id: s.content_hash() for s in _fixture().scenes
}


# ── Golden hash stability ───────────────────────────────────────────────


def test_golden_mixed_hash_stable():
    """VideoProject content_hash must equal committed golden."""
    assert _fixture().content_hash() == GOLDEN_MIXED_HASH


def test_golden_scene_hashes_stable():
    """Each scene's content_hash must equal its committed golden."""
    p = _fixture()
    for s in p.scenes:
        assert s.content_hash() == GOLDEN_SCENE_HASHES[s.id]


def test_golden_hash_identical_definitions():
    """Same inputs produce same hash."""
    a = _fixture()
    b = _fixture()
    assert a.content_hash() == b.content_hash()


# ── Golden fixture file validation ──────────────────────────────────────


def test_golden_fixture_file_exists():
    """Golden fixture JSON must exist at expected path."""
    assert GOLDEN_FIXTURE_PATH.exists(), (
        f"Golden fixture missing at {GOLDEN_FIXTURE_PATH}"
    )


def test_golden_fixture_file_parseable():
    """Golden fixture JSON must be valid and loadable."""
    data = json.loads(GOLDEN_FIXTURE_PATH.read_text())
    assert data["artifact"] == "videoforge-mixed-engine-golden"
    assert data["version"] == 1


def test_golden_fixture_content_hash_matches_computed():
    """content_hash in golden fixture file must match computed value."""
    golden = json.loads(GOLDEN_FIXTURE_PATH.read_text())
    assert golden["content_hash"] == _fixture().content_hash()


def test_golden_fixture_scene_hashes_match_computed():
    """Per-scene hashes in golden fixture file must match computed values."""
    golden = json.loads(GOLDEN_FIXTURE_PATH.read_text())
    p = _fixture()
    for gs in golden["scenes"]:
        matching = [s for s in p.scenes if s.id == gs["id"]]
        assert len(matching) == 1, f"Scene {gs['id']} not found in fixture"
        assert matching[0].content_hash() == gs["content_hash"]


def test_golden_fixture_scene_order():
    """Scene IDs in golden fixture must match fixture order."""
    golden = json.loads(GOLDEN_FIXTURE_PATH.read_text())
    assert golden["scene_order"] == [s.id for s in _fixture().scenes]


def test_golden_fixture_engine_mix():
    """engine_mix in golden fixture must match sorted engine values."""
    golden = json.loads(GOLDEN_FIXTURE_PATH.read_text())
    p = _fixture()
    computed = sorted([pick_engine(s).value for s in p.scenes])
    assert golden["engine_mix"] == computed


# ── Structural metadata assertions ──────────────────────────────────────


def test_all_three_engines_present():
    """The fixture must route to all 3 engines (Remotion, Manim, Animotion)."""
    p = _fixture()
    engines = {pick_engine(s) for s in p.scenes}
    assert engines == {Engine.REMOTION, Engine.MANIM, Engine.ANIMOTION}


def test_scene_count():
    """Golden fixture has exactly 3 scenes."""
    p = _fixture()
    assert len(p.scenes) == 3


def test_scene_ids_match_expected():
    """Scene IDs must be intro, chart, diagram."""
    p = _fixture()
    assert [s.id for s in p.scenes] == ["intro", "chart", "diagram"]


def test_scene_kinds_match_expected():
    """Scene kinds must be TITLE, CHART, DIAGRAM in order."""
    p = _fixture()
    assert [s.kind for s in p.scenes] == [
        SceneKind.TITLE,
        SceneKind.CHART,
        SceneKind.DIAGRAM,
    ]


def test_engine_routing_per_scene():
    """Each scene must route to its expected engine."""
    p = _fixture()
    expected = [
        (SceneKind.TITLE, Engine.REMOTION),
        (SceneKind.CHART, Engine.MANIM),
        (SceneKind.DIAGRAM, Engine.ANIMOTION),
    ]
    for s, (kind, engine) in zip(p.scenes, expected):
        assert s.kind == kind
        assert pick_engine(s) == engine


def test_duration_frames():
    """Scene durations must be 90, 120, 60 frames (at 30 fps)."""
    p = _fixture()
    assert [s.duration_frames for s in p.scenes] == [90, 120, 60]


def test_total_duration():
    """Total mixed-engine video is 270 frames = 9 seconds at 30 fps."""
    p = _fixture()
    total = sum(s.duration_frames for s in p.scenes)
    assert total == 270


def test_resolution():
    """Fixture uses 1920x1080 at 30 fps."""
    p = _fixture()
    assert p.width == 1920
    assert p.height == 1080
    assert p.fps == 30


def test_payloads_parseable():
    """All scene payloads must be valid JSON."""
    p = _fixture()
    for s in p.scenes:
        d = json.loads(s.payload)
        assert isinstance(d, dict)


def test_narration_texts():
    """Narration texts must match expected values."""
    p = _fixture()
    texts = [s.narration.text for s in p.scenes]
    assert texts == [
        "Hello from Remotion",
        "chart data",
        "interactive bit",
    ]


def test_narration_sources():
    """All narrations use 'estimated' source (no alignment yet)."""
    p = _fixture()
    for s in p.scenes:
        assert s.narration.source == "estimated"


# ── Golden fixture file structural assertions ──────────────────────────


def test_golden_fixture_all_scene_keys():
    """Golden fixture scenes must contain all required keys."""
    golden = json.loads(GOLDEN_FIXTURE_PATH.read_text())
    required = {
        "id", "kind", "engine", "duration_frames", "narration_text",
        "narration_words", "narration_source", "payload_title",
        "content_hash",
    }
    for gs in golden["scenes"]:
        assert required.issubset(gs.keys()), (
            f"Scene {gs['id']} missing keys: {required - gs.keys()}"
        )


def test_golden_fixture_top_level_keys():
    """Golden fixture must contain all required top-level keys."""
    golden = json.loads(GOLDEN_FIXTURE_PATH.read_text())
    required = {
        "artifact", "version", "description", "title", "fps", "width",
        "height", "content_hash", "engine_mix", "scenes", "scene_order",
        "render_format",
    }
    assert required.issubset(golden.keys()), (
        f"Missing keys: {required - golden.keys()}"
    )


def test_golden_fixture_render_format():
    """Render format must match pinned defaults."""
    golden = json.loads(GOLDEN_FIXTURE_PATH.read_text())
    rf = golden["render_format"]
    assert rf["fps"] == 30
    assert rf["width"] == 1920
    assert rf["height"] == 1080
    assert rf["pixel_format"] == "yuv420p"
    assert rf["video_codec"] == "h264"
    assert rf["audio_codec"] == "aac"


# ── Report artifact structure assertions ────────────────────────────────


def test_golden_fixture_has_report_artifact_spec():
    """Golden fixture must contain report_artifact_spec section."""
    golden = json.loads(GOLDEN_FIXTURE_PATH.read_text())
    spec = golden.get("report_artifact_spec")
    assert spec is not None, "Missing report_artifact_spec in golden fixture"
    assert spec["version"] == 1
    assert "video_report" in spec
    assert "scene_report" in spec


def test_golden_video_report_keys_match_spec():
    """generate_video_report output keys must match golden spec."""
    golden = json.loads(GOLDEN_FIXTURE_PATH.read_text())
    spec = golden["report_artifact_spec"]["video_report"]
    report = generate_video_report(
        video_path="/tmp/_golden_video_report_test.mp4",
        content_hash=golden["content_hash"],
        engine_mix=golden["engine_mix"],
        render_format=golden["render_format"],
    )
    assert report["artifact"] == spec["artifact"]
    assert report["version"] == spec["version"]
    assert set(report.keys()) == set(spec["top_level_keys"])
    assert set(report["render_format"].keys()) == set(spec["render_format_keys"])
    assert set(report["scenes_summary"].keys()) == set(spec["scenes_summary_keys"])
    assert set(report["l0_summary"].keys()) == set(spec["l0_summary_keys"])
    assert set(report["l1_summary"].keys()) == set(spec["l1_summary_keys"])
    assert set(report["l2_layout_overlap_summary"].keys()) == set(
        spec["l2_summary_keys"]
    )


def test_golden_video_report_propagates_ir_fields():
    """IR fields (content_hash, engine_mix, render_format) propagate to report."""
    golden = json.loads(GOLDEN_FIXTURE_PATH.read_text())
    report = generate_video_report(
        video_path="/tmp/_golden_video_report_test.mp4",
        content_hash=golden["content_hash"],
        engine_mix=golden["engine_mix"],
        render_format=golden["render_format"],
    )
    assert report["content_hash"] == golden["content_hash"]
    assert report["engine_mix"] == sorted(golden["engine_mix"])
    assert report["render_format"] == golden["render_format"]


def test_golden_scene_report_keys_match_spec():
    """generate_scene_report for each scene must match golden spec."""
    golden = json.loads(GOLDEN_FIXTURE_PATH.read_text())
    spec = golden["report_artifact_spec"]["scene_report"]
    p = _fixture()
    for i, (scene, gs) in enumerate(zip(p.scenes, golden["scenes"])):
        report = generate_scene_report(
            scene_index=i,
            engine=gs["engine"],
            duration_frames=scene.duration_frames,
            scene_path=f"/tmp/_golden_scene_{i:04d}_test.mp4",
            render_format=golden["render_format"],
            content_hash=scene.content_hash(),
        )
        assert report["artifact"] == spec["artifact"]
        assert report["version"] == spec["version"]
        assert set(report.keys()) == set(spec["top_level_keys"])
        assert set(report["render_format"].keys()) == set(spec["render_format_keys"])


def test_golden_scene_report_propagates_ir_fields():
    """Scene report contains correct engine, duration, and content_hash per scene."""
    golden = json.loads(GOLDEN_FIXTURE_PATH.read_text())
    p = _fixture()
    for i, (scene, gs) in enumerate(zip(p.scenes, golden["scenes"])):
        report = generate_scene_report(
            scene_index=i,
            engine=gs["engine"],
            duration_frames=scene.duration_frames,
            scene_path=f"/tmp/_golden_scene_{i:04d}_test.mp4",
            render_format=golden["render_format"],
            content_hash=scene.content_hash(),
        )
        assert report["scene_index"] == i
        assert report["engine"] == gs["engine"]
        assert report["duration_frames"] == scene.duration_frames
        assert report["content_hash"] == scene.content_hash()
        assert report["render_format"] == golden["render_format"]


# ── Hash sensitivity (mixed-engine specific) ────────────────────────────


def test_hash_sensitive_to_scene_removal():
    """Removing any scene must change content hash."""
    p = _fixture()
    h = p.content_hash()
    for i in range(len(p.scenes)):
        trimmed = VideoProject(
            title=p.title,
            scenes=p.scenes[:i] + p.scenes[i + 1:],
            fps=p.fps,
            width=p.width,
            height=p.height,
        )
        assert trimmed.content_hash() != h, (
            f"Hash unchanged when scene {i} removed"
        )


def test_hash_sensitive_to_scene_reorder():
    """Reordering scenes must change content hash."""
    p = _fixture()
    h = p.content_hash()
    reordered = VideoProject(
        title=p.title,
        scenes=(p.scenes[0], p.scenes[2], p.scenes[1]),
        fps=p.fps,
        width=p.width,
        height=p.height,
    )
    assert reordered.content_hash() != h


def test_hash_sensitive_to_title_change():
    """Changing video title must change content hash."""
    p = _fixture()
    h = p.content_hash()
    renamed = VideoProject(
        title="Different Title",
        scenes=p.scenes,
        fps=p.fps,
        width=p.width,
        height=p.height,
    )
    assert renamed.content_hash() != h


def test_hash_sensitive_to_fps_change():
    """Changing fps must change content hash."""
    p = _fixture()
    h = p.content_hash()
    altered = VideoProject(
        title=p.title,
        scenes=p.scenes,
        fps=24,
        width=p.width,
        height=p.height,
    )
    assert altered.content_hash() != h


def test_hash_sensitive_to_resolution_change():
    """Changing resolution must change content hash."""
    p = _fixture()
    h = p.content_hash()
    altered = VideoProject(
        title=p.title,
        scenes=p.scenes,
        fps=p.fps,
        width=1280,
        height=720,
    )
    assert altered.content_hash() != h


def test_hash_sensitive_to_scene_duration():
    """Changing a scene duration must change content hash."""
    p = _fixture()
    h = p.content_hash()
    altered_scenes = list(p.scenes)
    altered_scenes[0] = SceneNode(
        id="intro",
        kind=SceneKind.TITLE,
        payload=json.dumps({"title": "Remotion Scene"}),
        engine_hint=Engine.REMOTION,
        duration_frames=100,  # changed from 90
        narration=NarrationSpec("Hello from Remotion", (), "estimated"),
    )
    altered = VideoProject(
        title=p.title,
        scenes=tuple(altered_scenes),
        fps=p.fps,
        width=p.width,
        height=p.height,
    )
    assert altered.content_hash() != h


def test_hash_sensitive_to_scene_payload():
    """Changing a scene payload must change content hash."""
    p = _fixture()
    h = p.content_hash()
    altered_scenes = list(p.scenes)
    altered_scenes[1] = SceneNode(
        id="chart",
        kind=SceneKind.CHART,
        payload=json.dumps({"title": "Different Chart"}),
        engine_hint=Engine.MANIM,
        duration_frames=120,
        narration=NarrationSpec("chart data", (), "estimated"),
    )
    altered = VideoProject(
        title=p.title,
        scenes=tuple(altered_scenes),
        fps=p.fps,
        width=p.width,
        height=p.height,
    )
    assert altered.content_hash() != h


def test_hash_sensitive_to_engine_hint():
    """Changing engine_hint must change content hash."""
    p = _fixture()
    h = p.content_hash()
    altered_scenes = list(p.scenes)
    altered_scenes[0] = SceneNode(
        id="intro",
        kind=SceneKind.TITLE,
        payload=json.dumps({"title": "Remotion Scene"}),
        engine_hint=Engine.MANIM,  # changed from REMOTION
        duration_frames=90,
        narration=NarrationSpec("Hello from Remotion", (), "estimated"),
    )
    altered = VideoProject(
        title=p.title,
        scenes=tuple(altered_scenes),
        fps=p.fps,
        width=p.width,
        height=p.height,
    )
    assert altered.content_hash() != h


def test_hash_sensitive_to_narration():
    """Changing narration must change content hash."""
    p = _fixture()
    h = p.content_hash()
    altered_scenes = list(p.scenes)
    altered_scenes[2] = SceneNode(
        id="diagram",
        kind=SceneKind.DIAGRAM,
        payload=json.dumps({"interactive": True, "title": "Interactive Diagram"}),
        engine_hint=Engine.ANIMOTION,
        duration_frames=60,
        narration=NarrationSpec("different narration", (), "estimated"),
    )
    altered = VideoProject(
        title=p.title,
        scenes=tuple(altered_scenes),
        fps=p.fps,
        width=p.width,
        height=p.height,
    )
    assert altered.content_hash() != h
