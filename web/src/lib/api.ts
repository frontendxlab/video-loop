/* API client for VideoForge backend.
   Falls back to mock data when backend unavailable (dev). */

import type { Job } from "@/types/job"
import { getJobs, getJob } from "@/data/mock"

const BASE = "/api"

async function fetchJSON<T>(url: string): Promise<T | null> {
  try {
    const res = await fetch(`${BASE}${url}`)
    if (!res.ok) return null
    return (await res.json()) as T
  } catch {
    return null
  }
}

async function postJSON<T>(url: string, body?: Record<string, unknown>): Promise<T | null> {
  try {
    const res = await fetch(`${BASE}${url}`, {
      method: "POST",
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    })
    if (!res.ok) return null
    return (await res.json()) as T
  } catch {
    return null
  }
}

export interface JobSummaryDTO {
  id: string
  title: string
  status: string
  stage: string
  progressPct: number
  createdAt: string
  startedAt: string | null
  completedAt: string | null
  error: string | null
  subagentCount: number
  sceneCount: number
}

export interface SubagentDTO {
  id: string
  name: string
  engine: string
  task: string
  status: string
  startedAt: string | null
  completedAt: string | null
  durationMs: number | null
  error: string | null
  tokens: number
}

export interface SceneDTO {
  id: string
  kind: string
  engine: string
  status: string
  reviewIssues: number
  retryCount: number
  thumbnailUrl?: string
  frameUrl?: string
  reportUrl?: string
}

/** Build artifact URL for scene thumbnail */
export function artifactThumbnailUrl(jobId: string, sceneId: string): string {
  return `/api/artifacts/${encodeURIComponent(jobId)}/scenes/${encodeURIComponent(sceneId)}/thumbnail`
}

/** Build artifact URL for sampled frame */
export function artifactFrameUrl(jobId: string, sceneId: string): string {
  return `/api/artifacts/${encodeURIComponent(jobId)}/scenes/${encodeURIComponent(sceneId)}/frame`
}

/** Build artifact URL for scene report */
export function artifactReportUrl(jobId: string, sceneId: string): string {
  return `/api/artifacts/${encodeURIComponent(jobId)}/scenes/${encodeURIComponent(sceneId)}/report`
}

export interface JobDetailDTO {
  id: string
  title: string
  status: string
  stage: string
  progressPct: number
  createdAt: string
  startedAt: string | null
  completedAt: string | null
  error: string | null
  subagents: SubagentDTO[]
  scenes: SceneDTO[]
  events: Record<string, unknown>[]
}

/* Convert backend event (JobEvent.model_dump with nested payload) to SSEEvent */
function toSSEEvent(raw: Record<string, unknown>): import("@/types/sse").SSEEvent {
  const type = raw.type as string
  const timestamp = typeof raw.timestamp === "number"
    ? new Date(raw.timestamp * 1000).toISOString()
    : String(raw.timestamp ?? "")
  const { id: _id, type: _t, jobId, timestamp: _ts, payload, ...rest } = raw
  return {
    type: type as import("@/types/sse").SSEEventType,
    data: { jobId: jobId as string, timestamp, ...(payload as Record<string, unknown> || {}), ...rest } as import("@/types/sse").SSEEvent["data"],
  }
}

/* Convert backend DTO to frontend Job type */
function toJob(dto: JobDetailDTO): Job {
  return {
    id: dto.id,
    title: dto.title,
    status: dto.status as Job["status"],
    stage: dto.stage as Job["stage"],
    progressPct: dto.progressPct,
    createdAt: dto.createdAt,
    startedAt: dto.startedAt,
    completedAt: dto.completedAt,
    error: dto.error,
    subagents: dto.subagents.map((s) => ({
      id: s.id,
      name: s.name,
      engine: s.engine,
      task: s.task,
      status: s.status as Job["subagents"][0]["status"],
      startedAt: s.startedAt,
      completedAt: s.completedAt,
      durationMs: s.durationMs,
      error: s.error,
      tokens: s.tokens,
    })),
    scenes: dto.scenes.map((s) => ({
      id: s.id,
      kind: s.kind,
      engine: s.engine,
      status: s.status as Job["scenes"][0]["status"],
      reviewIssues: s.reviewIssues,
      retryCount: s.retryCount,
      thumbnailUrl: s.thumbnailUrl,
      frameUrl: s.frameUrl,
      reportUrl: s.reportUrl,
    })),
    events: (dto.events || []).map(toSSEEvent),
  }
}

function summaryToJob(s: JobSummaryDTO): Job {
  return {
    id: s.id,
    title: s.title,
    status: s.status as Job["status"],
    stage: s.stage as Job["stage"],
    progressPct: s.progressPct,
    createdAt: s.createdAt,
    startedAt: s.startedAt,
    completedAt: s.completedAt,
    error: s.error,
    subagents: [],
    scenes: [],
    events: [],
  }
}

export async function fetchJobs(): Promise<Job[]> {
  /* Fetch job list from backend. Fallback to mock on failure. */
  const data = await fetchJSON<JobSummaryDTO[]>("/jobs")
  if (data) return data.map(summaryToJob)

  // Fallback: augment mock jobs with subagent/scene counts
  return getJobs()
}

export async function fetchJob(id: string): Promise<Job | null> {
  /* Fetch single job detail from backend. Fallback to mock. */
  const data = await fetchJSON<JobDetailDTO>(`/jobs/${encodeURIComponent(id)}`)
  if (data) return toJob(data)

  // Fallback
  return getJob(id) ?? null
}

/* ── Job action endpoints ──────────────────────────────────────────────── */

export interface ActionResponse {
  status: string
  job_id?: string
  scene_id?: string
  engine?: string
}

export async function stopJob(jobId: string): Promise<ActionResponse | null> {
  return postJSON<ActionResponse>(`/jobs/${encodeURIComponent(jobId)}/stop`)
}

export async function retryJob(jobId: string): Promise<ActionResponse | null> {
  return postJSON<ActionResponse>(`/jobs/${encodeURIComponent(jobId)}/retry`)
}

export async function retryScene(jobId: string, sceneId: string): Promise<ActionResponse | null> {
  return postJSON<ActionResponse>(`/jobs/${encodeURIComponent(jobId)}/retry/${encodeURIComponent(sceneId)}`)
}

export async function rerouteScene(jobId: string, sceneId: string, engine: string): Promise<ActionResponse | null> {
  return postJSON<ActionResponse>(`/jobs/${encodeURIComponent(jobId)}/reroute/${encodeURIComponent(sceneId)}`, { engine })
}
