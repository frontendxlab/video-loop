import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
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
    expect(screen.getByText('code')).toBeInTheDocument()
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
    expect(screen.getByText(/Remotion/)).toBeInTheDocument()
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
})
