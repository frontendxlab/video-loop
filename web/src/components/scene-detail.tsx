import { useState, useCallback } from 'react'
import { type SceneNode, Engine, type OverlayItem, type MotionHint } from '@/lib/ir-types'
import { pickEngine, getRoutingReason } from '@/lib/director'
import { cn } from '@/lib/utils'
import { stopJob, retryScene, rerouteScene } from '@/lib/api'

const ENGINE_META: Record<Engine, { label: string; color: string }> = {
  [Engine.REMOTION]: { label: 'Remotion', color: 'bg-blue-600/20 text-blue-400 border-blue-500/40' },
  [Engine.MANIM]: { label: 'Manim', color: 'bg-green-600/20 text-green-400 border-green-500/40' },
  [Engine.ANIMOTION]: { label: 'Animotion', color: 'bg-purple-600/20 text-purple-400 border-purple-500/40' },
}

interface SceneDetailProps {
  scene: SceneNode | null
  /** Optional jobId for artifact fetching (used in job detail context) */
  jobId?: string
}

export function SceneDetail({ scene, jobId }: SceneDetailProps) {
  const [showPayload, setShowPayload] = useState(false)
  const [copied, setCopied] = useState(false)
  const [imgError, setImgError] = useState<Record<string, boolean>>({})
  const [actionState, setActionState] = useState<'idle' | 'loading' | 'done' | 'error'>('idle')

  if (!scene) {
    return <div className="flex items-center justify-center h-full min-h-[300px] text-muted-foreground text-sm">Select a scene from the graph to view details</div>
  }

  const engine = scene.routedEngine ?? pickEngine(scene)
  const engineMeta = ENGINE_META[engine]
  const reason = getRoutingReason(scene)
  const seconds = Math.round(scene.duration_frames / 30)

  // Build artifact URLs if jobId is provided
  const thumbUrl = jobId ? `/api/artifacts/${encodeURIComponent(jobId)}/scenes/${encodeURIComponent(scene.id)}/thumbnail` : null
  const reportUrl = jobId ? `/api/artifacts/${encodeURIComponent(jobId)}/scenes/${encodeURIComponent(scene.id)}/report` : null

  const handleCopyHash = async () => {
    if (scene.contentHash) {
      try { await navigator.clipboard.writeText(scene.contentHash); setCopied(true); setTimeout(() => setCopied(false), 1500) } catch { /* */ }
    }
  }

  const handleImgError = (url: string) => {
    setImgError(prev => ({ ...prev, [url]: true }))
  }

  const actionsEnabled = Boolean(jobId && scene)

  const handleStop = useCallback(async () => {
    if (!jobId) return
    setActionState('loading')
    const res = await stopJob(jobId)
    setActionState(res ? 'done' : 'error')
    if (res) setTimeout(() => setActionState('idle'), 2000)
  }, [jobId])

  const handleRetry = useCallback(async () => {
    if (!jobId || !scene) return
    setActionState('loading')
    const res = await retryScene(jobId, scene.id)
    setActionState(res ? 'done' : 'error')
    if (res) setTimeout(() => setActionState('idle'), 2000)
  }, [jobId, scene])

  const handleReroute = useCallback(async () => {
    if (!jobId || !scene) return
    setActionState('loading')
    const engines = [Engine.REMOTION, Engine.MANIM, Engine.ANIMOTION]
    const current = scene.routedEngine ?? pickEngine(scene)
    const next = engines[(engines.indexOf(current) + 1) % engines.length]
    const res = await rerouteScene(jobId, scene.id, next)
    setActionState(res ? 'done' : 'error')
    if (res) setTimeout(() => setActionState('idle'), 2000)
  }, [jobId, scene])

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

      {scene.overlay_stack && scene.overlay_stack.items.length > 0 && (
        <OverlayStackSection stack={scene.overlay_stack} />
      )}

      {scene.motion_hints && scene.motion_hints.length > 0 && (
        <MotionHintsSection hints={scene.motion_hints} />
      )}

      <ArtifactSection
        scene={scene}
        jobId={jobId}
        thumbUrl={thumbUrl}
        reportUrl={reportUrl}
        imgError={imgError}
        handleImgError={handleImgError}
      />

      <div className="flex gap-2 pt-1">
        <button
          type="button"
          disabled={!actionsEnabled || actionState === 'loading'}
          onClick={handleStop}
          className={cn(
            'inline-flex items-center rounded-md border border-input bg-transparent px-3 py-1.5 text-xs font-medium',
            actionsEnabled ? 'hover:bg-accent hover:text-accent-foreground' : 'opacity-50 cursor-not-allowed',
            actionState === 'done' && 'text-emerald-500 border-emerald-500/50',
            actionState === 'error' && 'text-destructive border-destructive/50',
          )}
        >
          {actionState === 'loading' ? '…' : actionState === 'done' ? 'Stopped' : actionState === 'error' ? 'Failed' : 'Stop'}
        </button>
        <button
          type="button"
          disabled={!actionsEnabled || actionState === 'loading'}
          onClick={handleRetry}
          className={cn(
            'inline-flex items-center rounded-md border border-input bg-transparent px-3 py-1.5 text-xs font-medium',
            actionsEnabled ? 'hover:bg-accent hover:text-accent-foreground' : 'opacity-50 cursor-not-allowed',
            actionState === 'done' && 'text-emerald-500 border-emerald-500/50',
            actionState === 'error' && 'text-destructive border-destructive/50',
          )}
        >
          {actionState === 'loading' ? '…' : actionState === 'done' ? 'Retried' : actionState === 'error' ? 'Failed' : 'Retry'}
        </button>
        <button
          type="button"
          disabled={!actionsEnabled || actionState === 'loading'}
          onClick={handleReroute}
          className={cn(
            'inline-flex items-center rounded-md border border-input bg-transparent px-3 py-1.5 text-xs font-medium',
            actionsEnabled ? 'hover:bg-accent hover:text-accent-foreground' : 'opacity-50 cursor-not-allowed',
            actionState === 'done' && 'text-emerald-500 border-emerald-500/50',
            actionState === 'error' && 'text-destructive border-destructive/50',
          )}
        >
          {actionState === 'loading' ? '…' : actionState === 'done' ? 'Rerouted' : actionState === 'error' ? 'Failed' : 'Reroute'}
        </button>
      </div>
    </div>
  )
}

/** Overlay stack section — displays ordered overlay layers on scene */
function OverlayStackSection({ stack }: { stack: { items: OverlayItem[] } }) {
  const [expanded, setExpanded] = useState(false)
  const items = stack.items
  return (
    <div>
      <button type="button" onClick={() => setExpanded(!expanded)} className="flex items-center gap-2 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors">
        <svg className={cn('w-3 h-3 transition-transform', expanded && 'rotate-90')} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 18l6-6-6-6"/></svg>
        Overlay Stack ({items.length} layer{items.length !== 1 ? 's' : ''})
      </button>
      {expanded && (
        <div className="mt-2 space-y-1.5">
          {items.map((item) => (
            <div key={item.id} className="bg-muted/40 rounded-lg px-3 py-2 border border-border/50">
              <div className="flex items-center gap-2 mb-0.5">
                <span className={cn(
                  'inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-medium',
                  item.type === 'text' && 'bg-blue-500/20 text-blue-300',
                  item.type === 'image' && 'bg-green-500/20 text-green-300',
                  item.type === 'shape' && 'bg-amber-500/20 text-amber-300',
                  item.type === 'logo' && 'bg-purple-500/20 text-purple-300',
                )}>{item.type}</span>
                <code className="text-[10px] font-mono text-muted-foreground">{item.id}</code>
                {item.animation && <span className="text-[10px] text-muted-foreground/60 ml-auto">anim: {item.animation}</span>}
              </div>
              <p className="text-[11px] text-foreground/70 truncate">{item.content}</p>
              <p className="text-[10px] text-muted-foreground/60">
                pos ({item.position.x},{item.position.y}) · frame {item.startFrame}–{item.startFrame + item.durationFrames} · opacity {Math.round(item.opacity * 100)}%
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

/** Motion hints section — displays entrance/exit/emphasis/path motions */
function MotionHintsSection({ hints }: { hints: MotionHint[] }) {
  const [expanded, setExpanded] = useState(false)
  return (
    <div>
      <button type="button" onClick={() => setExpanded(!expanded)} className="flex items-center gap-2 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors">
        <svg className={cn('w-3 h-3 transition-transform', expanded && 'rotate-90')} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 18l6-6-6-6"/></svg>
        Motion Hints ({hints.length})
      </button>
      {expanded && (
        <div className="mt-2 space-y-1.5">
          {hints.map((hint, i) => (
            <div key={i} className="bg-muted/40 rounded-lg px-3 py-2 border border-border/50">
              <div className="flex items-center gap-2 mb-0.5">
                <span className={cn(
                  'inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-medium',
                  hint.type === 'entrance' && 'bg-emerald-500/20 text-emerald-300',
                  hint.type === 'exit' && 'bg-red-500/20 text-red-300',
                  hint.type === 'emphasis' && 'bg-amber-500/20 text-amber-300',
                  hint.type === 'path' && 'bg-indigo-500/20 text-indigo-300',
                )}>{hint.type}</span>
                <code className="text-[10px] font-mono text-muted-foreground">{hint.animation}</code>
              </div>
              {hint.durationMs != null && (
                <p className="text-[10px] text-muted-foreground/60">
                  {hint.durationMs}ms{hint.delayMs != null ? ` · ${hint.delayMs}ms delay` : ''}{hint.easing ? ` · ${hint.easing}` : ''}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

/** Artifact section — displays thumbnail/frame/report with state-aware placeholders */
interface ArtifactSectionProps {
  scene: SceneNode
  jobId?: string
  thumbUrl: string | null
  reportUrl: string | null
  imgError: Record<string, boolean>
  handleImgError: (url: string) => void
}

function ArtifactSection({ scene, jobId, thumbUrl, reportUrl, imgError, handleImgError }: ArtifactSectionProps) {
  const artifactState = scene.artifacts?.thumbnail?.state ?? (jobId ? 'pending' : 'missing')
  const hasThumbnail = thumbUrl && !imgError[thumbUrl] && artifactState === 'ready'

  return (
    <>
      <div>
        <label className="block text-xs font-medium text-muted-foreground mb-1">Frame Preview</label>
        {jobId && artifactState === 'generating' ? (
          <ArtifactPlaceholder icon="spinner" title="Generating frame..." subtitle="Render in progress" />
        ) : artifactState === 'error' ? (
          <ArtifactPlaceholder icon="error" title="Frame generation failed" subtitle={scene.artifacts?.thumbnail?.errorMessage ?? 'Render error'} />
        ) : hasThumbnail ? (
          <div className="aspect-video bg-muted rounded-lg overflow-hidden border border-border">
            <img src={thumbUrl!} alt={`${scene.id} thumbnail`} className="w-full h-full object-cover" onError={() => handleImgError(thumbUrl!)} />
          </div>
        ) : (
          <ArtifactPlaceholder icon="frame" title="Frame thumbnail" subtitle={!jobId ? 'No image endpoint available yet' : 'Waiting for render'} />
        )}
      </div>

      <div>
        <label className="block text-xs font-medium text-muted-foreground mb-1">Per-Scene Report</label>
        {reportUrl ? (
          <ReportFetcher url={reportUrl} />
        ) : (
          <div className="bg-muted rounded-lg px-3 py-3 border border-dashed border-border">
            <p className="text-xs text-muted-foreground">Report not yet generated</p>
            <p className="text-[10px] text-muted-foreground/60 mt-0.5">Available after render + review pipeline completes</p>
          </div>
        )}
      </div>
    </>
  )
}

/** State-aware artifact placeholder icon/status */
function ArtifactPlaceholder({ icon, title, subtitle }: { icon: 'spinner' | 'error' | 'frame'; title: string; subtitle: string }) {
  return (
    <div className="aspect-video bg-muted rounded-lg flex items-center justify-center border border-dashed border-border">
      <div className="text-center px-4">
        {icon === 'spinner' ? (
          <div className="w-8 h-8 mx-auto mb-1 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        ) : icon === 'error' ? (
          <svg className="w-8 h-8 mx-auto mb-1 text-destructive/60" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <circle cx="12" cy="12" r="10"/><path d="M15 9l-6 6M9 9l6 6"/>
          </svg>
        ) : (
          <svg className="w-8 h-8 mx-auto mb-1 text-muted-foreground/50" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <rect x="2" y="2" width="20" height="20" rx="2" ry="2"/><path d="M8 2v20M16 2v20M2 8h20M2 16h20"/>
          </svg>
        )}
        <p className="text-[11px] text-muted-foreground">{title}</p>
        <p className="text-[10px] text-muted-foreground/60">{subtitle}</p>
      </div>
    </div>
  )
}

/** Inline report fetcher — loads report JSON on demand */
function ReportFetcher({ url }: { url: string }) {
  const [report, setReport] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(false)

  if (report) {
    return (
      <pre className="text-[11px] font-mono bg-muted p-3 rounded-lg overflow-x-auto max-h-48 overflow-y-auto">
        {JSON.stringify(report, null, 2)}
      </pre>
    )
  }

  if (error) {
    return (
      <div className="bg-muted rounded-lg px-3 py-3 border border-dashed border-border">
        <p className="text-xs text-muted-foreground">Report not yet generated</p>
        <p className="text-[10px] text-muted-foreground/60 mt-0.5">Available after render + review pipeline completes</p>
      </div>
    )
  }

  return (
    <button
      type="button"
      onClick={async () => {
        setLoading(true)
        try {
          const res = await fetch(url)
          if (!res.ok) throw new Error('Not found')
          setReport(await res.json() as Record<string, unknown>)
        } catch {
          setError(true)
        } finally {
          setLoading(false)
        }
      }}
      disabled={loading}
      className={cn(
        'inline-flex items-center rounded-md border border-input bg-transparent px-3 py-1.5 text-xs font-medium transition-colors',
        loading ? 'opacity-50 cursor-not-allowed' : 'hover:bg-accent'
      )}
    >
      {loading ? 'Loading…' : 'Load Report'}
    </button>
  )
}
