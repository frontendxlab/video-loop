"""Recipe payload builder tests — deterministic payload from recipe + content."""

from __future__ import annotations

import json

from videoforge.engine.recipes import clear_cache, get_recipe
from videoforge.orchestrator.recipe_payload import build_recipe_payload


def test_build_screenflow_payload():
    """screenflow recipe maps allowed_inputs to resolved payload."""
    clear_cache()
    content = {
        "showcase": {"kind": "screenflow", "screenshots": ["ui1.png", "ui2.png"]},
        "body": "Demo of new UI",
    }
    result = build_recipe_payload(content, "screenflow")
    assert result["recipe_id"] == "screenflow"
    assert result["entrance"] == "slide_in_right"
    assert result["exit_"] == "slide_out_left"
    assert result["engine_hint"] == "remotion"
    rp = result["recipe_payload"]
    assert rp.get("screenshots") == ["ui1.png", "ui2.png"]
    # callouts is non-required, not in content → None
    assert rp.get("callouts") is None


def test_build_dual_chart_payload():
    """dual-chart recipe maps bar_data/line_data from content."""
    clear_cache()
    content = {
        "showcase": {
            "kind": "dual-chart",
            "bar_data": [10, 20, 30],
            "line_data": [5, 15, 25],
            "chart_title": "Revenue vs Growth",
            "dual_axes": True,
        },
    }
    result = build_recipe_payload(content, "dual-chart")
    assert result["recipe_id"] == "dual-chart"
    assert result["engine_hint"] == "manim"
    rp = result["recipe_payload"]
    assert rp.get("bar_data") == [10, 20, 30]
    assert rp.get("line_data") == [5, 15, 25]
    assert rp.get("chart_title") == "Revenue vs Growth"
    assert rp.get("dual_axes") is True


def test_build_device_rise_payload():
    """device-rise recipe maps device_type from content."""
    clear_cache()
    content = {
        "showcase": {
            "kind": "device-rise",
            "device_type": "phone",
            "device_color": "#1a1a1a",
            "reflection_enabled": True,
        },
    }
    result = build_recipe_payload(content, "device-rise")
    assert result["recipe_id"] == "device-rise"
    assert result["entrance"] == "device_rise_in"
    assert result["exit_"] == "device_fall_out"
    rp = result["recipe_payload"]
    assert rp.get("device_type") == "phone"
    assert rp.get("device_color") == "#1a1a1a"
    assert rp.get("reflection_enabled") is True
    # rise_height is non-required, not in content → None
    assert rp.get("rise_height") is None


def test_build_audio_spectrum_payload():
    """audio-spectrum recipe maps audio_source and bar_count from content."""
    clear_cache()
    content = {
        "showcase": {
            "kind": "audio-spectrum",
            "audio_source": "/tmp/beat.wav",
            "bar_count": 64,
            "spectrum_style": "waveform",
        },
    }
    result = build_recipe_payload(content, "audio-spectrum")
    assert result["recipe_id"] == "audio-spectrum"
    rp = result["recipe_payload"]
    assert rp.get("audio_source") == "/tmp/beat.wav"
    assert rp.get("bar_count") == 64
    assert rp.get("spectrum_style") == "waveform"


def test_unknown_recipe_returns_empty():
    clear_cache()
    result = build_recipe_payload({"showcase": {"kind": "nope"}}, "nonexistent-recipe")
    assert result == {}


def test_missing_required_input_receives_default():
    """Required inputs that content doesn't provide get type-appropriate default."""
    clear_cache()
    content = {"showcase": {"kind": "device-rise"}}
    result = build_recipe_payload(content, "device-rise")
    rp = result["recipe_payload"]
    # device_type is required but missing from content → gets ""
    assert rp.get("device_type") == "", f"Expected '', got {rp.get('device_type')}"
    # Also check screen_content is optional → None
    assert rp.get("screen_content") is None


def test_pluck_from_showcase_subdict():
    """Payload builder prefers showcase.subdict over top-level content keys."""
    clear_cache()
    content = {
        "showcase": {
            "kind": "screenflow",
            "screenshots": ["from_showcase.png"],
        },
        "screenshots": ["from_root.png"],
    }
    result = build_recipe_payload(content, "screenflow")
    rp = result["recipe_payload"]
    assert rp.get("screenshots") == ["from_showcase.png"]


def test_payload_deterministic():
    """Same content + same recipe = same result."""
    clear_cache()
    content = {"showcase": {"kind": "dual-chart", "bar_data": [1, 2, 3]}}
    a = build_recipe_payload(content, "dual-chart")
    b = build_recipe_payload(content, "dual-chart")
    assert a == b
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
