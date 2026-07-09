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
      }} else {{
        el.style.opacity = t;
        el.style.transform = '';
      }}
    }}
  }};
}})();
"""
