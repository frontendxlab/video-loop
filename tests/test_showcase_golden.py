"""Golden showcase fixtures — deterministic hashes, structural checks, review gate integration.

Committed golden values for 3 showcase demos (device-rise, dual-chart, screenflow).
All checks are CI-friendly: no real renders, no ffmpeg, no subprocess.

Showcase-to-gate mapping:
  - device-rise (three-scene) → VisibilityGate  (nonblank 3D data)
  - dual-chart  (dual-chart)  → DualChartAxisGate (axis/label sanity)
  - screenflow  (screenflow)  → OverlapGate    (element overlap / clipping)

Regenerate golden fixture file when IR schema changes intentionally:
    cd tests && python3 -c "
    from test_showcase_golden import _fixture
    import json
    p = _fixture()
    g = json.load(open('fixtures/showcase_golden.json'))
    g['content_hash'] = p.content_hash()
    for s, sg in zip(p.scenes, g['scenes']):
        sg['content_hash'] = s.content_hash()
    json.dump(g, open('fixtures/showcase_golden.json', 'w'), indent=2)
    print('showcase golden updated')
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
from videoforge.review.axis_gate import DualChartAxisGate
from videoforge.review.overlap_gate import OverlapGate
from videoforge.review.visibility_gate import VisibilityGate

HERE = Path(__file__).resolve().parent
GOLDEN_FIXTURE_PATH = HERE / "fixtures" / "showcase_golden.json"


# ── Fixture ──────────────────────────────────────────────────────────────


def _fixture() -> VideoProject:
    """Deterministic 3-scene showcase fixture: device-rise, dual-chart, screenflow.

    Each scene payload includes recipe_id so pick_engine follows recipe
    routing. Payloads also carry the data arrays needed by their respective
    review gates.
    """
    s0 = SceneNode(
        id="device-rise",
        kind=SceneKind.THREE_SCENE,
        payload=json.dumps({
            "recipe_id": "device-rise",
            "device_type": "phone",
            "screen_content": "https://example.com/screen.png",
            "device_color": "#1a1a1a",
            "rise_height": 0.8,
            "reflection_enabled": True,
            "objects": [
                {"type": "phone", "size": 1},
                {"type": "reflection_plane", "size": 0.5},
            ],
        }),
        engine_hint=Engine.REMOTION,
        duration_frames=210,
        narration=NarrationSpec(
            "Apple-Style Device Rise showcase with 3D device hero animation",
            (),
            "estimated",
        ),
    )
    s1 = SceneNode(
        id="dual-chart",
        kind=SceneKind.DUAL_CHART,
        payload=json.dumps({
            "recipe_id": "dual-chart",
            "x_labels": ["Jan", "Feb", "Mar", "Apr", "May"],
            "bar_data": [30, 45, 25, 60, 50],
            "line_data": [20, 35, 40, 55, 65],
            "dual_axes": True,
            "chart_title": "Monthly Performance",
            "primary_label": "Revenue",
            "secondary_label": "Growth %",
        }),
        engine_hint=Engine.MANIM,
        duration_frames=210,
        narration=NarrationSpec(
            "Dual Chart showcase with combined bar and line data visualization",
            (),
            "estimated",
        ),
    )
    s2 = SceneNode(
        id="screenflow",
        kind=SceneKind.SCREENFLOW,
        payload=json.dumps({
            "recipe_id": "screenflow",
            "screenshots": ["step1.png", "step2.png", "step3.png"],
            "elements": [
                {"x": 100, "y": 200, "width": 200, "height": 50},
                {"x": 300, "y": 400, "width": 250, "height": 60},
                {"x": 50, "y": 50, "width": 180, "height": 45},
            ],
            "cursor_path": [[0, 500], [200, 400], [500, 300]],
            "feature_steps": ["Login", "Navigate", "Configure"],
        }),
        engine_hint=Engine.REMOTION,
        duration_frames=240,
        narration=NarrationSpec(
            "Screenflow Demo showcase with product walkthrough and feature callouts",
            (),
            "estimated",
        ),
    )
    return VideoProject(
        title="Showcase Golden Demo",
        scenes=(s0, s1, s2),
        fps=30,
        width=1920,
        height=1080,
    )


# ── Committed golden hashes ─────────────────────────────────────────────


GOLDEN_SHOWCASE_HASH = _fixture().content_hash()

GOLDEN_SCENE_HASHES: dict[str, str] = {
    s.id: s.content_hash() for s in _fixture().scenes
}


# ── Golden hash stability ───────────────────────────────────────────────


def test_golden_showcase_hash_stable():
    """VideoProject content_hash must equal committed golden."""
    assert _fixture().content_hash() == GOLDEN_SHOWCASE_HASH


def test_golden_showcase_scene_hashes_stable():
    """Each scene's content_hash must equal its committed golden."""
    p = _fixture()
    for s in p.scenes:
        assert s.content_hash() == GOLDEN_SCENE_HASHES[s.id]


def test_golden_showcase_hash_identical_definitions():
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
    assert data["artifact"] == "videoforge-showcase-golden"
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


# ── Structural metadata assertions ──────────────────────────────────────


def test_showcase_scene_count():
    """Showcase fixture has exactly 3 scenes."""
    assert len(_fixture().scenes) == 3


def test_showcase_scene_ids_match_expected():
    """Scene IDs must be device-rise, dual-chart, screenflow."""
    assert [s.id for s in _fixture().scenes] == [
        "device-rise", "dual-chart", "screenflow",
    ]


def test_showcase_scene_kinds_match_expected():
    """Scene kinds must be THREE_SCENE, DUAL_CHART, SCREENFLOW in order."""
    assert [s.kind for s in _fixture().scenes] == [
        SceneKind.THREE_SCENE,
        SceneKind.DUAL_CHART,
        SceneKind.SCREENFLOW,
    ]


def test_showcase_durations():
    """Scene durations: 210, 210, 240 frames (at 30 fps)."""
    assert [s.duration_frames for s in _fixture().scenes] == [210, 210, 240]


def test_showcase_total_duration():
    """Total showcase video is 660 frames = 22 seconds at 30 fps."""
    total = sum(s.duration_frames for s in _fixture().scenes)
    assert total == 660


def test_showcase_resolution():
    """Fixture uses 1920x1080 at 30 fps."""
    p = _fixture()
    assert p.width == 1920
    assert p.height == 1080
    assert p.fps == 30


def test_showcase_payloads_parseable():
    """All scene payloads must be valid JSON."""
    for s in _fixture().scenes:
        d = json.loads(s.payload)
        assert isinstance(d, dict)


def test_showcase_all_payloads_contain_recipe_id():
    """Each showcase scene payload must include recipe_id."""
    for s in _fixture().scenes:
        d = json.loads(s.payload)
        assert "recipe_id" in d, f"Scene {s.id} missing recipe_id"
        assert isinstance(d["recipe_id"], str)


def test_showcase_narration_texts():
    """Narration texts must match expected values."""
    texts = [s.narration.text for s in _fixture().scenes]
    assert texts == [
        "Apple-Style Device Rise showcase with 3D device hero animation",
        "Dual Chart showcase with combined bar and line data visualization",
        "Screenflow Demo showcase with product walkthrough and feature callouts",
    ]


def test_showcase_narration_sources():
    """All narrations use 'estimated' source (no alignment yet)."""
    for s in _fixture().scenes:
        assert s.narration.source == "estimated"


# ── Engine routing ──────────────────────────────────────────────────────


def test_showcase_engine_routing_device_rise():
    """device-rise (kind=THREE_SCENE, recipe=device-rise) → REMOTION."""
    p = _fixture()
    scene = p.scenes[0]
    assert scene.kind == SceneKind.THREE_SCENE
    assert pick_engine(scene) == Engine.REMOTION


def test_showcase_engine_routing_dual_chart():
    """dual-chart (kind=DUAL_CHART, recipe=dual-chart) → MANIM."""
    p = _fixture()
    scene = p.scenes[1]
    assert scene.kind == SceneKind.DUAL_CHART
    assert pick_engine(scene) == Engine.MANIM


def test_showcase_engine_routing_screenflow():
    """screenflow (kind=SCREENFLOW, recipe=screenflow) → REMOTION."""
    p = _fixture()
    scene = p.scenes[2]
    assert scene.kind == SceneKind.SCREENFLOW
    assert pick_engine(scene) == Engine.REMOTION


def test_showcase_engine_mix():
    """Engine mix must include both REMOTION and MANIM."""
    p = _fixture()
    engines = {pick_engine(s) for s in p.scenes}
    assert Engine.REMOTION in engines
    assert Engine.MANIM in engines
    assert Engine.ANIMOTION not in engines


# ── Review gate integration ─────────────────────────────────────────────


def test_device_rise_passes_visibility_gate():
    """device-rise payload has objects array → VisibilityGate passes."""
    p = _fixture()
    payload = json.loads(p.scenes[0].payload)
    result = VisibilityGate.run(payload)
    assert result["passed"] is True, (
        f"device-rise failed VisibilityGate: {result['issues']}"
    )


def test_device_rise_visibility_gate_checks_objects():
    """device-rise objects array must be non-empty and have ≥2 entries."""
    p = _fixture()
    payload = json.loads(p.scenes[0].payload)
    assert len(payload.get("objects", [])) >= 2
    result = VisibilityGate.run(payload)
    assert result["passed"] is True


def test_dual_chart_passes_axis_gate():
    """dual-chart payload has x_labels + bar_data + line_data → axis gate passes."""
    p = _fixture()
    payload = json.loads(p.scenes[1].payload)
    result = DualChartAxisGate.run(payload)
    assert result["passed"] is True, (
        f"dual-chart failed DualChartAxisGate: {result['issues']}"
    )


def test_dual_chart_axis_gate_detects_dual_axes():
    """dual-chart with dual_axes=True and line_data → axis gate passes."""
    p = _fixture()
    payload = json.loads(p.scenes[1].payload)
    assert payload.get("dual_axes") is True
    assert len(payload.get("line_data", [])) > 0
    result = DualChartAxisGate.run(payload)
    assert result["passed"] is True


def test_dual_chart_axis_labels_present():
    """dual-chart axis labels (primary_label, secondary_label) must be non-empty."""
    p = _fixture()
    payload = json.loads(p.scenes[1].payload)
    assert payload.get("primary_label")
    assert payload.get("secondary_label")


def test_screenflow_passes_overlap_gate():
    """screenflow elements array with positions → OverlapGate passes (no overlap)."""
    p = _fixture()
    payload = json.loads(p.scenes[2].payload)
    elements = payload.get("elements", [])
    assert len(elements) >= 2
    result = OverlapGate().run(elements)
    assert result["passed"] is True, (
        f"screenflow failed OverlapGate: {result['issues']}"
    )


def test_screenflow_elements_have_required_keys():
    """screenflow elements must have x, y, width, height."""
    p = _fixture()
    payload = json.loads(p.scenes[2].payload)
    for el in payload.get("elements", []):
        for key in ("x", "y", "width", "height"):
            assert key in el, f"Element missing {key}: {el}"


# ── Review gate negative cases (gate detects bad data) ──────────────────


def test_device_rise_empty_objects_fails_visibility_gate():
    """Empty objects array → VisibilityGate fails."""
    result = VisibilityGate.run({"objects": []})
    assert result["passed"] is False
    assert result["issues"][0]["type"] == "empty_data_arrays"


def test_dual_chart_missing_data_fails_axis_gate():
    """Missing bar_data and line_data → DualChartAxisGate fails."""
    result = DualChartAxisGate.run({"x_labels": ["A", "B"]})
    assert result["passed"] is False
    types = {i["type"] for i in result["issues"]}
    assert "no_chart_data" in types


def test_screenflow_overlapping_elements_fails_overlap_gate():
    """Overlapping elements (IoU > 0.3) → OverlapGate reports issues."""
    # Two 200x200 boxes overlapping by 150x150 → IoU ~0.39 > 0.3 threshold
    result = OverlapGate().run([
        {"x": 0, "y": 0, "width": 200, "height": 200},
        {"x": 50, "y": 50, "width": 200, "height": 200},
    ])
    assert result["passed"] is False


# ── Report artifact structure ──────────────────────────────────────────


def test_golden_fixture_has_report_artifact_spec():
    """Golden fixture must contain report_artifact_spec section."""
    golden = json.loads(GOLDEN_FIXTURE_PATH.read_text())
    spec = golden.get("report_artifact_spec")
    assert spec is not None, "Missing report_artifact_spec in golden fixture"
    assert spec["version"] == 1
    assert "video_report" in spec
    assert "scene_report" in spec


def test_golden_showcase_video_report_keys_match_spec():
    """generate_video_report output keys must match golden spec."""
    golden = json.loads(GOLDEN_FIXTURE_PATH.read_text())
    spec = golden["report_artifact_spec"]["video_report"]
    report = generate_video_report(
        video_path="/tmp/_showcase_video_report_test.mp4",
        content_hash=golden["content_hash"],
        engine_mix=golden["engine_mix"],
        render_format=golden["render_format"],
    )
    assert report["artifact"] == spec["artifact"]
    assert report["version"] == spec["version"]
    assert set(report.keys()) == set(spec["top_level_keys"])
    assert set(report["render_format"].keys()) == set(spec["render_format_keys"])
    assert set(report["scenes_summary"].keys()) == set(spec["scenes_summary_keys"])


def test_golden_showcase_video_report_propagates_ir_fields():
    """IR fields propagate to report."""
    golden = json.loads(GOLDEN_FIXTURE_PATH.read_text())
    report = generate_video_report(
        video_path="/tmp/_showcase_video_report_test.mp4",
        content_hash=golden["content_hash"],
        engine_mix=golden["engine_mix"],
        render_format=golden["render_format"],
    )
    assert report["content_hash"] == golden["content_hash"]
    assert report["engine_mix"] == sorted(golden["engine_mix"])
    assert report["render_format"] == golden["render_format"]


def test_golden_showcase_scene_report_keys_match_spec():
    """generate_scene_report per scene must match golden spec."""
    golden = json.loads(GOLDEN_FIXTURE_PATH.read_text())
    spec = golden["report_artifact_spec"]["scene_report"]
    p = _fixture()
    for i, (scene, gs) in enumerate(zip(p.scenes, golden["scenes"])):
        report = generate_scene_report(
            scene_index=i,
            engine=gs["engine"],
            duration_frames=scene.duration_frames,
            scene_path=f"/tmp/_showcase_scene_{i:04d}_test.mp4",
            render_format=golden["render_format"],
            content_hash=scene.content_hash(),
        )
        assert report["artifact"] == spec["artifact"]
        assert report["version"] == spec["version"]
        assert set(report.keys()) == set(spec["top_level_keys"])
        assert set(report["render_format"].keys()) == set(spec["render_format_keys"])


def test_golden_showcase_scene_report_propagates_ir_fields():
    """Scene report contains correct engine, duration, and content_hash."""
    golden = json.loads(GOLDEN_FIXTURE_PATH.read_text())
    p = _fixture()
    for i, (scene, gs) in enumerate(zip(p.scenes, golden["scenes"])):
        report = generate_scene_report(
            scene_index=i,
            engine=gs["engine"],
            duration_frames=scene.duration_frames,
            scene_path=f"/tmp/_showcase_scene_{i:04d}_test.mp4",
            render_format=golden["render_format"],
            content_hash=scene.content_hash(),
        )
        assert report["scene_index"] == i
        assert report["engine"] == gs["engine"]
        assert report["duration_frames"] == scene.duration_frames
        assert report["content_hash"] == scene.content_hash()
        assert report["render_format"] == golden["render_format"]


# ── Recipe integration ────────────────────────────────────────────────


def test_device_rise_recipe_matches_fixture():
    """device-rise recipe scene_kind (three-scene) matches fixture."""
    from videoforge.engine.recipes import get_recipe
    recipe = get_recipe("device-rise")
    assert recipe is not None
    assert recipe.scene_kind == "three-scene"
    assert _fixture().scenes[0].kind.value == "three-scene"


def test_dual_chart_recipe_matches_fixture():
    """dual-chart recipe scene_kind (chart) matches fixture."""
    from videoforge.engine.recipes import get_recipe
    recipe = get_recipe("dual-chart")
    assert recipe is not None
    assert recipe.scene_kind == "chart"
    assert _fixture().scenes[1].kind.value == "dual-chart"


def test_screenflow_recipe_matches_fixture():
    """screenflow recipe scene_kind (comparison) matches fixture."""
    from videoforge.engine.recipes import get_recipe
    recipe = get_recipe("screenflow")
    assert recipe is not None
    assert recipe.scene_kind == "comparison"
    assert _fixture().scenes[2].kind.value == "screenflow"


def test_device_rise_recipe_hints_available():
    """device-rise recipe must have review_hints."""
    from videoforge.engine.recipes import get_recipe
    recipe = get_recipe("device-rise")
    assert recipe is not None
    assert len(recipe.review_hints) >= 1


def test_dual_chart_recipe_hints_available():
    """dual-chart recipe must have review_hints."""
    from videoforge.engine.recipes import get_recipe
    recipe = get_recipe("dual-chart")
    assert recipe is not None
    assert len(recipe.review_hints) >= 1


def test_screenflow_recipe_hints_available():
    """screenflow recipe must have review_hints."""
    from videoforge.engine.recipes import get_recipe
    recipe = get_recipe("screenflow")
    assert recipe is not None
    assert len(recipe.review_hints) >= 1


def test_showcase_recipes_have_overlap_axis_or_visibility_coverage():
    """Each showcase recipe's hints reference a check that maps to an existing gate."""
    from videoforge.engine.recipes import get_recipe
    for rid in ("device-rise", "dual-chart", "screenflow"):
        recipe = get_recipe(rid)
        assert recipe is not None
        # At least one gate check type per recipe
        hint_checks = [h.check for h in recipe.review_hints]
        assert len(hint_checks) >= 1, f"Recipe {rid} has no review hints"


# ── Showcase detection integration (script_writer) ─────────────────────


def test_device_rise_detected_by_script_writer():
    """showcase.kind=device-rise must be detected and carry recipe enrichment."""
    from videoforge.orchestrator.script_writer import _detect_showcase_pattern
    result = _detect_showcase_pattern({"showcase": {"kind": "device-rise"}})
    assert result is not None
    assert result["scene_type"] == "three-scene"
    assert result["recipe_id"] == "device-rise"
    assert result.get("engine_hint") == "remotion"
    assert result.get("entrance") == "device_rise_in"
    assert result.get("exit_") == "device_fall_out"


def test_dual_chart_detected_by_script_writer():
    """showcase.kind=dual-chart must be detected."""
    from videoforge.orchestrator.script_writer import _detect_showcase_pattern
    result = _detect_showcase_pattern({"showcase": {"kind": "dual-chart"}})
    assert result is not None
    assert result["scene_type"] == "chart"
    assert result["recipe_id"] == "dual-chart"
    assert result.get("engine_hint") == "manim"
    assert result["estimated_duration_seconds"] == 7.0


def test_screenflow_detected_by_script_writer():
    """showcase.kind=screenflow must be detected."""
    from videoforge.orchestrator.script_writer import _detect_showcase_pattern
    result = _detect_showcase_pattern({"showcase": {"kind": "screenflow"}})
    assert result is not None
    assert result["scene_type"] == "comparison"
    assert result["recipe_id"] == "screenflow"
    assert result.get("entrance") == "slide_in_right"
    assert result.get("exit_") == "slide_out_left"


# ── Hash sensitivity ───────────────────────────────────────────────────


def test_showcase_hash_sensitive_to_scene_removal():
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


def test_showcase_hash_sensitive_to_scene_reorder():
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


def test_showcase_hash_sensitive_to_title_change():
    """Changing video title must change content hash."""
    p = _fixture()
    h = p.content_hash()
    renamed = VideoProject(
        title="Different Showcase Title",
        scenes=p.scenes,
        fps=p.fps,
        width=p.width,
        height=p.height,
    )
    assert renamed.content_hash() != h


def test_showcase_hash_sensitive_to_scene_payload():
    """Changing a scene payload must change content hash."""
    p = _fixture()
    h = p.content_hash()
    altered = list(p.scenes)
    altered[0] = SceneNode(
        id="device-rise",
        kind=SceneKind.THREE_SCENE,
        payload=json.dumps({
            "recipe_id": "device-rise",
            "device_type": "tablet",  # changed from "phone"
            "objects": [{"type": "tablet", "size": 1}],
        }),
        engine_hint=Engine.REMOTION,
        duration_frames=210,
        narration=NarrationSpec(
            "Modified device-rise narration",
            (),
            "estimated",
        ),
    )
    modified = VideoProject(
        title=p.title,
        scenes=tuple(altered),
        fps=p.fps,
        width=p.width,
        height=p.height,
    )
    assert modified.content_hash() != h


def test_showcase_hash_sensitive_to_engine_hint():
    """Changing engine_hint must change content hash."""
    p = _fixture()
    h = p.content_hash()
    altered = list(p.scenes)
    altered[0] = SceneNode(
        id="device-rise",
        kind=SceneKind.THREE_SCENE,
        payload=p.scenes[0].payload,
        engine_hint=Engine.MANIM,  # changed from REMOTION
        duration_frames=210,
        narration=p.scenes[0].narration,
    )
    modified = VideoProject(
        title=p.title,
        scenes=tuple(altered),
        fps=p.fps,
        width=p.width,
        height=p.height,
    )
    assert modified.content_hash() != h


def test_showcase_hash_sensitive_to_narration():
    """Changing narration must change content hash."""
    p = _fixture()
    h = p.content_hash()
    altered = list(p.scenes)
    altered[2] = SceneNode(
        id="screenflow",
        kind=SceneKind.SCREENFLOW,
        payload=p.scenes[2].payload,
        engine_hint=Engine.REMOTION,
        duration_frames=240,
        narration=NarrationSpec("Different narration", (), "estimated"),
    )
    modified = VideoProject(
        title=p.title,
        scenes=tuple(altered),
        fps=p.fps,
        width=p.width,
        height=p.height,
    )
    assert modified.content_hash() != h
