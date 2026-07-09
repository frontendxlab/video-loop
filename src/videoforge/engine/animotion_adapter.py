"""Animotion adapter — generate HTML/CSS/JS scenes from scene data + shared tokens.

Produces self-contained HTML documents with deterministic CSS+JS animations.
Consumes config/design-tokens.json animotion.theme section.
Exposes window.setFrame(frameIndex) for frame-by-frame capture.
"""

from __future__ import annotations

import html as html_mod
import json
from typing import Any

from videoforge.design_tokens import animotion_theme_stub


def get_animotion_render_config() -> dict[str, Any]:
    return {
        "renderer": "animotion",
        "theme": animotion_theme_stub(),
    }


def scene_to_html(
    title: str,
    kind: str,
    payload: dict[str, Any],
    duration_frames: int,
    fps: int = 30,
    width: int = 1920,
    height: int = 1080,
) -> str:
    """Generate self-contained HTML document for an Animotion scene.

    Returns HTML string. The HTML exposes window.setFrame(f) for
    frame-by-frame deterministic capture.
    """
    tokens = animotion_theme_stub()
    t = _Theme(tokens, width, height)

    html_content, extra_css = _build_scene_html(t, title, kind, payload, duration_frames, fps)
    anim_js = _build_animation_js(duration_frames)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width={width}, height={height}">
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  width: {width}px; height: {height}px;
  background: linear-gradient(135deg, {t.bg} 0%, #162033 55%, {t.panel_bg} 100%);
  font-family: {t.body_font}, -apple-system, sans-serif;
  color: {t.text_color};
  overflow: hidden;
  position: relative;
}}
.anim-element {{ will-change: transform, opacity; }}
{extra_css}
</style>
</head>
<body id="scene">
{html_content}
<script>
{anim_js}
window.setFrame(0);
</script>
</body>
</html>"""


class _Theme:
    """Lightweight design-token holder for HTML generation."""

    __slots__ = (
        "bg", "panel_bg", "text_color", "accent",
        "heading_font", "body_font", "mono_font",
        "width", "height",
    )

    def __init__(self, tokens: dict[str, Any], width: int, height: int) -> None:
        self.bg = tokens.get("deckBackground", "#0F172A")
        self.panel_bg = tokens.get("panelBackground", "#1E293B")
        self.text_color = tokens.get("textColor", "#E5EEF8")
        self.accent = tokens.get("accentColor", "#4A90D9")
        self.heading_font = tokens.get("headingFont", "Inter")
        self.body_font = tokens.get("bodyFont", "Inter")
        self.mono_font = tokens.get("monoFont", "JetBrains Mono")
        self.width = width
        self.height = height


# Diagram layout constants
_NODE_W = 160
_NODE_H = 56


def _layout_nodes(
    nodes: list[dict[str, Any]],
    canvas_w: int, canvas_h: int,
) -> list[dict[str, Any]]:
    """Auto-assign node positions if x/y missing — horizontal row layout."""
    if not nodes:
        return []
    has_all = all("x" in n and "y" in n for n in nodes)
    if has_all:
        return [dict(n) for n in nodes]
    count = len(nodes)
    gap = 80
    total_w = count * _NODE_W + (count - 1) * gap
    start_x = max(40, (canvas_w - total_w) // 2)
    center_y = canvas_h // 2 - _NODE_H // 2
    result = []
    for i, n in enumerate(nodes):
        node = dict(n)
        node.setdefault("x", start_x + i * (_NODE_W + gap))
        node.setdefault("y", center_y)
        result.append(node)
    return result


def _find_node(nodes: list[dict[str, Any]], node_id: str) -> dict[str, Any] | None:
    for n in nodes:
        if n.get("id") == node_id:
            return n
    return None


def _esc(s: str) -> str:
    return html_mod.escape(str(s), quote=True)


def _build_scene_html(
    t: _Theme, title: str, kind: str, payload: dict[str, Any],
    duration_frames: int, fps: int,
) -> tuple[str, str]:
    """Return (html_body, extra_css)."""
    dur = max(duration_frames, 1)

    if kind in ("title", "outro"):
        return _html_title(t, title, payload, dur, fps)
    elif kind == "bullets":
        return _html_bullets(t, title, payload, dur, fps)
    elif kind in ("code", "diff"):
        return _html_code(t, title, payload, dur, fps)
    elif kind in ("chart", "bar-chart"):
        return _html_chart(t, title, payload, dur, fps)
    elif kind == "comparison":
        return _html_comparison(t, title, payload, dur, fps)
    elif kind == "timeline":
        return _html_timeline(t, title, payload, dur, fps)
    elif kind == "diagram":
        return _html_diagram(t, title, payload, dur, fps)
    else:
        return _html_generic(t, title, payload, dur, fps)


def _anim_attrs(start: int, end: int, anim: str = "fade-up") -> str:
    return f'class="anim-element" data-start="{start}" data-end="{end}" data-anim="{anim}"'


def _html_title(
    t: _Theme, title: str, payload: dict[str, Any],
    duration_frames: int, fps: int,
) -> tuple[str, str]:
    subtitle = payload.get("subtitle", "")
    text = payload.get("text", "")
    # Title: 0-40%, subtitle: 20-60%, text: 40-80%
    t_end = int(duration_frames * 0.4)
    s_end = int(duration_frames * 0.6)
    x_end = int(duration_frames * 0.8)
    p_end = int(duration_frames * 0.2)

    lines = [
        f'<div {_anim_attrs(0, t_end, "fade-up")} style="text-align:center;padding-top:{t.height*0.28}px">',
        f'<h1 style="font-family:{t.heading_font};font-size:56px;font-weight:700;color:{t.text_color};">{_esc(title)}</h1>',
        "</div>",
    ]
    if subtitle:
        lines.insert(1, f'<div {_anim_attrs(p_end, s_end, "fade-up")} style="text-align:center;margin-top:{t.height*0.02}px">'
                         f'<p style="font-family:{t.body_font};font-size:28px;color:{t.accent};">{_esc(subtitle)}</p></div>')
    if text:
        lines.append(f'<div {_anim_attrs(s_end, x_end, "fade-up")} style="text-align:center;margin-top:{t.height*0.02}px;padding:0 10%">'
                     f'<p style="font-family:{t.body_font};font-size:22px;color:rgba(229,238,248,0.65);line-height:1.6;">{_esc(text)}</p></div>')

    css = ".anim-element { transition: none; }"
    return "\n".join(lines), css


def _html_bullets(
    t: _Theme, title: str, payload: dict[str, Any],
    duration_frames: int, fps: int,
) -> tuple[str, str]:
    points = payload.get("points", [])
    points = list(points)[:8]

    lines = [
        f'<div {_anim_attrs(0, int(duration_frames*0.15), "fade-up")} style="padding:{t.height*0.1}px {t.width*0.08}px 0">'
        f'<h2 style="font-family:{t.heading_font};font-size:36px;font-weight:600;color:{t.text_color};">{_esc(title)}</h2></div>',
    ]

    total_points = len(points)
    per_point = int(duration_frames * 0.55 / max(total_points, 1))
    start_offset = int(duration_frames * 0.18)

    for i, pt in enumerate(points):
        s = start_offset + i * per_point
        e = s + per_point
        lines.append(
            f'<div {_anim_attrs(s, e, "fade-left")} '
            f'style="padding:{t.height*0.015}px {t.width*0.12}px 0 {t.width*0.12}px;">'
            f'<p style="font-family:{t.body_font};font-size:24px;line-height:1.5;'
            f'color:{t.text_color};">'
            f'<span style="color:{t.accent};font-weight:700;margin-right:12px;">→</span>'
            f'{_esc(pt)}</p></div>'
        )

    css = """
.anim-element { transition: none; }
    """
    return "\n".join(lines), css


def _html_code(
    t: _Theme, title: str, payload: dict[str, Any],
    duration_frames: int, fps: int,
) -> tuple[str, str]:
    code = payload.get("code", "")
    lang = payload.get("lang", "")
    code_lines = code.split("\n")[:20]
    max_line_len = max((len(l) for l in code_lines), default=0)

    lines = [
        f'<div {_anim_attrs(0, int(duration_frames*0.15), "fade-up")} style="padding:{t.height*0.06}px {t.width*0.06}px 0">'
        f'<h2 style="font-family:{t.heading_font};font-size:28px;font-weight:600;color:{t.text_color};">'
        f'{_esc(title)}'
        + (f' <span style="font-size:16px;color:rgba(229,238,248,0.5);">{_esc(lang)}</span>' if lang else "")
        + "</h2></div>",
    ]

    # Code block panel
    line_count = len(code_lines)
    per_line = int(duration_frames * 0.7 / max(line_count, 1))
    start_offset = int(duration_frames * 0.18)
    font_size = max(14, min(20, int(90 / max(max_line_len, 1) * 20)))

    code_lines_html = []
    for i, cl in enumerate(code_lines):
        s = start_offset + i * per_line
        e = s + per_line
        display_text = cl if cl else " "
        code_lines_html.append(
            f'<div {_anim_attrs(s, e, "fade")} '
            f'style="font-family:{t.mono_font};font-size:{font_size}px;line-height:1.6;'
            f'padding:2px {t.width*0.015}px;white-space:pre;color:rgba(229,238,248,0.85);">'
            f'{_esc(display_text)}</div>'
        )

    lines.append(
        f'<div style="background:rgba(17,24,39,0.7);border-radius:8px;'
        f'margin:{t.height*0.02}px {t.width*0.06}px;'
        f'padding:{t.height*0.02}px 0;'
        f'border:1px solid rgba(148,163,184,0.18);">'
        + "\n".join(code_lines_html)
        + "</div>"
    )

    css = ".anim-element { transition: none; }"
    return "\n".join(lines), css


def _html_chart(
    t: _Theme, title: str, payload: dict[str, Any],
    duration_frames: int, fps: int,
) -> tuple[str, str]:
    """Render bar chart with sequential bar animation.

    Payload keys:
        labels (list[str]): Bar labels (bottom axis).
        values (list[float]): Bar heights (positive numbers).
        max_value (float, optional): Override chart max for consistent scale.

    Each bar animates in left-to-right via grow-up (scaleY) animation.
    """
    labels: list[str] = list(payload.get("labels", []) or [])
    values: list[float] = [float(v) for v in (payload.get("values", []) or [])]

    count = min(len(labels), len(values))
    labels = labels[:count]
    values = values[:count]

    if count == 0:
        return _html_generic(t, title, payload, duration_frames, fps)

    max_val = float(payload.get("max_value", 0)) or max(values) or 1

    # Layout constants
    chart_area_h = int(t.height * 0.68)
    bar_bottom = int(t.height * 0.10)

    bar_gap_pct = 0.15
    total_gap = bar_gap_pct * count
    bar_area_w = int(t.width * 0.76)
    bar_w = int(bar_area_w / (count + total_gap)) if count else 0
    gap_w = int(bar_w * bar_gap_pct) if count else 0
    start_x = int((t.width - count * bar_w - (count - 1) * gap_w) / 2)

    per_bar_frames = int(duration_frames * 0.65 / max(count, 1))
    start_offset = int(duration_frames * 0.18)

    colors = [
        t.accent, "#F59E0B", "#38BDF8", "#22C55E",
        "#F87171", "#A78BFA", "#F472B6", "#34D399",
    ]

    lines = [
        f'<div {_anim_attrs(0, int(duration_frames*0.1), "fade-up")} '
        f'style="position:absolute;top:{int(t.height*0.04)}px;left:0;width:100%;text-align:center;">'
        f'<h2 style="font-family:{t.heading_font};font-size:32px;font-weight:600;'
        f'color:{t.text_color};">{_esc(title)}</h2></div>'
    ]

    for i in range(count):
        s = start_offset + i * per_bar_frames
        e = s + per_bar_frames
        bar_h = int((values[i] / max_val) * chart_area_h) if max_val > 0 else 0
        bar_h = max(bar_h, 4)
        bar_color = colors[i % len(colors)]
        x = start_x + i * (bar_w + gap_w)

        lines.append(
            f'<div {_anim_attrs(s, e, "grow-up")} '
            f'style="position:absolute;left:{x}px;bottom:{bar_bottom}px;'
            f'width:{bar_w}px;height:{bar_h}px;'
            f'background:linear-gradient(180deg, {bar_color} 0%, {bar_color}cc 100%);'
            f'border-radius:4px 4px 0 0;'
            f'transform-origin:bottom center;">'
            f'<span style="position:absolute;top:-24px;left:0;width:100%;'
            f'text-align:center;font-family:{t.body_font};font-size:16px;'
            f'font-weight:600;color:{t.text_color};">'
            f'{_esc(str(int(values[i])))}</span></div>'
        )
        lines.append(
            f'<div style="position:absolute;left:{x}px;'
            f'top:{int(t.height*0.04) + 56 + chart_area_h + 8}px;'
            f'width:{bar_w}px;text-align:center;'
            f'font-family:{t.body_font};font-size:14px;'
            f'color:rgba(229,238,248,0.6);overflow:hidden;'
            f'text-overflow:ellipsis;white-space:nowrap;">'
            f'{_esc(labels[i])}</div>'
        )

    css = (
        '.anim-element[data-anim="grow-up"] {\n'
        '  transition: none;\n'
        '  transform: scaleY(0);\n'
        '}\n'
    )
    return "\n".join(lines), css


def _html_comparison(
    t: _Theme, title: str, payload: dict[str, Any],
    duration_frames: int, fps: int,
) -> tuple[str, str]:
    """Split-pane comparison — left/right headings + body text.

    Payload keys:
        left_heading (str): Heading for left pane.
        right_heading (str): Heading for right pane.
        left_body (str): Body content for left pane.
        right_body (str): Body content for right pane.

    Each pane animates in sequentially: title 0-20%, left 10-55%, right 40-85%.
    """
    left_heading = payload.get("left_heading", "")
    right_heading = payload.get("right_heading", "")
    left_body = payload.get("left_body", "")
    right_body = payload.get("right_body", "")

    dur = max(duration_frames, 1)
    title_end = int(dur * 0.2)
    left_start, left_end = int(dur * 0.1), int(dur * 0.55)
    right_start, right_end = int(dur * 0.4), int(dur * 0.85)

    def _panel(side: str, heading: str, body: str, s: int, e: int) -> str:
        margin = (
            f"margin-right:{t.width*0.02}px"
            if side == "left" else
            f"margin-left:{t.width*0.02}px"
        )
        parts: list[str] = []
        if heading:
            parts.append(
                f'<h3 style="font-family:{t.heading_font};font-size:24px;font-weight:600;'
                f'color:{t.text_color};margin-bottom:{t.height*0.02}px;">{_esc(heading)}</h3>'
            )
        if body:
            parts.append(
                f'<p style="font-family:{t.body_font};font-size:18px;line-height:1.6;'
                f'color:rgba(229,238,248,0.7);">{_esc(body)}</p>'
            )
        inner = "\n".join(parts)
        return (
            f'<div {_anim_attrs(s, e, "fade-up")} '
            f'style="width:44%;display:inline-block;vertical-align:top;text-align:left;{margin};">'
            f'<div style="background:{t.panel_bg};border-radius:8px;'
            f'padding:{t.height*0.025}px {t.width*0.025}px;'
            f'border:1px solid rgba(148,163,184,0.18);min-height:{t.height*0.35}px;">'
            f'{inner}</div></div>'
        )

    left_html = _panel("left", left_heading, left_body, left_start, left_end)
    right_html = _panel("right", right_heading, right_body, right_start, right_end)
    divider = (
        f'<div style="display:inline-block;width:1px;height:{t.height*0.4}px;'
        f'background:rgba(148,163,184,0.2);vertical-align:middle;"></div>'
    )

    lines = [
        f'<div {_anim_attrs(0, title_end, "fade-up")} style="text-align:center;'
        f'padding:{t.height*0.06}px {t.width*0.04}px {t.height*0.03}px;">'
        f'<h2 style="font-family:{t.heading_font};font-size:32px;font-weight:600;'
        f'color:{t.text_color};">{_esc(title)}</h2></div>',
        f'<div style="text-align:center;padding:0 {t.width*0.04}px;">'
        f'{left_html}{divider}{right_html}</div>',
    ]

    css = ".anim-element { transition: none; }"
    return "\n".join(lines), css


def _html_timeline(
    t: _Theme, title: str, payload: dict[str, Any],
    duration_frames: int, fps: int,
) -> tuple[str, str]:
    """Horizontal timeline with milestone nodes revealing by frame progress.

    Payload keys:
        milestones (list[dict]): Each with ``date``, ``title``, ``description``.

    Layout: title, horizontal track line with fill + cursor + milestone
    dots, then milestone labels (date/title) staggered beneath.
    """
    milestones = payload.get("milestones", [])
    milestones = list(milestones)[:10]
    n = len(milestones)

    title_end = int(duration_frames * 0.15)
    line_start = int(duration_frames * 0.10)
    line_end = int(duration_frames * 0.85)
    line_span = line_end - line_start
    hm = int(t.width * 0.06)

    parts = [
        f'<div {_anim_attrs(0, title_end, "fade-up")} '
        f'style="text-align:center;padding-top:{t.height*0.1}px;'
        f'margin-bottom:{int(t.height*0.03)}px;">'
        f'<h2 style="font-family:{t.heading_font};font-size:36px;font-weight:600;'
        f'color:{t.text_color};">{_esc(title)}</h2></div>',
    ]

    if n:
        line_y = int(t.height * 0.40)

        parts.append(
            f'<div style="position:relative;height:{int(t.height*0.68)}px;'
            f'margin:0 {hm}px;">'
        )

        # Background track line (static)
        parts.append(
            f'<div style="position:absolute;top:{line_y}px;left:0;right:0;'
            f'height:4px;background:rgba(148,163,184,0.12);'
            f'border-radius:2px;"></div>'
        )

        # Fill line — grows left-to-right via expand animation
        parts.append(
            f'<div {_anim_attrs(line_start, line_end, "expand")} '
            f'style="position:absolute;top:{line_y}px;left:0;'
            f'height:4px;background:{t.accent};'
            f'border-radius:2px;width:0%;"></div>'
        )

        # Progress cursor — slides along line via progress animation
        parts.append(
            f'<div {_anim_attrs(0, duration_frames, "progress")} '
            f'style="position:absolute;top:{line_y - 10}px;left:0%;'
            f'width:24px;height:24px;border-radius:50%;'
            f'background:{t.accent};border:3px solid {t.text_color};'
            f'box-shadow:0 0 16px rgba(74,144,217,0.5);'
            f'transform:translateX(-50%);z-index:3;"></div>'
        )

        # Milestone dots — one per milestone, positioned along line
        for i in range(n):
            left_pct = (i / (n - 1)) * 100 if n > 1 else 50
            parts.append(
                f'<div style="position:absolute;top:{line_y - 7}px;'
                f'left:{left_pct}%;transform:translateX(-50%);'
                f'width:14px;height:14px;border-radius:50%;'
                f'background:{t.text_color};'
                f'border:3px solid {t.accent};z-index:2;"></div>'
            )

        # Milestone labels — flex row with staggered fade-up
        parts.append(
            f'<div style="display:flex;justify-content:space-between;'
            f'position:absolute;top:{line_y + 20}px;left:0;right:0;">'
        )

        per_ms = int(line_span / max(n, 1))
        for i, ms in enumerate(milestones):
            s = line_start + i * per_ms
            e = min(s + per_ms, duration_frames)
            date = ms.get("date", "")
            title_ms = ms.get("title", "")
            desc = ms.get("description", "")

            parts.append(
                f'<div {_anim_attrs(s, e, "fade-up")} '
                f'style="display:flex;flex-direction:column;align-items:center;'
                f'flex:0 1 auto;max-width:{int(t.width*0.75/n)}px;'
                f'overflow:hidden;text-align:center;">'
            )

            if date:
                parts.append(
                    f'<span style="font-family:{t.mono_font};font-size:12px;'
                    f'font-weight:600;color:{t.accent};margin-bottom:2px;'
                    f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'
                    f'max-width:100%;">{_esc(date)}</span>'
                )
            if title_ms:
                parts.append(
                    f'<span style="font-family:{t.body_font};font-size:14px;'
                    f'font-weight:500;color:{t.text_color};'
                    f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'
                    f'max-width:100%;">{_esc(title_ms)}</span>'
                )
            if desc:
                parts.append(
                    f'<span style="font-family:{t.body_font};font-size:12px;'
                    f'color:rgba(229,238,248,0.55);margin-top:1px;'
                    f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'
                    f'max-width:100%;">{_esc(desc[:60])}</span>'
                )

            parts.append("</div>")

        parts.append("</div>")  # end labels row
        parts.append("</div>")  # end track container
    else:
        parts.append(
            f'<div style="text-align:center;padding-top:{t.height*0.2}px;'
            f'font-family:{t.body_font};font-size:22px;'
            f'color:rgba(229,238,248,0.4);">No timeline data</div>'
        )

    css = ".anim-element { transition: none; }"
    return "\n".join(parts), css


def _html_diagram(
    t: _Theme, title: str, payload: dict[str, Any],
    duration_frames: int, fps: int,
) -> tuple[str, str]:
    """Render interactive node-link diagram with nodes/edges.

    Payload keys:
        nodes (list[dict]): Each with id, label, x/y (optional), color (optional).
        edges (list[dict]): Each with source, target, label (optional).

    Nodes animate in staggered (fade-up). Edges fade in after connected nodes.
    Hover highlights nodes. Auto-layout when x/y omitted.
    Falls back to generic when nodes list empty.
    """
    raw_nodes = list(payload.get("nodes", []) or [])
    raw_edges = list(payload.get("edges", []) or [])
    dur = max(duration_frames, 1)

    if not raw_nodes:
        return _html_generic(t, title, payload, dur, fps)

    nodes = _layout_nodes(raw_nodes, t.width, t.height)
    node_ids = {n["id"] for n in nodes if "id" in n}
    valid_edges = [
        e for e in raw_edges
        if e.get("source") in node_ids and e.get("target") in node_ids
    ]

    title_end = int(dur * 0.15)
    node_start = int(dur * 0.15)
    node_span = int(dur * 0.55)
    edge_start = int(dur * 0.35)
    edge_span = int(dur * 0.50)
    per_node = max(1, node_span // max(len(nodes), 1))
    per_edge = max(1, edge_span // max(len(valid_edges), 1))

    colors = [
        t.accent, "#F59E0B", "#38BDF8", "#22C55E",
        "#F87171", "#A78BFA", "#F472B6", "#34D399",
    ]

    parts = [
        f'<div {_anim_attrs(0, title_end, "fade-up")} '
        f'style="text-align:center;padding-top:{int(t.height*0.04)}px;'
        f'position:relative;z-index:5;">'
        f'<h2 style="font-family:{t.heading_font};font-size:32px;font-weight:600;'
        f'color:{t.text_color};">{_esc(title)}</h2></div>',
    ]

    # SVG edge layer
    edge_lines = []
    for i, e in enumerate(valid_edges):
        sn = _find_node(nodes, e["source"])
        tn = _find_node(nodes, e["target"])
        if not sn or not tn:
            continue
        sx = sn["x"] + _NODE_W // 2
        sy = sn["y"] + _NODE_H // 2
        tx = tn["x"] + _NODE_W // 2
        ty = tn["y"] + _NODE_H // 2
        s_frame = edge_start + i * per_edge
        e_frame = min(s_frame + per_edge, dur)
        edge_lines.append(
            f'<line {_anim_attrs(s_frame, e_frame, "fade")} '
            f'x1="{sx}" y1="{sy}" x2="{tx}" y2="{ty}" '
            f'stroke="{t.accent}" stroke-width="2.5" '
            f'stroke-opacity="0.6" marker-end="url(#arrow)" '
            f'class="diagram-edge"/>',
        )

    arrow_marker = (
        f'<marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5" '
        f'markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
        f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{t.accent}" fill-opacity="0.6"/>'
        f'</marker>'
    )
    parts.append(
        f'<svg style="position:absolute;top:0;left:0;width:{t.width}px;'
        f'height:{t.height}px;pointer-events:none;z-index:1;" '
        f'xmlns="http://www.w3.org/2000/svg">'
        f'<defs>{arrow_marker}</defs>'
        + "\n".join(edge_lines)
        + "</svg>",
    )

    # Node elements
    for i, n in enumerate(nodes):
        s_frame = node_start + i * per_node
        e_frame = min(s_frame + per_node, dur)
        color = n.get("color", colors[i % len(colors)])
        nx = n["x"]
        ny = n["y"]
        label = n.get("label", n.get("id", ""))
        parts.append(
            f'<div {_anim_attrs(s_frame, e_frame, "fade-up")} '
            f'style="position:absolute;left:{nx}px;top:{ny}px;'
            f'width:{_NODE_W}px;height:{_NODE_H}px;'
            f'background:linear-gradient(135deg, {color} 0%, {color}cc 100%);'
            f'border-radius:8px;'
            f'box-shadow:0 4px 12px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.15);'
            f'display:flex;align-items:center;justify-content:center;'
            f'cursor:pointer;z-index:2;'
            f'transition:transform 0.2s, box-shadow 0.2s;" '
            f'class="diagram-node" '
            f'onmouseenter="this.style.transform=\'scale(1.08)\';'
            f'this.style.boxShadow=\'0 0 20px {color}66\'" '
            f'onmouseleave="this.style.transform=\'\';this.style.boxShadow=\'\'">'
            f'<span style="font-family:{t.body_font};font-size:14px;font-weight:600;'
            f'color:#fff;text-align:center;padding:0 8px;overflow:hidden;'
            f'text-overflow:ellipsis;white-space:nowrap;max-width:100%;">'
            f'{_esc(label)}</span></div>',
        )

    css = ".anim-element { transition: none; }"
    return "\n".join(parts), css


def _html_generic(
    t: _Theme, title: str, payload: dict[str, Any],
    duration_frames: int, fps: int,
) -> tuple[str, str]:
    text = payload.get("text", "") or payload.get("caption", "")

    lines = [
        f'<div {_anim_attrs(0, int(duration_frames*0.25), "fade-up")} style="padding:{t.height*0.15}px {t.width*0.08}px 0">'
        f'<h2 style="font-family:{t.heading_font};font-size:36px;font-weight:600;color:{t.text_color};">{_esc(title)}</h2></div>',
    ]
    if text:
        lines.append(
            f'<div {_anim_attrs(int(duration_frames*0.2), int(duration_frames*0.6), "fade-up")} '
            f'style="padding:{t.height*0.03}px {t.width*0.1}px 0;">'
            f'<p style="font-family:{t.body_font};font-size:24px;line-height:1.7;'
            f'color:rgba(229,238,248,0.75);">{_esc(text)}</p></div>'
        )

    css = ".anim-element { transition: none; }"
    return "\n".join(lines), css


def _build_animation_js(duration_frames: int) -> str:
    """Generate JS that drives element visibility/animation by frame."""
    return f"""
(function() {{
  var DURATION = {duration_frames};
  var elements = null;

  window.setFrame = function(f) {{
    if (!elements) {{
      elements = document.querySelectorAll('.anim-element');
    }}
    for (var i = 0; i < elements.length; i++) {{
      var el = elements[i];
      var start = parseInt(el.getAttribute('data-start') || '0');
      var end = parseInt(el.getAttribute('data-end') || '1');
      var anim = el.getAttribute('data-anim') || 'fade';

      if (f < start || f >= DURATION) {{
        el.style.display = 'none';
        continue;
      }}
      el.style.display = '';

      var t = (end > start) ? Math.min(1, Math.max(0, (f - start) / (end - start))) : 1;

      if (anim === 'fade-up') {{
        el.style.opacity = t;
        el.style.transform = 'translateY(' + ((1 - t) * 30) + 'px)';
      }} else if (anim === 'fade-left') {{
        el.style.opacity = t;
        el.style.transform = 'translateX(' + ((1 - t) * 40) + 'px)';
      }} else if (anim === 'grow-up') {{
        el.style.opacity = 1;
        el.style.transform = 'scaleY(' + t + ')';
      }} else if (anim === 'expand') {{
        el.style.opacity = 1;
        el.style.width = (t * 100) + '%';
      }} else if (anim === 'progress') {{
        el.style.opacity = 1;
        el.style.display = '';
        el.style.left = (t * 100) + '%';
      }} else {{
        el.style.opacity = t;
        el.style.transform = '';
      }}
    }}
  }};
}})();
"""
