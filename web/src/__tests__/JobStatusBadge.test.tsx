import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { JobStatusBadge } from '@/components/jobs/JobStatusBadge'

describe('JobStatusBadge', () => {
  it('renders Completed with success variant', () => {
    render(<JobStatusBadge status="completed" />)
    const badge = screen.getByText('Completed')
    expect(badge.className).toContain('emerald')
  })

  it('renders Failed with destructive variant', () => {
    render(<JobStatusBadge status="failed" />)
    const badge = screen.getByText('Failed')
    expect(badge.className).toContain('destructive')
  })

  it('renders Running with default variant', () => {
    render(<JobStatusBadge status="running" />)
    expect(screen.getByText('Running')).toBeTruthy()
  })

  it('renders Queued with secondary variant', () => {
    render(<JobStatusBadge status="queued" />)
    expect(screen.getByText('Queued')).toBeTruthy()
  })
})
