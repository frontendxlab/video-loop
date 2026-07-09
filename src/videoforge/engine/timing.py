"""Timing engine — deterministic frame-to-audio computation.

Converts word-level timestamps to animation progress values.
This is the core of audio-synced animations.
"""

from __future__ import annotations

from videoforge.engine.models import TimelineStep, WordTiming


def get_progress(
    current_frame: int,
    fps: int,
    step_start_ms: float,
    step_end_ms: float,
    scene_start_frame: int,
) -> float:
    """Compute animation progress (0 to 1) within an audio time window.

    Args:
        current_frame: Current frame number in the composition.
        fps: Frames per second.
        step_start_ms: When this animation step starts in the audio.
        step_end_ms: When this animation step ends in the audio.
        scene_start_frame: The composition frame where this scene starts.

    Returns:
        0.0 before the step starts, 1.0 after it ends, 0→1 during.
    """
    current_ms = ((current_frame - scene_start_frame) / fps) * 1000
    if current_ms < step_start_ms:
        return 0.0
    if current_ms >= step_end_ms:
        return 1.0
    duration = step_end_ms - step_start_ms
    if duration <= 0:
        return 1.0
    return (current_ms - step_start_ms) / duration


def build_timeline(
    words: list[WordTiming],
    words_per_step: int = 5,
) -> list[TimelineStep]:
    """Group word timestamps into timeline steps.

    Each step represents an animation phase (e.g., one bullet point, one code line).
    """
    steps: list[TimelineStep] = []
    if not words:
        return steps

    for i in range(0, len(words), words_per_step):
        chunk = words[i : i + words_per_step]
        start_ms = chunk[0].startMs
        end_ms = chunk[-1].endMs
        label = " ".join(w.text for w in chunk)
        steps.append(TimelineStep(
            startMs=start_ms,
            endMs=end_ms,
            durationMs=end_ms - start_ms,
            label=label,
        ))
    return steps


def get_active_step(
    current_frame: int,
    fps: int,
    steps: list[TimelineStep],
    scene_start_frame: int,
) -> int:
    """Return the index of the currently active timeline step."""
    if not steps:
        return -1
    current_ms = ((current_frame - scene_start_frame) / fps) * 1000
    for i in range(len(steps) - 1, -1, -1):
        if current_ms >= steps[i].startMs:
            return i
    return -1


def ms_to_frame(ms: float, fps: int) -> int:
    """Convert milliseconds to frame number."""
    return int(ms / 1000 * fps)


def frame_to_ms(frame: int, fps: int) -> float:
    """Convert frame number to milliseconds."""
    return (frame / fps) * 1000
