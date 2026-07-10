import type { FlowEdge, Position, Size } from '@/types/canvas'

interface FlowCanvasEdgesProps {
  edges: FlowEdge[]
  /** Map of node id → position + size */
  nodePositions: Record<string, { pos: Position; size: Size }>
  /** Color for edge lines */
  color?: string
}

/**
 * Draws bezier-curved edges between nodes on SVG overlay.
 * SVG positioned absolutely over the canvas at same origin.
 */
export function FlowCanvasEdges({
  edges,
  nodePositions,
  color = 'rgb(148 163 184 / 0.5)',
}: FlowCanvasEdgesProps) {
  if (edges.length === 0) return null

  // Compute bounding box for SVG viewport
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity
  for (const { pos, size } of Object.values(nodePositions)) {
    minX = Math.min(minX, pos.x)
    minY = Math.min(minY, pos.y)
    maxX = Math.max(maxX, pos.x + size.w)
    maxY = Math.max(maxY, pos.y + size.h)
  }
  if (!isFinite(minX)) return null

  const pad = 50
  const viewX = minX - pad
  const viewY = minY - pad
  const viewW = maxX - minX + pad * 2
  const viewH = maxY - minY + pad * 2

  return (
    <svg
      className="absolute inset-0 pointer-events-none"
      style={{ left: viewX, top: viewY, width: viewW, height: viewH, overflow: 'visible' }}
    >
      {edges.map((edge) => {
        const src = nodePositions[edge.source]
        const tgt = nodePositions[edge.target]
        if (!src || !tgt) return null

        // Coordinates relative to SVG origin (viewX, viewY)
        const x1 = src.pos.x + src.size.w / 2 - viewX
        const y1 = src.pos.y + src.size.h - viewY
        const x2 = tgt.pos.x + tgt.size.w / 2 - viewX
        const y2 = tgt.pos.y - viewY

        const cy = (y1 + y2) / 2
        const path = `M ${x1} ${y1} C ${x1} ${cy}, ${x2} ${cy}, ${x2} ${y2}`

        return (
          <g key={edge.id}>
            {/* Glow */}
            <path d={path} fill="none" stroke={color} strokeWidth={2} strokeOpacity={0.15} strokeLinecap="round" />
            {/* Main line */}
            <path d={path} fill="none" stroke={color} strokeWidth={1.5} strokeLinecap="round" />
            {/* Arrowhead at target top */}
            <polygon
              points="-5,-6 5,-6 0,0"
              fill={color}
              transform={`translate(${x2},${y2})`}
            />
            {edge.label && (
              <text
                x={(x1 + x2) / 2}
                y={cy - 4}
                textAnchor="middle"
                fill="currentColor"
                className="fill-muted-foreground text-[8px]"
              >
                {edge.label}
              </text>
            )}
          </g>
        )
      })}
    </svg>
  )
}
