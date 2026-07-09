import { Engine, SceneKind, type SceneNode, type RoutingEntry } from './ir-types'

export function pickEngine(node: SceneNode): Engine {
  const k = node.kind
  if (k === SceneKind.CODE || k === SceneKind.DIFF || k === SceneKind.BULLETS || k === SceneKind.TITLE || k === SceneKind.COMPARISON || k === SceneKind.QUOTE || k === SceneKind.OUTRO || k === SceneKind.MINDMAP) return Engine.REMOTION
  if (k === SceneKind.DIAGRAM) {
    const p = tryParse(node.payload)
    if (p?.layout === 'math_graph') return Engine.MANIM
    if (p?.interactive) return Engine.ANIMOTION
    return Engine.REMOTION
  }
  if (k === SceneKind.CHART || k === SceneKind.TIMELINE || k === SceneKind.MAP3D) return Engine.MANIM
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
]

function tryParse(p: string): Record<string, unknown> | null {
  try { return JSON.parse(p) } catch { return null }
}
