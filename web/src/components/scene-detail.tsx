import { useState } from 'react'
import { type SceneNode, Engine } from '@/lib/ir-types'
import { pickEngine, getRoutingReason } from '@/lib/director'
import { cn } from '@/lib/utils'

const ENGINE_META: Record<Engine, { label: string; color: string }> = {
  [Engine.REMOTION]: { label: 'Remotion', color: 'bg-blue-600/20 text-blue-400 border-blue-500/40' },
  [Engine.MANIM]: { label: 'Manim', color: 'bg-green-600/20 text-green-400 border-green-500/40' },
  [Engine.ANIMOTION]: { label: 'Animotion', color: 'bg-purple-600/20 text-purple-400 border-purple-500/40' },
}

interface SceneDetailProps { scene: SceneNode | null }

export function SceneDetail({ scene }: SceneDetailProps) {
  const [showPayload, setShowPayload] = useState(false)
  const [copied, setCopied] = useState(false)

  if (!scene) {
    return <div className="flex items-center justify-center h-full min-h-[300px] text-muted-foreground text-sm">Select a scene from the graph to view details</div>
  }

  const engine = pickEngine(scene)
  const engineMeta = ENGINE_META[engine]
  const reason = getRoutingReason(scene)
  const seconds = Math.round(scene.duration_frames / 30)

  const handleCopyHash = async () => {
    if (scene.contentHash) {
      try { await navigator.clipboard.writeText(scene.contentHash); setCopied(true); setTimeout(() => setCopied(false), 1500) } catch { /* */ }
    }
  }

  let payloadObj: Record<string, unknown> | null = null
  try { payloadObj = JSON.parse(scene.payload) } catch { /* */ }

  return (
    <div className="space-y-5">
      <div>
        <div className="flex items-center gap-2 mb-1">
          <h3 className="text-sm font-semibold text-foreground">{scene.id}</h3>
          <span className={cn('inline-flex items-center rounded border px-1.5 py-0.5 text-xs font-medium', engineMeta.color)}>{engineMeta.label}</span>
        </div>
        <p className="text-[11px] text-muted-foreground">{scene.kind} · {scene.duration_frames}f ({seconds}s at 30fps)</p>
      </div>

      <div>
        <label className="block text-xs font-medium text-muted-foreground mb-1">Content Hash</label>
        <div className="flex items-center gap-2">
          <code className="text-xs font-mono bg-muted px-2 py-1 rounded break-all flex-1">{scene.contentHash ?? '—'}</code>
          <button type="button" onClick={handleCopyHash} className="text-xs text-primary hover:underline shrink-0" aria-label="Copy hash">{copied ? 'Copied' : 'Copy'}</button>
        </div>
      </div>

      <div>
        <label className="block text-xs font-medium text-muted-foreground mb-1">Engine Routing</label>
        <div className="bg-muted/50 rounded-lg px-3 py-2">
          <div className="flex items-center gap-2 mb-1">
            <span className={cn('inline-flex items-center rounded border px-1.5 py-0.5 text-xs font-medium', engineMeta.color)}>{engineMeta.label}</span>
            <span className="text-xs text-muted-foreground">← from hint: {scene.engine_hint}</span>
          </div>
          <p className="text-xs text-muted-foreground">{reason}</p>
        </div>
      </div>

      <div>
        <label className="block text-xs font-medium text-muted-foreground mb-1">Narration ({scene.narration.source})</label>
        <p className="text-sm text-foreground/80 bg-muted/30 rounded-lg px-3 py-2">{scene.narration.text || <span className="italic text-muted-foreground">No narration</span>}</p>
        {scene.narration.words.length > 0 && <p className="text-[10px] text-muted-foreground mt-1">{scene.narration.words.length} word{scene.narration.words.length !== 1 ? 's' : ''} timed</p>}
      </div>

      <div>
        <button type="button" onClick={() => setShowPayload(!showPayload)} className="flex items-center gap-2 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors">
          <svg className={cn('w-3 h-3 transition-transform', showPayload && 'rotate-90')} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 18l6-6-6-6"/></svg>
          Payload JSON {payloadObj && <span className="text-muted-foreground/60 font-normal">({Object.keys(payloadObj).length} keys)</span>}
        </button>
        {showPayload && <pre className="mt-2 text-[11px] font-mono bg-muted p-3 rounded-lg overflow-x-auto max-h-64 overflow-y-auto">{JSON.stringify(payloadObj, null, 2)}</pre>}
      </div>

      <div>
        <label className="block text-xs font-medium text-muted-foreground mb-1">Frame Preview</label>
        <div className="aspect-video bg-muted rounded-lg flex items-center justify-center border border-dashed border-border">
          <div className="text-center px-4">
            <svg className="w-8 h-8 mx-auto mb-1 text-muted-foreground/50" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="2" y="2" width="20" height="20" rx="2" ry="2"/><path d="M8 2v20M16 2v20M2 8h20M2 16h20"/></svg>
            <p className="text-[11px] text-muted-foreground">Frame thumbnail</p>
            <p className="text-[10px] text-muted-foreground/60">No image endpoint available yet</p>
          </div>
        </div>
      </div>

      <div>
        <label className="block text-xs font-medium text-muted-foreground mb-1">Per-Scene Report</label>
        <div className="bg-muted rounded-lg px-3 py-3 border border-dashed border-border">
          <p className="text-xs text-muted-foreground">Report not yet generated</p>
          <p className="text-[10px] text-muted-foreground/60 mt-0.5">Available after render + review pipeline completes</p>
        </div>
      </div>

      <div className="flex gap-2 pt-1">
        <button type="button" disabled className="inline-flex items-center rounded-md border border-input bg-transparent px-3 py-1.5 text-xs font-medium text-muted-foreground opacity-50 cursor-not-allowed">Rerender</button>
        <button type="button" disabled className="inline-flex items-center rounded-md border border-input bg-transparent px-3 py-1.5 text-xs font-medium text-muted-foreground opacity-50 cursor-not-allowed">Retry</button>
        <button type="button" disabled className="inline-flex items-center rounded-md border border-input bg-transparent px-3 py-1.5 text-xs font-medium text-muted-foreground opacity-50 cursor-not-allowed">Reroute</button>
      </div>
    </div>
  )
}
