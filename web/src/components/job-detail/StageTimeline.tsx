import type { Job, JobStage } from '@/types/job'
import { STAGE_LABELS, STAGE_ORDER } from '@/types/job'
import { cn } from '@/lib/utils'
import { Check, Loader2, X } from 'lucide-react'

interface Props { job: Job }

function stageStatus(job: Job, stage: JobStage): 'done' | 'active' | 'pending' | 'failed' {
  if (job.status === 'failed' && stage === job.stage) return 'failed'
  if (job.status === 'completed') return 'done'
  const idx = STAGE_ORDER.indexOf(stage)
  const cur = STAGE_ORDER.indexOf(job.stage)
  if (idx < cur) return 'done'
  if (idx === cur) return 'active'
  return 'pending'
}

const ICON: Record<string, React.ReactNode> = {
  done: <Check className="h-4 w-4" />,
  active: <Loader2 className="h-4 w-4 animate-spin" />,
  failed: <X className="h-4 w-4" />,
  pending: null,
}

export function StageTimeline({ job }: Props) {
  return (
    <nav aria-label="Stage timeline">
      <ol className="flex flex-wrap gap-1 sm:flex-nowrap">
        {STAGE_ORDER.map((stage) => {
          const s = stageStatus(job, stage)
          return (
            <li key={stage} className="flex items-center gap-1">
              <span className={cn(
                'inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium transition-colors',
                s === 'done' && 'bg-emerald-600/20 text-emerald-400',
                s === 'active' && 'bg-primary/20 text-primary',
                s === 'failed' && 'bg-destructive/20 text-destructive',
                s === 'pending' && 'bg-secondary text-muted-foreground',
              )}>
                {ICON[s]}
                {STAGE_LABELS[stage]}
              </span>
              {STAGE_ORDER.indexOf(stage) < STAGE_ORDER.length - 1 && (
                <span className="hidden h-px w-3 bg-border sm:block" />
              )}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
