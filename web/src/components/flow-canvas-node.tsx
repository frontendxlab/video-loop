import { type CSSProperties } from 'react'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import { Check, Clock, Loader2, X, AlertTriangle } from 'lucide-react'

interface FlowCanvasNodeProps {
  id: string
  label: string
  type: 'job' | 'stage' | 'subagent' | 'scene'
  status: string
  progress?: number
  engine?: string
  kind?: string
  error?: string | null
  x: number
  y: number
  width?: number
  height?: number
  selected?: boolean
  onSelect?: (id: string) => void
}

const STATUS_ICON: Record<string, React.ReactNode> = {
  pending: <Clock className="h-3.5 w-3.5 text-muted-foreground" />,
  queued: <Clock className="h-3.5 w-3.5 text-muted-foreground" />,
  running: <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />,
  rendering: <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />,
  completed: <Check className="h-3.5 w-3.5 text-emerald-500" />,
  done: <Check className="h-3.5 w-3.5 text-emerald-500" />,
  failed: <X className="h-3.5 w-3.5 text-destructive" />,
  active: <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />,
}

const TYPE_STYLES: Record<string, string> = {
  job: 'border-blue-500/40 bg-blue-500/10',
  stage: 'border-amber-500/40 bg-amber-500/10',
  subagent: 'border-purple-500/40 bg-purple-500/10',
  scene: 'border-emerald-500/40 bg-emerald-500/10',
}

const TYPE_LABELS: Record<string, string> = {
  job: 'JOB',
  stage: 'STAGE',
  subagent: 'AGENT',
  scene: 'SCENE',
}

export function FlowCanvasNode({
  id,
  label,
  type,
  status,
  progress,
  engine,
  kind,
  error,
  x,
  y,
  width = 200,
  height = 80,
  selected,
  onSelect,
}: FlowCanvasNodeProps) {
  const icon = STATUS_ICON[status] ?? <Clock className="h-3.5 w-3.5 text-muted-foreground" />

  return (
    <div
      data-stop-propagation
      role="button"
      tabIndex={0}
      aria-label={`${type} ${label}`}
      onClick={() => onSelect?.(id)}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect?.(id) } }}
      className={cn(
        'absolute rounded-lg border-2 bg-card px-3 py-2.5 shadow-sm transition-shadow hover:shadow-md cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
        TYPE_STYLES[type],
        selected ? 'ring-2 ring-primary shadow-md' : '',
        error ? 'border-destructive/60' : '',
      )}
      style={{
        left: x,
        top: y,
        width,
        minHeight: height,
      } as CSSProperties}
    >
      {/* Header */}
      <div className="flex items-center gap-1.5 mb-1">
        <span className="text-[9px] font-semibold uppercase tracking-wider text-muted-foreground">
          {TYPE_LABELS[type] ?? type}
        </span>
        <span className="ml-auto">{icon}</span>
      </div>

      {/* Label */}
      <div className="text-xs font-medium leading-tight truncate mb-1" title={label}>
        {label}
      </div>

      {/* Progress bar */}
      {progress != null && (
        <div className="h-1 rounded-full bg-secondary overflow-hidden mb-1.5">
          <div
            className={cn(
              'h-full rounded-full transition-all',
              status === 'failed' ? 'bg-destructive' : 'bg-primary',
            )}
            style={{ width: `${progress}%` }}
          />
        </div>
      )}

      {/* Badge row */}
      <div className="flex flex-wrap gap-1">
        {engine && (
          <Badge variant="outline" className="text-[8px] px-1 py-0 h-auto leading-normal">
            {engine}
          </Badge>
        )}
        {kind && (
          <Badge variant="secondary" className="text-[8px] px-1 py-0 h-auto leading-normal">
            {kind}
          </Badge>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-1 mt-1 text-[9px] text-destructive">
          <AlertTriangle className="h-3 w-3 flex-shrink-0" />
          <span className="truncate">{error}</span>
        </div>
      )}
    </div>
  )
}
