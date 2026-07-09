/** Types mirroring Python engine/ir.py — frozen contract between director and engines */

export enum Engine {
  REMOTION = 'remotion',
  MANIM = 'manim',
  ANIMOTION = 'animotion',
}

export enum SceneKind {
  TITLE = 'title',
  CODE = 'code',
  DIFF = 'diff',
  BULLETS = 'bullets',
  DIAGRAM = 'diagram',
  CHART = 'chart',
  TIMELINE = 'timeline',
  MAP3D = 'map3d',
  COMPARISON = 'comparison',
  QUOTE = 'quote',
  OUTRO = 'outro',
  MINDMAP = 'mindmap',
}

export interface WordTiming {
  text: string
  startMs: number
  endMs: number
}

export interface NarrationSpec {
  text: string
  words: WordTiming[]
  source: 'forced_align' | 'exact_synthesis' | 'estimated'
}

export interface AudioTrackIR {
  src: string
  startFrame: number
  durationFrames: number
}

export interface SceneNode {
  id: string
  kind: SceneKind
  payload: string
  engine_hint: Engine
  duration_frames: number
  narration: NarrationSpec
  contentHash?: string
  routedEngine?: Engine
}

export interface VideoProject {
  title: string
  scenes: SceneNode[]
  fps: number
  width: number
  height: number
  audio_tracks: AudioTrackIR[]
  contentHash?: string
}

export interface RoutingEntry {
  kind: string
  engine: Engine
  reason: string
  layout?: string
  interactive?: boolean
}

export function computeSceneHash(scene: Omit<SceneNode, 'contentHash'>): string {
  const data = { id: scene.id, kind: scene.kind, payload: scene.payload, engine_hint: scene.engine_hint, duration_frames: scene.duration_frames, narration: scene.narration }
  return stableHash(JSON.stringify(data, Object.keys(data).sort())).slice(0, 16)
}

export function computeProjectHash(proj: Omit<VideoProject, 'contentHash'>): string {
  const audioStr = proj.audio_tracks.map(a => `${a.src}:${a.startFrame}:${a.durationFrames}`).join('')
  const header = `${proj.title}|${proj.fps}|${proj.width}|${proj.height}`
  return stableHash(header + proj.scenes.map(s => computeSceneHash(s)).join('') + audioStr).slice(0, 16)
}

function stableHash(input: string): string {
  let h1 = 5381, h2 = 52711
  for (let i = 0; i < input.length; i++) {
    const c = input.charCodeAt(i)
    h1 = ((h1 << 5) + h1 + c) | 0
    h2 = ((h2 << 5) + h2 + c) | 0
  }
  return ((h2 >>> 0).toString(16).padStart(8, '0') + (h1 >>> 0).toString(16).padStart(8, '0'))
}
