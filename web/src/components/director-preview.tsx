import { useState, useMemo } from 'react'
import { type SceneNode, type VideoProject, Engine, computeProjectHash, computeSceneHash } from '@/lib/ir-types'
import { pickEngine } from '@/lib/director'
import { SceneGraph } from './scene-graph'
import { SceneDetail } from './scene-detail'
import { cn } from '@/lib/utils'

const ENGINE_COLORS: Record<Engine, string> = {
  [Engine.REMOTION]: 'bg-blue-500',
  [Engine.MANIM]: 'bg-green-500',
  [Engine.ANIMOTION]: 'bg-purple-500',
}

const ENGINE_LABELS: Record<Engine, string> = {
  [Engine.REMOTION]: 'Remotion',
  [Engine.MANIM]: 'Manim',
  [Engine.ANIMOTION]: 'Animotion',
}

interface DirectorPreviewProps { project: VideoProject }

export function DirectorPreview({ project }: DirectorPreviewProps) {
  const [selectedId, setSelectedId] = useState<string | undefined>(project.scenes[0]?.id)

  const scenesWithHash = useMemo<SceneNode[]>(() =>
    project.scenes.map(s => ({ ...s, contentHash: s.contentHash ?? computeSceneHash(s) })), [project.scenes])

  const projectWithHash = useMemo<VideoProject>(() => ({
    ...project,
    scenes: scenesWithHash,
    contentHash: project.contentHash ?? computeProjectHash({ ...project, scenes: scenesWithHash }),
  }), [project, scenesWithHash])

  const selectedScene = scenesWithHash.find(s => s.id === selectedId) ?? null

  const engineCounts = useMemo(() => {
    const counts: Record<string, number> = { [Engine.REMOTION]: 0, [Engine.MANIM]: 0, [Engine.ANIMOTION]: 0 }
    let total = 0
    for (const s of scenesWithHash) { counts[s.routedEngine ?? pickEngine(s)]++; total++ }
    return { counts, total }
  }, [scenesWithHash])

  const totalFrames = useMemo(() => scenesWithHash.reduce((s, sc) => s + sc.duration_frames, 0), [scenesWithHash])
  const totalSeconds = Math.round(totalFrames / project.fps)

  return (
    <div className="space-y-4">
      <div className="bg-card border border-border rounded-xl p-4">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-foreground">{projectWithHash.title}</h2>
            <div className="flex flex-wrap gap-x-4 gap-y-1 mt-1 text-xs text-muted-foreground">
              <span>{scenesWithHash.length} scene{scenesWithHash.length !== 1 ? 's' : ''}</span>
              <span>{totalFrames}f ({totalSeconds}s)</span>
              <span>{projectWithHash.fps}fps</span>
              <span>{projectWithHash.width}×{projectWithHash.height}</span>
              {projectWithHash.audio_tracks.length > 0 && <span>{projectWithHash.audio_tracks.length} audio track{projectWithHash.audio_tracks.length !== 1 ? 's' : ''}</span>}
            </div>
          </div>
          <code className="text-[10px] font-mono text-muted-foreground text-right">#{projectWithHash.contentHash}</code>
        </div>

        <div className="mt-3">
          <label className="block text-xs font-medium text-muted-foreground mb-1.5 uppercase tracking-wider">Engine Routing</label>
          <div className="flex h-2 rounded-full overflow-hidden bg-secondary">
            {(Object.entries(engineCounts.counts) as [Engine, number][]).map(([e, c]) => c === 0 ? null : (
              <div key={e} className={cn(ENGINE_COLORS[e], 'transition-all')} style={{ width: `${(c / engineCounts.total) * 100}%` }} />
            ))}
          </div>
          <div className="flex flex-wrap gap-3 mt-1.5">
            {(Object.entries(engineCounts.counts) as [Engine, number][]).map(([e, c]) => c === 0 ? null : (
              <div key={e} className="flex items-center gap-1.5">
                <span className={cn('w-2 h-2 rounded-full', ENGINE_COLORS[e])} />
                <span className="text-[10px] text-muted-foreground">{ENGINE_LABELS[e]} {c} ({Math.round((c / engineCounts.total) * 100)}%)</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-card border border-border rounded-xl">
          <div className="px-4 py-3 border-b border-border">
            <h3 className="text-sm font-medium text-foreground">Scene Graph</h3>
            <p className="text-[10px] text-muted-foreground mt-0.5">{scenesWithHash.length} node{scenesWithHash.length !== 1 ? 's' : ''} · click to inspect</p>
          </div>
          <div className="p-3 max-h-[500px] overflow-y-auto">
            <SceneGraph scenes={scenesWithHash} selectedId={selectedId} onSelect={s => setSelectedId(s.id)} />
          </div>
        </div>
        <div className="bg-card border border-border rounded-xl">
          <div className="px-4 py-3 border-b border-border">
            <h3 className="text-sm font-medium text-foreground">Scene Detail</h3>
          </div>
          <div className="p-4 max-h-[500px] overflow-y-auto">
            <SceneDetail scene={selectedScene} />
          </div>
        </div>
      </div>
    </div>
  )
}
