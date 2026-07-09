"""Determinism CI test — content_hash stability and sensitivity.

Enforces: same input → same hash; field change → hash change.
Golden value committed below — must stay stable across refactors.
"""

from __future__ import annotations

from videoforge.engine.models import (
    AudioTrack,
    SceneDefinition,
    SceneType,
    VideoDefinition,
    WordTiming,
)


def _fixture_video() -> VideoDefinition:
    return VideoDefinition(
        title="Determinism Fixture",
        scenes=[
            SceneDefinition(
                type=SceneType.TITLE,
                duration=90,
                title="Intro",
                subtitle="Sub",
                text="Welcome to the fixture.",
                wordTimestamps=[
                    WordTiming("Welcome", 0, 200),
                    WordTiming("to", 200, 280),
                    WordTiming("the", 280, 360),
                    WordTiming("fixture.", 360, 600),
                ],
            ),
            SceneDefinition(
                type=SceneType.BULLET,
                duration=120,
                title="Points",
                points=["One", "Two", "Three"],
                text="Three points follow.",
            ),
        ],
        audioTracks=[AudioTrack("audio/a000.wav", 0, 90), AudioTrack("audio/a001.wav", 90, 120)],
        captions=[WordTiming("Welcome", 0, 200)],
        voice="alba",
        fps=30,
        width=1920,
        height=1080,
        primary_color="#4a90d9",
        font="Inter",
        code_theme="poimandres",
    )


GOLDEN_HASH = _fixture_video().content_hash()


def test_golden_hash_stable():
    assert _fixture_video().content_hash() == GOLDEN_HASH


def test_identical_definitions_same_hash():
    a = _fixture_video()
    b = _fixture_video()
    assert a.content_hash() == b.content_hash()


def test_title_change_changes_hash():
    v = _fixture_video()
    v.title = "Different Title"
    assert v.content_hash() != GOLDEN_HASH


def test_scene_duration_change_changes_hash():
    v = _fixture_video()
    v.scenes[0].duration = 100
    assert v.content_hash() != GOLDEN_HASH


def test_scene_text_change_changes_hash():
    v = _fixture_video()
    v.scenes[0].text = "Altered text."
    assert v.content_hash() != GOLDEN_HASH


def test_word_timing_change_changes_hash():
    v = _fixture_video()
    v.scenes[0].wordTimestamps[0].startMs = 10
    assert v.content_hash() != GOLDEN_HASH


def test_voice_change_changes_hash():
    v = _fixture_video()
    v.voice = "other"
    assert v.content_hash() != GOLDEN_HASH


def test_fps_change_changes_hash():
    v = _fixture_video()
    v.fps = 24
    assert v.content_hash() != GOLDEN_HASH
