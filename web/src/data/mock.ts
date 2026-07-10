/* Mock data matching backend types + SSE contract.
   Swap for real API calls when backend endpoints exist. */

import type { Job } from '@/types/job'
import type { SSEEvent, SSEEventType } from '@/types/sse'

const now = () => new Date().toISOString()
const ago = (ms: number) => new Date(Date.now() - ms).toISOString()

function makeSSEEvent(jobId: string, type: SSEEventType, extra: Record<string, unknown> = {}): SSEEvent {
  return { type, data: { jobId, timestamp: now(), ...extra } as any }
}

const JOB_SEED: Job[] = [
  {
    id: 'job_001', title: 'PR #142 — Add auth middleware',
    status: 'running', stage: 'render', progressPct: 62,
    createdAt: ago(120_000), startedAt: ago(115_000), completedAt: null, error: null,
    subagents: [
      { id: 'sa_1', name: 'Scene Planner', engine: 'director', task: 'Plan scene graph', status: 'completed', startedAt: ago(110_000), completedAt: ago(105_000), durationMs: 5000, error: null, tokens: 340 },
      { id: 'sa_2', name: 'Code Highlighter', engine: 'remotion', task: 'Syntax highlight CodeScene', status: 'completed', startedAt: ago(100_000), completedAt: ago(92_000), durationMs: 8000, error: null, tokens: 0 },
      { id: 'sa_3', name: 'Diff Renderer', engine: 'remotion', task: 'Render diff scene #3', status: 'running', startedAt: ago(80_000), completedAt: null, durationMs: null, error: null, tokens: 520 },
      { id: 'sa_4', name: 'Review Gate L0', engine: 'review', task: 'Check mixed-engine coherence', status: 'pending', startedAt: null, completedAt: null, durationMs: null, error: null, tokens: 0 },
    ],
    scenes: [
      { id: 'scene_1', kind: 'title', engine: 'remotion', status: 'completed', reviewIssues: 0, retryCount: 0, thumbnailUrl: '/api/artifacts/job_001/scenes/scene_1/thumbnail', frameUrl: '/api/artifacts/job_001/scenes/scene_1/frame', reportUrl: '/api/artifacts/job_001/scenes/scene_1/report' },
      { id: 'scene_2', kind: 'code', engine: 'remotion', status: 'completed', reviewIssues: 0, retryCount: 0, thumbnailUrl: '/api/artifacts/job_001/scenes/scene_2/thumbnail', frameUrl: '/api/artifacts/job_001/scenes/scene_2/frame', reportUrl: '/api/artifacts/job_001/scenes/scene_2/report' },
      { id: 'scene_3', kind: 'diff', engine: 'remotion', status: 'rendering', reviewIssues: 1, retryCount: 0 },
      { id: 'scene_4', kind: 'bullets', engine: 'remotion', status: 'pending', reviewIssues: 0, retryCount: 0 },
    ],
    events: [
      makeSSEEvent('job_001', 'job.started', { title: 'PR #142 — Add auth middleware' }),
      makeSSEEvent('job_001', 'job.stage', { stage: 'plan', progressPct: 5, phase: 'plan' }),
      makeSSEEvent('job_001', 'director.scene_planned', { sceneId: 'scene_1', sceneKind: 'title' }),
      makeSSEEvent('job_001', 'director.scene_routed', { sceneId: 'scene_1', sceneKind: 'title', engine: 'remotion' }),
      makeSSEEvent('job_001', 'job.stage', { stage: 'render', progressPct: 45, phase: 'render' }),
      makeSSEEvent('job_001', 'render.scene_started', { sceneId: 'scene_3', sceneKind: 'diff' }),
      makeSSEEvent('job_001', 'subagent.started', { subagentId: 'sa_3', name: 'Diff Renderer', engine: 'remotion', task: 'Render diff scene #3' }),
    ],
  },
  {
    id: 'job_002', title: 'Issue #89 — Fix caption sync drift',
    status: 'queued', stage: 'plan', progressPct: 0,
    createdAt: ago(30_000), startedAt: null, completedAt: null, error: null,
    subagents: [], scenes: [], events: [],
  },
  {
    id: 'job_003', title: 'Release v0.5 — Demo video',
    status: 'completed', stage: 'done', progressPct: 100,
    createdAt: ago(600_000), startedAt: ago(590_000), completedAt: ago(300_000), error: null,
    subagents: [
      { id: 'sa_5', name: 'Scene Planner', engine: 'director', task: 'Plan scene graph', status: 'completed', startedAt: ago(580_000), completedAt: ago(575_000), durationMs: 5000, error: null, tokens: 420 },
      { id: 'sa_6', name: 'TTS Engine', engine: 'tts', task: 'Generate narration', status: 'completed', startedAt: ago(570_000), completedAt: ago(540_000), durationMs: 30000, error: null, tokens: 0 },
      { id: 'sa_7', name: 'Compositor', engine: 'remotion', task: 'Render all scenes', status: 'completed', startedAt: ago(530_000), completedAt: ago(460_000), durationMs: 70000, error: null, tokens: 0 },
    ],
    scenes: [
      { id: 'scene_5', kind: 'title', engine: 'remotion', status: 'completed', reviewIssues: 0, retryCount: 0, thumbnailUrl: '/api/artifacts/job_003/scenes/scene_5/thumbnail', frameUrl: '/api/artifacts/job_003/scenes/scene_5/frame', reportUrl: '/api/artifacts/job_003/scenes/scene_5/report' },
      { id: 'scene_6', kind: 'code', engine: 'remotion', status: 'completed', reviewIssues: 0, retryCount: 0, thumbnailUrl: '/api/artifacts/job_003/scenes/scene_6/thumbnail', frameUrl: '/api/artifacts/job_003/scenes/scene_6/frame', reportUrl: '/api/artifacts/job_003/scenes/scene_6/report' },
      { id: 'scene_7', kind: 'diagram', engine: 'manim', status: 'completed', reviewIssues: 0, retryCount: 1, thumbnailUrl: '/api/artifacts/job_003/scenes/scene_7/thumbnail', frameUrl: '/api/artifacts/job_003/scenes/scene_7/frame', reportUrl: '/api/artifacts/job_003/scenes/scene_7/report' },
      { id: 'scene_8', kind: 'outro', engine: 'remotion', status: 'completed', reviewIssues: 0, retryCount: 0, thumbnailUrl: '/api/artifacts/job_003/scenes/scene_8/thumbnail', frameUrl: '/api/artifacts/job_003/scenes/scene_8/frame', reportUrl: '/api/artifacts/job_003/scenes/scene_8/report' },
    ],
    events: [
      makeSSEEvent('job_003', 'job.started', { title: 'Release v0.5 — Demo video' }),
      makeSSEEvent('job_003', 'job.stage', { stage: 'plan', progressPct: 5, phase: 'plan' }),
      makeSSEEvent('job_003', 'job.stage', { stage: 'tts', progressPct: 25, phase: 'tts' }),
      makeSSEEvent('job_003', 'job.stage', { stage: 'render', progressPct: 55, phase: 'render' }),
      makeSSEEvent('job_003', 'subagent.started', { subagentId: 'sa_5', name: 'Scene Planner', engine: 'director', task: 'Plan scene graph' }),
      makeSSEEvent('job_003', 'subagent.completed', { subagentId: 'sa_5', result: 'ok', durationMs: 5000 }),
      makeSSEEvent('job_003', 'subagent.token', { subagentId: 'sa_5', token: 'Planned 4 scenes' }),
      makeSSEEvent('job_003', 'subagent.started', { subagentId: 'sa_6', name: 'TTS Engine', engine: 'tts', task: 'Generate narration' }),
      makeSSEEvent('job_003', 'subagent.completed', { subagentId: 'sa_6', result: 'ok', durationMs: 30000 }),
      makeSSEEvent('job_003', 'subagent.started', { subagentId: 'sa_7', name: 'Compositor', engine: 'remotion', task: 'Render all scenes' }),
      makeSSEEvent('job_003', 'subagent.completed', { subagentId: 'sa_7', result: 'ok', durationMs: 70000 }),
      makeSSEEvent('job_003', 'job.completed', { title: 'Release v0.5 — Demo video' }),
    ],
  },
  {
    id: 'job_004', title: 'PR #156 — Fix layout overlap',
    status: 'failed', stage: 'repair', progressPct: 78,
    createdAt: ago(200_000), startedAt: ago(190_000), completedAt: ago(50_000),
    error: 'Repair retry budget exhausted for scene_10',
    subagents: [
      { id: 'sa_8', name: 'Review Gate L2', engine: 'review', task: 'Check layout overlap', status: 'completed', startedAt: ago(100_000), completedAt: ago(95_000), durationMs: 5000, error: null, tokens: 210 },
      { id: 'sa_9', name: 'Auto-Repair', engine: 'repair', task: 'Fix overlap in scene_10', status: 'failed', startedAt: ago(90_000), completedAt: ago(50_000), durationMs: 40000, error: 'Retry budget exhausted', tokens: 0 },
    ],
    scenes: [
      { id: 'scene_9', kind: 'comparison', engine: 'remotion', status: 'completed', reviewIssues: 0, retryCount: 0, thumbnailUrl: '/api/artifacts/job_004/scenes/scene_9/thumbnail', frameUrl: '/api/artifacts/job_004/scenes/scene_9/frame', reportUrl: '/api/artifacts/job_004/scenes/scene_9/report' },
      { id: 'scene_10', kind: 'diagram', engine: 'manim', status: 'failed', reviewIssues: 3, retryCount: 3, thumbnailUrl: '/api/artifacts/job_004/scenes/scene_10/thumbnail', frameUrl: '/api/artifacts/job_004/scenes/scene_10/frame' },
    ],
    events: [
      makeSSEEvent('job_004', 'job.started', { title: 'PR #156 — Fix layout overlap' }),
      makeSSEEvent('job_004', 'job.stage', { stage: 'plan', progressPct: 5, phase: 'plan' }),
      makeSSEEvent('job_004', 'job.stage', { stage: 'review', progressPct: 65, phase: 'review' }),
      makeSSEEvent('job_004', 'review.issue', { sceneId: 'scene_10', issue: 'Text overlaps chart boundary', severity: 'high' }),
      makeSSEEvent('job_004', 'repair.plan', { sceneId: 'scene_10', plan: 'Reduce font size, increase spacing', retryCount: 1 }),
      makeSSEEvent('job_004', 'repair.plan', { sceneId: 'scene_10', plan: 'Reduce font size, increase spacing (attempt 2)', retryCount: 2 }),
      makeSSEEvent('job_004', 'job.stage', { stage: 'repair', progressPct: 78, phase: 'repair' }),
      makeSSEEvent('job_004', 'job.failed', { title: 'PR #156 — Fix layout overlap', error: 'Repair retry budget exhausted' }),
    ],
  },
]

let jobs = [...JOB_SEED]

export function getJobs(): Job[] { return [...jobs] }
export function getJob(id: string): Job | undefined { return jobs.find((j) => j.id === id) }

/* ─── Report mock data ─────────────────────────────────────────────── */

import type { ReportSummary, VideoReport, ProvenanceGraph, SceneReport } from '@/types/report'

const _now = '2026-07-09T17:00:00.000Z'

const REPORT_SEED: ReportSummary[] = [
  {
    name: 'demo-video', artifact: 'videoforge-video-report',
    report_timestamp: _now, content_hash: 'a1b2c3d4e5f6g7h8',
    engine_mix: ['remotion', 'manim'],
    scenes_count: 3, total_duration_frames: 420,
    l0_status: 'pass', l1_passed: true,
    policy_verdict: 'pass',
    video_path: '/builds/demo-video.mp4', has_provenance: true,
  },
  {
    name: 'pr-142-auth', artifact: 'videoforge-video-report',
    report_timestamp: _now, content_hash: 'bbccddeeff001122',
    engine_mix: ['remotion'],
    scenes_count: 4, total_duration_frames: 540,
    l0_status: 'warn', l1_passed: true,
    policy_verdict: 'warn',
    video_path: '/builds/pr-142-auth.mp4', has_provenance: false,
  },
  {
    name: 'issue-89-caption', artifact: 'videoforge-video-report',
    report_timestamp: _now, content_hash: '3344556677889900',
    engine_mix: ['animotion', 'remotion'],
    scenes_count: 2, total_duration_frames: 210,
    l0_status: 'fail', l1_passed: false,
    policy_verdict: 'fail',
    video_path: '/builds/issue-89-caption.mp4', has_provenance: true,
  },
]

const DEMO_REPORT: VideoReport = {
  artifact: 'videoforge-video-report', version: 1,
  video_path: '/builds/demo-video.mp4',
  report_timestamp: _now,
  content_hash: 'a1b2c3d4e5f6g7h8',
  engine_mix: ['manim', 'remotion'],
  render_format: { fps: 30, width: 1920, height: 1080, pixel_format: 'yuv420p', video_codec: 'h264', audio_codec: 'aac' },
  scenes_summary: {
    count: 3,
    engines: { remotion: 2, manim: 1 },
    total_duration_frames: 420,
    scenes: [
      { index: 0, engine: 'remotion', duration_frames: 180 },
      { index: 1, engine: 'manim', duration_frames: 120 },
      { index: 2, engine: 'remotion', duration_frames: 120 },
    ],
  },
  l0_summary: {
    status: 'pass', passed: true, total_issues: 0,
    severity_counts: { high: 0, medium: 0, low: 0 },
    sampled_frames: 14, total_frames: 420, duration_seconds: 14.0,
    issues: [],
  },
  l1_summary: {
    passed: true, total_frames: 420, total_issues: 0, issues: [],
  },
  l2_layout_overlap_summary: {
    status: 'pass', passed: true, total_issues: 0,
    severity_counts: { high: 0, medium: 0, low: 0 },
    issues: [],
  },
  policy_verdict: 'pass',
}

const DEMO_PROVENANCE: ProvenanceGraph = {
  artifact: 'videoforge-provenance-graph', version: 1,
  video_path: '/builds/demo-video.mp4',
  report_timestamp: _now,
  content_hash: 'a1b2c3d4e5f6g7h8',
  engines: ['manim', 'remotion'],
  scenes: [
    {
      id: 'scene_0000', engine: 'remotion', kind: 'title',
      content_hash: 's0hash001', scene_path: '/builds/scene_0000.mp4',
      scene_report_path: '/builds/scene_0000.mp4.scene.report.json',
      duration_frames: 180, assets: { audio_src: 'audio/voice.wav' },
    },
    {
      id: 'scene_0001', engine: 'manim', kind: 'diagram',
      content_hash: 's1hash002', scene_path: '/builds/scene_0001.mp4',
      scene_report_path: '/builds/scene_0001.mp4.scene.report.json',
      duration_frames: 120, assets: {},
    },
    {
      id: 'scene_0002', engine: 'remotion', kind: 'outro',
      content_hash: 's2hash003', scene_path: '/builds/scene_0002.mp4',
      scene_report_path: '/builds/scene_0002.mp4.scene.report.json',
      duration_frames: 120, assets: { props_path: '/builds/props_0002.json' },
    },
  ],
  reports: {
    video_report: '/builds/demo-video.mp4.report.json',
    provenance_graph: '/builds/demo-video.provenance.json',
  },
}

const DEMO_SCENES: SceneReport[] = [
  {
    artifact: 'videoforge-scene-report', version: 1,
    scene_index: 0, engine: 'remotion', duration_frames: 180,
    scene_path: '/builds/scene_0000.mp4',
    report_timestamp: _now, content_hash: 's0hash001',
    render_format: { fps: 30, width: 1920, height: 1080, pixel_format: 'yuv420p', video_codec: 'h264', audio_codec: 'aac' },
  },
  {
    artifact: 'videoforge-scene-report', version: 1,
    scene_index: 1, engine: 'manim', duration_frames: 120,
    scene_path: '/builds/scene_0001.mp4',
    report_timestamp: _now, content_hash: 's1hash002',
    render_format: { fps: 30, width: 1920, height: 1080, pixel_format: 'yuv420p', video_codec: 'h264', audio_codec: 'aac' },
  },
  {
    artifact: 'videoforge-scene-report', version: 1,
    scene_index: 2, engine: 'remotion', duration_frames: 120,
    scene_path: '/builds/scene_0002.mp4',
    report_timestamp: _now, content_hash: 's2hash003',
    render_format: { fps: 30, width: 1920, height: 1080, pixel_format: 'yuv420p', video_codec: 'h264', audio_codec: 'aac' },
  },
]

export function getReports(): ReportSummary[] { return [...REPORT_SEED] }
export function getReport(name: string): VideoReport | undefined {
  return REPORT_SEED.find((r) => r.name === name) ? { ...DEMO_REPORT } : undefined
}
export function getProvenance(name: string): ProvenanceGraph | undefined {
  return REPORT_SEED.find((r) => r.name === name && r.has_provenance) ? { ...DEMO_PROVENANCE } : undefined
}
export function getSceneReports(name: string): SceneReport[] {
  return REPORT_SEED.find((r) => r.name === name) ? [...DEMO_SCENES] : []
}

/* Swap with real EventSource(url) when backend serves /api/jobs/:id/stream */
export function subscribeToJobEvents(
  jobId: string,
  onEvent: (event: SSEEvent) => void,
  onError: (err: Error) => void,
): () => void {
  const job = getJob(jobId)
  if (!job) { onError(new Error(`Job ${jobId} not found`)); return () => {} }
  let idx = 0
  const timer = setInterval(() => {
    if (idx >= job.events.length) { clearInterval(timer); return }
    onEvent(job.events[idx]); idx++
  }, 800)
  return () => clearInterval(timer)
}

export function resetMock() { jobs = [...JOB_SEED] }
