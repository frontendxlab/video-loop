"""Engine-agnostic assembler wiring — render_scenes accepts VideoProject IR."""

from __future__ import annotations

import json
import inspect
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from videoforge.engine.renderer import render_scenes, _ir_scene_props, _mux_audio_track
from videoforge.engine.ir import (
    Engine, NarrationSpec, SceneKind, SceneNode, VideoProject, WordTiming,
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
