import type { JobStatus } from '@/types/job'
import { Badge } from '@/components/ui/badge'

const VARIANT: Record<JobStatus, 'success' | 'warning' | 'default' | 'destructive' | 'secondary'> = {
  completed: 'success',
  running: 'default',
  queued: 'secondary',
  failed: 'destructive',
  cancelled: 'outline',
} as Record<JobStatus, any>

const LABEL: Record<JobStatus, string> = {
  completed: 'Completed', running: 'Running', queued: 'Queued', failed: 'Failed', cancelled: 'Cancelled',
}

export function JobStatusBadge({ status }: { status: JobStatus }) {
  return <Badge variant={VARIANT[status]}>{LABEL[status]}</Badge>
}
