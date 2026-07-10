import { type ReactNode } from 'react'
import { cn } from '@/lib/utils'
import { useCanvasPan } from '@/hooks/useCanvasPan'

interface FlowCanvasProps {
  children?: ReactNode
  className?: string
  /** Dotted background spacing in px at scale=1 */
  dotSpacing?: number
  /** Dot color */
  dotColor?: string
  /** Dot radius */
  dotRadius?: number
  /** Show zoom level indicator */
  showZoom?: boolean
  /** Reset button */
  showReset?: boolean
}

export function FlowCanvas({
  children,
  className,
  dotSpacing = 24,
  dotColor = 'rgb(148 163 184 / 0.3)',
  dotRadius = 1.5,
  showZoom = true,
  showReset = true,
}: FlowCanvasProps) {
  const { transform, handlers, reset, zoomTo, scale } = useCanvasPan()

  return (
    <div
      className={cn('relative overflow-hidden bg-secondary/20 select-none', className)}
      {...handlers}
    >
      {/* Dotted background layer */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage: `radial-gradient(circle, ${dotColor} ${dotRadius}px, transparent ${dotRadius}px)`,
          backgroundSize: `${dotSpacing}px ${dotSpacing}px`,
          transform,
        }}
      />

      {/* Transform layer for nodes + edges */}
      <div
        className="absolute inset-0"
        style={{ transform, transformOrigin: '0 0' }}
      >
        {children}
      </div>

      {/* Controls */}
      {(showZoom || showReset) && (
        <div className="absolute bottom-3 right-3 flex items-center gap-2 rounded-lg border bg-background/80 px-2.5 py-1.5 text-xs backdrop-blur-sm">
          {showZoom && (
            <span className="text-muted-foreground">{Math.round(scale * 100)}%</span>
          )}
          {showZoom && (
            <>
              <button
                type="button"
                onClick={() => zoomTo(scale * 0.8)}
                className="rounded px-1.5 py-0.5 hover:bg-accent transition-colors"
                aria-label="Zoom out"
              >
                −
              </button>
              <button
                type="button"
                onClick={() => zoomTo(scale * 1.25)}
                className="rounded px-1.5 py-0.5 hover:bg-accent transition-colors"
                aria-label="Zoom in"
              >
                +
              </button>
            </>
          )}
          {showReset && (
            <button
              type="button"
              onClick={reset}
              className="rounded px-1.5 py-0.5 hover:bg-accent transition-colors"
              aria-label="Reset view"
            >
              ⌂
            </button>
          )}
        </div>
      )}
    </div>
  )
}
