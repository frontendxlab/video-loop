import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

/* Mock the job data to control job status */
vi.mock('@/data/mock', () => ({
  getJob: vi.fn((id: string) => {
    if (id === 'running_job') {
      return {
        id: 'running_job',
        title: 'Running Job',
        status: 'running',
        stage: 'render',
        progressPct: 45,
        createdAt: new Date().toISOString(),
        startedAt: new Date().toISOString(),
        completedAt: null,
        error: null,
        subagents: [],
        scenes: [],
        events: [],
      }
    }
    if (id === 'failed_job') {
      return {
        id: 'failed_job',
        title: 'Failed Job',
        status: 'failed',
        stage: 'render',
        progressPct: 78,
        createdAt: new Date().toISOString(),
        startedAt: new Date().toISOString(),
        completedAt: new Date().toISOString(),
        error: 'Render crashed',
        subagents: [],
        scenes: [],
        events: [],
      }
    }
    return undefined
  }),
  subscribeToJobEvents: vi.fn(() => () => {}),
}))

vi.mock('@/lib/api', () => ({
  stopJob: vi.fn(),
  retryJob: vi.fn(),
  retryScene: vi.fn(),
  rerouteScene: vi.fn(),
}))

vi.mock('@/hooks/useSSE', () => ({
  useSSE: vi.fn(() => ({ events: [], connected: false })),
}))

/* We test the components directly, not the route pages.
   The JobDetailPage is tested via its sub-components. */

import { SceneDetail } from '@/components/scene-detail'
import { Engine, SceneKind, type SceneNode } from '@/lib/ir-types'

function makeScene(overrides: Partial<SceneNode> = {}): SceneNode {
  return {
    id: 'scene_test',
    kind: SceneKind.CODE,
    payload: '{}',
    engine_hint: Engine.REMOTION,
    duration_frames: 150,
    narration: { text: '', words: [], source: 'estimated' },
    ...overrides,
  }
}

describe('SceneDetail with jobId — API wiring', () => {
  it('stop button calls stopJob on click', async () => {
    const { stopJob } = await import('@/lib/api')
    render(<SceneDetail scene={makeScene()} jobId="job_001" />)
    fireEvent.click(screen.getByText('Stop'))
    expect(stopJob).toHaveBeenCalledWith('job_001')
  })

  it('retry button calls retryScene on click', async () => {
    const { retryScene } = await import('@/lib/api')
    render(<SceneDetail scene={makeScene({ id: 'scene_42' })} jobId="job_001" />)
    fireEvent.click(screen.getByText('Retry'))
    expect(retryScene).toHaveBeenCalledWith('job_001', 'scene_42')
  })

  it('reroute button calls rerouteScene on click', async () => {
    const { rerouteScene } = await import('@/lib/api')
    render(<SceneDetail scene={makeScene({ id: 'scene_42' })} jobId="job_001" />)
    fireEvent.click(screen.getByText('Reroute'))
    expect(rerouteScene).toHaveBeenCalled()
    // Should pass jobId, sceneId, and an engine
    const args = (rerouteScene as ReturnType<typeof vi.fn>).mock.calls[0]
    expect(args[0]).toBe('job_001')
    expect(args[1]).toBe('scene_42')
  })
})
