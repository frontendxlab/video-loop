/* SSE event model — matches docs/STUDY-ui-showcase-next.md §5 */

export type SSEEventType =
  | 'job.started'
  | 'job.stage'
  | 'job.todo'
  | 'prompt.grilled'
  | 'director.scene_planned'
  | 'director.scene_routed'
  | 'subagent.started'
  | 'subagent.token'
  | 'subagent.completed'
  | 'subagent.failed'
  | 'render.scene_started'
  | 'render.scene_completed'
  | 'review.issue'
  | 'repair.plan'
  | 'retry.started'
  | 'artifact.ready'
  | 'job.completed'
  | 'job.failed'

export interface SSEBaseData {
  jobId: string
  timestamp: string
}

export interface JobStartedData extends SSEBaseData { title: string }
export interface JobStageData extends SSEBaseData { stage: string; progressPct: number; phase: string }
export interface SubagentStartedData extends SSEBaseData { subagentId: string; name: string; engine: string; task: string }
export interface SubagentTokenData extends SSEBaseData { subagentId: string; token: string }
export interface SubagentDoneData extends SSEBaseData { subagentId: string; result: string; durationMs: number }
export interface SubagentFailedData extends SSEBaseData { subagentId: string; error: string }
export interface SceneEventData extends SSEBaseData { sceneId: string; sceneKind: string }
export interface ReviewIssueData extends SSEBaseData { sceneId: string; issue: string; severity: 'low' | 'medium' | 'high' }
export interface RepairPlanData extends SSEBaseData { sceneId: string; plan: string; retryCount: number }
export interface RetryEventData extends SSEBaseData { sceneId: string; attempt: number; reason: string }
export interface ArtifactReadyData extends SSEBaseData { artifactType: string; path: string }
export interface TodoEventData extends SSEBaseData { item: string; done: boolean }

export type SSEEventData =
  | JobStartedData | JobStageData
  | SubagentStartedData | SubagentTokenData | SubagentDoneData | SubagentFailedData
  | SceneEventData | ReviewIssueData | RepairPlanData | RetryEventData
  | ArtifactReadyData | TodoEventData

export interface SSEEvent {
  type: SSEEventType
  data: SSEEventData
}

export interface StageInfo {
  stage: string
  status: 'pending' | 'active' | 'done' | 'failed'
  progressPct: number
  startedAt: string | null
}
