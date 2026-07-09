import { type SceneNode, Engine, SceneKind } from '@/lib/ir-types'
import { pickEngine } from '@/lib/director'
import { cn } from '@/lib/utils'

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
}

const ENGINE_META: Record<Engine, { label: string; color: string }> = {
  [Engine.REMOTION]: { label: 'Remotion', color: 'bg-blue-600/20 text-blue-400 border-blue-500/40' },
  [Engine.MANIM]: { label: 'Manim', color: 'bg-green-600/20 text-green-400 border-green-500/40' },
  [Engine.ANIMOTION]: { label: 'Animotion', color: 'bg-purple-600/20 text-purple-400 border-purple-500/40' },
}

interface SceneGraphProps { scenes: SceneNode[]; selectedId?: string; onSelect: (scene: SceneNode) => void }

export function SceneGraph({ scenes, selectedId, onSelect }: SceneGraphProps) {
  if (scenes.length === 0) {
    return <div className="flex items-center justify-center h-48 text-muted-foreground text-sm">No scenes in project</div>
  }
  return (
    <div className="space-y-1.5" role="list" aria-label="Scene graph">
      {scenes.map((scene, idx) => {
        const engine = scene.routedEngine ?? pickEngine(scene)
        const kindMeta = KIND_META[scene.kind] ?? KIND_META[SceneKind.TITLE]
        const engineMeta = ENGINE_META[engine]
        const seconds = Math.round(scene.duration_frames / 30)
        return (
          <button key={scene.id} role="listitem" type="button" onClick={() => onSelect(scene)}
            className={cn('w-full text-left rounded-lg border px-3 py-2.5 transition-all hover:bg-card/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring', selectedId === scene.id ? 'border-primary/50 bg-primary/5 shadow-sm' : 'border-border bg-card')}>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-muted text-muted-foreground text-xs font-medium flex items-center justify-center">{idx + 1}</span>
              <span className={cn('inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium', kindMeta.color)}>{kindMeta.label}</span>
              <span className={cn('inline-flex items-center rounded border px-1.5 py-0.5 text-xs font-medium', engineMeta.color)}>{engineMeta.label}</span>
              <code className="ml-auto text-[10px] text-muted-foreground font-mono">#{scene.contentHash?.slice(0, 8) ?? '—'}</code>
            </div>
            <div className="flex items-center gap-3 text-[11px] text-muted-foreground">
              <span>{scene.duration_frames}f</span><span>({seconds}s @ 30fps)</span>
              <span className="ml-auto truncate max-w-[120px]">{scene.id}</span>
            </div>
          </button>
        )
      })}
    </div>
  )
}
