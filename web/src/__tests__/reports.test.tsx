import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ReportSummaryTab } from '@/components/reports/ReportSummary'
import { ReportProvenanceTab } from '@/components/reports/ReportProvenance'
import { ReportScenesTab } from '@/components/reports/ReportScenes'
import type { VideoReport, ProvenanceGraph, SceneReport } from '@/types/report'

const baseReport: VideoReport = {
  artifact: 'videoforge-video-report',
  version: 1,
  video_path: '/builds/test.mp4',
  report_timestamp: '2026-07-09T17:00:00.000Z',
  content_hash: 'abc123def456',
  engine_mix: ['remotion', 'manim'],
  render_format: { fps: 30, width: 1920, height: 1080, pixel_format: 'yuv420p', video_codec: 'h264', audio_codec: 'aac' },
  scenes_summary: {
    count: 2,
    engines: { remotion: 1, manim: 1 },
    total_duration_frames: 300,
    scenes: [
      { index: 0, engine: 'remotion', duration_frames: 180 },
      { index: 1, engine: 'manim', duration_frames: 120 },
    ],
  },
  l0_summary: {
    status: 'pass', passed: true, total_issues: 0,
    severity_counts: { high: 0, medium: 0, low: 0 },
    sampled_frames: 10, total_frames: 300, duration_seconds: 10.0,
    issues: [],
  },
  l1_summary: { passed: true, total_frames: 300, total_issues: 0, issues: [] },
  l2_layout_overlap_summary: {
    status: 'pass', passed: true, total_issues: 0,
    severity_counts: { high: 0, medium: 0, low: 0 },
    issues: [],
  },
  policy_verdict: 'pass',
}

const baseProvenance: ProvenanceGraph = {
  artifact: 'videoforge-provenance-graph',
  version: 1,
  video_path: '/builds/test.mp4',
  report_timestamp: '2026-07-09T17:00:00.000Z',
  content_hash: 'abc123def456',
  engines: ['manim', 'remotion'],
  scenes: [
    { id: 'scene_0000', engine: 'remotion', kind: 'title', content_hash: 'h1', scene_path: '/s0.mp4', scene_report_path: '/s0.report.json', duration_frames: 180, assets: { audio_src: 'voice.wav' } },
    { id: 'scene_0001', engine: 'manim', kind: 'diagram', content_hash: 'h2', scene_path: '/s1.mp4', scene_report_path: '/s1.report.json', duration_frames: 120, assets: {} },
  ],
  reports: {
    video_report: '/builds/test.mp4.report.json',
    provenance_graph: '/builds/test.provenance.json',
  },
}

const baseScenes: SceneReport[] = [
  { artifact: 'videoforge-scene-report', version: 1, scene_index: 0, engine: 'remotion', duration_frames: 180, scene_path: '/s0.mp4', report_timestamp: 'ts', content_hash: 'h1', render_format: { fps: 30, width: 1920, height: 1080, pixel_format: 'yuv420p', video_codec: 'h264', audio_codec: 'aac' } },
  { artifact: 'videoforge-scene-report', version: 1, scene_index: 1, engine: 'manim', duration_frames: 120, scene_path: '/s1.mp4', report_timestamp: 'ts', content_hash: 'h2', render_format: { fps: 30, width: 1920, height: 1080, pixel_format: 'yuv420p', video_codec: 'h264', audio_codec: 'aac' } },
]

describe('ReportSummaryTab', () => {
  it('renders render format', () => {
    render(<ReportSummaryTab report={baseReport} />)
    expect(screen.getByText('1920×1080')).toBeDefined()
    expect(screen.getByText('30')).toBeDefined()
    expect(screen.getByText('h264')).toBeDefined()
  })

  it('renders scene count and duration', () => {
    render(<ReportSummaryTab report={baseReport} />)
    expect(screen.getByText('Count')).toBeDefined()
    expect(screen.getByText('Duration')).toBeDefined()
    // 10.0s appears in scenes summary and L0 duration — use getAllByText
    expect(screen.getAllByText('10.0s').length).toBeGreaterThanOrEqual(1)
  })

  it('renders scene table with engine badge', () => {
    render(<ReportSummaryTab report={baseReport} />)
    expect(screen.getByText('Frames')).toBeDefined()
    expect(screen.getByText('remotion')).toBeDefined()
    expect(screen.getByText('manim')).toBeDefined()
  })

  it('renders L0 status heading', () => {
    render(<ReportSummaryTab report={baseReport} />)
    expect(screen.getByText('L0 — Mixed Engine Review')).toBeDefined()
  })

  it('renders L1 integrity section', () => {
    render(<ReportSummaryTab report={baseReport} />)
    expect(screen.getByText('L1 — Frame Integrity')).toBeDefined()
  })

  it('renders L2 layout overlap section', () => {
    render(<ReportSummaryTab report={baseReport} />)
    expect(screen.getByText('L2b — Layout Overlap')).toBeDefined()
  })

  it('renders policy verdict', () => {
    render(<ReportSummaryTab report={baseReport} />)
    expect(screen.getByText('Policy Verdict:')).toBeDefined()
    const passElements = screen.getAllByText('pass')
    expect(passElements.length).toBeGreaterThanOrEqual(1)
  })

  it('shows L0 issues list', () => {
    const reportWithIssues: VideoReport = {
      ...baseReport,
      l0_summary: {
        ...baseReport.l0_summary,
        total_issues: 2, passed: false, status: 'fail',
        severity_counts: { high: 1, medium: 1, low: 0 },
        issues: [
          { type: 'blank_frame', severity: 'high', detail: 'Frame 0 blank', frame_index: 0 },
          { type: 'palette_drift', severity: 'medium', detail: 'Color shift', frame_index: 5 },
        ],
      },
    }
    render(<ReportSummaryTab report={reportWithIssues} />)
    expect(screen.getByText('blank_frame: Frame 0 blank')).toBeDefined()
    expect(screen.getByText('palette_drift: Color shift')).toBeDefined()
  })

  it('shows coherence summary when present', () => {
    const report = {
      ...baseReport,
      coherence_summary: {
        coherent: true, total_issues: 0, issues: [],
        has_complete_arc: true, missing_phases: [], duplicate_phases: [], phase_order_valid: true,
      },
    }
    render(<ReportSummaryTab report={report} />)
    expect(screen.getByText('Coherence')).toBeDefined()
    expect(screen.getByText('Coherent')).toBeDefined()
  })

  it('shows L1 issues', () => {
    const report: VideoReport = {
      ...baseReport,
      l1_summary: { passed: false, total_frames: 300, total_issues: 1, issues: [{ type: 'black_frame', start: 0, end: 5 }] },
    }
    render(<ReportSummaryTab report={report} />)
    expect(screen.getByText(/black_frame/)).toBeDefined()
  })
})

describe('ReportProvenanceTab', () => {
  it('renders provenance overview heading', () => {
    render(<ReportProvenanceTab provenance={baseProvenance} />)
    expect(screen.getByText('Provenance Overview')).toBeDefined()
  })

  it('renders engine badge badges', () => {
    render(<ReportProvenanceTab provenance={baseProvenance} />)
    const engines = screen.getAllByText(/remotion|manim/)
    expect(engines.length).toBeGreaterThanOrEqual(2)
  })

  it('renders scene lineage table', () => {
    render(<ReportProvenanceTab provenance={baseProvenance} />)
    expect(screen.getByText('scene_0000')).toBeDefined()
    expect(screen.getByText('scene_0001')).toBeDefined()
    expect(screen.getByText('title')).toBeDefined()
    expect(screen.getByText('diagram')).toBeDefined()
  })

  it('renders asset badges', () => {
    render(<ReportProvenanceTab provenance={baseProvenance} />)
    expect(screen.getByText('audio_src')).toBeDefined()
  })

  it('renders artifact paths section', () => {
    render(<ReportProvenanceTab provenance={baseProvenance} />)
    expect(screen.getByText('Artifact Paths')).toBeDefined()
    expect(screen.getByText('video_report:')).toBeDefined()
    expect(screen.getByText('provenance_graph:')).toBeDefined()
  })

  it('renders scene count label', () => {
    render(<ReportProvenanceTab provenance={baseProvenance} />)
    expect(screen.getByText('Scenes')).toBeDefined()
  })
})

describe('ReportScenesTab', () => {
  it('renders empty state', () => {
    render(<ReportScenesTab scenes={[]} />)
    expect(screen.getByText('No per-scene report artifacts found.')).toBeDefined()
  })

  it('renders scene rows', () => {
    render(<ReportScenesTab scenes={baseScenes} />)
    expect(screen.getAllByText(/remotion|manim/).length).toBeGreaterThanOrEqual(2)
  })

  it('renders engine breakdown section', () => {
    render(<ReportScenesTab scenes={baseScenes} />)
    expect(screen.getByText('Engine Breakdown')).toBeDefined()
  })

  it('renders duration in seconds', () => {
    render(<ReportScenesTab scenes={baseScenes} />)
    expect(screen.getByText('180f (6.0s)')).toBeDefined()
    expect(screen.getByText('120f (4.0s)')).toBeDefined()
  })

  it('renders format string', () => {
    render(<ReportScenesTab scenes={baseScenes} />)
    const formatTexts = screen.getAllByText(/1920×1080 @ 30fps/)
    expect(formatTexts.length).toBe(2)
  })

  it('renders scene count header', () => {
    render(<ReportScenesTab scenes={baseScenes} />)
    expect(screen.getByText('Per-Scene Reports (2)')).toBeDefined()
  })

  it('renders preview column header', () => {
    render(<ReportScenesTab scenes={baseScenes} />)
    expect(screen.getByText('Preview')).toBeDefined()
  })

  it('renders scene preview thumbnails from scene_path', () => {
    render(<ReportScenesTab scenes={baseScenes} />)
    const imgs = screen.getAllByRole('img')
    // Each scene with .mp4 path gets a thumbnail img
    imgs.forEach(img => {
      expect(img.getAttribute('src')).toMatch(/\.thumb\.jpg$/)
    })
  })

  it('does not render preview img when scene_path missing', () => {
    const noPathScenes = baseScenes.map(s => ({ ...s, scene_path: '' }))
    render(<ReportScenesTab scenes={noPathScenes} />)
    const imgs = screen.queryAllByRole('img')
    expect(imgs.length).toBe(0)
  })

  it('renders preview column in provenance scene lineage', () => {
    render(<ReportProvenanceTab provenance={baseProvenance} />)
    expect(screen.getByText('Preview')).toBeDefined()
  })

  it('renders scene preview thumbnails in provenance', () => {
    render(<ReportProvenanceTab provenance={baseProvenance} />)
    const imgs = screen.getAllByRole('img')
    expect(imgs.length).toBeGreaterThanOrEqual(2)
    imgs.forEach(img => {
      expect(img.getAttribute('src')).toMatch(/\.thumb\.jpg$/)
    })
  })
})
