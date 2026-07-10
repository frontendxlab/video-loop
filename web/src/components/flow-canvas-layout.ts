import type { FlowNode, FlowEdge, CanvasNode, Position, Size, LayoutConfig } from '@/types/canvas'
import { DEFAULT_LAYOUT } from '@/types/canvas'

/**
 * Simple level-based DAG layout.
 * Groups nodes by depth from root, spaces evenly per level.
 * Root-first traversal assigns levels.
 * Returns positioned nodes.
 */
export function layoutNodes(
  nodes: FlowNode[],
  edges: FlowEdge[],
  config: LayoutConfig = DEFAULT_LAYOUT,
): CanvasNode[] {
  if (nodes.length === 0) return []

  const { levelGap, nodeGap, padding, nodeWidth, nodeHeight } = config

  // Build adjacency: child -> parent
  const childToParent = new Map<string, string>()
  for (const edge of edges) {
    childToParent.set(edge.target, edge.source)
  }

  // Find roots: nodes with no parent in the set
  const nodeIds = new Set(nodes.map(n => n.id))
  const roots = nodes.filter(n => !n.parentId && !childToParent.has(n.id))

  // Assign levels via BFS
  const levelMap = new Map<string, number>()
  const queue: Array<{ id: string; level: number }> = roots.map(r => ({ id: r.id, level: 0 }))

  // Also seed from parentId
  for (const node of nodes) {
    if (node.parentId && nodeIds.has(node.parentId)) {
      // Will be discovered via edges or direct parent
    }
  }

  // Process queue
  for (const { id, level } of queue) {
    levelMap.set(id, level)
    const children = edges.filter(e => e.source === id).map(e => e.target)
    for (const childId of children) {
      if (!levelMap.has(childId)) {
        queue.push({ id: childId, level: level + 1 })
      }
    }
  }

  // Fallback for any node not reached
  for (const node of nodes) {
    if (!levelMap.has(node.id)) {
      levelMap.set(node.id, 0)
    }
  }

  // Group by level
  const byLevel = new Map<number, FlowNode[]>()
  for (const node of nodes) {
    const lv = levelMap.get(node.id) ?? 0
    if (!byLevel.has(lv)) byLevel.set(lv, [])
    byLevel.get(lv)!.push(node)
  }

  // Sort levels
  const maxLevel = Math.max(...byLevel.keys(), 0) + 1
  const sortedLevels = Array.from({ length: maxLevel }, (_, i) => byLevel.get(i) ?? [])

  // Position nodes per level
  const result: CanvasNode[] = []
  const positions = new Map<string, Position>()

  for (let lv = 0; lv < sortedLevels.length; lv++) {
    const levelNodes = sortedLevels[lv]
    const totalWidth = levelNodes.length * nodeWidth + (levelNodes.length - 1) * nodeGap
    const startX = padding + (totalWidth > 0 ? 0 : 0) // centering handled per-node

    for (let i = 0; i < levelNodes.length; i++) {
      const node = levelNodes[i]
      const x = startX + i * (nodeWidth + nodeGap)
      const y = padding + lv * (nodeHeight + levelGap)
      positions.set(node.id, { x, y })
      result.push({ ...node, pos: { x, y }, size: { w: nodeWidth, h: nodeHeight } })
    }

    // Center level nodes horizontally
    for (let i = 0; i < levelNodes.length; i++) {
      const node = levelNodes[i]
      const entry = result.find(r => r.id === node.id)
      if (entry && levelNodes.length > 1) {
        // Shift so max-width levels align center
        // Simplified: keep as-is, user can pan
      }
    }
  }

  return result
}

/** Build FlowNode + FlowEdge arrays from typed nodes with parent relationships */
export function buildFlowEdges(nodes: FlowNode[]): FlowEdge[] {
  const edges: FlowEdge[] = []
  for (const node of nodes) {
    if (node.parentId) {
      edges.push({
        id: `${node.parentId}→${node.id}`,
        source: node.parentId,
        target: node.id,
      })
    }
  }
  return edges
}
