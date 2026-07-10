import { useMemo, useState } from 'react'
import type { Job } from '@/types/job'
import type { FlowNode, FlowEdge } from '@/types/canvas'
import { FlowCanvas } from './flow-canvas'
import { FlowCanvasNode } from './flow-canvas-node'
import { FlowCanvasEdges } from './flow-canvas-edges'
import { layoutNodes, buildFlowEdges } from './flow-canvas-layout'

interface FlowJobCanvasProps {
  job: Job
  className?: string
}

/**
 * Maps a Job to flow canvas nodes + edges and renders the interactive canvas.
 */
export function FlowJobCanvas({ job, className }: FlowJobCanvasProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const { flowNodes, flowEdges } = useMemo(() => {
    const nodes: FlowNode[] = []

    // Root job node
    nodes.push({
      id: job.id,
      type: 'job',
      label: job.title,
      status: job.status,
      progress: job.progressPct,
    })

    // Stage nodes
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

    const edges = buildFlowEdges(nodes)
    return { flowNodes: nodes, flowEdges: edges }
  }, [job])

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
