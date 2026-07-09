import { describe, it, expect } from 'vitest'
import { getJobs, getJob, resetMock } from '@/data/mock'

describe('mock data', () => {
  it('returns list of jobs', () => {
    const jobs = getJobs()
    expect(jobs.length).toBeGreaterThanOrEqual(4)
  })

  it('finds job by id', () => {
    const job = getJob('job_001')
    expect(job).toBeDefined()
    expect(job!.title).toContain('PR #142')
  })

  it('returns undefined for unknown job', () => {
    expect(getJob('nonexistent')).toBeUndefined()
  })

  it('has job with varied statuses', () => {
    const jobs = getJobs()
    const statuses = new Set(jobs.map((j) => j.status))
    expect(statuses.has('running')).toBe(true)
    expect(statuses.has('queued')).toBe(true)
    expect(statuses.has('completed')).toBe(true)
    expect(statuses.has('failed')).toBe(true)
  })

  it('running job has SSE events', () => {
    const job = getJob('job_001')
    expect(job!.events.length).toBeGreaterThan(0)
  })

  it('resetMock restores original data', () => {
    const original = getJobs().length
    resetMock()
    expect(getJobs().length).toBe(original)
  })
})
