/**
 * Tests for director preview, scene graph, scene detail, and routing logic.
 */

import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Engine, SceneKind, computeSceneHash, computeProjectHash, type SceneNode, type VideoProject } from '~/lib/ir-types'
import { pickEngine, getRoutingReason } from '~/lib/director'
import { SceneGraph } from '~/components/scene-graph'
import { SceneDetail } from '~/components/scene-detail'
import { DirectorPreview } from '~/components/director-preview'

function makeScene(overrides: Partial<SceneNode> = {}): SceneNode {
  return {
    id: 'test_scene',
    kind: SceneKind.TITLE,
    payload: '{}',
    engine_hint: Engine.REMOTION,
    duration_frames: 90,
    narration: { text: 'Hello', words: [], source: 'estimated' },
    ...overrides,
  }
}

function makeProject(scenes: SceneNode[] = []): VideoProject {
  return {
    title: 'Test Project',
    fps: 30,
    width: 1920,
    height: 1080,
    audio_tracks: [],
    scenes,
  }
}

describe('pickEngine', () => {
  it('routes code to remotion', () => {
    expect(pickEngine(makeScene({ kind: SceneKind.CODE }))).toBe(Engine.REMOTION)
  })
  it('routes diff to remotion', () => {
    expect(pickEngine(makeScene({ kind: SceneKind.DIFF }))).toBe(Engine.REMOTION)
  })
  it('routes bullets to remotion', () => {
    expect(pickEngine(makeScene({ kind: SceneKind.BULLETS }))).toBe(Engine.REMOTION)
  })
  it('routes title to remotion', () => {
    expect(pickEngine(makeScene({ kind: SceneKind.TITLE }))).toBe(Engine.REMOTION)
  })
  it('routes comparison to remotion', () => {
    expect(pickEngine(makeScene({ kind: SceneKind.COMPARISON }))).toBe(Engine.REMOTION)
  })
  it('routes quote to remotion', () => {
    expect(pickEngine(makeScene({ kind: SceneKind.QUOTE }))).toBe(Engine.REMOTION)
  })
  it('routes outro to remotion', () => {
    expect(pickEngine(makeScene({ kind: SceneKind.OUTRO }))).toBe(Engine.REMOTION)
  })
  it('routes mindmap to remotion', () => {
    expect(pickEngine(makeScene({ kind: SceneKind.MINDMAP }))).toBe(Engine.REMOTION)
  })
  it('routes default diagram to remotion', () => {
    expect(pickEngine(makeScene({ kind: SceneKind.DIAGRAM, payload: JSON.stringify({ layout: 'default' }) }))).toBe(Engine.REMOTION)
  })
  it('routes math_graph diagram to manim', () => {
    expect(pickEngine(makeScene({ kind: SceneKind.DIAGRAM, payload: JSON.stringify({ layout: 'math_graph' }) }))).toBe(Engine.MANIM)
  })
  it('routes interactive diagram to animotion', () => {
    expect(pickEngine(makeScene({ kind: SceneKind.DIAGRAM, payload: JSON.stringify({ interactive: true }) }))).toBe(Engine.ANIMOTION)
  })
  it('routes non-interactive default diagram to remotion', () => {
    expect(pickEngine(makeScene({ kind: SceneKind.DIAGRAM, payload: JSON.stringify({ interactive: false }) }))).toBe(Engine.REMOTION)
  })
  it('routes diagram with no layout to remotion', () => {
    expect(pickEngine(makeScene({ kind: SceneKind.DIAGRAM, payload: JSON.stringify({}) }))).toBe(Engine.REMOTION)
  })
  it('routes chart to manim', () => {
    expect(pickEngine(makeScene({ kind: SceneKind.CHART }))).toBe(Engine.MANIM)
  })
  it('routes timeline to manim', () => {
    expect(pickEngine(makeScene({ kind: SceneKind.TIMELINE }))).toBe(Engine.MANIM)
  })
  it('routes map3d to manim', () => {
    expect(pickEngine(makeScene({ kind: SceneKind.MAP3D }))).toBe(Engine.MANIM)
  })
  it('is deterministic', () => {
    const n = makeScene({ kind: SceneKind.CHART })
    expect(pickEngine(n)).toBe(pickEngine(n))
  })
})

describe('getRoutingReason', () => {
  it('returns reason for code', () => {
    expect(getRoutingReason(makeScene({ kind: SceneKind.CODE }))).toContain('Shiki')
  })
  it('returns reason for math_graph diagram', () => {
    const r = getRoutingReason(makeScene({ kind: SceneKind.DIAGRAM, payload: JSON.stringify({ layout: 'math_graph' }) }))
    expect(r).toContain('graph')
  })
  it('returns reason for interactive diagram', () => {
    const r = getRoutingReason(makeScene({ kind: SceneKind.DIAGRAM, payload: JSON.stringify({ interactive: true }) }))
    expect(r).toContain('CSS')
  })
})

describe('computeSceneHash', () => {
  it('returns 16-char hex', () => {
    const h = computeSceneHash(makeScene())
    expect(h).toHaveLength(16)
    expect(/^[0-9a-f]+$/.test(h)).toBe(true)
  })
  it('is deterministic', () => {
    expect(computeSceneHash(makeScene())).toBe(computeSceneHash(makeScene()))
  })
  it('changes when kind changes', () => {
    const a = computeSceneHash(makeScene({ kind: SceneKind.TITLE }))
    const b = computeSceneHash(makeScene({ kind: SceneKind.CODE }))
    expect(a).not.toBe(b)
  })
  it('changes when payload changes', () => {
    const a = computeSceneHash(makeScene({ payload: '{"a":1}' }))
    const b = computeSceneHash(makeScene({ payload: '{"a":2}' }))
    expect(a).not.toBe(b)
  })
})

describe('computeProjectHash', () => {
  it('returns 16-char hex', () => {
    const h = computeProjectHash(makeProject([makeScene()]))
    expect(h).toHaveLength(16)
    expect(/^[0-9a-f]+$/.test(h)).toBe(true)
  })
  it('is deterministic', () => {
    expect(computeProjectHash(makeProject([makeScene()]))).toBe(computeProjectHash(makeProject([makeScene()])))
  })
  it('changes with different scenes', () => {
    const a = computeProjectHash(makeProject([makeScene({ kind: SceneKind.TITLE })]))
    const b = computeProjectHash(makeProject([makeScene({ kind: SceneKind.CODE })]))
    expect(a).not.toBe(b)
  })
})

describe('SceneGraph', () => {
  it('renders empty state', () => {
    render(<SceneGraph scenes={[]} onSelect={() => {}} />)
    expect(screen.getByText('No scenes in project')).toBeDefined()
  })
  it('renders kind badges', () => {
    render(<SceneGraph scenes={[makeScene({ id: 's0', kind: SceneKind.TITLE }), makeScene({ id: 's1', kind: SceneKind.CODE })]} onSelect={() => {}} />)
    expect(screen.getByText('Title')).toBeDefined()
    expect(screen.getByText('Code')).toBeDefined()
  })
  it('renders Remotion badge for each scene', () => {
    render(<SceneGraph scenes={[makeScene({ id: 's0' }), makeScene({ id: 's1' })]} onSelect={() => {}} />)
    expect(screen.getAllByText('Remotion').length).toBe(2)
  })
  it('renders scene numbers', () => {
    render(<SceneGraph scenes={[makeScene({ id: 's0' }), makeScene({ id: 's1' })]} onSelect={() => {}} />)
    expect(screen.getByText('1')).toBeDefined()
    expect(screen.getByText('2')).toBeDefined()
  })
  it('calls onSelect on click', () => {
    const onSelect = vi.fn()
    render(<SceneGraph scenes={[makeScene({ id: 'clickable' })]} onSelect={onSelect} />)
    fireEvent.click(screen.getByRole('listitem'))
    expect(onSelect).toHaveBeenCalledWith(expect.objectContaining({ id: 'clickable' }))
  })
  it('highlights selected scene', () => {
    const { container } = render(
      <SceneGraph scenes={[makeScene({ id: 'a' }), makeScene({ id: 'b' })]} selectedId="a" onSelect={() => {}} />
    )
    const items = container.querySelectorAll('[role="listitem"]')
    expect(items[0].className).toContain('border-primary')
    expect(items[1].className).not.toContain('border-primary')
  })
})

describe('SceneDetail', () => {
  it('renders empty state', () => {
    render(<SceneDetail scene={null} />)
    expect(screen.getByText('Select a scene from the graph to view details')).toBeDefined()
  })
  it('renders scene id and kind', () => {
    render(<SceneDetail scene={makeScene({ id: 'my_scene', kind: SceneKind.CODE })} />)
    expect(screen.getByText('my_scene')).toBeDefined()
    expect(screen.getByText(/code/)).toBeDefined()
  })
  it('renders engine badge', () => {
    render(<SceneDetail scene={makeScene({ kind: SceneKind.CHART })} />)
    expect(screen.getAllByText('Manim').length).toBe(1)
  })
  it('renders narration text', () => {
    render(<SceneDetail scene={makeScene({ narration: { text: 'Hello world', words: [], source: 'estimated' } })} />)
    expect(screen.getByText('Hello world')).toBeDefined()
  })
  it('renders frame placeholder', () => {
    render(<SceneDetail scene={makeScene()} />)
    expect(screen.getByText('Frame thumbnail')).toBeDefined()
    expect(screen.getByText('No image endpoint available yet')).toBeDefined()
  })
  it('renders report placeholder', () => {
    render(<SceneDetail scene={makeScene()} />)
    expect(screen.getByText('Report not yet generated')).toBeDefined()
  })
  it('toggles payload JSON', () => {
    render(<SceneDetail scene={makeScene({ payload: JSON.stringify({ title: 'Test' }) })} />)
    expect(screen.queryByText('"Test"')).toBeNull()
    fireEvent.click(screen.getByText(/Payload JSON/))
    expect(screen.getByText('"Test"')).toBeDefined()
  })
  it('renders copy hash button', () => {
    render(<SceneDetail scene={{ ...makeScene(), contentHash: 'aabbccdd11223344' }} />)
    expect(screen.getByLabelText('Copy hash')).toBeDefined()
  })
})

describe('DirectorPreview', () => {
  it('renders project title', () => {
    render(<DirectorPreview project={makeProject([makeScene()])} />)
    expect(screen.getByText('Test Project')).toBeDefined()
  })
  it('renders scene count', () => {
    render(<DirectorPreview project={makeProject([makeScene({ id: 'a' }), makeScene({ id: 'b' }), makeScene({ id: 'c' })])} />)
    expect(screen.getByText('3 scenes')).toBeDefined()
  })
  it('renders panel headers', () => {
    render(<DirectorPreview project={makeProject([makeScene()])} />)
    expect(screen.getByText('Scene Graph')).toBeDefined()
    expect(screen.getByText('Scene Detail')).toBeDefined()
  })
  it('renders duration info', () => {
    render(<DirectorPreview project={makeProject([makeScene({ duration_frames: 90 }), makeScene({ duration_frames: 150 })])} />)
    expect(screen.getByText(/240f/)).toBeDefined()
    expect(screen.getByText(/8s/)).toBeDefined()
  })
  it('renders resolution', () => {
    render(<DirectorPreview project={makeProject([makeScene()])} />)
    expect(screen.getByText(/1920×1080/)).toBeDefined()
  })
  it('renders content hash', () => {
    const { container } = render(<DirectorPreview project={makeProject([makeScene()])} />)
    const codeEls = container.querySelectorAll('code')
    const hashEl = Array.from(codeEls).find(el => el.textContent?.startsWith('#'))
    expect(hashEl).toBeDefined()
    expect(hashEl!.textContent!).toMatch(/^#[0-9a-f]{16}$/)
  })
  it('selects first scene by default', () => {
    const { container } = render(
      <DirectorPreview project={makeProject([makeScene({ id: 'first_scene' }), makeScene({ id: 'second_scene' })])} />
    )
    const h3s = container.querySelectorAll('h3')
    const firstH3 = Array.from(h3s).find(h => h.textContent?.startsWith('first_scene'))
    expect(firstH3).toBeDefined()
  })
  it('switches selected scene on click', () => {
    const { container } = render(
      <DirectorPreview project={makeProject([makeScene({ id: 'scene_a' }), makeScene({ id: 'scene_b' })])} />
    )
    const items = container.querySelectorAll('[role="listitem"]')
    fireEvent.click(items[1])
    const h3s = container.querySelectorAll('h3')
    const secondH3 = Array.from(h3s).find(h => h.textContent?.startsWith('scene_b'))
    expect(secondH3).toBeDefined()
  })
})
