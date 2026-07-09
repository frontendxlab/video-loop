/* Job types — mirrors Python backend (StateMachine, Pipeline) + SSE events */

export type JobStatus = 'queued' | 'running' | 'completed' | 'failed' | 'cancelled'

export type JobStage =
  | 'plan' | 'grill' | 'director' | 'tts' | 'render'
  | 'review' | 'repair' | 'assemble' | 'report' | 'done'

export interface Subagent {
  id: string
  name: string
  engine: string
  task: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  startedAt: string | null
  completedAt: string | null
  durationMs: number | null
  error: string | null
  tokens: number
}

export interface SceneInfo {
  id: string
  kind: string
  engine: string
  status: 'pending' | 'rendering' | 'completed' | 'failed'
  reviewIssues: number
  retryCount: number
}

export interface Job {
  id: string
  title: string
  status: JobStatus
  stage: JobStage
  progressPct: number
  createdAt: string
  startedAt: string | null
  completedAt: string | null
  error: string | null
  subagents: Subagent[]
  scenes: SceneInfo[]
  events: import('./sse').SSEEvent[]
}

export const STAGE_LABELS: Record<JobStage, string> = {
  plan: 'Planning', grill: 'Grill', director: 'Director', tts: 'TTS',
  render: 'Render', review: 'Review', repair: 'Repair', assemble: 'Assemble',
  report: 'Report', done: 'Done',
}

export const STAGE_ORDER: JobStage[] = [
  'plan', 'grill', 'director', 'tts', 'render',
  'review', 'repair', 'assemble', 'report', 'done',
]
