import { useEffect, useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { DirectorPreview } from '@/components/director-preview'
import { Engine, SceneKind, type VideoProject } from '@/lib/ir-types'

export const Route = createFileRoute('/director-preview')({ component: DirectorPreviewRoute })

const FALLBACK_DATA: VideoProject = {
  title: 'Introduction to Quantum Computing', fps: 30, width: 1920, height: 1080,
  audio_tracks: [{ src: 'tts/output.wav', startFrame: 0, durationFrames: 540 }],
  scenes: [
    { id: 'scene_0', kind: SceneKind.TITLE, payload: JSON.stringify({ title: 'Quantum Computing', subtitle: 'A New Paradigm' }), engine_hint: Engine.REMOTION, duration_frames: 90, narration: { text: 'Quantum computing represents a fundamental shift.', words: [], source: 'estimated' } },
    { id: 'scene_1', kind: SceneKind.CODE, payload: JSON.stringify({ code: 'from qiskit import QuantumCircuit\nqc = QuantumCircuit(2,2)\nqc.h(0)\nqc.cx(0,1)', lang: 'python', title: 'Bell State Circuit' }), engine_hint: Engine.REMOTION, duration_frames: 150, narration: { text: 'A simple Bell state circuit in Qiskit.', words: [], source: 'estimated' } },
    { id: 'scene_2', kind: SceneKind.DIAGRAM, payload: JSON.stringify({ layout: 'math_graph', nodes: [{ id: '|0>', label: '|0⟩' }, { id: '|1>', label: '|1⟩' }] }), engine_hint: Engine.MANIM, duration_frames: 120, narration: { text: 'Qubits in superposition states.', words: [], source: 'estimated' } },
    { id: 'scene_3', kind: SceneKind.CHART, payload: JSON.stringify({ chartType: 'bar', title: 'Quantum Volume', data: [{ label: '2019', value: 8 }, { label: '2020', value: 32 }, { label: '2021', value: 64 }, { label: '2022', value: 128 }, { label: '2023', value: 256 }] }), engine_hint: Engine.MANIM, duration_frames: 120, narration: { text: 'Quantum volume doubled each year.', words: [], source: 'estimated' } },
    { id: 'scene_4', kind: SceneKind.OUTRO, payload: JSON.stringify({ title: 'Thank You', cta: 'Learn more' }), engine_hint: Engine.REMOTION, duration_frames: 60, narration: { text: 'Thank you for watching.', words: [], source: 'estimated' } },
  ],
}

function DirectorPreviewRoute() {
  const [project, setProject] = useState<VideoProject | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)

    fetch('/api/director/preview')
      .then(res => {
        if (!res.ok) throw new Error(`Backend returned ${res.status}`)
        return res.json() as Promise<VideoProject>
      })
      .then(data => { if (!cancelled) setProject(data) })
      .catch(err => {
        if (cancelled) return
        console.warn('Director preview backend unavailable, using fallback:', err)
        setProject(FALLBACK_DATA)
        setError('Using local sample data — backend preview endpoint unavailable')
      })
      .finally(() => { if (!cancelled) setLoading(false) })

    return () => { cancelled = true }
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-background p-4 md:p-6">
        <div className="max-w-6xl mx-auto">
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-foreground">Director Preview</h1>
          </div>
          <div className="flex items-center justify-center h-64 text-muted-foreground">
            <div className="flex flex-col items-center gap-2">
              <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
              <p className="text-sm">Loading preview from backend...</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (!project) {
    return (
      <div className="min-h-screen bg-background p-4 md:p-6">
        <div className="max-w-6xl mx-auto">
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-foreground">Director Preview</h1>
          </div>
          <div className="flex items-center justify-center h-64 text-muted-foreground">
            <p>No preview data available.</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background p-4 md:p-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-foreground">Director Preview</h1>
          <p className="text-sm text-muted-foreground mt-1">Scene graph, engine routing, and scene detail inspection</p>
          {error && <p className="text-xs text-amber-500 mt-1">{error}</p>}
        </div>
        <DirectorPreview project={project} />
      </div>
    </div>
  )
}
