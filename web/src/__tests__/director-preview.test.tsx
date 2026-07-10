import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Engine, SceneKind, computeSceneHash, computeProjectHash, type SceneNode, type VideoProject } from '@/lib/ir-types'
import { pickEngine, getRoutingReason } from '@/lib/director'
import { SceneGraph } from '@/components/scene-graph'
import { SceneDetail } from '@/components/scene-detail'
import { DirectorPreview } from '@/components/director-preview'

function makeScene(o: Partial<SceneNode> = {}): SceneNode {
  return { id: 'test_scene', kind: SceneKind.TITLE, payload: '{}', engine_hint: Engine.REMOTION, duration_frames: 90, narration: { text: 'Hello', words: [], source: 'estimated' }, ...o }
}
function makeProject(scenes: SceneNode[] = []): VideoProject {
  return { title: 'Test Project', fps: 30, width: 1920, height: 1080, audio_tracks: [], scenes }
}

describe('pickEngine', () => {
  const cases: [SceneKind, Engine][] = [
    [SceneKind.CODE, Engine.REMOTION], [SceneKind.DIFF, Engine.REMOTION],
    [SceneKind.BULLETS, Engine.REMOTION], [SceneKind.TITLE, Engine.REMOTION],
    [SceneKind.COMPARISON, Engine.REMOTION], [SceneKind.QUOTE, Engine.REMOTION],
    [SceneKind.OUTRO, Engine.REMOTION], [SceneKind.MINDMAP, Engine.REMOTION],
    [SceneKind.CHART, Engine.MANIM], [SceneKind.TIMELINE, Engine.MANIM],
    [SceneKind.MAP3D, Engine.MANIM],
    /* Showcase kinds */
    [SceneKind.SHOWCASE, Engine.REMOTION], [SceneKind.SPLIT, Engine.REMOTION],
    [SceneKind.MOCKUP, Engine.REMOTION], [SceneKind.HERO, Engine.REMOTION],
  ]
  for (const [kind, engine] of cases) {
    it(`routes ${kind} to ${engine}`, () => expect(pickEngine(makeScene({ kind }))).toBe(engine))
  }
  it('routes math_graph diagram to manim', () => expect(pickEngine(makeScene({ kind: SceneKind.DIAGRAM, payload: JSON.stringify({ layout: 'math_graph' }) }))).toBe(Engine.MANIM))
  it('routes interactive diagram to animotion', () => expect(pickEngine(makeScene({ kind: SceneKind.DIAGRAM, payload: JSON.stringify({ interactive: true }) }))).toBe(Engine.ANIMOTION))
  it('routes default diagram to remotion', () => expect(pickEngine(makeScene({ kind: SceneKind.DIAGRAM, payload: JSON.stringify({}) }))).toBe(Engine.REMOTION))
  it('routes non-interactive diagram to remotion', () => expect(pickEngine(makeScene({ kind: SceneKind.DIAGRAM, payload: JSON.stringify({ interactive: false }) }))).toBe(Engine.REMOTION))
  it('is deterministic', () => { const n = makeScene({ kind: SceneKind.CHART }); expect(pickEngine(n)).toBe(pickEngine(n)) })
})

describe('getRoutingReason', () => {
  it('returns reason for code', () => expect(getRoutingReason(makeScene({ kind: SceneKind.CODE }))).toContain('Shiki'))
  it('returns reason for math_graph', () => expect(getRoutingReason(makeScene({ kind: SceneKind.DIAGRAM, payload: JSON.stringify({ layout: 'math_graph' }) }))).toContain('graph'))
  it('returns reason for interactive', () => expect(getRoutingReason(makeScene({ kind: SceneKind.DIAGRAM, payload: JSON.stringify({ interactive: true }) }))).toContain('CSS'))
  it('returns reason for showcase', () => expect(getRoutingReason(makeScene({ kind: SceneKind.SHOWCASE }))).toContain('showcase'))
  it('returns reason for split', () => expect(getRoutingReason(makeScene({ kind: SceneKind.SPLIT }))).toMatch(/split/i))
  it('returns reason for mockup', () => expect(getRoutingReason(makeScene({ kind: SceneKind.MOCKUP }))).toContain('mockup'))
  it('returns reason for hero', () => expect(getRoutingReason(makeScene({ kind: SceneKind.HERO }))).toContain('hero'))
})

describe('computeSceneHash', () => {
  it('returns 16-char hex', () => { const h = computeSceneHash(makeScene()); expect(h).toHaveLength(16); expect(/^[0-9a-f]+$/.test(h)).toBe(true) })
  it('deterministic', () => expect(computeSceneHash(makeScene())).toBe(computeSceneHash(makeScene())))
  it('changes with kind', () => expect(computeSceneHash(makeScene({ kind: SceneKind.TITLE }))).not.toBe(computeSceneHash(makeScene({ kind: SceneKind.CODE }))))
})

describe('computeProjectHash', () => {
  it('returns 16-char hex', () => { const h = computeProjectHash(makeProject([makeScene()])); expect(h).toHaveLength(16); expect(/^[0-9a-f]+$/.test(h)).toBe(true) })
  it('deterministic', () => expect(computeProjectHash(makeProject([makeScene()]))).toBe(computeProjectHash(makeProject([makeScene()]))))
})

describe('SceneGraph', () => {
  it('renders empty state', () => { render(<SceneGraph scenes={[]} onSelect={() => {}} />); expect(screen.getByText('No scenes in project')).toBeDefined() })
  it('renders kind badges', () => {
    render(<SceneGraph scenes={[makeScene({ id: 's0', kind: SceneKind.TITLE }), makeScene({ id: 's1', kind: SceneKind.CODE })]} onSelect={() => {}} />)
    expect(screen.getByText('Title')).toBeDefined(); expect(screen.getByText('Code')).toBeDefined()
  })
  it('renders engine badges', () => {
    render(<SceneGraph scenes={[makeScene({ id: 's0' }), makeScene({ id: 's1' })]} onSelect={() => {}} />)
    expect(screen.getAllByText('Remotion').length).toBe(2)
  })
  it('renders scene numbers', () => {
    render(<SceneGraph scenes={[makeScene({ id: 's0' }), makeScene({ id: 's1' })]} onSelect={() => {}} />)
    expect(screen.getByText('1')).toBeDefined(); expect(screen.getByText('2')).toBeDefined()
  })
  it('calls onSelect on click', () => {
    const onSelect = vi.fn(); render(<SceneGraph scenes={[makeScene({ id: 'clickable' })]} onSelect={onSelect} />)
    fireEvent.click(screen.getByRole('listitem')); expect(onSelect).toHaveBeenCalledWith(expect.objectContaining({ id: 'clickable' }))
  })
  it('highlights selected', () => {
    const { container } = render(<SceneGraph scenes={[makeScene({ id: 'a' }), makeScene({ id: 'b' })]} selectedId="a" onSelect={() => {}} />)
    const items = container.querySelectorAll('[role="listitem"]')
    expect(items[0].className).toContain('border-primary'); expect(items[1].className).not.toContain('border-primary')
  })
  it('renders showcase kind badges', () => {
    render(<SceneGraph scenes={[makeScene({ id: 's0', kind: SceneKind.SHOWCASE }), makeScene({ id: 's1', kind: SceneKind.SPLIT }), makeScene({ id: 's2', kind: SceneKind.MOCKUP }), makeScene({ id: 's3', kind: SceneKind.HERO })]} onSelect={() => {}} />)
    expect(screen.getByText('Showcase')).toBeDefined()
    expect(screen.getByText('Split')).toBeDefined()
    expect(screen.getByText('Mockup')).toBeDefined()
    expect(screen.getByText('Hero')).toBeDefined()
  })
})

describe('SceneDetail', () => {
  it('renders empty state', () => { render(<SceneDetail scene={null} />); expect(screen.getByText('Select a scene from the graph to view details')).toBeDefined() })
  it('renders scene id and kind', () => { render(<SceneDetail scene={makeScene({ id: 'my_scene', kind: SceneKind.CODE })} />); expect(screen.getByText('my_scene')).toBeDefined() })
  it('renders engine badge in header and routing section', () => {
    render(<SceneDetail scene={makeScene({ kind: SceneKind.CHART })} />)
    const badges = screen.getAllByText('Manim')
    expect(badges.length).toBeGreaterThanOrEqual(2)
  })
  it('renders narration', () => { render(<SceneDetail scene={makeScene({ narration: { text: 'Hello world', words: [], source: 'estimated' } })} />); expect(screen.getByText('Hello world')).toBeDefined() })
  it('renders frame placeholder', () => { render(<SceneDetail scene={makeScene()} />); expect(screen.getByText('Frame thumbnail')).toBeDefined(); expect(screen.getByText('No image endpoint available yet')).toBeDefined() })
  it('renders report placeholder', () => { render(<SceneDetail scene={makeScene()} />); expect(screen.getByText('Report not yet generated')).toBeDefined() })
  it('toggles payload JSON', () => {
    render(<SceneDetail scene={makeScene({ payload: JSON.stringify({ title: 'Test' }) })} />)
    expect(screen.queryByText(/Test/)).toBeNull()
    fireEvent.click(screen.getByText(/Payload JSON/))
    expect(screen.getByText(/Test/)).toBeDefined()
  })
  it('renders copy hash button', () => { render(<SceneDetail scene={{ ...makeScene(), contentHash: 'aabbccdd11223344' }} />); expect(screen.getByLabelText('Copy hash')).toBeDefined() })
  it('shows load report button when jobId provided', () => { render(<SceneDetail scene={makeScene()} jobId="job_001" />); expect(screen.getByText('Load Report')).toBeDefined() })
  it('hides no-image text when jobId provided', () => { render(<SceneDetail scene={makeScene()} jobId="job_001" />); expect(screen.queryByText('No image endpoint available yet')).toBeNull() })
  it('shows no-image text when jobId absent', () => { render(<SceneDetail scene={makeScene()} />); expect(screen.getByText('No image endpoint available yet')).toBeDefined() })
  it('loads and displays report on button click', async () => {
    const fakeReport = { artifact: 'videoforge-scene-report', engine: 'remotion' }
    globalThis.fetch = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve(fakeReport) })
    render(<SceneDetail scene={makeScene()} jobId="job_001" />)
    fireEvent.click(screen.getByText('Load Report'))
    await screen.findByText(/"engine": "remotion"/)
  })
  it('shows report fallback when fetch fails', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({ ok: false })
    render(<SceneDetail scene={makeScene()} jobId="job_001" />)
    fireEvent.click(screen.getByText('Load Report'))
    await screen.findByText('Report not yet generated')
  })

  /* ─── New: Overlay stack ─── */
  it('renders overlay stack section with layers', () => {
    const overlayScene = makeScene({
      overlay_stack: {
        items: [
          { id: 'ol_0', type: 'text', content: 'Title Overlay', position: { x: 100, y: 200 }, startFrame: 10, durationFrames: 60, opacity: 0.9, animation: 'fade_in' },
          { id: 'ol_1', type: 'logo', content: '/logo.png', position: { x: 800, y: 50 }, startFrame: 0, durationFrames: 120, opacity: 0.5 },
        ],
      },
    })
    render(<SceneDetail scene={overlayScene} />)
    expect(screen.getByText(/Overlay Stack/)).toBeInTheDocument()
    expect(screen.getByText(/2 layers/)).toBeInTheDocument()
    fireEvent.click(screen.getByText(/Overlay Stack/))
    expect(screen.getByText('Title Overlay')).toBeInTheDocument()
    expect(screen.getByText('text')).toBeInTheDocument()
    expect(screen.getByText('logo')).toBeInTheDocument()
    expect(screen.getByText(/fade_in/)).toBeInTheDocument()
  })

  it('shows overlay item position and frame info', () => {
    const scene = makeScene({
      overlay_stack: {
        items: [
          { id: 'ol_pos', type: 'shape', content: 'Box', position: { x: 50, y: 100 }, startFrame: 5, durationFrames: 30, opacity: 1.0 },
        ],
      },
    })
    render(<SceneDetail scene={scene} />)
    fireEvent.click(screen.getByText(/Overlay Stack/))
    expect(screen.getByText(/pos \(50,100\)/)).toBeInTheDocument()
    expect(screen.getByText(/frame 5–35/)).toBeInTheDocument()
    expect(screen.getByText(/opacity 100%/)).toBeInTheDocument()
  })

  /* ─── New: Motion hints ─── */
  it('renders motion hints section', () => {
    const scene = makeScene({
      motion_hints: [
        { type: 'entrance', animation: 'slide_up', durationMs: 500, easing: 'ease-out' },
        { type: 'emphasis', animation: 'pulse', durationMs: 2000 },
      ],
    })
    render(<SceneDetail scene={scene} />)
    expect(screen.getByText(/Motion Hints/)).toBeInTheDocument()
    expect(screen.getByText(/2/)).toBeInTheDocument()
    fireEvent.click(screen.getByText(/Motion Hints/))
    expect(screen.getByText('entrance')).toBeInTheDocument()
    expect(screen.getByText('emphasis')).toBeInTheDocument()
    expect(screen.getByText(/slide_up/)).toBeInTheDocument()
    expect(screen.getByText(/pulse/)).toBeInTheDocument()
  })

  it('shows motion hint timing details', () => {
    const scene = makeScene({
      motion_hints: [
        { type: 'entrance', animation: 'zoom_in', durationMs: 800, delayMs: 200, easing: 'cubic-bezier(0.16, 1, 0.3, 1)' },
      ],
    })
    render(<SceneDetail scene={scene} />)
    fireEvent.click(screen.getByText(/Motion Hints/))
    expect(screen.getByText(/800ms/)).toBeInTheDocument()
    expect(screen.getByText(/200ms delay/)).toBeInTheDocument()
    expect(screen.getByText(/cubic-bezier/)).toBeInTheDocument()
  })

  /* ─── New: Artifact placeholder states ─── */
  it('renders generating artifact state', () => {
    const scene = makeScene({
      artifacts: { thumbnail: { state: 'generating' }, frame: { state: 'pending' }, report: { state: 'missing' } },
    })
    render(<SceneDetail scene={scene} jobId="job_001" />)
    expect(screen.getByText('Generating frame...')).toBeInTheDocument()
    expect(screen.getByText('Render in progress')).toBeInTheDocument()
  })

  it('renders error artifact state with message', () => {
    const scene = makeScene({
      artifacts: { thumbnail: { state: 'error', errorMessage: 'Render timeout' } },
    })
    render(<SceneDetail scene={scene} jobId="job_001" />)
    expect(screen.getByText('Frame generation failed')).toBeInTheDocument()
    expect(screen.getByText('Render timeout')).toBeInTheDocument()
  })

  it('renders ready artifact state shows image', () => {
    const scene = makeScene({
      artifacts: { thumbnail: { state: 'ready' } },
    })
    render(<SceneDetail scene={scene} jobId="job_001" />)
    const imgs = screen.getAllByRole('img')
    expect(imgs.length).toBeGreaterThanOrEqual(1)
  })
})

describe('DirectorPreview', () => {
  it('renders project title', () => { render(<DirectorPreview project={makeProject([makeScene()])} />); expect(screen.getByText('Test Project')).toBeDefined() })
  it('renders scene count', () => { render(<DirectorPreview project={makeProject([makeScene({ id: 'a' }), makeScene({ id: 'b' }), makeScene({ id: 'c' })])} />); expect(screen.getByText('3 scenes')).toBeDefined() })
  it('renders panel headers', () => { render(<DirectorPreview project={makeProject([makeScene()])} />); expect(screen.getByText('Scene Graph')).toBeDefined(); expect(screen.getByText('Scene Detail')).toBeDefined() })
  it('renders duration', () => { render(<DirectorPreview project={makeProject([makeScene({ duration_frames: 90 }), makeScene({ duration_frames: 150 })])} />); expect(screen.getByText(/240f/)).toBeDefined() })
  it('renders resolution', () => { render(<DirectorPreview project={makeProject([makeScene()])} />); expect(screen.getByText(/1920×1080/)).toBeDefined() })
  it('renders content hash', () => {
    const { container } = render(<DirectorPreview project={makeProject([makeScene()])} />)
    const hashEl = Array.from(container.querySelectorAll('code')).find(el => el.textContent?.startsWith('#'))
    expect(hashEl).toBeDefined(); expect(hashEl!.textContent!).toMatch(/^#[0-9a-f]{16}$/)
  })
  it('selects first scene by default', () => {
    const { container } = render(<DirectorPreview project={makeProject([makeScene({ id: 'first_scene' }), makeScene({ id: 'second_scene' })])} />)
    expect(Array.from(container.querySelectorAll('h3')).find(h => h.textContent?.startsWith('first_scene'))).toBeDefined()
  })
  it('switches scene on click', () => {
    const { container } = render(<DirectorPreview project={makeProject([makeScene({ id: 'scene_a' }), makeScene({ id: 'scene_b' })])} />)
    fireEvent.click(container.querySelectorAll('[role="listitem"]')[1])
    expect(Array.from(container.querySelectorAll('h3')).find(h => h.textContent?.startsWith('scene_b'))).toBeDefined()
  })
  it('renders showcase kind scenes', () => {
    render(<DirectorPreview project={makeProject([makeScene({ id: 'show', kind: SceneKind.SHOWCASE }), makeScene({ id: 'spl', kind: SceneKind.SPLIT }), makeScene({ id: 'mck', kind: SceneKind.MOCKUP }), makeScene({ id: 'hr', kind: SceneKind.HERO })])} />)
    expect(screen.getByText('Showcase')).toBeDefined()
    expect(screen.getByText('Split')).toBeDefined()
    expect(screen.getByText('Mockup')).toBeDefined()
    expect(screen.getByText('Hero')).toBeDefined()
  })
  it('routes showcase kinds to remotion by default', () => {
    render(<DirectorPreview project={makeProject([makeScene({ kind: SceneKind.SHOWCASE }), makeScene({ kind: SceneKind.SPLIT }), makeScene({ kind: SceneKind.MOCKUP }), makeScene({ kind: SceneKind.HERO })])} />)
    const remotionLabels = screen.getAllByText('Remotion')
    expect(remotionLabels.length).toBeGreaterThanOrEqual(4)
  })
})
