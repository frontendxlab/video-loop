import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { SceneTable } from '@/components/job-detail/SceneTable'
import type { SceneInfo } from '@/types/job'

function makeScene(id: string, overrides: Partial<SceneInfo> = {}): SceneInfo {
  return { id, kind: 'title', engine: 'remotion', status: 'completed', reviewIssues: 0, retryCount: 0, ...overrides }
}

describe('SceneTable', () => {
  it('renders empty state', () => {
    const { container } = render(<SceneTable scenes={[]} jobId="job_001" />)
    expect(screen.getByText('No scenes yet')).toBeDefined()
  })

  it('renders scene rows', () => {
    render(<SceneTable scenes={[makeScene('s1'), makeScene('s2')]} jobId="job_001" />)
    expect(screen.getByText('s1')).toBeDefined()
    expect(screen.getByText('s2')).toBeDefined()
  })

  it('shows artifact panel on row click', () => {
    render(<SceneTable scenes={[makeScene('clickable_scene')]} jobId="job_001" />)
    fireEvent.click(screen.getByText('clickable_scene'))
    expect(screen.getByText(/Artifacts/)).toBeDefined()
  })

  it('hides artifact panel on second click', () => {
    render(<SceneTable scenes={[makeScene('toggle_scene')]} jobId="job_001" />)
    const cell = screen.getByText('toggle_scene')
    fireEvent.click(cell)
    expect(screen.getByText(/Artifacts/)).toBeDefined()
    fireEvent.click(cell)
    expect(screen.queryByText(/Artifacts/)).toBeNull()
  })

  it('renders multiple rows with status badges', () => {
    const scenes = [
      makeScene('s1', { status: 'completed' }),
      makeScene('s2', { status: 'failed' }),
      makeScene('s3', { status: 'rendering', kind: 'code', engine: 'remotion', reviewIssues: 2 }),
    ]
    render(<SceneTable scenes={scenes} jobId="job_001" />)
    expect(screen.getByText('completed')).toBeDefined()
    expect(screen.getByText('failed')).toBeDefined()
    expect(screen.getByText('rendering')).toBeDefined()
    expect(screen.getByText('2')).toBeDefined() // reviewIssues
  })
})
