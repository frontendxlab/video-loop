"""Tests for PipelineRunner — verifies real TTS/render/concat wiring."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import ANY, MagicMock, patch

import pytest

from videoforge.engine.models import (
    AudioTrack,
    SceneDefinition,
    SceneType,
    VideoDefinition,
    WordTiming,
)
from videoforge.orchestrator.runner import (
    AgentStatus,
    PipelineRunner,
    Stage,
)


# ─── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture
def runner() -> PipelineRunner:
    return PipelineRunner()


@pytest.fixture
def sample_scenes() -> list[dict]:
    return [
        {"type": "title", "title": "Intro", "text": "Welcome to the video."},
        {"type": "code", "title": "Code Example", "text": "Here is some code."},
    ]


def _fake_tts_result(duration: float = 2.0, word_count: int = 5) -> dict:
    words = [f"word{i}" for i in range(word_count)]
    per_word = (duration * 1000) / word_count
    return {
        "audio_path": "/tmp/fake/audio.wav",
        "duration_seconds": duration,
        "sample_rate": 24000,
        "word_timestamps": [
            {"text": w, "startMs": round(i * per_word), "endMs": round((i + 1) * per_word)}
            for i, w in enumerate(words)
        ],
        "alignment_metadata": {"source": "test", "confidence": 0.5, "fallback_used": True},
    }


# ─── _build_video_def tests ───────────────────────────────────────────────


class TestBuildVideoDef:
    def test_builds_from_enriched_scenes(self, runner: PipelineRunner):
        scenes = [
            {
                "type": "title",
                "title": "Intro",
                "text": "Hello world",
                "duration": 90,
                "audio_path": "/tmp/audio/scene_0000.wav",
                "wordTimestamps": [
                    {"text": "Hello", "startMs": 0, "endMs": 500},
                    {"text": "world", "startMs": 500, "endMs": 1000},
                ],
            }
        ]
        video_def = runner._build_video_def("Test Video", scenes)
        assert isinstance(video_def, VideoDefinition)
        assert video_def.title == "Test Video"
        assert len(video_def.scenes) == 1
        assert video_def.scenes[0].type == SceneType.TITLE
        assert video_def.scenes[0].duration == 90
        assert len(video_def.audioTracks) == 1
        assert video_def.audioTracks[0].src == "/tmp/audio/scene_0000.wav"
        assert video_def.audioTracks[0].startFrame == 0
        assert video_def.fps == 30

    def test_no_audio_path_skips_track(self, runner: PipelineRunner):
        scenes = [{"type": "title", "title": "No Audio", "duration": 60}]
        video_def = runner._build_video_def("Test", scenes)
        assert len(video_def.audioTracks) == 0

    def test_empty_scenes(self, runner: PipelineRunner):
        video_def = runner._build_video_def("Empty", [])
        assert video_def.title == "Empty"
        assert len(video_def.scenes) == 0
        assert len(video_def.audioTracks) == 0

    def test_offset_accumulates(self, runner: PipelineRunner):
        scenes = [
            {"type": "title", "title": "S1", "duration": 90, "audio_path": "/a/1.wav", "wordTimestamps": []},
            {"type": "code", "title": "S2", "duration": 60, "audio_path": "/a/2.wav", "wordTimestamps": []},
        ]
        video_def = runner._build_video_def("Multi", scenes)
        assert video_def.scenes[0].sceneStartFrame == 0
        assert video_def.scenes[1].sceneStartFrame == 90


# ─── run_pipeline tests (with mocks) ──────────────────────────────────────


class TestPipelineRunner:
    @patch("videoforge.orchestrator.runner.generate_audio")
    @patch("videoforge.orchestrator.runner.render_scenes")
    @patch("videoforge.orchestrator.runner.concatenate_scenes")
    async def test_full_pipeline_calls_real_functions(
        self,
        mock_concat: MagicMock,
        mock_render: MagicMock,
        mock_tts: MagicMock,
        runner: PipelineRunner,
        tmp_path: Path,
    ):
        """Pipeline calls generate_audio, render_scenes, concatenate_scenes."""
        output = tmp_path / "final.mp4"
        mock_tts.side_effect = lambda text, path, voice, tts_url: _fake_tts_result(duration=1.0)
        mock_render.return_value = [str(tmp_path / "build/scene_0000.mp4")]
        mock_concat.return_value = str(output)

        result = await runner.run_pipeline(
            topic="Test topic",
            scenes_json="",
            voice="alba",
            tts_url="http://tts:8000",
            output_path=str(output),
            remotion_dir=str(tmp_path),
            fps=30,
        )

        assert result == str(output)
        # TTS called with scene text
        mock_tts.assert_called_once()
        # render_scenes called with VideoDefinition
        mock_render.assert_called_once()
        args, _ = mock_render.call_args
        video_def = args[0]
        assert isinstance(video_def, VideoDefinition)
        assert video_def.title == "Test topic"
        assert len(video_def.scenes) == 1  # default scene
        # concat called with scene paths
        mock_concat.assert_called_once_with(
            [str(tmp_path / "build/scene_0000.mp4")], str(output)
        )

    @patch("videoforge.orchestrator.runner.generate_audio")
    @patch("videoforge.orchestrator.runner.render_scenes")
    @patch("videoforge.orchestrator.runner.concatenate_scenes")
    async def test_tts_called_per_scene(
        self,
        mock_concat: MagicMock,
        mock_render: MagicMock,
        mock_tts: MagicMock,
        runner: PipelineRunner,
        tmp_path: Path,
    ):
        """Each scene gets TTS with correct text and voice."""
        scenes_json = tmp_path / "scenes.json"
        scenes_json.write_text('''[
            {"type": "title", "title": "Scene1", "text": "First scene text."},
            {"type": "code", "title": "Scene2", "text": "Second scene code."}
        ]''')
        mock_tts.side_effect = lambda text, path, voice, tts_url: {
            **_fake_tts_result(duration=1.5),
            "word_timestamps": [
                {"text": w, "startMs": i * 500, "endMs": (i + 1) * 500}
                for i, w in enumerate(text.split())
            ],
        }
        mock_render.return_value = [
            str(tmp_path / "build/scene_0000.mp4"),
            str(tmp_path / "build/scene_0001.mp4"),
        ]
        mock_concat.return_value = str(tmp_path / "final.mp4")

        await runner.run_pipeline(
            topic="Multi scene",
            scenes_json=str(scenes_json),
            voice="custom-voice",
            output_path=str(tmp_path / "final.mp4"),
            remotion_dir=str(tmp_path),
        )

        assert mock_tts.call_count == 2
        call_texts = [c[0][0] for c in mock_tts.call_args_list]
        assert "First scene text." in call_texts
        assert "Second scene code." in call_texts
        # Voice passed through
        for c in mock_tts.call_args_list:
            assert c[0][2] == "custom-voice"  # voice is 3rd positional arg

    @patch("videoforge.orchestrator.runner.generate_audio")
    @patch("videoforge.orchestrator.runner.render_scenes")
    @patch("videoforge.orchestrator.runner.concatenate_scenes")
    async def test_cancel_stops_pipeline(
        self,
        mock_concat: MagicMock,
        mock_render: MagicMock,
        mock_tts: MagicMock,
        runner: PipelineRunner,
        tmp_path: Path,
    ):
        """Cancel flag stops mid-pipeline and returns early."""
        runner.cancel()
        mock_tts.side_effect = RuntimeError("should not be called")

        result = await runner.run_pipeline(
            topic="Cancelled",
            output_path=str(tmp_path / "final.mp4"),
        )

        # Should return early without calling TTS/render/concat
        mock_tts.assert_not_called()
        mock_render.assert_not_called()
        mock_concat.assert_not_called()

    @patch("videoforge.orchestrator.runner.generate_audio")
    @patch("videoforge.orchestrator.runner.render_scenes")
    @patch("videoforge.orchestrator.runner.concatenate_scenes")
    async def test_stage_callbacks_fire(
        self,
        mock_concat: MagicMock,
        mock_render: MagicMock,
        mock_tts: MagicMock,
        tmp_path: Path,
    ):
        """Stage callback receives transition events."""
        events: list[tuple[str, str, float, str]] = []
        runner = PipelineRunner(
            stage_callback=lambda stage, status, progress, msg: events.append((stage, status, progress, msg))
        )
        mock_tts.side_effect = lambda text, path, voice, tts_url: _fake_tts_result(duration=0.5)
        mock_render.return_value = [str(tmp_path / "build/scene_0000.mp4")]
        mock_concat.return_value = str(tmp_path / "final.mp4")

        await runner.run_pipeline(topic="Events", output_path=str(tmp_path / "final.mp4"))

        stage_names = {s for s, _, _, _ in events}
        assert "grill" in stage_names
        assert "plan" in stage_names
        assert "tts" in stage_names
        assert "timing" in stage_names
        assert "render" in stage_names
        assert "concat" in stage_names
        assert "done" in stage_names

        # Check all complete
        complete_stages = {s for s, st, _, _ in events if st == "complete"}
        assert len(complete_stages) >= 6

    @patch("videoforge.orchestrator.runner.generate_audio")
    @patch("videoforge.orchestrator.runner.render_scenes")
    @patch("videoforge.orchestrator.runner.concatenate_scenes")
    async def test_tts_error_propagates(
        self,
        mock_concat: MagicMock,
        mock_render: MagicMock,
        mock_tts: MagicMock,
        runner: PipelineRunner,
        tmp_path: Path,
    ):
        """TTS failure propagates up."""
        mock_tts.side_effect = RuntimeError("TTS server unreachable")

        with pytest.raises(RuntimeError, match="TTS server unreachable"):
            await runner.run_pipeline(
                topic="Fail TTS",
                output_path=str(tmp_path / "final.mp4"),
            )

    @patch("videoforge.orchestrator.runner.generate_audio")
    @patch("videoforge.orchestrator.runner.render_scenes")
    @patch("videoforge.orchestrator.runner.concatenate_scenes")
    async def test_render_error_propagates(
        self,
        mock_concat: MagicMock,
        mock_render: MagicMock,
        mock_tts: MagicMock,
        runner: PipelineRunner,
        tmp_path: Path,
    ):
        """Render failure propagates up."""
        mock_tts.side_effect = lambda text, path, voice, tts_url: _fake_tts_result(duration=0.5)
        mock_render.side_effect = RuntimeError("Remotion render failed")

        with pytest.raises(RuntimeError, match="Remotion render failed"):
            await runner.run_pipeline(
                topic="Fail Render",
                output_path=str(tmp_path / "final.mp4"),
            )
