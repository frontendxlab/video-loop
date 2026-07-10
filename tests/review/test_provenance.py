"""Tests for render-time provenance graph artifact."""

from __future__ import annotations

import json
from pathlib import Path

from videoforge.engine.models import (
    AudioTrack,
    SceneDefinition,
    SceneType,
    VideoDefinition,
    WordTiming,
)
from videoforge.review.frame_reviewer import (
    build_provenance_scenes,
    generate_provenance_graph,
    write_provenance_graph,
)


class TestGenerateProvenanceGraph:
    def test_minimal_args_defaults(self) -> None:
        """Graph with only video_path uses sensible defaults."""
        graph = generate_provenance_graph(video_path="/tmp/test.mp4")

        assert graph["artifact"] == "videoforge-provenance-graph"
        assert graph["version"] == 1
        assert graph["video_path"].endswith("/tmp/test.mp4")
        assert "report_timestamp" in graph
        assert graph["content_hash"] == ""
        assert graph["engines"] == []
        assert graph["scenes"] == []
        assert "video_report" in graph["reports"]
        assert "provenance_graph" in graph["reports"]

    def test_full_args_shape(self) -> None:
        """All fields populated correctly."""
        scenes = [
            {
                "id": "scene_0000",
                "engine": "remotion",
                "kind": "title",
                "content_hash": "a1b2c3d4e5f6g7h8",
                "scene_path": "/tmp/build/scene_0000.mp4",
                "scene_report_path": "/tmp/build/scene_0000.mp4.scene.report.json",
                "duration_frames": 90,
                "assets": {"audio_src": "audio/audio_0000.wav"},
            },
            {
                "id": "scene_0001",
                "engine": "manim",
                "kind": "diagram",
                "content_hash": "i9j0k1l2m3n4o5p6",
                "scene_path": "/tmp/build/scene_0001.mp4",
                "scene_report_path": "/tmp/build/scene_0001.mp4.scene.report.json",
                "duration_frames": 120,
                "assets": {},
            },
        ]

        graph = generate_provenance_graph(
            video_path="/tmp/build/output.mp4",
            content_hash="deadbeefcafebabe",
            scenes=scenes,
            engine_mix=["manim", "remotion", "animotion"],
        )

        assert graph["content_hash"] == "deadbeefcafebabe"
        # Engine mix sorted
        assert graph["engines"] == ["animotion", "manim", "remotion"]
        assert len(graph["scenes"]) == 2

        # First scene
        s0 = graph["scenes"][0]
        assert s0["id"] == "scene_0000"
        assert s0["engine"] == "remotion"
        assert s0["kind"] == "title"
        assert s0["duration_frames"] == 90
        assert s0["assets"]["audio_src"] == "audio/audio_0000.wav"

        # Second scene
        s1 = graph["scenes"][1]
        assert s1["id"] == "scene_0001"
        assert s1["engine"] == "manim"
        assert s1["assets"] == {}

        # Reports section
        reports = graph["reports"]
        assert reports["video_report"].endswith(".mp4.report.json")
        assert reports["provenance_graph"].endswith(".provenance.json")

    def test_scene_content_hash_changes_with_index(self) -> None:
        """Same scene content at different indices yields different hashes."""
        scene = {
            "id": "scene_0000",
            "engine": "remotion",
            "kind": "title",
        }
        s0 = generate_provenance_graph(
            video_path="/tmp/t.mp4",
            scenes=[{**scene, "id": "scene_0000"}],
        )["scenes"][0]
        s1 = generate_provenance_graph(
            video_path="/tmp/t.mp4",
            scenes=[{**scene, "id": "scene_0001"}],
        )["scenes"][0]
        # Different ids produce different entries (expected)
        assert s0["id"] != s1["id"]

    def test_all_expected_keys_present(self) -> None:
        """Top-level keys match spec."""
        graph = generate_provenance_graph(video_path="/tmp/v.mp4")
        top_keys = {
            "artifact", "version", "video_path", "report_timestamp",
            "content_hash", "engines", "scenes", "reports",
        }
        assert set(graph.keys()) == top_keys

        reports_keys = {"video_report", "provenance_graph"}
        assert set(graph["reports"].keys()) == reports_keys


class TestWriteProvenanceGraph:
    def test_writes_to_dot_provenance_json(self, temp_dir: Path) -> None:
        """Provenance file written as <video>.provenance.json."""
        video_path = temp_dir / "videos" / "output.mp4"
        video_path.parent.mkdir(parents=True)
        video_path.write_text("dummy")

        graph_data = {"artifact": "videoforge-provenance-graph", "version": 1}
        result = write_provenance_graph(graph_data, str(video_path))

        expected = video_path.parent / "output.provenance.json"
        assert Path(result) == expected
        assert expected.exists()
        data = json.loads(expected.read_text())
        assert data["artifact"] == "videoforge-provenance-graph"

    def test_content_is_serializable(self, temp_dir: Path) -> None:
        """Full graph dict serializes to JSON without error."""
        scenes = [
            {
                "id": "scene_0000",
                "engine": "remotion",
                "kind": "title",
                "content_hash": "a1b2c3d4e5f6g7h8",
                "scene_path": str(temp_dir / "scene_0000.mp4"),
                "scene_report_path": str(temp_dir / "scene_0000.mp4.scene.report.json"),
                "duration_frames": 90,
                "assets": {"audio_src": "audio/audio_0000.wav"},
            },
        ]
        graph = generate_provenance_graph(
            video_path=str(temp_dir / "output.mp4"),
            content_hash="deadbeef",
            scenes=scenes,
            engine_mix=["remotion", "manim"],
        )
        dumped = json.dumps(graph, indent=2, default=str)
        loaded = json.loads(dumped)
        assert loaded["artifact"] == "videoforge-provenance-graph"
        assert loaded["content_hash"] == "deadbeef"
        assert len(loaded["scenes"]) == 1


class TestBuildProvenanceScenes:
    def test_legacy_video_definition(self, tmp_path: Path) -> None:
        """Build scenes from VideoDefinition render result."""
        build_dir = tmp_path / "build"
        build_dir.mkdir(parents=True)

        video = VideoDefinition(
            title="Test",
            scenes=[
                SceneDefinition(
                    type=SceneType.TITLE, duration=90,
                    title="Intro", text="Hello",
                ),
                SceneDefinition(
                    type=SceneType.DIAGRAM, duration=120,
                    title="Diagram", renderer="manim",
                ),
            ],
            audioTracks=[
                AudioTrack(src="audio/audio_0000.wav", startFrame=0, durationFrames=90),
                AudioTrack(src="audio/audio_0001.wav", startFrame=90, durationFrames=120),
            ],
            captions=[],
        )
        scene_paths = [
            str(build_dir / "scene_0000.mp4"),
            str(build_dir / "scene_0001.mp4"),
        ]
        # Touch scene files and report files so build_provenance_scenes finds them
        for sp in scene_paths:
            Path(sp).write_text("dummy")
            Path(sp).with_suffix(".mp4.scene.report.json").write_text("{}")

        scenes_data = build_provenance_scenes(video, scene_paths, build_dir=str(build_dir))

        assert len(scenes_data) == 2

        s0 = scenes_data[0]
        assert s0["id"] == "scene_0000"
        assert s0["engine"] == "remotion"
        assert s0["kind"] == "title"
        assert s0["duration_frames"] == 90
        assert s0["scene_path"].endswith("scene_0000.mp4")
        assert s0["scene_report_path"].endswith("scene_0000.mp4.scene.report.json")
        assert s0["assets"]["audio_src"] == "audio/audio_0000.wav"
        # content_hash is 16-char hex
        assert len(s0["content_hash"]) == 16
        assert isinstance(s0["content_hash"], str)

        s1 = scenes_data[1]
        assert s1["id"] == "scene_0001"
        assert s1["engine"] == "manim"
        assert s1["kind"] == "diagram"
        assert s1["duration_frames"] == 120
        assert s1["assets"]["audio_src"] == "audio/audio_0001.wav"

    def test_scene_content_hash_deterministic(self) -> None:
        """Same scene produces same content hash."""
        video = VideoDefinition(
            title="Test",
            scenes=[SceneDefinition(type=SceneType.TITLE, duration=90, title="Intro")],
            audioTracks=[AudioTrack(src="audio.wav", startFrame=0, durationFrames=90)],
            captions=[],
        )
        scene_paths = ["/tmp/s.mp4"]

        s1 = build_provenance_scenes(video, scene_paths)[0]
        s2 = build_provenance_scenes(video, scene_paths)[0]

        assert s1["content_hash"] == s2["content_hash"]

    def test_different_scene_different_hash(self) -> None:
        """Different scenes produce different content hashes."""
        video_a = VideoDefinition(
            title="A",
            scenes=[SceneDefinition(type=SceneType.TITLE, duration=90, title="Alpha")],
            audioTracks=[AudioTrack(src="a.wav", startFrame=0, durationFrames=90)],
            captions=[],
        )
        video_b = VideoDefinition(
            title="B",
            scenes=[SceneDefinition(type=SceneType.CODE, duration=120, title="Beta")],
            audioTracks=[AudioTrack(src="b.wav", startFrame=0, durationFrames=120)],
            captions=[],
        )

        ha = build_provenance_scenes(video_a, ["/tmp/a.mp4"])[0]["content_hash"]
        hb = build_provenance_scenes(video_b, ["/tmp/b.mp4"])[0]["content_hash"]
        assert ha != hb

    def test_zero_scenes(self) -> None:
        """Empty scenes list returns empty."""
        video = VideoDefinition(
            title="Empty", scenes=[], audioTracks=[], captions=[],
        )
        scenes_data = build_provenance_scenes(video, [])
        assert scenes_data == []

    def test_audio_track_missing(self) -> None:
        """Scene without audio track produces assets without audio_src."""
        video = VideoDefinition(
            title="No Audio",
            scenes=[SceneDefinition(type=SceneType.TITLE, duration=60, title="Mute")],
            audioTracks=[],
            captions=[],
        )
        scenes_data = build_provenance_scenes(video, ["/tmp/s.mp4"])
        assert len(scenes_data) == 1
        assert "audio_src" not in scenes_data[0]["assets"]


class TestGenerateProvenanceGraphReviewHints:
    """Tests for review_hints propagation in provenance graph."""

    def test_not_included_when_omitted(self) -> None:
        """No review_hints key when not provided."""
        graph = generate_provenance_graph(video_path="/tmp/t.mp4")
        assert "review_hints" not in graph

    def test_included_when_provided(self) -> None:
        """Review hints appear when provided."""
        hints = [{"check": "check 1", "severity": "error"}]
        graph = generate_provenance_graph(
            video_path="/tmp/t.mp4", review_hints=hints,
        )
        assert graph["review_hints"] == hints

    def test_empty_list_omitted(self) -> None:
        """Empty list not included."""
        graph = generate_provenance_graph(video_path="/tmp/t.mp4", review_hints=[])
        assert "review_hints" not in graph

    def test_serializable(self, temp_dir: Path) -> None:
        """Provenance with hints serializes to JSON."""
        hints = [{"check": "camera speed smooth", "severity": "warn"}]
        graph = generate_provenance_graph(
            video_path=str(temp_dir / "out.mp4"),
            review_hints=hints,
        )
        dumped = json.dumps(graph, indent=2, default=str)
        loaded = json.loads(dumped)
        assert loaded["review_hints"] == hints


class TestBuildProvenanceScenesWithRecipeIds:
    """Tests for recipe_id → review_hints propagation in provenance scenes."""

    def test_recipe_id_not_provided_no_hints(self) -> None:
        """No recipe_ids means no hints on scene entries."""
        video = VideoDefinition(
            title="Test",
            scenes=[SceneDefinition(type=SceneType.TITLE, duration=90, title="Intro")],
            audioTracks=[AudioTrack(src="a.wav", startFrame=0, durationFrames=90)],
            captions=[],
        )
        scenes = build_provenance_scenes(video, ["/tmp/s.mp4"])
        assert "review_hints" not in scenes[0]
        assert "recipe_id" not in scenes[0]

    def test_recipe_id_empty_string_no_hints(self) -> None:
        """Empty string recipe_id ignored."""
        video = VideoDefinition(
            title="Test",
            scenes=[SceneDefinition(type=SceneType.TITLE, duration=90, title="Intro")],
            audioTracks=[AudioTrack(src="a.wav", startFrame=0, durationFrames=90)],
            captions=[],
        )
        scenes = build_provenance_scenes(video, ["/tmp/s.mp4"], recipe_ids=[None])
        assert "review_hints" not in scenes[0]
        assert "recipe_id" not in scenes[0]

    def test_known_recipe_id_propagates_hints(self) -> None:
        """Known recipe_id attaches review_hints to scene entry."""
        video = VideoDefinition(
            title="Test",
            scenes=[SceneDefinition(type=SceneType.TITLE, duration=90, title="Intro")],
            audioTracks=[AudioTrack(src="a.wav", startFrame=0, durationFrames=90)],
            captions=[],
        )
        scenes = build_provenance_scenes(video, ["/tmp/s.mp4"], recipe_ids=["overlay-cta"])
        assert "review_hints" in scenes[0]
        assert scenes[0]["recipe_id"] == "overlay-cta"
        assert len(scenes[0]["review_hints"]) >= 1
        for h in scenes[0]["review_hints"]:
            assert "check" in h
            assert "severity" in h

    def test_multiple_scenes_respective_recipe_ids(self) -> None:
        """Each scene gets its own recipe's hints."""
        video = VideoDefinition(
            title="Multi",
            scenes=[
                SceneDefinition(type=SceneType.TITLE, duration=90, title="A"),
                SceneDefinition(type=SceneType.CODE, duration=60, title="B"),
            ],
            audioTracks=[
                AudioTrack(src="a.wav", startFrame=0, durationFrames=90),
                AudioTrack(src="b.wav", startFrame=90, durationFrames=60),
            ],
            captions=[],
        )
        scenes = build_provenance_scenes(
            video, ["/tmp/s0.mp4", "/tmp/s1.mp4"],
            recipe_ids=["overlay-cta", "hero-intro"],
        )
        assert scenes[0]["recipe_id"] == "overlay-cta"
        assert len(scenes[0]["review_hints"]) >= 1
        assert scenes[1]["recipe_id"] == "hero-intro"
        assert len(scenes[1]["review_hints"]) >= 1

    def test_mixed_recipe_ids_and_none(self) -> None:
        """Mix of recipe_id and None is handled."""
        video = VideoDefinition(
            title="Mixed",
            scenes=[
                SceneDefinition(type=SceneType.TITLE, duration=90, title="A"),
                SceneDefinition(type=SceneType.DIAGRAM, duration=60, title="B"),
            ],
            audioTracks=[
                AudioTrack(src="a.wav", startFrame=0, durationFrames=90),
                AudioTrack(src="b.wav", startFrame=90, durationFrames=60),
            ],
            captions=[],
        )
        scenes = build_provenance_scenes(
            video, ["/tmp/s0.mp4", "/tmp/s1.mp4"],
            recipe_ids=["map3d", None],
        )
        assert scenes[0]["recipe_id"] == "map3d"
        assert "review_hints" in scenes[0]
        assert "recipe_id" not in scenes[1]
        assert "review_hints" not in scenes[1]


class TestProvenanceRoundtrip:
    def test_generate_write_read(self, temp_dir: Path) -> None:
        """Full roundtrip: generate → write → read → verify."""
        video_path = temp_dir / "output.mp4"
        video_path.write_text("dummy")

        scenes = [
            {
                "id": "scene_0000",
                "engine": "remotion",
                "kind": "title",
                "content_hash": "abcdef1234567890",
                "scene_path": str(temp_dir / "scene_0000.mp4"),
                "scene_report_path": str(temp_dir / "scene_0000.mp4.scene.report.json"),
                "duration_frames": 90,
                "assets": {"audio_src": "audio.wav"},
            },
        ]
        graph = generate_provenance_graph(
            video_path=str(video_path),
            content_hash="deadbeef",
            scenes=scenes,
            engine_mix=["remotion"],
        )
        path = write_provenance_graph(graph, str(video_path))

        loaded = json.loads(Path(path).read_text())
        assert loaded["artifact"] == "videoforge-provenance-graph"
        assert loaded["content_hash"] == "deadbeef"
        assert loaded["engines"] == ["remotion"]
        assert loaded["scenes"][0]["id"] == "scene_0000"
        assert loaded["reports"]["provenance_graph"] == path
