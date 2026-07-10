"""Map/Geo scene payload builder — deterministic, no tile deps.

Produces JSON payload for SceneKind.MAP_GEO scenes. The payload
encodes center, zoom, markers, route, and style. Every payload is
sort_keys=True stable for IR content hashing.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class GeoPoint:
    lat: float
    lng: float


@dataclass(frozen=True)
class GeoMarker:
    lat: float
    lng: float
    label: str = ""
    color: str = "#4A90D9"


@dataclass(frozen=True)
class GeoRoute:
    points: tuple[GeoPoint, ...]
    color: str = "#F59E0B"
    width: int = 3


def map_geo_payload(
    center_lat: float = 0.0,
    center_lng: float = 0.0,
    zoom: int = 5,
    markers: tuple[GeoMarker, ...] = (),
    routes: tuple[GeoRoute, ...] = (),
    style: str = "streets",
    title: str = "",
) -> str:
    """Build deterministic map/geo scene payload.

    All numeric values are deterministic. No external tile or geo service
    is called at payload-build time.

    ponytail: style enum expansion. Add satellite/dark styles when
    MapScene component supports them.
    """
    payload: dict[str, Any] = {
        "centerLat": center_lat,
        "centerLng": center_lng,
        "zoom": zoom,
        "style": style,
        "title": title,
        "markers": [asdict(m) for m in markers],
        "routes": [
            {
                "points": [asdict(p) for p in r.points],
                "color": r.color,
                "width": r.width,
            }
            for r in routes
        ],
    }
    return json.dumps(payload, sort_keys=True)
