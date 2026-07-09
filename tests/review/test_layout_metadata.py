"""Tests for layout metadata model and overlap gate converters."""

from __future__ import annotations

import json

import pytest

from videoforge.review.layout_metadata import (
    LayoutElement,
    LayoutMetadata,
    dict_to_element,
    dicts_to_layout_metadata,
    element_to_box,
    element_to_dict,
    layout_metadata_to_boxes,
    layout_metadata_to_element_dicts,
    scene_payload_to_layout_metadata,
)
from videoforge.review.overlap_gate import OverlapGate


# ── LayoutElement model ──────────────────────────────────────────────────────────


class TestLayoutElement:
    def test_minimal_construction(self) -> None:
        el = LayoutElement(id="a", x=10.0, y=20.0, width=100.0, height=50.0)
        assert el.id == "a"
        assert el.x == 10.0
        assert el.y == 20.0
        assert el.width == 100.0
        assert el.height == 50.0
        assert el.z_index == 0  # default
        assert el.type_hint == "shape"  # default

    def test_full_construction(self) -> None:
        el = LayoutElement(
            id="b", x=5.5, y=10.2, width=200.0, height=80.0,
            z_index=3, type_hint="text",
        )
        assert el.z_index == 3
        assert el.type_hint == "text"

    def test_frozen(self) -> None:
        el = LayoutElement(id="c", x=0, y=0, width=10, height=10)
        with pytest.raises(AttributeError):
            el.x = 99  # type: ignore[misc]

    def test_int_coords_accepted(self) -> None:
        # Python dataclass float annotation does not coerce; int values
        # are stored as int but work correctly in numeric contexts.
        el = LayoutElement(id="d", x=1, y=2, width=100, height=50)
        assert isinstance(el.x, (int, float))
        assert isinstance(el.y, (int, float))
        assert isinstance(el.width, (int, float))
        assert isinstance(el.height, (int, float))
        # element_to_box handles both int and float
        from videoforge.review.layout_metadata import element_to_box
        box = element_to_box(el)
        assert all(isinstance(v, float) for v in box)


# ── LayoutMetadata model ────────────────────────────────────────────────────────


class TestLayoutMetadata:
    def test_minimal_construction(self) -> None:
        meta = LayoutMetadata(elements=())
        assert meta.elements == ()
        assert meta.viewport_w == 1920.0
        assert meta.viewport_h == 1080.0

    def test_custom_viewport(self) -> None:
        el = LayoutElement(id="a", x=0, y=0, width=100, height=100)
        meta = LayoutMetadata(
            elements=(el,),
            viewport_w=1280.0,
            viewport_h=720.0,
        )
        assert meta.viewport_w == 1280.0
        assert meta.viewport_h == 720.0

    def test_frozen(self) -> None:
        meta = LayoutMetadata(elements=())
        with pytest.raises(AttributeError):
            meta.viewport_w = 999  # type: ignore[misc]


# ── element_to_box ──────────────────────────────────────────────────────────────


class TestElementToBox:
    def test_simple(self) -> None:
        el = LayoutElement(id="a", x=10, y=20, width=100, height=50)
        assert element_to_box(el) == (10.0, 20.0, 110.0, 70.0)

    def test_zero_sized_element(self) -> None:
        el = LayoutElement(id="z", x=0, y=0, width=0, height=0)
        assert element_to_box(el) == (0.0, 0.0, 0.0, 0.0)

    def test_negative_position(self) -> None:
        el = LayoutElement(id="neg", x=-50, y=-30, width=100, height=60)
        assert element_to_box(el) == (-50.0, -30.0, 50.0, 30.0)


# ── element_to_dict / dict_to_element roundtrip ─────────────────────────────────


class TestElementDictRoundtrip:
    def test_roundtrip(self) -> None:
        original = LayoutElement(
            id="r1", x=15.5, y=25.3, width=120.0, height=70.0,
            z_index=2, type_hint="image",
        )
        d = element_to_dict(original)
        restored = dict_to_element(d)
        assert restored == original

    def test_roundtrip_defaults(self) -> None:
        original = LayoutElement(id="r2", x=0, y=0, width=50, height=50)
        d = element_to_dict(original)
        restored = dict_to_element(d)
        assert restored == original

    def test_dict_to_element_missing_x(self) -> None:
        assert dict_to_element({"y": 10, "width": 100, "height": 50}) is None

    def test_dict_to_element_missing_y(self) -> None:
        assert dict_to_element({"x": 10, "width": 100, "height": 50}) is None

    def test_dict_to_element_missing_width(self) -> None:
        assert dict_to_element({"x": 10, "y": 10, "height": 50}) is None

    def test_dict_to_element_missing_height(self) -> None:
        assert dict_to_element({"x": 10, "y": 10, "width": 100}) is None

    def test_dict_to_element_empty(self) -> None:
        assert dict_to_element({}) is None

    def test_dict_to_element_extra_keys_ignored(self) -> None:
        el = dict_to_element({
            "x": 10, "y": 20, "width": 100, "height": 50,
            "color": "red", "opacity": 0.8,
        })
        assert el is not None
        assert el.id == ""
        assert el.x == 10.0
        assert el.y == 20.0
        assert el.width == 100.0
        assert el.height == 50.0

    def test_dict_to_element_string_id(self) -> None:
        el = dict_to_element({
            "id": "my-label", "x": 0, "y": 0, "width": 50, "height": 50,
        })
        assert el is not None
        assert el.id == "my-label"

    def test_dict_to_element_int_id_converted_to_str(self) -> None:
        el = dict_to_element({
            "id": 42, "x": 0, "y": 0, "width": 50, "height": 50,
        })
        assert el is not None
        assert el.id == "42"


# ── dicts_to_layout_metadata ────────────────────────────────────────────────────


class TestDictsToLayoutMetadata:
    def test_empty_list(self) -> None:
        meta = dicts_to_layout_metadata([])
        assert meta.elements == ()
        assert meta.viewport_w == 1920.0
        assert meta.viewport_h == 1080.0

    def test_mixed_valid_invalid(self) -> None:
        dicts = [
            {"id": "good", "x": 0, "y": 0, "width": 100, "height": 50},
            {"id": "bad", "x": 0, "y": 0},  # missing width/height
            {"id": "also_good", "x": 50, "y": 50, "width": 200, "height": 100},
        ]
        meta = dicts_to_layout_metadata(dicts, viewport_w=1280, viewport_h=720)
        assert len(meta.elements) == 2
        assert meta.elements[0].id == "good"
        assert meta.elements[1].id == "also_good"
        assert meta.viewport_w == 1280.0
        assert meta.viewport_h == 720.0

    def test_custom_viewport(self) -> None:
        meta = dicts_to_layout_metadata([], viewport_w=800, viewport_h=600)
        assert meta.viewport_w == 800.0
        assert meta.viewport_h == 600.0


# ── layout_metadata_to_boxes / layout_metadata_to_element_dicts ─────────────────


class TestMetadataCollectionConverters:
    def test_metadata_to_boxes(self) -> None:
        els = (
            LayoutElement(id="a", x=0, y=0, width=100, height=50),
            LayoutElement(id="b", x=50, y=25, width=100, height=50),
        )
        meta = LayoutMetadata(elements=els)
        boxes = layout_metadata_to_boxes(meta)
        assert boxes == [(0.0, 0.0, 100.0, 50.0), (50.0, 25.0, 150.0, 75.0)]

    def test_metadata_to_element_dicts(self) -> None:
        els = (
            LayoutElement(
                id="x", x=10, y=20, width=100, height=50,
                z_index=1, type_hint="text",
            ),
        )
        meta = LayoutMetadata(elements=els)
        dicts = layout_metadata_to_element_dicts(meta)
        assert len(dicts) == 1
        assert dicts[0]["id"] == "x"
        assert dicts[0]["x"] == 10.0
        assert dicts[0]["z_index"] == 1
        assert dicts[0]["type_hint"] == "text"

    def test_empty_metadata(self) -> None:
        meta = LayoutMetadata(elements=())
        assert layout_metadata_to_boxes(meta) == []
        assert layout_metadata_to_element_dicts(meta) == []


# ── scene_payload_to_layout_metadata ─────────────────────────────────────────────


class TestScenePayloadToLayoutMetadata:
    def test_empty_payload(self) -> None:
        meta = scene_payload_to_layout_metadata("{}")
        assert meta.elements == ()
        assert meta.viewport_w == 1920.0
        assert meta.viewport_h == 1080.0

    def test_elements_in_payload(self) -> None:
        payload = json.dumps({
            "width": 1920,
            "height": 1080,
            "elements": [
                {"id": "title", "x": 100, "y": 50, "width": 800, "height": 100},
                {"id": "body", "x": 100, "y": 200, "width": 800, "height": 400},
            ],
        })
        meta = scene_payload_to_layout_metadata(payload)
        assert len(meta.elements) == 2
        assert meta.elements[0].id == "title"
        assert meta.elements[1].id == "body"
        assert meta.viewport_w == 1920.0
        assert meta.viewport_h == 1080.0

    def test_partial_elements_skipped(self) -> None:
        payload = json.dumps({
            "elements": [
                {"id": "valid", "x": 0, "y": 0, "width": 100, "height": 100},
                {"id": "invalid", "x": 50},  # missing y, width, height
            ],
        })
        meta = scene_payload_to_layout_metadata(payload)
        assert len(meta.elements) == 1
        assert meta.elements[0].id == "valid"

    def test_non_list_elements(self) -> None:
        payload = json.dumps({"elements": "not_a_list"})
        meta = scene_payload_to_layout_metadata(payload)
        assert meta.elements == ()

    def test_custom_default_viewport(self) -> None:
        meta = scene_payload_to_layout_metadata(
            "{}",
            default_viewport_w=1280.0,
            default_viewport_h=720.0,
        )
        assert meta.viewport_w == 1280.0
        assert meta.viewport_h == 720.0


# ── Integration: model converters feed OverlapGate directly ──────────────────────


class TestOverlapGateIntegration:
    def test_element_dicts_via_gate_run(self) -> None:
        """LayoutMetadata → dicts → OverlapGate.run() detects overlaps."""
        els = (
            LayoutElement(id="a", x=0, y=0, width=200, height=200),
            LayoutElement(id="b", x=50, y=50, width=200, height=200),
        )
        meta = LayoutMetadata(elements=els, viewport_w=1920, viewport_h=1080)
        dicts = layout_metadata_to_element_dicts(meta)

        gate = OverlapGate()
        result = gate.run(dicts)
        assert result["passed"] is False
        assert any(i["type"] == "overlap" for i in result["issues"])

    def test_boxes_via_compute_overlaps(self) -> None:
        """LayoutMetadata → boxes → OverlapGate.compute_overlaps()."""
        els = (
            LayoutElement(id="a", x=0, y=0, width=100, height=100),
            LayoutElement(id="b", x=200, y=200, width=100, height=100),
        )
        meta = LayoutMetadata(elements=els)
        boxes = layout_metadata_to_boxes(meta)

        issues = OverlapGate.compute_overlaps(boxes, threshold=0.1)
        assert issues == []  # no overlap

    def test_clipping_detected_through_model(self) -> None:
        """OverlapGate.run() with LayoutMetadata-derived dicts detects clipping."""
        els = (
            LayoutElement(id="off_right", x=1900, y=0, width=200, height=100),
        )
        meta = LayoutMetadata(elements=els, viewport_w=1920, viewport_h=1080)
        dicts = layout_metadata_to_element_dicts(meta)

        gate = OverlapGate()
        result = gate.run(dicts)
        assert result["passed"] is False
        assert any(i["type"] == "clipped" for i in result["issues"])

    def test_scene_payload_roundtrip_through_gate(self) -> None:
        """Full chain: scene payload → LayoutMetadata → dicts → gate.run()."""
        payload = json.dumps({
            "width": 1920,
            "height": 1080,
            "elements": [
                {"id": "title", "x": 0, "y": 0, "width": 400, "height": 200},
                {"id": "overlap", "x": 50, "y": 50, "width": 400, "height": 200},
            ],
        })
        meta = scene_payload_to_layout_metadata(payload)
        dicts = layout_metadata_to_element_dicts(meta)

        gate = OverlapGate()
        result = gate.run(dicts)
        assert result["passed"] is False
        overlap_types = {i["type"] for i in result["issues"]}
        assert "overlap" in overlap_types

    def test_non_overlapping_scene_payload_passes(self) -> None:
        payload = json.dumps({
            "elements": [
                {"id": "a", "x": 0, "y": 0, "width": 100, "height": 100},
                {"id": "b", "x": 200, "y": 0, "width": 100, "height": 100},
            ],
        })
        meta = scene_payload_to_layout_metadata(payload)
        dicts = layout_metadata_to_element_dicts(meta)

        gate = OverlapGate()
        result = gate.run(dicts)
        assert result["passed"] is True
