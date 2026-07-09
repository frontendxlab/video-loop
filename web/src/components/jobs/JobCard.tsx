import { Link } from '@tanstack/react-router'
import type { Job } from '@/types/job'
import { Card, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { JobStatusBadge } from '@/components/jobs/JobStatusBadge'

export function JobCard({ job }: { job: Job }) {
  const ts = new Date(job.createdAt).toLocaleString()
  return (
    <Link to="/jobs/$jobId" params={{ jobId: job.id }} className="block">
      <Card className="transition-colors hover:border-primary/50">
        <CardContent className="p-4">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <h3 className="truncate font-medium">{job.title}</h3>
                <JobStatusBadge status={job.status} />
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                {job.stage} · {job.subagents.length} subagents · {ts}
              </p>
            </div>
            <div className="flex flex-col items-end gap-1">
              <span className="text-sm font-medium">{job.progressPct}%</span>
              <Progress value={job.progressPct} className="w-20" />
            </div>
          </div>
          {job.error && <p className="mt-2 text-xs text-destructive">{job.error}</p>}
        </CardContent>
      </Card>
    </Link>
  )
}
