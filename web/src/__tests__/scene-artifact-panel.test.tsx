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

  it('shows no thumbnail fallback when no artifact URLs', () => {
    render(<SceneArtifactPanel scene={makeScene()} jobId="job_001" onClose={onClose} />)
    expect(screen.getByText('No thumbnail')).toBeDefined()
  })

  it('shows no frame fallback when no artifact URLs', () => {
    render(<SceneArtifactPanel scene={makeScene()} jobId="job_001" onClose={onClose} />)
    expect(screen.getByText('No frame sample')).toBeDefined()
  })

  it('shows load report button when no reportUrl', () => {
    render(<SceneArtifactPanel scene={makeScene()} jobId="job_001" onClose={onClose} />)
    expect(screen.getByText('Load Report')).toBeDefined()
  })

  it('renders thumbnail img when thumbnailUrl provided', () => {
    render(<SceneArtifactPanel scene={makeScene({ thumbnailUrl: '/fake/thumb.jpg' })} jobId="job_001" onClose={onClose} />)
    const img = screen.getByAltText('scene_test thumbnail') as HTMLImageElement
    expect(img).toBeDefined()
    expect(img.src).toContain('/fake/thumb.jpg')
  })

  it('renders frame img when frameUrl provided', () => {
    render(<SceneArtifactPanel scene={makeScene({ frameUrl: '/fake/frame.png' })} jobId="job_001" onClose={onClose} />)
    const img = screen.getByAltText('scene_test frame') as HTMLImageElement
    expect(img).toBeDefined()
    expect(img.src).toContain('/fake/frame.png')
  })

  it('falls back to generated URLs when only jobId given', () => {
    /* With mocks returning undefined, both artifact URLs fail open */
    render(<SceneArtifactPanel scene={makeScene()} jobId="job_007" onClose={onClose} />)
    const imgs = screen.queryAllByRole('img')
    expect(imgs.length).toBe(0)
    expect(screen.getByText('No thumbnail')).toBeDefined()
    expect(screen.getByText('No frame sample')).toBeDefined()
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
