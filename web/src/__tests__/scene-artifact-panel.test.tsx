import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { SceneArtifactPanel } from '@/components/job-detail/SceneArtifactPanel'
import type { SceneInfo } from '@/types/job'

/* Mock artifact URL builders to control fallback behavior */
vi.mock('@/lib/api', async (importOriginal) => {
  const actual = await importOriginal()
  return {
    ...(actual as Record<string, unknown>),
    artifactThumbnailUrl: () => undefined,
    artifactFrameUrl: () => undefined,
    artifactReportUrl: () => '/api/artifacts/job_001/scenes/scene_test/report',
  }
})

function makeScene(overrides: Partial<SceneInfo> = {}): SceneInfo {
  return {
    id: 'scene_test',
    kind: 'title',
    engine: 'remotion',
    status: 'completed',
    reviewIssues: 0,
    retryCount: 0,
    ...overrides,
  }
}

describe('SceneArtifactPanel', () => {
  const onClose = vi.fn()

  beforeEach(() => {
    onClose.mockClear()
  })

  it('renders scene id', () => {
    render(<SceneArtifactPanel scene={makeScene()} jobId="job_001" onClose={onClose} />)
    expect(screen.getByText(/scene_test/)).toBeDefined()
  })

  it('renders kind badge', () => {
    render(<SceneArtifactPanel scene={makeScene({ kind: 'code' })} jobId="job_001" onClose={onClose} />)
    expect(screen.getByText('code')).toBeDefined()
  })

  it('shows generating state for rendering scene (no artifactState)', () => {
    render(<SceneArtifactPanel scene={makeScene({ status: 'rendering' })} jobId="job_001" onClose={onClose} />)
    // Two previews (thumbnail + frame) — use getAllByText
    expect(screen.getAllByText('Generating...').length).toBe(2)
    expect(screen.getAllByText('Render in progress').length).toBe(2)
  })

  it('shows generating state for pending scene (no artifactState)', () => {
    render(<SceneArtifactPanel scene={makeScene({ status: 'pending' })} jobId="job_001" onClose={onClose} />)
    expect(screen.getAllByText('Generating...').length).toBe(2)
  })

  it('shows artifact error for failed scene (no artifactState)', () => {
    render(<SceneArtifactPanel scene={makeScene({ status: 'failed' })} jobId="job_001" onClose={onClose} />)
    expect(screen.getAllByText('Artifact unavailable').length).toBe(2)
    expect(screen.getAllByText('Generation failed').length).toBe(2)
  })

  it('shows artifact error with custom message from artifactError', () => {
    render(<SceneArtifactPanel scene={makeScene({ status: 'failed', artifactState: 'error', artifactError: 'Render timeout after 30s' })} jobId="job_001" onClose={onClose} />)
    expect(screen.getAllByText('Artifact unavailable').length).toBe(2)
    expect(screen.getAllByText('Render timeout after 30s').length).toBe(2)
  })

  it('shows not-available state for completed scene without URLs', () => {
    render(<SceneArtifactPanel scene={makeScene({ status: 'completed' })} jobId="job_001" onClose={onClose} />)
    expect(screen.getAllByText('Not available yet').length).toBe(2)
  })

  it('renders thumbnail img when thumbnailUrl provided with artifactState ready', () => {
    render(<SceneArtifactPanel scene={makeScene({ thumbnailUrl: '/fake/thumb.jpg', artifactState: 'ready' })} jobId="job_001" onClose={onClose} />)
    const img = screen.getByAltText('scene_test Thumbnail') as HTMLImageElement
    expect(img).toBeDefined()
    expect(img.src).toContain('/fake/thumb.jpg')
  })

  it('renders frame img when frameUrl provided with artifactState ready', () => {
    render(<SceneArtifactPanel scene={makeScene({ frameUrl: '/fake/frame.png', artifactState: 'ready' })} jobId="job_001" onClose={onClose} />)
    const img = screen.getByAltText('scene_test Sampled Frame') as HTMLImageElement
    expect(img).toBeDefined()
    expect(img.src).toContain('/fake/frame.png')
  })

  it('shows thumbnail from URL even on failed scene with artifactState ready', () => {
    render(<SceneArtifactPanel scene={makeScene({ status: 'failed', thumbnailUrl: '/fake/thumb.jpg', artifactState: 'ready' })} jobId="job_001" onClose={onClose} />)
    const img = screen.getByAltText('scene_test Thumbnail') as HTMLImageElement
    expect(img).toBeDefined()
    expect(img.src).toContain('/fake/thumb.jpg')
  })

  it('calls onClose when close button clicked', () => {
    render(<SceneArtifactPanel scene={makeScene()} jobId="job_001" onClose={onClose} />)
    fireEvent.click(screen.getByText('✕'))
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('loads report on button click', async () => {
    const fakeReport = { artifact: 'videoforge-scene-report', engine: 'remotion', duration_frames: 180 }
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(fakeReport),
    })

    render(<SceneArtifactPanel scene={makeScene()} jobId="job_001" onClose={onClose} />)
    fireEvent.click(screen.getByText('Load Report'))

    await waitFor(() => {
      expect(screen.getByText(/"artifact": "videoforge-scene-report"/)).toBeDefined()
    })
  })

  it('shows report fallback when fetch fails', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({ ok: false })

    render(<SceneArtifactPanel scene={makeScene()} jobId="job_001" onClose={onClose} />)
    fireEvent.click(screen.getByText('Load Report'))

    await waitFor(() => {
      expect(screen.getByText('Report not yet generated')).toBeDefined()
    })
  })

  it('shows report fallback when fetch rejects', async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new Error('Network error'))

    render(<SceneArtifactPanel scene={makeScene()} jobId="job_001" onClose={onClose} />)
    fireEvent.click(screen.getByText('Load Report'))

    await waitFor(() => {
      expect(screen.getByText('Report not yet generated')).toBeDefined()
    })
  })
})
