/* Report artifact types — mirrors Python video report / provenance / scene artifacts */

export interface ReportSummary {
  name: string
  artifact: string
  report_timestamp: string
  content_hash: string
  engine_mix: string[]
  scenes_count: number
  total_duration_frames: number
  l0_status: string
  l1_passed: boolean | null
  policy_verdict: string
  video_path: string | null
  has_provenance: boolean
  error?: string
}

export interface RenderFormat {
  fps: number
  width: number
  height: number
  pixel_format: string
  video_codec: string
  audio_codec: string
}

export interface L0Summary {
  status: string
  passed: boolean
  total_issues: number
  severity_counts: { high: number; medium: number; low: number }
  sampled_frames: number
  total_frames: number
  duration_seconds: number
  issues: Issue[]
}

export interface L1Summary {
  passed: boolean
  total_frames: number
  total_issues: number
  issues: Issue[]
}

export interface L2Summary {
  status: string
  passed: boolean
  total_issues: number
  severity_counts: { high: number; medium: number; low: number }
  issues: Issue[]
}

export interface SceneRef {
  index: number
  engine: string
  duration_frames: number
}

export interface ScenesSummary {
  count: number
  engines: Record<string, number>
  total_duration_frames: number
  scenes?: SceneRef[]
}

export interface CoherenceSummary {
  coherent: boolean
  total_issues: number
  issues: Issue[]
  has_complete_arc: boolean
  missing_phases: string[]
  duplicate_phases: string[]
  phase_order_valid: boolean
}

export interface Issue {
  type: string
  severity?: string
  detail?: string
  start?: number
  end?: number
  element?: string
  element_a?: string
  element_b?: string
  iou?: number
  frame_index?: number
}

export interface VideoReport {
  artifact: string
  version: number
  video_path: string
  report_timestamp: string
  content_hash: string
  engine_mix: string[]
  render_format: RenderFormat
  scenes_summary: ScenesSummary
  l0_summary: L0Summary
  l1_summary: L1Summary
  l2_layout_overlap_summary: L2Summary
  coherence_summary?: CoherenceSummary
  policy_verdict?: string
}

export interface ProvenanceScene {
  id: string
  engine: string
  kind: string
  content_hash: string
  scene_path: string
  scene_report_path: string
  duration_frames: number
  assets: Record<string, string>
}

export interface ProvenanceGraph {
  artifact: string
  version: number
  video_path: string
  report_timestamp: string
  content_hash: string
  engines: string[]
  scenes: ProvenanceScene[]
  reports: {
    video_report: string
    provenance_graph: string
  }
}

export interface SceneReport {
  artifact: string
  version: number
  scene_index: number
  engine: string
  duration_frames: number
  scene_path: string
  report_timestamp: string
  content_hash: string
  render_format: RenderFormat
}
