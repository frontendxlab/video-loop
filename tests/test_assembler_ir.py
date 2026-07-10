"""Engine-agnostic assembler wiring — render_scenes accepts VideoProject IR."""

from __future__ import annotations

import json
import inspect
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from videoforge.engine.renderer import render_scenes, _ir_scene_props, _mux_audio_track
from videoforge.engine.ir import (
    AudioTrackIR, Engine, NarrationSpec, SceneKind, SceneNode, VideoProject, WordTiming,
)
from videoforge.engine.director import pick_engine
from videoforge.engine.models import AudioTrack, SceneDefinition, SceneType, VideoDefinition


def _animotion_project() -> VideoProject:
    n0 = SceneNode(
        id="s0", kind=SceneKind.DIAGRAM,
        payload='{"interactive": true, "title":"Interactive"}',
        engine_hint=Engine.ANIMOTION, duration_frames=90,
        narration=NarrationSpec("t", (), "estimated"),
    )
    return VideoProject("Animotion", (n0,), 30, 1920, 1080)


def _project() -> VideoProject:
    n0 = SceneNode(
        id="s0", kind=SceneKind.TITLE,
        payload='{"title":"Hi","text":"hello"}',
        engine_hint=Engine.REMOTION, duration_frames=90,
        narration=NarrationSpec("hello", (WordTiming("hello", 0, 400),), "estimated"),
    )
    n1 = SceneNode(
        id="s1", kind=SceneKind.CHART,
        payload='{"title":"Chart"}',
        engine_hint=Engine.MANIM, duration_frames=120,
        narration=NarrationSpec("chart", (), "estimated"),
    )
    return VideoProject("T", (n0, n1), 30, 1920, 1080)


def test_render_scenes_accepts_video_project():
    sig = inspect.signature(render_scenes)
    ann = str(sig.parameters["video"].annotation)
    assert "VideoProject" in ann or "VideoDefinition" in ann


def test_ir_scene_props_builds_remotion_props():
    p = _project()
    props = _ir_scene_props(p, 0)
    assert props["scenes"][0]["type"] == "title"
    assert props["scenes"][0]["duration"] == 90
    assert props["scenes"][0]["wordTimestamps"][0]["text"] == "hello"


def test_director_routes_ir_scene_to_correct_engine():
    p = _project()
    assert pick_engine(p.scenes[0]) == Engine.REMOTION
    assert pick_engine(p.scenes[1]) == Engine.MANIM


def test_ir_scene_props_includes_payload_fields():
    n = SceneNode(
        id="s0", kind=SceneKind.CODE,
        payload='{"code":"print(1)","lang":"python","highlightLines":[2]}',
        engine_hint=Engine.REMOTION, duration_frames=60,
        narration=NarrationSpec("t", (), "estimated"),
    )
    p = VideoProject("T", (n,), 30, 1920, 1080)
    props = _ir_scene_props(p, 0)
    sc = props["scenes"][0]
    assert sc["code"] == "print(1)"
    assert sc["lang"] == "python"
    assert sc["highlightLines"] == [2]


def test_director_routes_interactive_diagram_to_animotion():
    p = _animotion_project()
    assert pick_engine(p.scenes[0]) == Engine.ANIMOTION


# ── Audio mux for Animotion scenes ──────────────────────────────────────────


def test_legacy_remotion_serializes_audio_track_in_props(tmp_path: Path):
    """Legacy Remotion path serializes AudioTrack to dict for json.dump.

    Before fix, raw AudioTrack dataclass objects were placed in scene_props,
    causing TypeError: Object of type AudioTrack is not JSON serializable.
    """
    scene = SceneDefinition(
        type=SceneType.TITLE, duration=30, title="Legacy Remotion",
    )
    track = AudioTrack(src="/fake/audio.wav", startFrame=0, durationFrames=30)
    video = VideoDefinition(
        title="Test", scenes=[scene], audioTracks=[track],
        captions=[], fps=30,
    )

    # Patch subprocess.run to avoid actual remotion call
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        # Also patch output_path.exists to return True (remotion creates it)
        # trigger the success path after subprocess.run
        with patch("pathlib.Path.exists", return_value=True):
            rendered = render_scenes(
                video, remotion_dir=tmp_path / "remotion",
                output_dir=tmp_path / "out", tmpdir=tmp_path / "tmp",
            )

    # Verify props file was written with valid JSON containing audio track
    props_file = tmp_path / "out" / "props_0000.json"
    assert props_file.exists(), "Props JSON should exist"
    props = json.loads(props_file.read_text())
    assert len(props["audioTracks"]) == 1
    assert props["audioTracks"][0]["src"] == "/fake/audio.wav"
    assert props["audioTracks"][0]["startFrame"] == 0
    assert props["audioTracks"][0]["durationFrames"] == 30


def test_legacy_remotion_serializes_no_audio_tracks_as_empty(tmp_path: Path):
    """Legacy Remotion path with no audio tracks — audioTracks is empty list."""
    scene = SceneDefinition(
        type=SceneType.TITLE, duration=30, title="No Audio",
    )
    video = VideoDefinition(
        title="Test", scenes=[scene], audioTracks=[],
        captions=[], fps=30,
    )

    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        with patch("pathlib.Path.exists", return_value=True):
            rendered = render_scenes(
                video, remotion_dir=tmp_path / "remotion",
                output_dir=tmp_path / "out", tmpdir=tmp_path / "tmp",
            )

    props_file = tmp_path / "out" / "props_0000.json"
    assert props_file.exists()
    props = json.loads(props_file.read_text())
    assert props["audioTracks"] == []
    assert props["scenes"][0]["type"] == "title"


def test_legacy_remotion_multiple_scenes_audio_tracks(tmp_path: Path):
    """Each scene gets its own audio track in legacy Remotion path."""
    s0 = SceneDefinition(type=SceneType.TITLE, duration=30, title="Scene 0")
    s1 = SceneDefinition(type=SceneType.CODE, duration=60, title="Scene 1")
    t0 = AudioTrack(src="/audio0.wav", startFrame=0, durationFrames=30)
    t1 = AudioTrack(src="/audio1.wav", startFrame=0, durationFrames=60)
    video = VideoDefinition(
        title="Multi", scenes=[s0, s1], audioTracks=[t0, t1],
        captions=[], fps=30,
    )

    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        with patch("pathlib.Path.exists", return_value=True):
            render_scenes(
                video, remotion_dir=tmp_path / "remotion",
                output_dir=tmp_path / "out", tmpdir=tmp_path / "tmp",
            )

    # Check props for scene 0
    p0 = json.loads((tmp_path / "out" / "props_0000.json").read_text())
    assert p0["audioTracks"][0]["src"] == "/audio0.wav"
    assert p0["scenes"][0]["type"] == "title"

    # Check props for scene 1
    p1 = json.loads((tmp_path / "out" / "props_0001.json").read_text())
    assert p1["audioTracks"][0]["src"] == "/audio1.wav"
    assert p1["scenes"][0]["type"] == "code"


def test_mux_audio_track_muxes_real_audio(tmp_path: Path):
    """_mux_audio_track replaces silent track with real audio via FFmpeg."""
    video = tmp_path / "scene.mp4"
    audio = tmp_path / "narration.wav"
    video.write_text("dummy")
    audio.write_text("dummy")

    track = AudioTrack(src=str(audio), startFrame=0, durationFrames=90)

    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        # Create the muxed output so the move succeeds
        muxed = tmp_path / "scene_0000_muxed.mp4"
        muxed.write_text("muxed")

        _mux_audio_track(track, video, tmp_path, 0)

        assert mock_run.called
        args = mock_run.call_args[0][0]
        assert "-map" in args
        map_v = args.index("-map")
        assert args[map_v + 1] == "0:v:0"
        assert args[map_v + 2] == "-map"
        assert args[map_v + 3] == "1:a:0"
        assert "-c:v" in args
        assert "copy" in args[args.index("-c:v") + 1]
        assert "-c:a" in args
        assert args[args.index("-c:a") + 1] == "aac"


def test_mux_audio_track_skips_missing_file(tmp_path: Path, caplog):
    """_mux_audio_track logs warning and returns when audio file missing."""
    video = tmp_path / "scene.mp4"
    video.write_text("dummy")
    track = AudioTrack(src="/nonexistent/audio.wav", startFrame=0, durationFrames=90)

    _mux_audio_track(track, video, tmp_path, 0)
    assert "not found" in caplog.text


def test_render_scenes_legacy_animotion_muxes_audio(tmp_path: Path):
    """render_scenes muxes narration audio into legacy Animotion clips."""
    scene = SceneDefinition(
        type=SceneType.TITLE, duration=30, title="Anim Audio",
        renderer="animotion",
    )
    audio_file = tmp_path / "scene_audio.wav"
    audio_file.write_text("fake-audio")
    audio_track = AudioTrack(src=str(audio_file), startFrame=0, durationFrames=30)
    video = VideoDefinition(
        title="Test", scenes=[scene], audioTracks=[audio_track],
        captions=[], fps=30,
    )

    with (
        patch("subprocess.run") as mock_run,
        patch("videoforge.engine.animotion_renderer.render_scene") as mock_anim_render,
    ):
        # Mock animotion render to return success immediately (skip CDP)
        out_video = tmp_path / "out" / "scene_0000.mp4"
        mock_anim_render.return_value = {
            "success": True,
            "video_path": str(out_video),
            "log": "mocked",
        }

        def _fake_run(cmd, *a, **kw):
            r = MagicMock()
            r.returncode = 0
            for token in cmd:
                if isinstance(token, str) and token.endswith(".mp4"):
                    Path(token).parent.mkdir(parents=True, exist_ok=True)
                    Path(token).write_text("dummy")
            return r

        mock_run.side_effect = _fake_run

        rendered = render_scenes(
            video, remotion_dir=tmp_path / "remotion", output_dir=tmp_path / "out",
            tmpdir=tmp_path / "tmp",
        )
        assert len(rendered) == 1

    # Verify ffmpeg called with audio mux args
    mux_calls = [
        c for c in mock_run.call_args_list
        if "-map" in c[0][0] and "1:a:0" in c[0][0]
    ]
    assert len(mux_calls) == 1, "Audio mux FFmpeg should be called exactly once"
    args = mux_calls[0][0][0]
    assert "-c:v" in args and "copy" in args
    assert "-c:a" in args and "aac" in args[args.index("-c:a") + 1]


def test_render_scenes_legacy_animotion_no_audio_gives_silent_track(tmp_path: Path):
    """render_scenes for Animotion with no audio tracks still produces audio stream."""
    scene = SceneDefinition(
        type=SceneType.TITLE, duration=30, title="Silent Anim",
        renderer="animotion",
    )
    video = VideoDefinition(
        title="Test", scenes=[scene], audioTracks=[],
        captions=[], fps=30,
    )

    with (
        patch("subprocess.run") as mock_run,
        patch("videoforge.engine.animotion_renderer.render_scene") as mock_anim_render,
    ):
        out_video = tmp_path / "out" / "scene_0000.mp4"
        mock_anim_render.return_value = {
            "success": True,
            "video_path": str(out_video),
            "log": "mocked",
        }

        def _fake_run(cmd, *a, **kw):
            r = MagicMock()
            r.returncode = 0
            for token in cmd:
                if isinstance(token, str) and token.endswith(".mp4"):
                    Path(token).parent.mkdir(parents=True, exist_ok=True)
                    Path(token).write_text("dummy")
            return r

        mock_run.side_effect = _fake_run

        rendered = render_scenes(
            video, remotion_dir=tmp_path / "remotion", output_dir=tmp_path / "out",
            tmpdir=tmp_path / "tmp",
        )
        assert len(rendered) == 1

    # Verify no audio mux call (no audio tracks)
    mux_calls = [
        c for c in mock_run.call_args_list
        if "-map" in c[0][0] and "1:a:0" in c[0][0]
    ]
    assert len(mux_calls) == 0, "No audio mux should happen when no audio tracks exist"


# ── Audio mux for Manim scenes ───────────────────────────────────────────────


def test_render_scenes_legacy_manim_muxes_audio(tmp_path: Path):
    """render_scenes muxes narration audio into legacy Manim clips."""
    scene = SceneDefinition(
        type=SceneType.TITLE, duration=30, title="Manim Audio",
        renderer="manim",
    )
    audio_file = tmp_path / "manim_audio.wav"
    audio_file.write_text("fake-audio")
    audio_track = AudioTrack(src=str(audio_file), startFrame=0, durationFrames=30)
    video = VideoDefinition(
        title="Test", scenes=[scene], audioTracks=[audio_track],
        captions=[], fps=30,
    )

    with (
        patch("subprocess.run") as mock_run,
        patch("videoforge.engine.manim_renderer.render_scene") as mock_manim_render,
    ):
        out_video = tmp_path / "out" / "scene_0000.mp4"
        mock_manim_render.return_value = {
            "success": True,
            "video_path": str(out_video),
            "log": "mocked",
        }

        def _fake_run(cmd, *a, **kw):
            r = MagicMock()
            r.returncode = 0
            for token in cmd:
                if isinstance(token, str) and token.endswith(".mp4"):
                    Path(token).parent.mkdir(parents=True, exist_ok=True)
                    Path(token).write_text("dummy")
            return r

        mock_run.side_effect = _fake_run

        rendered = render_scenes(
            video, remotion_dir=tmp_path / "remotion", output_dir=tmp_path / "out",
            tmpdir=tmp_path / "tmp",
        )
        assert len(rendered) == 1

    # Verify ffmpeg called with audio mux args
    mux_calls = [
        c for c in mock_run.call_args_list
        if "-map" in c[0][0] and "1:a:0" in c[0][0]
    ]
    assert len(mux_calls) == 1, "Audio mux FFmpeg should be called exactly once"
    args = mux_calls[0][0][0]
    assert "-c:v" in args and "copy" in args
    assert "-c:a" in args and "aac" in args[args.index("-c:a") + 1]


def test_render_scenes_legacy_manim_no_audio(tmp_path: Path):
    """render_scenes for Manim with no audio tracks — no mux call."""
    scene = SceneDefinition(
        type=SceneType.TITLE, duration=30, title="Silent Manim",
        renderer="manim",
    )
    video = VideoDefinition(
        title="Test", scenes=[scene], audioTracks=[],
        captions=[], fps=30,
    )

    with (
        patch("subprocess.run") as mock_run,
        patch("videoforge.engine.manim_renderer.render_scene") as mock_manim_render,
    ):
        out_video = tmp_path / "out" / "scene_0000.mp4"
        mock_manim_render.return_value = {
            "success": True,
            "video_path": str(out_video),
            "log": "mocked",
        }

        def _fake_run(cmd, *a, **kw):
            r = MagicMock()
            r.returncode = 0
            for token in cmd:
                if isinstance(token, str) and token.endswith(".mp4"):
                    Path(token).parent.mkdir(parents=True, exist_ok=True)
                    Path(token).write_text("dummy")
            return r

        mock_run.side_effect = _fake_run

        rendered = render_scenes(
            video, remotion_dir=tmp_path / "remotion", output_dir=tmp_path / "out",
            tmpdir=tmp_path / "tmp",
        )
        assert len(rendered) == 1

    # Verify no audio mux call (no audio tracks)
    mux_calls = [
        c for c in mock_run.call_args_list
        if "-map" in c[0][0] and "1:a:0" in c[0][0]
    ]
    assert len(mux_calls) == 0, "No audio mux should happen when no audio tracks exist"


# ── IR Audio path — Remotion ──────────────────────────────────────────────────


def test_ir_remotion_includes_audio_tracks_in_props():
    """IR Remotion path serializes AudioTrackIR into props JSON."""
    n0 = SceneNode(
        id="s0", kind=SceneKind.TITLE,
        payload='{"title":"Hi","text":"hello"}',
        engine_hint=Engine.REMOTION, duration_frames=90,
        narration=NarrationSpec("hello", (WordTiming("hello", 0, 400),), "estimated"),
    )
    project = VideoProject(
        "T", (n0,), 30, 1920, 1080,
        audio_tracks=(AudioTrackIR("audio.wav", 0, 90),),
    )
    props = _ir_scene_props(project, 0)
    assert len(props["audioTracks"]) == 1
    assert props["audioTracks"][0]["src"] == "audio.wav"
    assert props["audioTracks"][0]["startFrame"] == 0
    assert props["audioTracks"][0]["durationFrames"] == 90


def test_ir_remotion_no_audio_tracks_gives_empty_list():
    """IR Remotion path with no audio tracks — audioTracks is empty list."""
    n0 = SceneNode(
        id="s0", kind=SceneKind.TITLE,
        payload='{"title":"Hi"}',
        engine_hint=Engine.REMOTION, duration_frames=90,
        narration=NarrationSpec("hi", (), "estimated"),
    )
    project = VideoProject("T", (n0,), 30, 1920, 1080)
    props = _ir_scene_props(project, 0)
    assert props["audioTracks"] == []


def test_ir_remotion_audio_out_of_range_gives_empty():
    """IR Remotion path with index beyond audio_tracks len — no crash, empty list."""
    n0 = SceneNode(
        id="s0", kind=SceneKind.TITLE,
        payload='{"title":"Hi"}',
        engine_hint=Engine.REMOTION, duration_frames=90,
        narration=NarrationSpec("hi", (), "estimated"),
    )
    project = VideoProject(
        "T", (n0,), 30, 1920, 1080,
        audio_tracks=(AudioTrackIR("a.wav", 0, 30), AudioTrackIR("b.wav", 30, 60)),
    )
    # scene 0 has 2 audio tracks but props only include matching index
    props = _ir_scene_props(project, 0)
    assert len(props["audioTracks"]) == 1
    assert props["audioTracks"][0]["src"] == "a.wav"

    props1 = _ir_scene_props(project, 0)
    assert props1["audioTracks"][0]["src"] == "a.wav"


def test_ir_remotion_render_passes_audio_tracks(tmp_path: Path):
    """Full render_scenes with IR — verifies audio tracks in written props JSON."""
    n0 = SceneNode(
        id="s0", kind=SceneKind.TITLE,
        payload='{"title":"Hi"}',
        engine_hint=Engine.REMOTION, duration_frames=90,
        narration=NarrationSpec("hi", (), "estimated"),
    )
    project = VideoProject(
        "T", (n0,), 30, 1920, 1080,
        audio_tracks=(AudioTrackIR("narration.wav", 0, 90),),
    )

    with (
        patch("subprocess.run") as mock_run,
        patch("pathlib.Path.exists", return_value=True),
    ):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        render_scenes(
            project, remotion_dir=tmp_path / "remotion",
            output_dir=tmp_path / "out", tmpdir=tmp_path / "tmp",
        )

    props_file = tmp_path / "out" / "props_0000.json"
    assert props_file.exists()
    props = json.loads(props_file.read_text())
    assert len(props["audioTracks"]) == 1
    assert props["audioTracks"][0]["src"] == "narration.wav"
    assert props["audioTracks"][0]["startFrame"] == 0
    assert props["audioTracks"][0]["durationFrames"] == 90


# ── IR Audio path — Animotion ────────────────────────────────────────────────


def test_ir_animotion_muxes_audio(tmp_path: Path):
    """render_scenes muxes narration audio into IR Animotion clips."""
    n0 = SceneNode(
        id="s0", kind=SceneKind.DIAGRAM,
        payload='{"interactive": true, "title":"Interactive"}',
        engine_hint=Engine.ANIMOTION, duration_frames=90,
        narration=NarrationSpec("interactive", (), "estimated"),
    )
    audio_file = tmp_path / "scene_audio.wav"
    audio_file.write_text("fake-audio")
    project = VideoProject(
        "Test", (n0,), 30, 1920, 1080,
        audio_tracks=(AudioTrackIR(str(audio_file), 0, 90),),
    )

    with (
        patch("subprocess.run") as mock_run,
        patch("videoforge.engine.animotion_renderer.render_scene") as mock_anim_render,
    ):
        out_video = tmp_path / "out" / "scene_0000.mp4"
        mock_anim_render.return_value = {
            "success": True,
            "video_path": str(out_video),
            "log": "mocked",
        }

        def _fake_run(cmd, *a, **kw):
            r = MagicMock()
            r.returncode = 0
            for token in cmd:
                if isinstance(token, str) and token.endswith(".mp4"):
                    Path(token).parent.mkdir(parents=True, exist_ok=True)
                    Path(token).write_text("dummy")
            return r

        mock_run.side_effect = _fake_run

        rendered = render_scenes(
            project, remotion_dir=tmp_path / "remotion",
            output_dir=tmp_path / "out", tmpdir=tmp_path / "tmp",
        )
        assert len(rendered) == 1

    # Verify ffmpeg called with audio mux args
    mux_calls = [
        c for c in mock_run.call_args_list
        if "-map" in c[0][0] and "1:a:0" in c[0][0]
    ]
    assert len(mux_calls) == 1, "Audio mux FFmpeg should be called exactly once for IR Animotion"
    args = mux_calls[0][0][0]
    assert "-c:v" in args and "copy" in args
    assert "-c:a" in args and "aac" in args[args.index("-c:a") + 1]


def test_ir_animotion_no_audio_gives_silent_track(tmp_path: Path):
    """render_scenes for IR Animotion with no audio — no mux call."""
    n0 = SceneNode(
        id="s0", kind=SceneKind.DIAGRAM,
        payload='{"interactive": true, "title":"Interactive"}',
        engine_hint=Engine.ANIMOTION, duration_frames=90,
        narration=NarrationSpec("interactive", (), "estimated"),
    )
    project = VideoProject("Test", (n0,), 30, 1920, 1080)

    with (
        patch("subprocess.run") as mock_run,
        patch("videoforge.engine.animotion_renderer.render_scene") as mock_anim_render,
    ):
        out_video = tmp_path / "out" / "scene_0000.mp4"
        mock_anim_render.return_value = {
            "success": True,
            "video_path": str(out_video),
            "log": "mocked",
        }

        def _fake_run(cmd, *a, **kw):
            r = MagicMock()
            r.returncode = 0
            for token in cmd:
                if isinstance(token, str) and token.endswith(".mp4"):
                    Path(token).parent.mkdir(parents=True, exist_ok=True)
                    Path(token).write_text("dummy")
            return r

        mock_run.side_effect = _fake_run

        rendered = render_scenes(
            project, remotion_dir=tmp_path / "remotion",
            output_dir=tmp_path / "out", tmpdir=tmp_path / "tmp",
        )
        assert len(rendered) == 1

    mux_calls = [
        c for c in mock_run.call_args_list
        if "-map" in c[0][0] and "1:a:0" in c[0][0]
    ]
    assert len(mux_calls) == 0, "No audio mux should happen when no audio tracks exist"


# ── IR Audio path — Manim ────────────────────────────────────────────────────


def test_ir_manim_muxes_audio(tmp_path: Path):
    """render_scenes muxes narration audio into IR Manim clips."""
    n0 = SceneNode(
        id="s0", kind=SceneKind.CHART,
        payload='{"title":"Chart"}',
        engine_hint=Engine.MANIM, duration_frames=120,
        narration=NarrationSpec("chart data", (), "estimated"),
    )
    audio_file = tmp_path / "manim_audio.wav"
    audio_file.write_text("fake-audio")
    project = VideoProject(
        "Test", (n0,), 30, 1920, 1080,
        audio_tracks=(AudioTrackIR(str(audio_file), 0, 120),),
    )

    with (
        patch("subprocess.run") as mock_run,
        patch("videoforge.engine.manim_renderer.render_scene") as mock_manim_render,
    ):
        out_video = tmp_path / "out" / "scene_0000.mp4"
        mock_manim_render.return_value = {
            "success": True,
            "video_path": str(out_video),
            "log": "mocked",
        }

        def _fake_run(cmd, *a, **kw):
            r = MagicMock()
            r.returncode = 0
            for token in cmd:
                if isinstance(token, str) and token.endswith(".mp4"):
                    Path(token).parent.mkdir(parents=True, exist_ok=True)
                    Path(token).write_text("dummy")
            return r

        mock_run.side_effect = _fake_run

        rendered = render_scenes(
            project, remotion_dir=tmp_path / "remotion",
            output_dir=tmp_path / "out", tmpdir=tmp_path / "tmp",
        )
        assert len(rendered) == 1

    mux_calls = [
        c for c in mock_run.call_args_list
        if "-map" in c[0][0] and "1:a:0" in c[0][0]
    ]
    assert len(mux_calls) == 1, "Audio mux FFmpeg should be called exactly once for IR Manim"
    args = mux_calls[0][0][0]
    assert "-c:v" in args and "copy" in args
    assert "-c:a" in args and "aac" in args[args.index("-c:a") + 1]


def test_ir_manim_no_audio(tmp_path: Path):
    """render_scenes for IR Manim with no audio — no mux call."""
    n0 = SceneNode(
        id="s0", kind=SceneKind.CHART,
        payload='{"title":"Chart"}',
        engine_hint=Engine.MANIM, duration_frames=120,
        narration=NarrationSpec("chart data", (), "estimated"),
    )
    project = VideoProject("Test", (n0,), 30, 1920, 1080)

    with (
        patch("subprocess.run") as mock_run,
        patch("videoforge.engine.manim_renderer.render_scene") as mock_manim_render,
    ):
        out_video = tmp_path / "out" / "scene_0000.mp4"
        mock_manim_render.return_value = {
            "success": True,
            "video_path": str(out_video),
            "log": "mocked",
        }

        def _fake_run(cmd, *a, **kw):
            r = MagicMock()
            r.returncode = 0
            for token in cmd:
                if isinstance(token, str) and token.endswith(".mp4"):
                    Path(token).parent.mkdir(parents=True, exist_ok=True)
                    Path(token).write_text("dummy")
            return r

        mock_run.side_effect = _fake_run

        rendered = render_scenes(
            project, remotion_dir=tmp_path / "remotion",
            output_dir=tmp_path / "out", tmpdir=tmp_path / "tmp",
        )
        assert len(rendered) == 1

    mux_calls = [
        c for c in mock_run.call_args_list
        if "-map" in c[0][0] and "1:a:0" in c[0][0]
    ]
    assert len(mux_calls) == 0, "No audio mux should happen when no audio tracks exist"


# ── IR Mixed engine with audio ───────────────────────────────────────────────


def test_ir_mixed_engine_all_three_with_audio(tmp_path: Path):
    """IR project with all 3 engines and audio tracks — each engine gets audio."""
    n0 = SceneNode(
        id="s0", kind=SceneKind.TITLE,
        payload='{"title":"Remotion Scene"}',
        engine_hint=Engine.REMOTION, duration_frames=90,
        narration=NarrationSpec("Hello", (), "estimated"),
    )
    n1 = SceneNode(
        id="s1", kind=SceneKind.CHART,
        payload='{"title":"Chart Scene"}',
        engine_hint=Engine.MANIM, duration_frames=120,
        narration=NarrationSpec("chart data", (), "estimated"),
    )
    n2 = SceneNode(
        id="s2", kind=SceneKind.DIAGRAM,
        payload='{"interactive": true, "title":"Interactive"}',
        engine_hint=Engine.ANIMOTION, duration_frames=60,
        narration=NarrationSpec("interactive bit", (), "estimated"),
    )

    a0 = tmp_path / "audio0.wav"
    a1 = tmp_path / "audio1.wav"
    a2 = tmp_path / "audio2.wav"
    a0.write_text("dummy0")
    a1.write_text("dummy1")
    a2.write_text("dummy2")

    project = VideoProject(
        "Mixed Audio",
        (n0, n1, n2),
        30, 1920, 1080,
        audio_tracks=(
            AudioTrackIR(str(a0), 0, 90),
            AudioTrackIR(str(a1), 0, 120),
            AudioTrackIR(str(a2), 0, 60),
        ),
    )

    with (
        patch("subprocess.run") as mock_run,
        patch("videoforge.engine.manim_renderer.render_scene") as mock_manim,
        patch("videoforge.engine.animotion_renderer.render_scene") as mock_anim,
    ):
        out_dir = tmp_path / "out"

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
                project,
                remotion_dir=tmp_path / "remotion",
                output_dir=out_dir,
                tmpdir=tmp_path / "tmp",
            )

    assert len(rendered) == 3

    # Remotion scene 0 — audio in props JSON
    props_file = tmp_path / "out" / "props_0000.json"
    assert props_file.exists()
    props = json.loads(props_file.read_text())
    assert len(props["audioTracks"]) == 1
    assert props["audioTracks"][0]["src"] == str(a0)

    # Manim scene 1 — audio mux via ffmpeg
    manim_mux = [
        c for c in mock_run.call_args_list
        if "-map" in c[0][0] and "1:a:0" in c[0][0]
        and str(a1) in str(c[0][0])
    ]
    assert len(manim_mux) == 1, "Manim scene should mux audio"

    # Animotion scene 2 — audio mux via ffmpeg
    anim_mux = [
        c for c in mock_run.call_args_list
        if "-map" in c[0][0] and "1:a:0" in c[0][0]
        and str(a2) in str(c[0][0])
    ]
    assert len(anim_mux) == 1, "Animotion scene should mux audio"


# ── _track_count and _get_track helpers ──────────────────────────────────────


def test_track_count_ir():
    project = VideoProject("T", (), 30, 1920, 1080,
                           audio_tracks=(AudioTrackIR("a.wav", 0, 30), AudioTrackIR("b.wav", 30, 60)))
    from videoforge.engine.renderer import _track_count, _get_track
    assert _track_count(project) == 2


def test_track_count_ir_empty():
    project = VideoProject("T", (), 30, 1920, 1080)
    from videoforge.engine.renderer import _track_count, _get_track
    assert _track_count(project) == 0


def test_track_count_legacy():
    video = VideoDefinition(title="T", scenes=[], audioTracks=[AudioTrack("a.wav", 0, 30)], captions=[])
    from videoforge.engine.renderer import _track_count, _get_track
    assert _track_count(video) == 1


def test_get_track_ir():
    project = VideoProject("T", (), 30, 1920, 1080,
                           audio_tracks=(AudioTrackIR("a.wav", 0, 30), AudioTrackIR("b.wav", 30, 60)))
    from videoforge.engine.renderer import _track_count, _get_track
    t = _get_track(project, 1)
    assert t is not None
    assert t.src == "b.wav"


def test_get_track_ir_out_of_range():
    project = VideoProject("T", (), 30, 1920, 1080)
    from videoforge.engine.renderer import _get_track
    assert _get_track(project, 0) is None


def test_get_track_legacy():
    video = VideoDefinition(title="T", scenes=[], audioTracks=[AudioTrack("a.wav", 0, 30)], captions=[])
    from videoforge.engine.renderer import _get_track
    t = _get_track(video, 0)
    assert t is not None
    assert t.src == "a.wav"


def test_get_track_legacy_out_of_range():
    video = VideoDefinition(title="T", scenes=[], audioTracks=[], captions=[])
    from videoforge.engine.renderer import _get_track
    assert _get_track(video, 0) is None


# ── Overlay compositing ──────────────────────────────────────────────────────


def test_is_overlay_scene_ir_true():
    """OVERLAY_CTA scene node detected as overlay."""
    from videoforge.engine.renderer import _is_overlay_scene
    n = SceneNode(
        id="s0", kind=SceneKind.OVERLAY_CTA,
        payload='{"title":"Check it out"}',
        engine_hint=Engine.REMOTION, duration_frames=90,
        narration=NarrationSpec("check", (), "estimated"),
    )
    assert _is_overlay_scene(n, is_ir=True) is True


def test_is_overlay_scene_ir_false():
    """Non-overlay scene node NOT detected as overlay."""
    from videoforge.engine.renderer import _is_overlay_scene
    n = SceneNode(
        id="s0", kind=SceneKind.TITLE,
        payload='{"title":"Hi"}',
        engine_hint=Engine.REMOTION, duration_frames=90,
        narration=NarrationSpec("hi", (), "estimated"),
    )
    assert _is_overlay_scene(n, is_ir=True) is False


def test_is_overlay_scene_legacy_true():
    """Legacy overlay-cta scene detected as overlay."""
    from videoforge.engine.renderer import _is_overlay_scene
    scene = SceneDefinition(type=SceneType.OVERLAY_CTA, duration=60, title="CTA")
    assert _is_overlay_scene(scene) is True


def test_is_overlay_scene_legacy_false():
    """Legacy non-overlay scene NOT detected as overlay."""
    from videoforge.engine.renderer import _is_overlay_scene
    scene = SceneDefinition(type=SceneType.TITLE, duration=60, title="Title")
    assert _is_overlay_scene(scene) is False


def test_parse_position_center():
    """_parse_position returns centered FFmpeg expression."""
    from videoforge.engine.renderer import _parse_position
    x, y = _parse_position("center")
    assert x == "(W-w)/2"
    assert y == "(H-h)/2"


def test_parse_position_bottom_left():
    """_parse_position returns bottom-left FFmpeg expression."""
    from videoforge.engine.renderer import _parse_position
    x, y = _parse_position("bottom-left")
    assert x == "0"
    assert y == "H-h"


def test_parse_position_fallback():
    """_parse_position falls back to center for unknown position."""
    from videoforge.engine.renderer import _parse_position
    x, y = _parse_position("nonexistent")
    assert x == "(W-w)/2"


def test_composite_overlay_ffmpeg_args(tmp_path: Path):
    """composite_overlay builds correct FFmpeg command with overlay filter."""
    from videoforge.engine.renderer import composite_overlay

    base = tmp_path / "base.mp4"
    overlay = tmp_path / "overlay.mp4"
    output = tmp_path / "out" / "composited.mp4"
    base.write_text("fake-base")
    overlay.write_text("fake-overlay")

    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        # Create output file so exists check passes
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("fake-composited")

        result = composite_overlay(base, overlay, output, position="center")

    assert result == str(output.resolve())
    assert mock_run.called
    args = mock_run.call_args[0][0]
    assert "ffmpeg" in args[0]
    assert "-filter_complex" in args
    filter_idx = args.index("-filter_complex")
    filter_expr = args[filter_idx + 1]
    assert "overlay=(W-w)/2:(H-h)/2:format=auto" in filter_expr
    assert "-map" in args
    map_idx = args.index("-map")
    assert args[map_idx + 1] == "[outv]"
    assert "-map" in args[map_idx + 2:]
    assert args[args.index("-pix_fmt") + 1] == "yuv420p"
    assert "-c:v" in args
    assert "libx264" in args[args.index("-c:v") + 1]
    assert "-c:a" in args
    assert "copy" in args[args.index("-c:a") + 1]


def test_composite_overlay_custom_position(tmp_path: Path):
    """composite_overlay accepts custom position string."""
    from videoforge.engine.renderer import composite_overlay

    base = tmp_path / "base.mp4"
    overlay = tmp_path / "overlay.mp4"
    output = tmp_path / "out" / "composited.mp4"
    base.write_text("fake-base")
    overlay.write_text("fake-overlay")

    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("fake-composited")

        composite_overlay(base, overlay, output, position="bottom-left")

    args = mock_run.call_args[0][0]
    filter_idx = args.index("-filter_complex")
    filter_expr = args[filter_idx + 1]
    assert "overlay=0:H-h:format=auto" in filter_expr


def test_composite_overlay_opacity(tmp_path: Path):
    """composite_overlay with opacity <1 uses colorchannelmixer."""
    from videoforge.engine.renderer import composite_overlay

    base = tmp_path / "base.mp4"
    overlay = tmp_path / "overlay.mp4"
    output = tmp_path / "out" / "composited.mp4"
    base.write_text("fake-base")
    overlay.write_text("fake-overlay")

    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("fake-composited")

        composite_overlay(base, overlay, output, position="center", opacity=0.5)

    args = mock_run.call_args[0][0]
    filter_idx = args.index("-filter_complex")
    filter_expr = args[filter_idx + 1]
    assert "colorchannelmixer=aa=0.5" in filter_expr


def test_composite_overlay_failure_raises(tmp_path: Path):
    """composite_overlay raises RuntimeError on FFmpeg failure."""
    from videoforge.engine.renderer import composite_overlay

    base = tmp_path / "base.mp4"
    overlay = tmp_path / "overlay.mp4"
    output = tmp_path / "out" / "composited.mp4"
    base.write_text("fake-base")
    overlay.write_text("fake-overlay")

    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "error"
        mock_run.return_value = mock_result

        with pytest.raises(RuntimeError, match="Overlay compositing failed"):
            composite_overlay(base, overlay, output)


def test_render_scenes_overlay_compositing_ir(tmp_path: Path):
    """render_scenes composites OVERLAY_CTA over preceding base scene."""
    from videoforge.engine.renderer import render_scenes

    s0 = SceneNode(
        id="s0", kind=SceneKind.TITLE,
        payload='{"title":"Base Scene"}',
        engine_hint=Engine.REMOTION, duration_frames=90,
        narration=NarrationSpec("base", (), "estimated"),
    )
    s1 = SceneNode(
        id="s1", kind=SceneKind.OVERLAY_CTA,
        payload='{"title":"Subscribe","cta":"Click here"}',
        engine_hint=Engine.REMOTION, duration_frames=60,
        narration=NarrationSpec("cta", (), "estimated"),
    )
    project = VideoProject("Overlay Test", (s0, s1), 30, 1920, 1080)

    with (
        patch("subprocess.run") as mock_run,
        patch("pathlib.Path.exists", return_value=True),
    ):
        out_dir = tmp_path / "out"

        def _fake_run(cmd, *a, **kw):
            r = MagicMock()
            r.returncode = 0
            for token in cmd:
                if isinstance(token, str) and token.endswith(".mp4") and not token.startswith("-"):
                    Path(token).parent.mkdir(parents=True, exist_ok=True)
                    Path(token).write_text("fake")
            return r

        mock_run.side_effect = _fake_run

        rendered = render_scenes(
            project,
            remotion_dir=tmp_path / "remotion",
            output_dir=out_dir,
            tmpdir=tmp_path / "tmp",
        )

    # Should return 1 composited clip (not 2 separate)
    assert len(rendered) == 1, f"Expected 1 composited clip, got {len(rendered)}"

    # Path should be composited output
    composited_path = Path(rendered[0])
    assert "composited" in composited_path.name

    # Verify FFmpeg overlay filter was called
    # c[0] is positional args tuple; c[0][0] is the cmd list
    overlay_calls = [
        c for c in mock_run.call_args_list
        if any("overlay=" in str(t) for t in c[0][0])
    ]
    assert len(overlay_calls) >= 1, "Expected at least one ffmpeg overlay call"
    overlay_tokens = overlay_calls[0][0][0]
    cmd_str = " ".join(str(t) for t in overlay_tokens)
    assert "overlay=(W-w)/2" in cmd_str

    # Verify base scene was rendered with yuv420p (standard)
    render_calls = [
        c for c in mock_run.call_args_list
        if "remotion" in " ".join(c[0][0]) and "--pixel-format" in c[0][0]
    ]
    pix_fmts = [
        c[0][0][c[0][0].index("--pixel-format") + 1]
        for c in render_calls
    ]
    # At least one yuv420p (base) and one yuva420p (overlay)
    assert "yuv420p" in pix_fmts
    assert "yuva420p" in pix_fmts


def test_render_scenes_no_overlay_passthrough(tmp_path: Path):
    """render_scenes with no overlay — backward compat, all scenes concatenated."""
    from videoforge.engine.renderer import render_scenes

    s0 = SceneNode(
        id="s0", kind=SceneKind.TITLE,
        payload='{"title":"Scene 0"}',
        engine_hint=Engine.REMOTION, duration_frames=90,
        narration=NarrationSpec("s0", (), "estimated"),
    )
    s1 = SceneNode(
        id="s1", kind=SceneKind.CODE,
        payload='{"title":"Scene 1","code":"print(1)"}',
        engine_hint=Engine.REMOTION, duration_frames=120,
        narration=NarrationSpec("s1", (), "estimated"),
    )
    project = VideoProject("No Overlay", (s0, s1), 30, 1920, 1080)

    with (
        patch("subprocess.run") as mock_run,
        patch("pathlib.Path.exists", return_value=True),
    ):
        out_dir = tmp_path / "out"

        def _fake_run(cmd, *a, **kw):
            r = MagicMock()
            r.returncode = 0
            for token in cmd:
                if isinstance(token, str) and token.endswith(".mp4") and not token.startswith("-"):
                    Path(token).parent.mkdir(parents=True, exist_ok=True)
                    Path(token).write_text("fake")
            return r

        mock_run.side_effect = _fake_run

        rendered = render_scenes(
            project,
            remotion_dir=tmp_path / "remotion",
            output_dir=out_dir,
            tmpdir=tmp_path / "tmp",
        )

    # Should return 2 individual clips (no compositing)
    assert len(rendered) == 2

    # Both should be scene_* files, not composited
    names = [Path(p).name for p in rendered]
    assert all("composited" not in n for n in names)
    assert "scene_0000.mp4" in names[0]
    assert "scene_0001.mp4" in names[1]


def test_render_scenes_overlay_standalone_fallback(tmp_path: Path):
    """Overlay scene with no preceding base renders standalone (fallback)."""
    from videoforge.engine.renderer import render_scenes

    s0 = SceneNode(
        id="s0", kind=SceneKind.OVERLAY_CTA,
        payload='{"title":"Standalone Overlay"}',
        engine_hint=Engine.REMOTION, duration_frames=60,
        narration=NarrationSpec("overlay", (), "estimated"),
    )
    project = VideoProject("Standalone", (s0,), 30, 1920, 1080)

    with (
        patch("subprocess.run") as mock_run,
        patch("pathlib.Path.exists", return_value=True),
    ):
        out_dir = tmp_path / "out"

        def _fake_run(cmd, *a, **kw):
            r = MagicMock()
            r.returncode = 0
            for token in cmd:
                if isinstance(token, str) and token.endswith(".mp4") and not token.startswith("-"):
                    Path(token).parent.mkdir(parents=True, exist_ok=True)
                    Path(token).write_text("fake")
            return r

        mock_run.side_effect = _fake_run

        rendered = render_scenes(
            project,
            remotion_dir=tmp_path / "remotion",
            output_dir=out_dir,
            tmpdir=tmp_path / "tmp",
        )

    assert len(rendered) == 1
    # Should be standalone scene (no compositing), rendered with yuva420p
    overlay_render_calls = [
        c for c in mock_run.call_args_list
        if "remotion" in " ".join(c[0][0])
        and "--pixel-format" in c[0][0]
        and "yuva420p" in c[0][0][c[0][0].index("--pixel-format") + 1]
    ]
    assert len(overlay_render_calls) >= 1


def test_render_scenes_overlay_after_non_overlay_works(tmp_path: Path):
    """Non-overlay scene after overlay composite renders normally."""
    from videoforge.engine.renderer import render_scenes

    s0 = SceneNode(
        id="s0", kind=SceneKind.TITLE,
        payload='{"title":"Base"}',
        engine_hint=Engine.REMOTION, duration_frames=90,
        narration=NarrationSpec("base", (), "estimated"),
    )
    s1 = SceneNode(
        id="s1", kind=SceneKind.OVERLAY_CTA,
        payload='{"title":"Overlay","cta":"Click"}',
        engine_hint=Engine.REMOTION, duration_frames=60,
        narration=NarrationSpec("cta", (), "estimated"),
    )
    s2 = SceneNode(
        id="s2", kind=SceneKind.OUTRO,
        payload='{"title":"The End"}',
        engine_hint=Engine.REMOTION, duration_frames=60,
        narration=NarrationSpec("end", (), "estimated"),
    )
    project = VideoProject("Multi", (s0, s1, s2), 30, 1920, 1080)

    with (
        patch("subprocess.run") as mock_run,
        patch("pathlib.Path.exists", return_value=True),
    ):
        out_dir = tmp_path / "out"

        def _fake_run(cmd, *a, **kw):
            r = MagicMock()
            r.returncode = 0
            for token in cmd:
                if isinstance(token, str) and token.endswith(".mp4") and not token.startswith("-"):
                    Path(token).parent.mkdir(parents=True, exist_ok=True)
                    Path(token).write_text("fake")
            return r

        mock_run.side_effect = _fake_run

        rendered = render_scenes(
            project,
            remotion_dir=tmp_path / "remotion",
            output_dir=out_dir,
            tmpdir=tmp_path / "tmp",
        )

    # 3 scenes: (base+overlay → composited) + outro = 2 clips
    assert len(rendered) == 2, f"Expected 2 clips, got {len(rendered)}"

    # First clip should be composited (base+overlay)
    assert "composited" in Path(rendered[0]).name
    # Second clip should be normal outro
    assert "composited" not in Path(rendered[1]).name
    assert Path(rendered[1]).suffix == ".mp4"