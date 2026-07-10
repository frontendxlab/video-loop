import { useState } from 'react'
import type { SceneInfo, ArtifactState } from '@/types/job'
import { artifactThumbnailUrl, artifactFrameUrl, artifactReportUrl } from '@/lib/api'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'

interface Props {
  scene: SceneInfo
  jobId: string
  onClose: () => void
}

/** Infer artifact state from scene status when backend doesn't provide artifactState */
function inferArtifactState(scene: SceneInfo): ArtifactState {
  if (scene.artifactState) return scene.artifactState
  if (scene.status === 'rendering') return 'generating'
  if (scene.status === 'pending') return 'pending'
  if (scene.status === 'failed') return 'error'
  return 'missing'
}

/** State-aware artifact placeholder */
function ArtifactPreview({
  label,
  url,
  sceneId,
  state,
  errorMsg,
  onImgError,
}: {
  label: string
  url: string | null
  sceneId: string
  state: ArtifactState
  errorMsg?: string
  onImgError: (url: string) => void
}) {
  const showImg = url && state === 'ready'

  return (
    <div>
      <label className="block text-xs font-medium text-muted-foreground mb-1">{label}</label>
      {showImg ? (
        <div className="aspect-video bg-muted rounded-lg overflow-hidden border border-border">
          <img
            src={url}
            alt={`${sceneId} ${label}`}
            className="w-full h-full object-cover"
            onError={() => onImgError(url)}
          />
        </div>
      ) : (
        <div className="aspect-video bg-muted rounded-lg flex items-center justify-center border border-dashed border-border">
          <div className="text-center px-4">
            {state === 'generating' ? (
              <>
                <div className="w-8 h-8 mx-auto mb-1 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                <p className="text-[11px] text-muted-foreground">Generating...</p>
                <p className="text-[10px] text-muted-foreground/60">Render in progress</p>
              </>
            ) : state === 'error' ? (
              <>
                <svg className="w-8 h-8 mx-auto mb-1 text-destructive/60" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <circle cx="12" cy="12" r="10"/><path d="M15 9l-6 6M9 9l6 6"/>
                </svg>
                <p className="text-[11px] text-muted-foreground">Artifact unavailable</p>
                <p className="text-[10px] text-muted-foreground/60">{errorMsg ?? 'Generation failed'}</p>
              </>
            ) : (
              <>
                <svg className="w-8 h-8 mx-auto mb-1 text-muted-foreground/50" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <rect x="2" y="2" width="20" height="20" rx="2" ry="2"/><path d="M8 2v20M16 2v20M2 8h20M2 16h20"/>
                </svg>
                <p className="text-[11px] text-muted-foreground">Not available yet</p>
                <p className="text-[10px] text-muted-foreground/60">Waiting for render</p>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export function SceneArtifactPanel({ scene, jobId, onClose }: Props) {
  const [imgError, setImgError] = useState<Record<string, boolean>>({})
  const [report, setReport] = useState<Record<string, unknown> | null>(null)
  const [reportLoading, setReportLoading] = useState(false)
  const [reportError, setReportError] = useState(false)

  const thumbUrl = scene.thumbnailUrl ?? artifactThumbnailUrl(jobId, scene.id)
  const frameUrl = scene.frameUrl ?? artifactFrameUrl(jobId, scene.id)
  const reportUrl = scene.reportUrl ?? artifactReportUrl(jobId, scene.id)

  const artifactState = inferArtifactState(scene)

  const effectiveThumbState: ArtifactState =
    (thumbUrl && artifactState === 'ready') ? 'ready'
    : artifactState === 'error' ? 'error'
    : artifactState === 'generating' ? 'generating'
    : (scene.status === 'rendering' || scene.status === 'pending') ? 'generating'
    : artifactState

  const effectiveFrameState: ArtifactState = effectiveThumbState

  const fetchReport = async () => {
    if (report || reportLoading) return
    setReportLoading(true)
    setReportError(false)
    try {
      const res = await fetch(reportUrl)
      if (!res.ok) throw new Error('Not found')
      setReport(await res.json() as Record<string, unknown>)
    } catch {
      setReportError(true)
    } finally {
      setReportLoading(false)
    }
  }

  const handleImgError = (url: string) => {
    setImgError(prev => ({ ...prev, [url]: true }))
  }

  return (
    <div className="rounded-lg border border-border bg-card p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold">{scene.id} — Artifacts</h4>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-[10px]">{scene.kind}</Badge>
          <button
            type="button"
            onClick={onClose}
            className="text-xs text-muted-foreground hover:text-foreground"
          >
            ✕
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <ArtifactPreview
          label="Thumbnail"
          url={thumbUrl && !imgError[thumbUrl] ? thumbUrl : null}
          sceneId={scene.id}
          state={effectiveThumbState}
          errorMsg={scene.artifactError}
          onImgError={handleImgError}
        />
        <ArtifactPreview
          label="Sampled Frame"
          url={frameUrl && !imgError[frameUrl] ? frameUrl : null}
          sceneId={scene.id}
          state={effectiveFrameState}
          errorMsg={scene.artifactError}
          onImgError={handleImgError}
        />
      </div>

      {/* Report */}
      <div>
        <label className="block text-xs font-medium text-muted-foreground mb-1">Scene Report</label>
        {report ? (
          <pre className="text-[11px] font-mono bg-muted p-3 rounded-lg overflow-x-auto max-h-48 overflow-y-auto">
            {JSON.stringify(report, null, 2)}
          </pre>
        ) : reportError ? (
          <div className="bg-muted rounded-lg px-3 py-3 border border-dashed border-border">
            <p className="text-xs text-muted-foreground">Report not yet generated</p>
            <p className="text-[10px] text-muted-foreground/60 mt-0.5">Available after render + review pipeline completes</p>
          </div>
        ) : (
          <div>
            <button
              type="button"
              onClick={fetchReport}
              disabled={reportLoading}
              className={cn(
                'inline-flex items-center rounded-md border border-input bg-transparent px-3 py-1.5 text-xs font-medium transition-colors',
                reportLoading ? 'opacity-50 cursor-not-allowed' : 'hover:bg-accent'
              )}
            >
              {reportLoading ? 'Loading…' : 'Load Report'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
