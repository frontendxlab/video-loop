import { Engine, SceneKind, type SceneNode, type RoutingEntry } from './ir-types'

export function pickEngine(node: SceneNode): Engine {
  const k = node.kind
  if (k === SceneKind.CODE || k === SceneKind.DIFF || k === SceneKind.BULLETS || k === SceneKind.TITLE || k === SceneKind.COMPARISON || k === SceneKind.QUOTE || k === SceneKind.OUTRO || k === SceneKind.MINDMAP || k === SceneKind.SCREENFLOW || k === SceneKind.OVERLAY_CTA || k === SceneKind.AUDIO_REACTIVE || k === SceneKind.DOCUMENT_HIGHLIGHT || k === SceneKind.SVG_MORPH || k === SceneKind.SHOWCASE || k === SceneKind.SPLIT || k === SceneKind.MOCKUP || k === SceneKind.HERO || k === SceneKind.MAP_GEO) return Engine.REMOTION
  if (k === SceneKind.DIAGRAM) {
    const p = tryParse(node.payload)
    if (p?.layout === 'math_graph') return Engine.MANIM
    if (p?.interactive) return Engine.ANIMOTION
    return Engine.REMOTION
  }
  if (k === SceneKind.CHART || k === SceneKind.TIMELINE || k === SceneKind.MAP3D || k === SceneKind.DUAL_CHART || k === SceneKind.THREE_SCENE) return Engine.MANIM
  return Engine.REMOTION
}

export function getRoutingReason(node: SceneNode): string {
  const k = node.kind
  const p = tryParse(node.payload)
  if (k === SceneKind.DIAGRAM) {
    if (p?.layout === 'math_graph') return 'Real graph layout with dot/spring algorithm'
    if (p?.interactive) return 'Web-animated diagrams with CSS/JS transitions'
    return 'Fallback to React-based diagram'
  }
  const reasons: Record<string, string> = {
    [SceneKind.CODE]: 'Shiki syntax highlighting, React typography',
    [SceneKind.DIFF]: 'Real diff parsing with aligned line matching',
    [SceneKind.BULLETS]: 'Flexbox layout, spring physics',
    [SceneKind.TITLE]: 'Typography, animated entrance',
    [SceneKind.COMPARISON]: 'Split-pane, animated divider',
    [SceneKind.QUOTE]: 'Typography, emphasis animation',
    [SceneKind.OUTRO]: 'Call-to-action, fade out',
    [SceneKind.MINDMAP]: 'Tree layout via d3-hierarchy',
    [SceneKind.CHART]: 'BarChart, NumberLine, Axes primitives',
    [SceneKind.TIMELINE]: 'MoveAlongPath, deterministic tick math',
    [SceneKind.MAP3D]: '3D geometry and camera movement',
    [SceneKind.DUAL_CHART]: 'Dual-axis bar/line combination chart with Manim primitives',
    [SceneKind.THREE_SCENE]: 'Three-dimensional scene with perspective camera movement',
    [SceneKind.SCREENFLOW]: 'Multi-step screen recording with callout annotations',
    [SceneKind.OVERLAY_CTA]: 'Transparent overlay with call-to-action text and fade-out',
    [SceneKind.AUDIO_REACTIVE]: 'Audio waveform visualization with beat-synced React animation',
    [SceneKind.DOCUMENT_HIGHLIGHT]: 'Document close-up with animated text highlight reveal',
    [SceneKind.SVG_MORPH]: 'SVG path-to-path morphing with spring physics',
    [SceneKind.SHOWCASE]: 'Product showcase with highlight cards and transitions',
    [SceneKind.SPLIT]: 'Split-screen comparison with synced playback',
    [SceneKind.MOCKUP]: 'Device mockup frame with inner content scroll',
    [SceneKind.HERO]: 'Full-screen hero section with animated headline',
    [SceneKind.MAP_GEO]: 'SVG geo map with markers, routes, and grid overlay',
  }
  return reasons[k] ?? 'Default routing'
}

export const ROUTING_TABLE: RoutingEntry[] = [
  { kind: 'code', engine: Engine.REMOTION, reason: 'Shiki syntax highlighting, React typography' },
  { kind: 'diff', engine: Engine.REMOTION, reason: 'Real diff parsing with aligned line matching' },
  { kind: 'bullets', engine: Engine.REMOTION, reason: 'Flexbox layout, spring physics' },
  { kind: 'title', engine: Engine.REMOTION, reason: 'Typography, animated entrance' },
  { kind: 'comparison', engine: Engine.REMOTION, reason: 'Split-pane, animated divider' },
  { kind: 'quote', engine: Engine.REMOTION, reason: 'Typography, emphasis animation' },
  { kind: 'outro', engine: Engine.REMOTION, reason: 'Call-to-action, fade out' },
  { kind: 'mindmap', engine: Engine.REMOTION, reason: 'Tree layout via d3-hierarchy' },
  { kind: 'diagram', engine: Engine.MANIM, reason: 'Real graph layout with dot/spring algorithm', layout: 'math_graph' },
  { kind: 'diagram', engine: Engine.ANIMOTION, reason: 'Web-animated diagrams with CSS/JS transitions', interactive: true },
  { kind: 'diagram', engine: Engine.REMOTION, reason: 'Fallback to React-based diagram', layout: 'default' },
  { kind: 'chart', engine: Engine.MANIM, reason: 'BarChart, NumberLine, Axes primitives' },
  { kind: 'timeline', engine: Engine.MANIM, reason: 'MoveAlongPath, deterministic tick math' },
  { kind: 'map3d', engine: Engine.MANIM, reason: '3D geometry and camera movement' },
  { kind: 'dual-chart', engine: Engine.MANIM, reason: 'Dual-axis bar/line combination chart with Manim primitives' },
  { kind: 'three-scene', engine: Engine.MANIM, reason: 'Three-dimensional scene with perspective camera movement' },
  { kind: 'screenflow', engine: Engine.REMOTION, reason: 'Multi-step screen recording with callout annotations' },
  { kind: 'overlay-cta', engine: Engine.REMOTION, reason: 'Transparent overlay with call-to-action text and fade-out' },
  { kind: 'audio-reactive', engine: Engine.REMOTION, reason: 'Audio waveform visualization with beat-synced React animation' },
  { kind: 'document-highlight', engine: Engine.REMOTION, reason: 'Document close-up with animated text highlight reveal' },
  { kind: 'svg-morph', engine: Engine.REMOTION, reason: 'SVG path-to-path morphing with spring physics' },
  { kind: 'showcase', engine: Engine.REMOTION, reason: 'Product showcase with highlight cards and transitions' },
  { kind: 'split', engine: Engine.REMOTION, reason: 'Split-screen comparison with synced playback' },
  { kind: 'mockup', engine: Engine.REMOTION, reason: 'Device mockup frame with inner content scroll' },
  { kind: 'hero', engine: Engine.REMOTION, reason: 'Full-screen hero section with animated headline' },
  { kind: 'map-geo', engine: Engine.REMOTION, reason: 'SVG geo map with markers, routes, and grid overlay' },
]

function tryParse(p: string): Record<string, unknown> | null {
  try { return JSON.parse(p) } catch { return null }
}
