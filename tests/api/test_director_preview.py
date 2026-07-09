"""Tests for director preview endpoint — IR scene graph exposed as live API."""

from __future__ import annotations

from fastapi.testclient import TestClient

from videoforge.api.app import create_app
from videoforge.engine.ir import Engine


def _client():
    return TestClient(create_app())


class TestDirectorPreviewEndpoint:
    """GET /api/director/preview contract tests."""

    def test_returns_200(self):
        resp = _client().get("/api/director/preview")
        assert resp.status_code == 200

    def test_content_type_json(self):
        resp = _client().get("/api/director/preview")
        assert resp.headers["content-type"].startswith("application/json")

    def test_top_level_keys(self):
        resp = _client().get("/api/director/preview")
        data = resp.json()
        expected = {"title", "fps", "width", "height", "audio_tracks", "scenes", "contentHash"}
        assert set(data.keys()) == expected

    def test_title(self):
        data = _client().get("/api/director/preview").json()
        assert data["title"] == "Introduction to Quantum Computing"

    def test_fps_and_dimensions(self):
        data = _client().get("/api/director/preview").json()
        assert data["fps"] == 30
        assert data["width"] == 1920
        assert data["height"] == 1080

    def test_has_five_scenes(self):
        data = _client().get("/api/director/preview").json()
        assert len(data["scenes"]) == 5

    def test_scene_keys(self):
        data = _client().get("/api/director/preview").json()
        expected = {"id", "kind", "payload", "engine_hint", "duration_frames",
                     "narration", "contentHash", "routedEngine"}
        for scene in data["scenes"]:
            assert set(scene.keys()) == expected, f"Bad keys in scene {scene['id']}"

    def test_scene_content_hash_present(self):
        data = _client().get("/api/director/preview").json()
        for scene in data["scenes"]:
            h = scene["contentHash"]
            assert isinstance(h, str) and len(h) == 16

    def test_scene_routed_engine_valid(self):
        data = _client().get("/api/director/preview").json()
        valid = {e.value for e in Engine}
        for scene in data["scenes"]:
            assert scene["routedEngine"] in valid, f"Bad engine in {scene['id']}"

    def test_scene_kind_string(self):
        data = _client().get("/api/director/preview").json()
        for scene in data["scenes"]:
            assert isinstance(scene["kind"], str)

    def test_narration_structure(self):
        data = _client().get("/api/director/preview").json()
        for scene in data["scenes"]:
            n = scene["narration"]
            assert {"text", "words", "source"} == set(n.keys())
            assert isinstance(n["text"], str)
            assert isinstance(n["words"], list)
            assert n["source"] in ("forced_align", "exact_synthesis", "estimated")

    def test_audio_tracks(self):
        data = _client().get("/api/director/preview").json()
        assert len(data["audio_tracks"]) == 1
        track = data["audio_tracks"][0]
        assert {"src", "startFrame", "durationFrames"} == set(track.keys())
        assert track["src"] == "tts/output.wav"
        assert track["startFrame"] == 0
        assert track["durationFrames"] == 540

    def test_content_hash_stable(self):
        client = _client()
        hash1 = client.get("/api/director/preview").json()["contentHash"]
        hash2 = client.get("/api/director/preview").json()["contentHash"]
        assert hash1 == hash2

    def test_scene_0_routed_to_remotion(self):
        data = _client().get("/api/director/preview").json()
        assert data["scenes"][0]["routedEngine"] == "remotion"

    def test_scene_2_diagram_math_graph_routed_to_manim(self):
        data = _client().get("/api/director/preview").json()
        assert data["scenes"][2]["routedEngine"] == "manim"

    def test_scene_3_chart_routed_to_manim(self):
        data = _client().get("/api/director/preview").json()
        assert data["scenes"][3]["routedEngine"] == "manim"

    def test_scene_4_outro_routed_to_remotion(self):
        data = _client().get("/api/director/preview").json()
        assert data["scenes"][4]["routedEngine"] == "remotion"
