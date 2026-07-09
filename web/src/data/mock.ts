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
      { id: 'scene_1', kind: 'title', engine: 'remotion', status: 'completed', reviewIssues: 0, retryCount: 0 },
      { id: 'scene_2', kind: 'code', engine: 'remotion', status: 'completed', reviewIssues: 0, retryCount: 0 },
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
      { id: 'scene_5', kind: 'title', engine: 'remotion', status: 'completed', reviewIssues: 0, retryCount: 0 },
      { id: 'scene_6', kind: 'code', engine: 'remotion', status: 'completed', reviewIssues: 0, retryCount: 0 },
      { id: 'scene_7', kind: 'diagram', engine: 'manim', status: 'completed', reviewIssues: 0, retryCount: 1 },
      { id: 'scene_8', kind: 'outro', engine: 'remotion', status: 'completed', reviewIssues: 0, retryCount: 0 },
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
      { id: 'scene_9', kind: 'comparison', engine: 'remotion', status: 'completed', reviewIssues: 0, retryCount: 0 },
      { id: 'scene_10', kind: 'diagram', engine: 'manim', status: 'failed', reviewIssues: 3, retryCount: 3 },
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
