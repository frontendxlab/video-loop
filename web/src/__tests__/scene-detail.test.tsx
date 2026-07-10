import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { SceneDetail } from '@/components/scene-detail'
import { Engine, SceneKind, type SceneNode } from '@/lib/ir-types'

function makeScene(overrides: Partial<SceneNode> = {}): SceneNode {
  return {
    id: 'scene_test',
    kind: SceneKind.CODE,
    payload: '{"code":"test"}',
    engine_hint: Engine.REMOTION,
    duration_frames: 150,
    narration: { text: 'Hello world', words: [], source: 'estimated' },
    contentHash: 'abc123def456',
    ...overrides,
  }
}

describe('SceneDetail', () => {
  it('renders placeholder when no scene', () => {
    render(<SceneDetail scene={null} />)
    expect(screen.getByText('Select a scene from the graph to view details')).toBeInTheDocument()
  })

  it('renders scene id and kind', () => {
    render(<SceneDetail scene={makeScene()} />)
    expect(screen.getByText('scene_test')).toBeInTheDocument()
    expect(screen.getByText(/^code/)).toBeInTheDocument()
  })

  it('renders content hash', () => {
    render(<SceneDetail scene={makeScene()} />)
    expect(screen.getByText('abc123def456')).toBeInTheDocument()
  })

  it('renders copy hash button', () => {
    render(<SceneDetail scene={makeScene()} />)
    expect(screen.getByLabelText('Copy hash')).toBeInTheDocument()
  })

  it('renders engine routing info', () => {
    render(<SceneDetail scene={makeScene()} />)
    expect(screen.getAllByText(/Remotion/).length).toBeGreaterThanOrEqual(1)
  })

  it('renders narration text', () => {
    render(<SceneDetail scene={makeScene()} />)
    expect(screen.getByText('Hello world')).toBeInTheDocument()
  })

  it('renders payload toggle', () => {
    render(<SceneDetail scene={makeScene()} />)
    expect(screen.getByText(/Payload JSON/)).toBeInTheDocument()
  })

  describe('action buttons without jobId', () => {
    it('renders stop button disabled', () => {
      render(<SceneDetail scene={makeScene()} />)
      const btn = screen.getByText('Stop')
      expect(btn).toBeDisabled()
    })

    it('renders retry button disabled', () => {
      render(<SceneDetail scene={makeScene()} />)
      const btn = screen.getByText('Retry')
      expect(btn).toBeDisabled()
    })

    it('renders reroute button disabled', () => {
      render(<SceneDetail scene={makeScene()} />)
      const btn = screen.getByText('Reroute')
      expect(btn).toBeDisabled()
    })
  })

  describe('action buttons with jobId', () => {
    it('renders stop button enabled', () => {
      render(<SceneDetail scene={makeScene()} jobId="job_001" />)
      const btn = screen.getByText('Stop')
      expect(btn).not.toBeDisabled()
    })

    it('renders retry button enabled', () => {
      render(<SceneDetail scene={makeScene()} jobId="job_001" />)
      const btn = screen.getByText('Retry')
      expect(btn).not.toBeDisabled()
    })

    it('renders reroute button enabled', () => {
      render(<SceneDetail scene={makeScene()} jobId="job_001" />)
      const btn = screen.getByText('Reroute')
      expect(btn).not.toBeDisabled()
    })
  })

  describe('overlay stack', () => {
    it('renders overlay stack toggle with layer count', () => {
      render(<SceneDetail scene={makeScene({ overlay_stack: { items: [{ id: 'ol1', type: 'text', content: 'Hi', position: { x: 0, y: 0 }, startFrame: 0, durationFrames: 30, opacity: 1 }] } })} />)
      expect(screen.getByText(/Overlay Stack/)).toBeInTheDocument()
      expect(screen.getByText(/1 layer/)).toBeInTheDocument()
    })

    it('expands to show overlay items on click', () => {
      render(<SceneDetail scene={makeScene({ overlay_stack: { items: [{ id: 'ol1', type: 'text', content: 'Hello Overlay', position: { x: 10, y: 20 }, startFrame: 5, durationFrames: 60, opacity: 0.8, animation: 'fade_in' }] } })} />)
      fireEvent.click(screen.getByText(/Overlay Stack/))
      expect(screen.getByText('Hello Overlay')).toBeInTheDocument()
      expect(screen.getByText('text')).toBeInTheDocument()
      expect(screen.getByText(/fade_in/)).toBeInTheDocument()
      expect(screen.getByText(/pos \(10,20\)/)).toBeInTheDocument()
      expect(screen.getByText(/frame 5–65/)).toBeInTheDocument()
      expect(screen.getByText(/opacity 80%/)).toBeInTheDocument()
    })

    it('does not render section when no overlay stack', () => {
      render(<SceneDetail scene={makeScene()} />)
      expect(screen.queryByText(/Overlay Stack/)).not.toBeInTheDocument()
    })
  })

  describe('motion hints', () => {
    it('renders motion hints toggle with count', () => {
      render(<SceneDetail scene={makeScene({ motion_hints: [{ type: 'entrance', animation: 'slide_up', durationMs: 500 }] })} />)
      expect(screen.getByText(/Motion Hints/)).toBeInTheDocument()
    })

    it('expands to show hints on click', () => {
      render(<SceneDetail scene={makeScene({ motion_hints: [{ type: 'exit', animation: 'fade_out', durationMs: 300, delayMs: 100, easing: 'ease-in' }] })} />)
      fireEvent.click(screen.getByText(/Motion Hints/))
      expect(screen.getByText('exit')).toBeInTheDocument()
      expect(screen.getByText(/fade_out/)).toBeInTheDocument()
      expect(screen.getByText(/300ms/)).toBeInTheDocument()
      expect(screen.getByText(/100ms delay/)).toBeInTheDocument()
      expect(screen.getByText(/ease-in/)).toBeInTheDocument()
    })

    it('does not render section when no motion hints', () => {
      render(<SceneDetail scene={makeScene()} />)
      expect(screen.queryByText(/Motion Hints/)).not.toBeInTheDocument()
    })
  })

  describe('artifact placeholders', () => {
    it('shows generating state with spinner', () => {
      render(<SceneDetail scene={makeScene({ artifacts: { thumbnail: { state: 'generating' }, frame: { state: 'pending' }, report: { state: 'missing' } } })} jobId="job_001" />)
      expect(screen.getByText('Generating frame...')).toBeInTheDocument()
      expect(screen.getByText('Render in progress')).toBeInTheDocument()
    })

    it('shows error state with message', () => {
      render(<SceneDetail scene={makeScene({ artifacts: { thumbnail: { state: 'error', errorMessage: 'Timeout' } } })} jobId="job_001" />)
      expect(screen.getByText('Frame generation failed')).toBeInTheDocument()
      expect(screen.getByText('Timeout')).toBeInTheDocument()
    })

    it('shows missing state when no jobId', () => {
      render(<SceneDetail scene={makeScene({ artifacts: { thumbnail: { state: 'missing' } } })} />)
      expect(screen.getByText('Frame thumbnail')).toBeInTheDocument()
      expect(screen.getByText('No image endpoint available yet')).toBeInTheDocument()
    })

    it('shows waiting state when jobId but artifact pending', () => {
      render(<SceneDetail scene={makeScene({ artifacts: { thumbnail: { state: 'pending' } } })} jobId="job_001" />)
      expect(screen.getByText('Frame thumbnail')).toBeInTheDocument()
      expect(screen.getByText('Waiting for render')).toBeInTheDocument()
    })
  })
})
