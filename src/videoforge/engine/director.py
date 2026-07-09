"""Director — deterministic scene→engine routing table.

Pure, no I/O, no LLM. The routing rules live in config/engine_routing.yaml
and are mirrored by pick_engine() for testability without YAML.
"""

from __future__ import annotations

import json
from pathlib import Path

from videoforge.engine.ir import Engine, SceneKind, SceneNode


def pick_engine(node: SceneNode) -> Engine:
    """Route a SceneNode to the engine that should render it.

    Deterministic, table-driven. Override per scene by editing the table.
    """
    k = node.kind
    if k in (
        SceneKind.CODE, SceneKind.DIFF, SceneKind.BULLETS, SceneKind.TITLE,
        SceneKind.COMPARISON, SceneKind.QUOTE, SceneKind.OUTRO, SceneKind.MINDMAP,
    ):
        return Engine.REMOTION
    if k == SceneKind.DIAGRAM:
        payload = json.loads(node.payload)
        if payload.get("layout") == "math_graph":
            return Engine.MANIM
        if payload.get("interactive"):
            return Engine.ANIMOTION
        return Engine.REMOTION
    if k in (SceneKind.CHART, SceneKind.TIMELINE, SceneKind.MAP3D):
        return Engine.MANIM
    return Engine.REMOTION


_ROUTING_CACHE: dict[str, Engine] | None = None


def load_routing_table(path: str | Path | None = None) -> dict[str, Engine]:
    """Load kind→engine map from YAML (kind+layout keys for diagrams).

    Returns a flat dict keyed by kind (or 'diagram:math_graph' / 'diagram:default').
    """
    global _ROUTING_CACHE
    if _ROUTING_CACHE is not None and path is None:
        return _ROUTING_CACHE
    import yaml

    p = Path(path) if path else Path(__file__).resolve().parents[3] / "config" / "engine_routing.yaml"
    data = yaml.safe_load(p.read_text()) if p.exists() else {"routing": []}
    table: dict[str, Engine] = {}
    for entry in data.get("routing", []):
        kind = entry.get("kind", "")
        qualifiers = []
        if entry.get("layout"):
            qualifiers.append(f"layout:{entry['layout']}")
        if entry.get("interactive"):
            qualifiers.append("interactive:true")
        key = f"{kind}:{':'.join(qualifiers)}" if qualifiers else kind
        table[key] = Engine(entry.get("engine", "remotion"))
    if path is None:
        _ROUTING_CACHE = table
    return table
