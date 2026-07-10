import { useState, useRef, useCallback, useMemo, useEffect } from 'react'
import { type SceneNode, Engine, SceneKind } from '@/lib/ir-types'
import { pickEngine } from '@/lib/director'
import { cn } from '@/lib/utils'

/* ─── Layout constants ─── */
const NODE_W = 200
const NODE_H = 92
const GAP_X = 100

const ENGINE_Y_OFFSET: Record<string, number> = {
  [Engine.REMOTION]: -48,
  [Engine.MANIM]: 0,
  [Engine.ANIMOTION]: 48,
}

/* ─── Kind meta (mirrors scene-graph.tsx) ─── */
const KIND_META: Record<SceneKind, { label: string; color: string }> = {
  [SceneKind.TITLE]: { label: 'Title', color: 'bg-blue-500/20 text-blue-300' },
  [SceneKind.CODE]: { label: 'Code', color: 'bg-cyan-500/20 text-cyan-300' },
  [SceneKind.DIFF]: { label: 'Diff', color: 'bg-teal-500/20 text-teal-300' },
  [SceneKind.BULLETS]: { label: 'Bullets', color: 'bg-indigo-500/20 text-indigo-300' },
  [SceneKind.DIAGRAM]: { label: 'Diagram', color: 'bg-violet-500/20 text-violet-300' },
  [SceneKind.CHART]: { label: 'Chart', color: 'bg-orange-500/20 text-orange-300' },
  [SceneKind.TIMELINE]: { label: 'Timeline', color: 'bg-pink-500/20 text-pink-300' },
  [SceneKind.MAP3D]: { label: 'Map 3D', color: 'bg-rose-500/20 text-rose-300' },
  [SceneKind.COMPARISON]: { label: 'Comparison', color: 'bg-amber-500/20 text-amber-300' },
  [SceneKind.QUOTE]: { label: 'Quote', color: 'bg-yellow-500/20 text-yellow-300' },
  [SceneKind.OUTRO]: { label: 'Outro', color: 'bg-gray-500/20 text-gray-300' },
  [SceneKind.MINDMAP]: { label: 'Mind Map', color: 'bg-emerald-500/20 text-emerald-300' },
  [SceneKind.DUAL_CHART]: { label: 'Dual Chart', color: 'bg-fuchsia-500/20 text-fuchsia-300' },
  [SceneKind.THREE_SCENE]: { label: '3D Scene', color: 'bg-sky-500/20 text-sky-300' },
  [SceneKind.SCREENFLOW]: { label: 'Screenflow', color: 'bg-lime-500/20 text-lime-300' },
  [SceneKind.OVERLAY_CTA]: { label: 'Overlay CTA', color: 'bg-rose-500/20 text-rose-300' },
  [SceneKind.AUDIO_REACTIVE]: { label: 'Audio Reactive', color: 'bg-cyan-500/20 text-cyan-300' },
  [SceneKind.DOCUMENT_HIGHLIGHT]: { label: 'Doc Highlight', color: 'bg-yellow-500/20 text-yellow-300' },
  [SceneKind.SVG_MORPH]: { label: 'SVG Morph', color: 'bg-purple-500/20 text-purple-300' },
  [SceneKind.SHOWCASE]: { label: 'Showcase', color: 'bg-pink-500/20 text-pink-300' },
  [SceneKind.SPLIT]: { label: 'Split', color: 'bg-orange-500/20 text-orange-300' },
  [SceneKind.MOCKUP]: { label: 'Mockup', color: 'bg-slate-500/20 text-slate-300' },
  [SceneKind.HERO]: { label: 'Hero', color: 'bg-red-500/20 text-red-300' },
  [SceneKind.MAP_GEO]: { label: 'Map Geo', color: 'bg-stone-500/20 text-stone-300' },
}

const ENGINE_NODE: Record<Engine, { border: string; dot: string }> = {
  [Engine.REMOTION]: { border: 'border-blue-500/40', dot: 'bg-blue-400' },
  [Engine.MANIM]: { border: 'border-green-500/40', dot: 'bg-green-400' },
  [Engine.ANIMOTION]: { border: 'border-purple-500/40', dot: 'bg-purple-400' },
}

/* ─── Derived status from scene data ─── */
type VisualStatus = 'draft' | 'planned' | 'routed' | 'rendering' | 'ready' | 'error'

function getVisualStatus(scene: SceneNode): VisualStatus {
  if (scene.artifacts?.thumbnail?.state === 'ready') return 'ready'
  if (scene.artifacts?.thumbnail?.state === 'error') return 'error'
  if (scene.artifacts?.thumbnail?.state === 'generating') return 'rendering'
  if (scene.routedEngine) return 'routed'
  if (scene.contentHash) return 'planned'
  return 'draft'
}

const STATUS_META: Record<VisualStatus, string> = {
  draft: 'bg-gray-400',
  planned: 'bg-blue-400',
  routed: 'bg-indigo-400',
  rendering: 'bg-amber-400',
  ready: 'bg-emerald-400',
  error: 'bg-red-400',
}

/* ─── Positioned node layout ─── */
interface PositionedNode {
  scene: SceneNode
  x: number
  y: number
  engine: Engine
  idx: number
}

function computeLayout(scenes: SceneNode[]): PositionedNode[] {
  return scenes.map((scene, i) => {
    const engine = scene.routedEngine ?? pickEngine(scene)
    const x = i * (NODE_W + GAP_X)
    const y = ENGINE_Y_OFFSET[engine] ?? 0
    return { scene, x, y, engine, idx: i }
  })
}

/* ─── Connector SVG line between two nodes ─── */
function ConnectorCurve({ from, to }: { from: PositionedNode; to: PositionedNode }) {
  const x1 = from.x + NODE_W
  const y1 = from.y + NODE_H / 2
  const x2 = to.x
  const y2 = to.y + NODE_H / 2
  const dx = Math.max(Math.abs(x2 - x1) * 0.4, 30)
  const d = `M ${x1} ${y1} C ${x1 + dx} ${y1}, ${x2 - dx} ${y2}, ${x2} ${y2}`
  return <path d={d} fill="none" stroke="hsl(var(--border))" strokeWidth="1.5" strokeDasharray="5 3" />
}

/* ─── Single canvas node ─── */
function SceneCanvasNode({
  node,
  selected,
  onClick,
}: {
  node: PositionedNode
  selected: boolean
  onClick: () => void
}) {
  const { scene, x, y, engine, idx } = node
  const kindMeta = KIND_META[scene.kind] ?? KIND_META[SceneKind.TITLE]
  const engineStyle = ENGINE_NODE[engine]
  const status = getVisualStatus(scene)
  const statusClass = STATUS_META[status]
  const seconds = Math.round(scene.duration_frames / 30)
  const hasOverlays = scene.overlay_stack && scene.overlay_stack.items.length > 0
  const hasArtifacts = scene.artifacts && Object.values(scene.artifacts).some(a => a && a.state === 'ready')

  return (
    <div
      data-node-id={scene.id}
      onClick={(e) => { e.stopPropagation(); onClick() }}
      className={cn(
        'absolute rounded-xl border-2 bg-card/95 backdrop-blur-sm cursor-pointer transition-all duration-150 select-none',
        'hover:shadow-lg hover:-translate-y-0.5 hover:z-10',
        engineStyle.border,
        selected ? 'ring-2 ring-primary shadow-xl z-10 translate-y-0' : 'shadow-sm',
      )}
      style={{ left: x, top: y, width: NODE_W, height: NODE_H }}
    >
      {/* Top row: index, kind badge, engine badge, status dot */}
      <div className="flex items-center gap-1.5 px-2.5 pt-2.5 pb-1">
        <span className="flex-shrink-0 w-5 h-5 rounded-full bg-muted text-muted-foreground text-[10px] font-semibold flex items-center justify-center">
          {idx + 1}
        </span>
        <span className={cn('inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-medium leading-none', kindMeta.color)}>
          {kindMeta.label}
        </span>
        <span className={cn(
          'inline-flex items-center rounded border px-1.5 py-0.5 text-[9px] font-medium leading-none',
          engine === Engine.REMOTION && 'border-blue-500/30 text-blue-400',
          engine === Engine.MANIM && 'border-green-500/30 text-green-400',
          engine === Engine.ANIMOTION && 'border-purple-500/30 text-purple-400',
        )}>
          {engine === Engine.REMOTION ? 'Rem' : engine === Engine.MANIM ? 'Man' : 'Ani'}
        </span>
        <span className={cn('ml-auto w-2 h-2 rounded-full flex-shrink-0', statusClass)} title={status} />
      </div>

      {/* Middle row: hash + duration */}
      <div className="flex items-center gap-2 px-2.5 py-0.5 text-[10px] text-muted-foreground font-mono">
        <span className="truncate max-w-[100px]">#{scene.contentHash?.slice(0, 8) ?? '------'}</span>
        <span className="ml-auto whitespace-nowrap">{scene.duration_frames}f ({seconds}s)</span>
      </div>

      {/* Bottom badges: overlays + artifacts */}
      {(hasOverlays || hasArtifacts) && (
        <div className="flex items-center gap-1.5 px-2.5 pt-0.5">
          {hasOverlays && (
            <span className="inline-flex items-center rounded px-1 py-0.5 text-[9px] font-medium bg-rose-500/15 text-rose-300 leading-none">
              OL:{scene.overlay_stack!.items.length}
            </span>
          )}
          {hasArtifacts && (
            <span className="inline-flex items-center rounded px-1 py-0.5 text-[9px] font-medium bg-emerald-500/15 text-emerald-300 leading-none">
              Art:✓
            </span>
          )}
        </div>
      )}
    </div>
  )
}

/* ══════════════════════════════════════════════════
   CanvasSceneGraph — infinite canvas scene graph
   ══════════════════════════════════════════════════ */
export interface CanvasSceneGraphProps {
  scenes: SceneNode[]
  selectedId?: string
  onSelect: (scene: SceneNode) => void
}

export function CanvasSceneGraph({ scenes, selectedId, onSelect }: CanvasSceneGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [t, setT] = useState({ x: 0, y: 0, scale: 0.65 })
  const panning = useRef(false)
  const startPos = useRef({ x: 0, y: 0 })
  const lastT = useRef(t)
  const fitted = useRef(false)

  // Keep lastT in sync
  useEffect(() => { lastT.current = t }, [t])

  /* ─── Layout (memoized) ─── */
  const layout = useMemo(() => computeLayout(scenes), [scenes])
  const graphBounds = useMemo(() => {
    if (layout.length === 0) return { minX: 0, maxX: NODE_W, minY: -NODE_H, maxY: NODE_H }
    return {
      minX: Math.min(...layout.map(n => n.x)),
      maxX: Math.max(...layout.map(n => n.x + NODE_W)),
      minY: Math.min(...layout.map(n => n.y + (ENGINE_Y_OFFSET[Engine.REMOTION] ?? 0))),
      maxY: Math.max(...layout.map(n => n.y + NODE_H + (ENGINE_Y_OFFSET[Engine.ANIMOTION] ?? 0))),
    }
  }, [layout])

  /* ─── Fit-to-view on mount ─── */
  useEffect(() => {
    if (fitted.current || layout.length === 0) return
    const el = containerRef.current
    if (!el) return
    fitted.current = true
    const rect = el.getBoundingClientRect()
    const gw = graphBounds.maxX - graphBounds.minX
    const gh = graphBounds.maxY - graphBounds.minY
    const pad = 48
    const s = Math.min((rect.width - pad * 2) / (gw || 1), (rect.height - pad * 2) / (gh || 1), 1.2)
    const cx = (graphBounds.minX + graphBounds.maxX) / 2
    const cy = (graphBounds.minY + graphBounds.maxY) / 2
    setT({ x: rect.width / 2 - cx * s, y: rect.height / 2 - cy * s, scale: Math.max(0.2, s) })
  }, [layout, graphBounds])

  /* ─── Mouse pan ─── */
  const onMouseDown = useCallback((e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest('[data-node-id]')) return
    panning.current = true
    startPos.current = { x: e.clientX, y: e.clientY }
    lastT.current = t
  }, [t])

  const onMouseMove = useCallback((e: React.MouseEvent) => {
    if (!panning.current) return
    setT(prev => ({
      ...prev,
      x: lastT.current.x + e.clientX - startPos.current.x,
      y: lastT.current.y + e.clientY - startPos.current.y,
    }))
  }, [])

  const onMouseUp = useCallback(() => { panning.current = false }, [])

  /* ─── Wheel zoom (non-passive via ref pattern) ─── */
  const wheelHandlerRef = useRef<(e: WheelEvent) => void>()
  wheelHandlerRef.current = useCallback((e: WheelEvent) => {
    const el = containerRef.current
    if (!el) return
    e.preventDefault()
    const rect = el.getBoundingClientRect()
    const delta = e.deltaY > 0 ? 0.88 : 1 / 0.88
    const ns = Math.max(0.15, Math.min(3, lastT.current.scale * delta))
    const cx = e.clientX - rect.left
    const cy = e.clientY - rect.top
    const lt = lastT.current
    setT({
      x: cx - (cx - lt.x) * ns / lt.scale,
      y: cy - (cy - lt.y) * ns / lt.scale,
      scale: ns,
    })
  }, [])

  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const handler = (e: WheelEvent) => wheelHandlerRef.current?.(e)
    el.addEventListener('wheel', handler, { passive: false })
    return () => el.removeEventListener('wheel', handler)
  }, [])

  /* ─── Touch pan ─── */
  const touchRef = useRef({ id: 0, sx: 0, sy: 0, panning: false })
  const onTouchStart = useCallback((e: React.TouchEvent) => {
    if ((e.target as HTMLElement).closest('[data-node-id]')) return
    if (e.touches.length !== 1) return
    touchRef.current = { id: e.touches[0].identifier, sx: e.touches[0].clientX, sy: e.touches[0].clientY, panning: true }
    lastT.current = t
  }, [t])

  const onTouchMove = useCallback((e: React.TouchEvent) => {
    if (!touchRef.current.panning) return
    const touch = Array.from(e.touches).find(t => t.identifier === touchRef.current.id)
    if (!touch) return
    const dx = touch.clientX - touchRef.current.sx
    const dy = touch.clientY - touchRef.current.sy
    setT(prev => ({
      ...prev,
      x: lastT.current.x + dx,
      y: lastT.current.y + dy,
    }))
  }, [])

  const onTouchEnd = useCallback(() => { touchRef.current.panning = false }, [])

  if (scenes.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground text-sm bg-muted/20 rounded-xl border border-dashed border-border">
        No scenes to display on canvas
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      data-canvas-container
      className={cn(
        'relative overflow-hidden rounded-xl bg-background border border-border h-[500px] w-full',
        'bg-[radial-gradient(ellipse_at_center,_hsl(var(--border)/0.3)_0.5px,_transparent_0.5px)]',
        'bg-[length:20px_20px]',
        panning.current ? 'cursor-grabbing' : 'cursor-grab',
      )}
      onMouseDown={onMouseDown}
      onMouseMove={onMouseMove}
      onMouseUp={onMouseUp}
      onMouseLeave={onMouseUp}
      onTouchStart={onTouchStart}
      onTouchMove={onTouchMove}
      onTouchEnd={onTouchEnd}
    >
      {/* Connectors SVG */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none z-0" style={{ transform: `translate(${t.x}px, ${t.y}px) scale(${t.scale})`, transformOrigin: '0 0' }}>
        {layout.slice(0, -1).map((from, i) => (
          <ConnectorCurve key={`conn-${from.scene.id}`} from={from} to={layout[i + 1]} />
        ))}
      </svg>

      {/* Nodes */}
      <div className="absolute inset-0 z-10" style={{ transform: `translate(${t.x}px, ${t.y}px) scale(${t.scale})`, transformOrigin: '0 0' }}>
        {layout.map(n => (
          <SceneCanvasNode key={n.scene.id} node={n} selected={n.scene.id === selectedId} onClick={() => onSelect(n.scene)} />
        ))}
      </div>

      {/* Zoom indicator */}
      <div className="absolute bottom-2 right-2 z-20 flex items-center gap-2">
        <button
          type="button"
          onClick={() => setT(prev => ({ ...prev, scale: Math.max(0.15, prev.scale * 0.8) }))}
          className="w-6 h-6 rounded bg-background/80 border border-border text-muted-foreground text-xs flex items-center justify-center hover:bg-accent transition-colors"
          aria-label="Zoom out"
        >−</button>
        <span className="text-[10px] text-muted-foreground tabular-nums w-8 text-center">
          {Math.round(t.scale * 100)}%
        </span>
        <button
          type="button"
          onClick={() => setT(prev => ({ ...prev, scale: Math.min(3, prev.scale * 1.25) }))}
          className="w-6 h-6 rounded bg-background/80 border border-border text-muted-foreground text-xs flex items-center justify-center hover:bg-accent transition-colors"
          aria-label="Zoom in"
        >+</button>
      </div>

      {/* Scene count */}
      <div className="absolute top-2 left-2 z-20 text-[10px] text-muted-foreground bg-background/80 px-2 py-1 rounded border border-border">
        {layout.length} scene{layout.length !== 1 ? 's' : ''} · drag to pan · scroll to zoom
      </div>

      {/* Legend */}
      <div className="absolute bottom-2 left-2 z-20 flex items-center gap-3 bg-background/80 px-2 py-1 rounded border border-border">
        <span className="flex items-center gap-1 text-[9px] text-muted-foreground">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-400" /> Remotion
        </span>
        <span className="flex items-center gap-1 text-[9px] text-muted-foreground">
          <span className="w-1.5 h-1.5 rounded-full bg-green-400" /> Manim
        </span>
        <span className="flex items-center gap-1 text-[9px] text-muted-foreground">
          <span className="w-1.5 h-1.5 rounded-full bg-purple-400" /> Animotion
        </span>
      </div>
    </div>
  )
}
