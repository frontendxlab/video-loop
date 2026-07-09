import type { Subagent } from '@/types/job'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { Check, Clock, Loader2, X } from 'lucide-react'

interface Props { subagent: Subagent }

const STATUS_ICON: Record<string, React.ReactNode> = {
  pending: <Clock className="h-4 w-4 text-muted-foreground" />,
  running: <Loader2 className="h-4 w-4 animate-spin text-primary" />,
  completed: <Check className="h-4 w-4 text-emerald-400" />,
  failed: <X className="h-4 w-4 text-destructive" />,
}

export function SubagentCard({ subagent }: Props) {
  return (
    <Card className={cn(subagent.status === 'failed' && 'border-destructive/50')}>
      <CardContent className="flex items-start gap-3 p-4">
        <div className="mt-0.5">{STATUS_ICON[subagent.status]}</div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="font-medium">{subagent.name}</span>
            <Badge variant="outline" className="text-[10px]">{subagent.engine}</Badge>
          </div>
          <p className="mt-0.5 text-xs text-muted-foreground">{subagent.task}</p>
          <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
            {subagent.startedAt && <span>Started {new Date(subagent.startedAt).toLocaleTimeString()}</span>}
            {subagent.durationMs != null && <span>{(subagent.durationMs / 1000).toFixed(1)}s</span>}
            {subagent.tokens > 0 && <span>{subagent.tokens} tokens</span>}
          </div>
          {subagent.error && <p className="mt-1 text-xs text-destructive">{subagent.error}</p>}
        </div>
      </CardContent>
    </Card>
  )
}
