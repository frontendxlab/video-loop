import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { StageTimeline } from '@/components/job-detail/StageTimeline'
import type { Job } from '@/types/job'

const baseJob: Job = {
  id: 'test', title: 'Test', status: 'running', stage: 'render', progressPct: 50,
  createdAt: new Date().toISOString(), startedAt: null, completedAt: null, error: null,
  subagents: [], scenes: [], events: [],
}

describe('StageTimeline', () => {
  it('marks stages before current as done', () => {
    render(<StageTimeline job={baseJob} />)
    expect(screen.getByText('Planning').className).toContain('emerald')
  })

  it('marks current stage as active', () => {
    render(<StageTimeline job={baseJob} />)
    expect(screen.getByText('Render').className).toContain('primary')
  })

  it('marks stages after current as pending', () => {
    render(<StageTimeline job={baseJob} />)
    expect(screen.getByText('Review').className).toContain('muted')
  })

  it('marks failed stage correctly', () => {
    const failed: Job = { ...baseJob, status: 'failed', stage: 'repair' }
    render(<StageTimeline job={failed} />)
    expect(screen.getByText('Repair').className).toContain('destructive')
  })

  it('marks all stages done for completed job', () => {
    const done: Job = { ...baseJob, status: 'completed', stage: 'done', progressPct: 100 }
    render(<StageTimeline job={done} />)
    const doneEl = screen.getByText('Done')
    expect(doneEl.className).toContain('emerald')
    expect(screen.getByText('Planning').className).toContain('emerald')
  })
})
