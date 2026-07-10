import { useMemo, useState } from 'react'
import type { Job } from '@/types/job'
import type { SSEEvent } from '@/types/sse'
import type { FlowNode, FlowEdge } from '@/types/canvas'
import { FlowCanvas } from './flow-canvas'
import { FlowCanvasNode } from './flow-canvas-node'
import { FlowCanvasEdges } from './flow-canvas-edges'
import { layoutNodes, buildFlowEdges } from './flow-canvas-layout'

interface FlowJobCanvasProps {
  job: Job
  /** Live SSE events to derive real-time node status overrides */
  sseEvents?: SSEEvent[]
  className?: string
}

/**
 * Build base FlowNode[] from static Job data.
 */
function buildBaseNodes(job: Job): FlowNode[] {
  const nodes: FlowNode[] = []

  // Root job node
  nodes.push({
    id: job.id,
    type: 'job',
    label: job.title,
    status: job.status,
    progress: job.progressPct,
  })

  // Stage node
  nodes.push({
    id: `${job.id}-stage`,
    type: 'stage',
    label: `Stage: ${job.stage}`,
    status: job.status === 'completed' ? 'done' : job.status === 'failed' ? 'failed' : 'active',
    progress: job.progressPct,
    parentId: job.id,
  })

  // Subagent nodes
  for (const sa of job.subagents) {
    nodes.push({
      id: sa.id,
      type: 'subagent',
      label: sa.name,
      status: sa.status,
      engine: sa.engine,
      error: sa.error,
      meta: { task: sa.task, tokens: sa.tokens, durationMs: sa.durationMs },
      parentId: `${job.id}-stage`,
    })
  }

  // Scene nodes
  for (const sc of job.scenes) {
    nodes.push({
      id: sc.id,
      type: 'scene',
      label: sc.id,
      status: sc.status,
      engine: sc.engine,
      kind: sc.kind,
      meta: { reviewIssues: sc.reviewIssues, retryCount: sc.retryCount },
      parentId: `${job.id}-stage`,
    })
  }

  return nodes
}

/**
 * Apply SSE event deltas over static FlowNode[] to derive live state.
 * Only overrides fields that SSE events explicitly update — other fields
 * (label, engine, kind, parentId) stay from the static base.
 */
function applySSEToNodes(nodes: FlowNode[], events: SSEEvent[], jobId: string): FlowNode[] {
  if (events.length === 0) return nodes

  const overrides = new Map<string, Partial<FlowNode>>()

  for (const ev of events) {
    switch (ev.type) {
      case 'job.stage': {
        const d = ev.data as { stage?: string; progressPct?: number }
        const stageId = `${jobId}-stage`
        overrides.set(stageId, {
          progress: d.progressPct,
          label: d.stage ? `Stage: ${d.stage}` : undefined,
          status: 'active',
        })
        break
      }
      case 'job.completed': {
        overrides.set(jobId, { status: 'done', progress: 100 })
        overrides.set(`${jobId}-stage`, { status: 'done', progress: 100 })
        break
      }
      case 'job.failed': {
        const d = ev.data as { error?: string }
        overrides.set(jobId, { status: 'failed', error: d.error })
        overrides.set(`${jobId}-stage`, { status: 'failed', error: d.error })
        break
      }
      case 'subagent.started': {
        const d = ev.data as { subagentId: string }
        overrides.set(d.subagentId, { status: 'running' })
        break
      }
      case 'subagent.completed': {
        const d = ev.data as { subagentId: string }
        overrides.set(d.subagentId, { status: 'completed' })
        break
      }
      case 'subagent.failed': {
        const d = ev.data as { subagentId: string; error?: string }
        overrides.set(d.subagentId, { status: 'failed', error: d.error })
        break
      }
      case 'render.scene_started': {
        const d = ev.data as { sceneId: string }
        overrides.set(d.sceneId, { status: 'rendering' })
        break
      }
      case 'render.scene_completed': {
        const d = ev.data as { sceneId: string }
        overrides.set(d.sceneId, { status: 'completed' })
        break
      }
    }
  }

  return nodes.map(n => {
    const override = overrides.get(n.id)
    if (!override) return n
    return { ...n, ...override }
  })
}

/**
 * Maps a Job + optional SSE events to flow canvas nodes + edges
 * and renders the interactive canvas.
 */
export function FlowJobCanvas({ job, sseEvents, className }: FlowJobCanvasProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const { flowNodes, flowEdges } = useMemo(() => {
    const nodes = buildBaseNodes(job)
    const edges = buildFlowEdges(nodes)
    const liveNodes = sseEvents?.length ? applySSEToNodes(nodes, sseEvents, job.id) : nodes
    return { flowNodes: liveNodes, flowEdges: edges }
  }, [job, sseEvents])

  const canvasNodes = useMemo(() => layoutNodes(flowNodes, flowEdges), [flowNodes, flowEdges])

  // Build position lookup for edges
  const nodePositions = useMemo(() => {
    const map: Record<string, { pos: { x: number; y: number }; size: { w: number; h: number } }> = {}
    for (const cn of canvasNodes) {
      map[cn.id] = { pos: cn.pos, size: cn.size }
    }
    return map
  }, [canvasNodes])

  return (
    <FlowCanvas className={className}>
      <FlowCanvasEdges edges={flowEdges} nodePositions={nodePositions} />
      {canvasNodes.map((node) => (
        <FlowCanvasNode
          key={node.id}
          id={node.id}
          label={node.label}
          type={node.type}
          status={node.status}
          progress={node.progress}
          engine={node.engine}
          kind={node.kind}
          error={node.error}
          x={node.pos.x}
          y={node.pos.y}
          selected={selectedId === node.id}
          onSelect={setSelectedId}
        />
      ))}
    </FlowCanvas>
  )
}
