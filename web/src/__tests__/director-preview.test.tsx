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
})
