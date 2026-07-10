/* Flow canvas node/edge types — generic, reusable across job/scene/subagent views */

export type FlowNodeType = 'job' | 'stage' | 'subagent' | 'scene' | 'root'

export interface FlowNode {
  id: string
  type: FlowNodeType
  label: string
  status: string
  progress?: number
  parentId?: string
  engine?: string
  kind?: string
  error?: string | null
  meta?: Record<string, unknown>
}

export interface FlowEdge {
  id: string
  source: string
  target: string
  label?: string
}

export interface Position {
  x: number
  y: number
}

export interface Size {
  w: number
  h: number
}

export interface CanvasNode extends FlowNode {
  pos: Position
  size: Size
}

/** Level-based layout config */
export interface LayoutConfig {
  levelGap: number   // vertical gap between levels
  nodeGap: number    // horizontal gap between nodes
  padding: number    // top/left padding
  nodeWidth: number
  nodeHeight: number
}

export const DEFAULT_LAYOUT: LayoutConfig = {
  levelGap: 100,
  nodeGap: 32,
  padding: 80,
  nodeWidth: 200,
  nodeHeight: 80,
}
