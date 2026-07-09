"""IR tests — hash stability, sensitivity, legacy conversion."""

from __future__ import annotations

from videoforge.engine.ir import (
    AudioTrackIR,
    Engine,
    NarrationSpec,
    SceneKind,
    SceneNode,
    VideoProject,
    WordTiming,
)
from videoforge.engine.models import (
    AudioTrack,
    SceneDefinition,
    SceneType,
    VideoDefinition,
    WordTiming as LegacyWordTiming,
)


def _node(scene_id: str = "scene_0", kind: SceneKind = SceneKind.TITLE) -> SceneNode:
    payload = '{"title":"Hi","text":"hello world"}'
    narration = NarrationSpec(
        text="hello world",
        words=(WordTiming("hello", 0, 200), WordTiming("world", 200, 400)),
        source="estimated",
    )
    return SceneNode(
        id=scene_id, kind=kind, payload=payload,
        engine_hint=Engine.REMOTION, duration_frames=90, narration=narration,
    )


def test_scene_node_hash_stable():
    assert _node().content_hash() == _node().content_hash()


def test_scene_node_hash_sensitive_to_id():
    a = _node("scene_0")
    b = _node("scene_1")
    assert a.content_hash() != b.content_hash()


def test_scene_node_hash_sensitive_to_payload():
    a = _node()
    b = SceneNode(
        id="scene_0", kind=SceneKind.TITLE, payload='{"title":"Bye"}',
        engine_hint=Engine.REMOTION, duration_frames=90,
        narration=NarrationSpec("hi", (), "estimated"),
    )
    assert a.content_hash() != b.content_hash()


def test_scene_node_hash_sensitive_to_duration():
    a = _node()
    b = SceneNode(
        id="scene_0", kind=SceneKind.TITLE, payload=a.payload,
        engine_hint=Engine.REMOTION, duration_frames=100,
        narration=a.narration,
    )
    assert a.content_hash() != b.content_hash()


def test_scene_node_frozen():
    n = _node()
    try:
        n.id = "x"  # type: ignore[misc]
    except Exception:
        return
    raise AssertionError("SceneNode should be frozen")


def test_video_project_hash_stable():
    p = VideoProject("T", (_node("s0"), _node("s1")), 30, 1920, 1080)
    assert p.content_hash() == p.content_hash()


def test_video_project_hash_sensitive_to_title():
    a = VideoProject("A", (_node(),), 30, 1920, 1080)
    b = VideoProject("B", (_node(),), 30, 1920, 1080)
    assert a.content_hash() != b.content_hash()


def test_video_project_hash_sensitive_to_scenes():
    a = VideoProject("T", (_node("s0"),), 30, 1920, 1080)
    b = VideoProject("T", (_node("s0"), _node("s1")), 30, 1920, 1080)
    assert a.content_hash() != b.content_hash()


def test_payload_dict_roundtrip():
    n = _node()
    d = n.payload_dict()
    assert d["title"] == "Hi"


def _legacy_video() -> VideoDefinition:
    return VideoDefinition(
        title="Legacy",
        scenes=[
            SceneDefinition(
                type=SceneType.TITLE, duration=90, title="Intro",
                text="Hello.", wordTimestamps=[LegacyWordTiming("Hello.", 0, 400)],
            ),
            SceneDefinition(
                type=SceneType.BULLET, duration=120, title="Pts",
                points=["a", "b"], text="Two points.",
            ),
        ],
        audioTracks=[AudioTrack("a.wav", 0, 90)],
        captions=[],
    )


def test_from_legacy_maps_kinds():
    vp = VideoProject.from_legacy(_legacy_video())
    assert vp.title == "Legacy"
    assert len(vp.scenes) == 2
    assert vp.scenes[0].kind == SceneKind.TITLE
    assert vp.scenes[1].kind == SceneKind.BULLETS


def test_from_legacy_preserves_timings():
    vp = VideoProject.from_legacy(_legacy_video())
    words = vp.scenes[0].narration.words
    assert len(words) == 1
    assert words[0].text == "Hello."
    assert words[0].startMs == 0


def test_from_legacy_preserves_fps_dims():
    vp = VideoProject.from_legacy(_legacy_video())
    assert vp.fps == 30
    assert vp.width == 1920
    assert vp.height == 1080


def test_from_legacy_preserves_audio_tracks():
    vp = VideoProject.from_legacy(_legacy_video())
    assert len(vp.audio_tracks) == 1
    assert vp.audio_tracks[0].src == "a.wav"
    assert vp.audio_tracks[0].startFrame == 0
    assert vp.audio_tracks[0].durationFrames == 90


def test_video_project_hash_sensitive_to_audio():
    a = VideoProject("T", (_node(),), 30, 1920, 1080)
    b = VideoProject("T", (_node(),), 30, 1920, 1080,
                     audio_tracks=(AudioTrackIR("bgm.mp3", 0, 90),))
    assert a.content_hash() != b.content_hash()


def test_audio_track_frozen():
    t = AudioTrackIR("a.wav", 0, 90)
    try:
        t.src = "b.wav"  # type: ignore[misc]
    except Exception:
        return
    raise AssertionError("AudioTrackIR should be frozen")
