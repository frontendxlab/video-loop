"""Map/Geo payload tests — determinism, structure, routing."""

from __future__ import annotations

import json

from videoforge.engine.director import pick_engine
from videoforge.engine.ir import Engine, NarrationSpec, SceneKind, SceneNode, WordTiming
from videoforge.engine.map_geo import GeoMarker, GeoPoint, GeoRoute, map_geo_payload


def _node(kind: SceneKind, payload: str) -> SceneNode:
    return SceneNode(
        id=f"n_{kind.value}",
        kind=kind,
        payload=payload,
        engine_hint=Engine.REMOTION,
        duration_frames=150,
        narration=NarrationSpec("map scene", (), "estimated"),
    )


def test_map_geo_routes_to_remotion():
    p = map_geo_payload(center_lat=48.8566, center_lng=2.3522, zoom=10)
    n = _node(SceneKind.MAP_GEO, p)
    assert pick_engine(n) == Engine.REMOTION


def test_payload_is_deterministic():
    a = map_geo_payload(51.5, -0.12, zoom=8, title="London")
    b = map_geo_payload(51.5, -0.12, zoom=8, title="London")
    assert a == b
    assert json.loads(a) == json.loads(b)


def test_payload_sensitive_to_center():
    a = map_geo_payload(48.8566, 2.3522, zoom=10)
    b = map_geo_payload(40.7128, -74.0060, zoom=10)
    assert a != b


def test_payload_sensitive_to_zoom():
    a = map_geo_payload(48.8566, 2.3522, zoom=5)
    b = map_geo_payload(48.8566, 2.3522, zoom=10)
    assert a != b


def test_payload_contains_title():
    p = map_geo_payload(title="Paris")
    d = json.loads(p)
    assert d["title"] == "Paris"


def test_payload_with_markers():
    markers = (
        GeoMarker(48.8566, 2.3522, label="Paris", color="#FF5733"),
        GeoMarker(48.5734, 7.7520, label="Strasbourg"),
    )
    p = map_geo_payload(48.8566, 2.3522, zoom=8, markers=markers, title="Route")
    d = json.loads(p)
    assert len(d["markers"]) == 2
    assert d["markers"][0]["label"] == "Paris"
    assert d["markers"][0]["color"] == "#FF5733"
    assert d["markers"][1]["label"] == "Strasbourg"


def test_payload_with_route():
    route = GeoRoute(
        points=(GeoPoint(48.8566, 2.3522), GeoPoint(48.5734, 7.7520)),
        color="#F59E0B",
        width=4,
    )
    p = map_geo_payload(48.8566, 2.3522, zoom=8, routes=(route,))
    d = json.loads(p)
    assert len(d["routes"]) == 1
    assert len(d["routes"][0]["points"]) == 2
    assert d["routes"][0]["color"] == "#F59E0B"


def test_payload_defaults():
    p = map_geo_payload()
    d = json.loads(p)
    assert d["centerLat"] == 0.0
    assert d["centerLng"] == 0.0
    assert d["zoom"] == 5
    assert d["style"] == "streets"
    assert d["markers"] == []
    assert d["routes"] == []


def test_payload_is_json_sort_keys():
    p = map_geo_payload(center_lat=48.8566, center_lng=2.3522, title="Paris")
    # Verify keys are sorted
    d = json.loads(p)
    keys = list(d.keys())
    assert keys == sorted(keys), f"Payload keys not sorted: {keys}"
