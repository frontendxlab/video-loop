"""Mixed-engine fixture — one Remotion, one Manim, one Animotion scene.

Proves the orchestration path routes and dispatches across all 3 engines
without heavyweight CI renders. All engine backends are mocked.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from videoforge.engine.director import pick_engine
from videoforge.engine.ir import (
    Engine,
    NarrationSpec,
    SceneKind,
    SceneNode,
    VideoProject,
)
from videoforge.engine.renderer import render_scenes

# ── Fixture ──────────────────────────────────────────────────────────────


@pytest.fixture
def mixed_project() -> VideoProject:
    """VideoProject with 3 scenes — one routing to each engine."""
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


# ── Routing tests ──────────────────────────────────────────────────────


def test_routes_all_three_engines(mixed_project: VideoProject):
    assert pick_engine(mixed_project.scenes[0]) == Engine.REMOTION
    assert pick_engine(mixed_project.scenes[1]) == Engine.MANIM
    assert pick_engine(mixed_project.scenes[2]) == Engine.ANIMOTION


def test_all_three_engines_are_distinct(mixed_project: VideoProject):
    engines = {pick_engine(s) for s in mixed_project.scenes}
    assert engines == {Engine.REMOTION, Engine.MANIM, Engine.ANIMOTION}


def test_scene_order_preserved(mixed_project: VideoProject):
    assert [s.id for s in mixed_project.scenes] == ["intro", "chart", "diagram"]
    assert [s.kind for s in mixed_project.scenes] == [
        SceneKind.TITLE,
        SceneKind.CHART,
        SceneKind.DIAGRAM,
    ]


# ── Determinism ──────────────────────────────────────────────────────────


def test_content_hash_deterministic(mixed_project: VideoProject):
    assert mixed_project.content_hash() == mixed_project.content_hash()


def test_content_hash_differs_when_scene_removed(mixed_project: VideoProject):
    h1 = mixed_project.content_hash()
    trimmed = VideoProject(
        title=mixed_project.title,
        scenes=mixed_project.scenes[:2],
        fps=mixed_project.fps,
        width=mixed_project.width,
        height=mixed_project.height,
    )
    assert trimmed.content_hash() != h1


def test_content_hash_differs_when_payload_changes(mixed_project: VideoProject):
    h1 = mixed_project.content_hash()
    alt = list(mixed_project.scenes)
    alt[0] = SceneNode(
        id="intro",
        kind=SceneKind.TITLE,
        payload=json.dumps({"title": "Different Title"}),
        engine_hint=Engine.REMOTION,
        duration_frames=90,
        narration=NarrationSpec("Hello from Remotion", (), "estimated"),
    )
    altered = VideoProject(
        title=mixed_project.title,
        scenes=tuple(alt),
        fps=mixed_project.fps,
        width=mixed_project.width,
        height=mixed_project.height,
    )
    assert altered.content_hash() != h1


# ── Payload integrity ────────────────────────────────────────────────────


def test_all_payloads_valid_json(mixed_project: VideoProject):
    for s in mixed_project.scenes:
        d = json.loads(s.payload)
        assert isinstance(d, dict)


def test_payloads_contain_expected_titles(mixed_project: VideoProject):
    titles = [json.loads(s.payload)["title"] for s in mixed_project.scenes]
    assert titles == ["Remotion Scene", "Chart Scene", "Interactive Diagram"]


# ── Render orchestration (mocked, no heavyweight CI render) ──────────────


def test_render_dispatches_all_three_engines(
    mixed_project: VideoProject,
    tmp_path: Path,
):
    """Full render_scenes call — verifies all 3 engine backends are invoked.

    Mocks subprocess.run (Remotion), manim_renderer.render_scene, and
    animotion_renderer.render_scene. No actual rendering happens.
    """
    with (
        patch("subprocess.run") as mock_run,
        patch("videoforge.engine.manim_renderer.render_scene") as mock_manim,
        patch("videoforge.engine.animotion_renderer.render_scene") as mock_anim,
    ):
        out_dir = tmp_path / "out"
        out_dir.mkdir(parents=True, exist_ok=True)

        def _mock_manim(sd, output_dir, **kw):
            vp = Path(str(output_dir)) / "scene_0001.mp4"
            vp.parent.mkdir(parents=True, exist_ok=True)
            vp.write_text("dummy")
            return {"success": True, "video_path": str(vp), "log": "mocked_manim"}

        def _mock_anim(sd, output_dir, **kw):
            vp = Path(str(output_dir)) / "scene_0002.mp4"
            vp.parent.mkdir(parents=True, exist_ok=True)
            vp.write_text("dummy")
            return {"success": True, "video_path": str(vp), "log": "mocked_anim"}

        mock_manim.side_effect = _mock_manim
        mock_anim.side_effect = _mock_anim

        def _fake_run(cmd, *a, **kw):
            r = MagicMock()
            r.returncode = 0
            for token in cmd:
                if isinstance(token, str) and token.endswith(".mp4") and not token.startswith("-"):
                    Path(token).parent.mkdir(parents=True, exist_ok=True)
                    Path(token).write_text("dummy")
            return r

        mock_run.side_effect = _fake_run

        with patch("pathlib.Path.exists", return_value=True):
            rendered = render_scenes(
                mixed_project,
                remotion_dir=tmp_path / "remotion",
                output_dir=out_dir,
                tmpdir=tmp_path / "tmp",
            )

    assert len(rendered) == 3, "All 3 scenes should render"
    assert mock_run.called, "subprocess.run should be called (Remotion scene)"
    assert mock_manim.called, "Manim backend should be called (CHART scene)"
    assert mock_anim.called, "Animotion backend should be called (DIAGRAM interactive scene)"

    # Verify scene output paths exist in order
    for i in range(3):
        out_path = out_dir / f"scene_{i:04d}.mp4"
        assert out_path.exists(), f"Output {out_path} should exist"
