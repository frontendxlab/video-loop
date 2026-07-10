import { useMemo, useState } from 'react'
import type { SceneNode } from '@/lib/ir-types'
import { Engine } from '@/lib/ir-types'
import { pickEngine } from '@/lib/director'
import type { FlowNode, FlowEdge } from '@/types/canvas'
import { FlowCanvas } from './flow-canvas'
import { FlowCanvasNode } from './flow-canvas-node'
import { FlowCanvasEdges } from './flow-canvas-edges'
import { layoutNodes, buildFlowEdges } from './flow-canvas-layout'

interface FlowSceneCanvasProps {
  scenes: SceneNode[]
  className?: string
}

const ENGINE_TO_STATUS: Record<string, string> = {
  [Engine.REMOTION]: 'completed',
  [Engine.MANIM]: 'running',
  [Engine.ANIMOTION]: 'pending',
}

/**
 * Maps SceneNode[] to flow canvas — shows scene routing and engine assignment.
 */
export function FlowSceneCanvas({ scenes, className }: FlowSceneCanvasProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const { flowNodes, flowEdges } = useMemo(() => {
    const nodes: FlowNode[] = []

    // Root node
    const rootId = 'scene-root'
    nodes.push({
      id: rootId,
      type: 'root',
      label: `Scene Graph (${scenes.length} scenes)`,
      status: 'done',
      parentId: undefined,
    })

    // Group by engine
    const byEngine = new Map<string, SceneNode[]>()
    for (const scene of scenes) {
      const engine = scene.routedEngine ?? pickEngine(scene)
      if (!byEngine.has(engine)) byEngine.set(engine, [])
      byEngine.get(engine)!.push(scene)
    }

    // Engine group nodes + scene nodes
    let engineIdx = 0
    for (const [engine, engineScenes] of byEngine) {
      const engineId = `engine-${engine}-${engineIdx++}`
      nodes.push({
        id: engineId,
        type: 'stage',
        label: `${engine.charAt(0).toUpperCase() + engine.slice(1)} (${engineScenes.length})`,
        status: ENGINE_TO_STATUS[engine] ?? 'pending',
        engine,
        parentId: rootId,
      })

      for (const scene of engineScenes) {
        nodes.push({
          id: scene.id,
          type: 'scene',
          label: `${scene.kind} — ${scene.id.slice(0, 16)}`,
          status: 'completed',
          engine,
          kind: scene.kind,
          meta: { duration: scene.duration_frames },
          parentId: engineId,
        })
      }
    }

    const edges = buildFlowEdges(nodes)
    return { flowNodes: nodes, flowEdges: edges }
  }, [scenes])

  const canvasNodes = useMemo(() => layoutNodes(flowNodes, flowEdges), [flowNodes, flowEdges])

  const nodePositions = useMemo(() => {
    const map: Record<string, { pos: { x: number; y: number }; size: { w: number; h: number } }> = {}
    for (const cn of canvasNodes) map[cn.id] = { pos: cn.pos, size: cn.size }
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
          type={node.type as 'job' | 'stage' | 'subagent' | 'scene'}
          status={node.status}
          engine={node.engine}
          kind={node.kind}
          x={node.pos.x}
          y={node.pos.y}
          selected={selectedId === node.id}
          onSelect={setSelectedId}
        />
      ))}
    </FlowCanvas>
  )
}
