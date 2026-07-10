import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { FlowCanvas } from '@/components/flow-canvas'
import { FlowCanvasNode } from '@/components/flow-canvas-node'
import { FlowCanvasEdges } from '@/components/flow-canvas-edges'
import { layoutNodes, buildFlowEdges } from '@/components/flow-canvas-layout'
import { FlowJobCanvas } from '@/components/flow-job-canvas'
import { FlowSceneCanvas } from '@/components/flow-scene-canvas'
import type { FlowNode, FlowEdge, CanvasNode } from '@/types/canvas'
import { getJobs } from '@/data/mock'

/* ── FlowCanvas ────────────────────────────────────────────────────── */

describe('FlowCanvas', () => {
  it('renders with children', () => {
    render(<FlowCanvas><div data-testid="child" /></FlowCanvas>)
    expect(screen.getByTestId('child')).toBeDefined()
  })

  it('renders zoom controls', () => {
    render(<FlowCanvas />)
    expect(screen.getByLabelText('Zoom out')).toBeDefined()
    expect(screen.getByLabelText('Zoom in')).toBeDefined()
    expect(screen.getByLabelText('Reset view')).toBeDefined()
  })

  it('shows zoom percentage', () => {
    render(<FlowCanvas />)
    expect(screen.getByText('100%')).toBeDefined()
  })

  it('hides controls when disabled', () => {
    render(<FlowCanvas showZoom={false} showReset={false} />)
    expect(screen.queryByLabelText('Zoom out')).toBeNull()
    expect(screen.queryByText('100%')).toBeNull()
  })

  it('applies custom className', () => {
    const { container } = render(<FlowCanvas className="custom-class" />)
    expect(container.firstChild).toHaveProperty('className', expect.stringContaining('custom-class'))
  })
})

/* ── FlowCanvasNode ─────────────────────────────────────────────────── */

describe('FlowCanvasNode', () => {
  const baseProps = {
    id: 'test-node', label: 'Test Node', type: 'stage' as const,
    status: 'running', x: 100, y: 200,
  }

  it('renders at correct position', () => {
    render(<FlowCanvasNode {...baseProps} />)
    const el = screen.getByRole('button')
    expect(el.style.left).toBe('100px')
    expect(el.style.top).toBe('200px')
  })

  it('renders label', () => {
    render(<FlowCanvasNode {...baseProps} label="My Node" />)
    expect(screen.getByText('My Node')).toBeDefined()
  })

  it('renders type badge', () => {
    render(<FlowCanvasNode {...baseProps} />)
    expect(screen.getByText('STAGE')).toBeDefined()
  })

  it('renders engine badge', () => {
    render(<FlowCanvasNode {...baseProps} engine="remotion" />)
    expect(screen.getByText('remotion')).toBeDefined()
  })

  it('renders kind badge', () => {
    render(<FlowCanvasNode {...baseProps} kind="code" />)
    expect(screen.getByText('code')).toBeDefined()
  })

  it('renders progress bar', () => {
    render(<FlowCanvasNode {...baseProps} progress={62} />)
    const bar = screen.getByRole('button').querySelector('.h-1 div')
    expect(bar).toBeDefined()
    expect(bar?.getAttribute('style')).toContain('width: 62%')
  })

  it('renders error message', () => {
    render(<FlowCanvasNode {...baseProps} error="Something went wrong" />)
    expect(screen.getByText('Something went wrong')).toBeDefined()
  })

  it('calls onSelect on click', () => {
    const onSelect = vi.fn()
    render(<FlowCanvasNode {...baseProps} onSelect={onSelect} />)
    fireEvent.click(screen.getByRole('button'))
    expect(onSelect).toHaveBeenCalledWith('test-node')
  })

  it('shows selected state', () => {
    const { container } = render(<FlowCanvasNode {...baseProps} selected />)
    const el = screen.getByRole('button')
    expect(el.className).toContain('ring-2')
  })

  it('renders different type styles', () => {
    const types: Array<{ type: 'job' | 'stage' | 'subagent' | 'scene'; label: string }> = [
      { type: 'job', label: 'JOB' },
      { type: 'stage', label: 'STAGE' },
      { type: 'subagent', label: 'AGENT' },
      { type: 'scene', label: 'SCENE' },
    ]
    for (const { type, label } of types) {
      const { unmount } = render(<FlowCanvasNode {...{ ...baseProps, id: `n-${type}`, type }} />)
      expect(screen.getByText(label)).toBeDefined()
      unmount()
    }
  })

  it('renders all status icons without error', () => {
    const statuses = ['pending', 'queued', 'running', 'rendering', 'completed', 'done', 'failed', 'active']
    for (const s of statuses) {
      const { unmount } = render(<FlowCanvasNode {...{ ...baseProps, id: `s-${s}`, status: s }} />)
      unmount()
    }
    // No crash = pass
  })
})

/* ── FlowCanvasEdges ────────────────────────────────────────────────── */

describe('FlowCanvasEdges', () => {
  const nodePositions = {
    a: { pos: { x: 0, y: 0 }, size: { w: 200, h: 80 } },
    b: { pos: { x: 80, y: 300 }, size: { w: 200, h: 80 } },
  }

  it('renders nothing with no edges', () => {
    const { container } = render(<FlowCanvasEdges edges={[]} nodePositions={nodePositions} />)
    expect(container.innerHTML).toBe('')
  })

  it('renders SVG for edges', () => {
    const edges: FlowEdge[] = [{ id: 'a→b', source: 'a', target: 'b' }]
    const { container } = render(<FlowCanvasEdges edges={edges} nodePositions={nodePositions} />)
    const svg = container.querySelector('svg')
    expect(svg).toBeDefined()
    expect(svg!.querySelector('path')).toBeDefined()
  })

  it('renders arrowhead', () => {
    const edges: FlowEdge[] = [{ id: 'a→b', source: 'a', target: 'b' }]
    const { container } = render(<FlowCanvasEdges edges={edges} nodePositions={nodePositions} />)
    expect(container.querySelector('polygon')).toBeDefined()
  })

  it('skips edges with missing source/target', () => {
    const edges: FlowEdge[] = [
      { id: 'a→b', source: 'a', target: 'b' },
      { id: 'missing', source: 'nonexistent', target: 'b' },
    ]
    const { container } = render(<FlowCanvasEdges edges={edges} nodePositions={nodePositions} />)
    // Each valid edge renders 2 paths (glow + main)
    expect(container.querySelectorAll('path').length).toBe(2)
  })

  it('renders edge label', () => {
    const edges: FlowEdge[] = [{ id: 'a→b', source: 'a', target: 'b', label: 'routes to' }]
    const { container } = render(<FlowCanvasEdges edges={edges} nodePositions={nodePositions} />)
    expect(container.querySelector('text')).toBeDefined()
  })
})

/* ── layoutNodes / buildFlowEdges ───────────────────────────────────── */

describe('layoutNodes', () => {
  it('returns empty for empty input', () => {
    expect(layoutNodes([], [])).toEqual([])
  })

  it('positions single node at padding offset', () => {
    const nodes: FlowNode[] = [{ id: 'a', type: 'job', label: 'A', status: 'done' }]
    const result = layoutNodes(nodes, [])
    expect(result).toHaveLength(1)
    expect(result[0].pos.x).toBe(80) // padding
    expect(result[0].pos.y).toBe(80)
  })

  it('creates levels for parent-child chain', () => {
    const nodes: FlowNode[] = [
      { id: 'root', type: 'job', label: 'Root', status: 'done' },
      { id: 'child', type: 'scene', label: 'Child', status: 'pending', parentId: 'root' },
    ]
    const edges = buildFlowEdges(nodes)
    const result = layoutNodes(nodes, edges)
    expect(result).toHaveLength(2)
    const root = result.find(n => n.id === 'root')!
    const child = result.find(n => n.id === 'child')!
    expect(child.pos.y).toBeGreaterThan(root.pos.y) // child below root
  })

  it('spreads multiple nodes in same level', () => {
    const nodes: FlowNode[] = [
      { id: 'a', type: 'scene', label: 'A', status: 'done' },
      { id: 'b', type: 'scene', label: 'B', status: 'done' },
      { id: 'c', type: 'scene', label: 'C', status: 'done' },
    ]
    const result = layoutNodes(nodes, [])
    expect(result).toHaveLength(3)
    // Each node should have different x positions
    const xs = result.map(n => n.pos.x)
    expect(new Set(xs).size).toBe(3)
  })

  it('handles complex DAG with multiple levels', () => {
    const nodes: FlowNode[] = [
      { id: 'r', type: 'job', label: 'Root', status: 'done' },
      { id: 's1', type: 'stage', label: 'Stage 1', status: 'active', parentId: 'r' },
      { id: 's2', type: 'stage', label: 'Stage 2', status: 'pending', parentId: 'r' },
      { id: 'sa1', type: 'subagent', label: 'Agent 1', status: 'running', parentId: 's1' },
      { id: 'sc1', type: 'scene', label: 'Scene 1', status: 'rendering', parentId: 's1' },
    ]
    const edges = buildFlowEdges(nodes)
    const result = layoutNodes(nodes, edges)
    expect(result).toHaveLength(5)

    const byId = new Map(result.map(n => [n.id, n]))
    expect(byId.get('r')!.pos.y).toBe(80) // level 0
    expect(byId.get('s1')!.pos.y).toBe(260) // level 1: padding + (80+100)
    expect(byId.get('s2')!.pos.y).toBe(260)
  })
})

describe('buildFlowEdges', () => {
  it('creates edges from parentId', () => {
    const nodes: FlowNode[] = [
      { id: 'a', type: 'job', label: 'A', status: 'done' },
      { id: 'b', type: 'scene', label: 'B', status: 'pending', parentId: 'a' },
    ]
    const edges = buildFlowEdges(nodes)
    expect(edges).toHaveLength(1)
    expect(edges[0]).toEqual({ id: 'a→b', source: 'a', target: 'b' })
  })

  it('handles nodes without parentId', () => {
    const nodes: FlowNode[] = [
      { id: 'a', type: 'job', label: 'A', status: 'done' },
    ]
    expect(buildFlowEdges(nodes)).toEqual([])
  })
})

/* ── FlowJobCanvas ──────────────────────────────────────────────────── */

describe('FlowJobCanvas', () => {
  const mockJob = getJobs()[0] // job_001 - running job with subagents + scenes

  it('renders job title on canvas', () => {
    render(<FlowJobCanvas job={mockJob} />)
    expect(screen.getByText(mockJob.title)).toBeDefined()
  })

  it('renders stage label', () => {
    render(<FlowJobCanvas job={mockJob} />)
    expect(screen.getByText(/Stage/)).toBeDefined()
  })

  it('renders subagent nodes', () => {
    render(<FlowJobCanvas job={mockJob} />)
    for (const sa of mockJob.subagents) {
      expect(screen.getByText(sa.name)).toBeDefined()
    }
  })

  it('renders scene nodes', () => {
    render(<FlowJobCanvas job={mockJob} />)
    for (const sc of mockJob.scenes) {
      expect(screen.getByText(sc.id)).toBeDefined()
    }
  })

  it('renders zoom controls', () => {
    render(<FlowJobCanvas job={mockJob} />)
    expect(screen.getByLabelText('Zoom out')).toBeDefined()
  })

  it('handles empty subagents + scenes', () => {
    const minimalJob = { ...mockJob, subagents: [], scenes: [] }
    const { container } = render(<FlowJobCanvas job={minimalJob} />)
    expect(container.querySelector('[role="button"]')).toBeDefined()
  })
})

/* ── FlowSceneCanvas ────────────────────────────────────────────────── */

describe('FlowSceneCanvas', () => {
  it('renders root node with scene count', () => {
    render(<FlowSceneCanvas scenes={[]} />)
    expect(screen.getByText(/Scene Graph/)).toBeDefined()
  })
})
