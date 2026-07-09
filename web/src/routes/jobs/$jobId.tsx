import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowLeft, RefreshCw } from "lucide-react";
import { getJob } from "@/data/mock";
import { useSSE } from "@/hooks/useSSE";
import { JobStatusBadge } from "@/components/jobs/JobStatusBadge";
import { Progress } from "@/components/ui/progress";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { StageTimeline } from "@/components/job-detail/StageTimeline";
import { EventLog } from "@/components/job-detail/EventLog";
import { SubagentCard } from "@/components/job-detail/SubagentCard";
import { SceneTable } from "@/components/job-detail/SceneTable";

export const Route = createFileRoute("/jobs/$jobId")({
  component: JobDetailPage,
});

function JobDetailPage() {
  const { jobId } = Route.useParams();
  const job = getJob(jobId);
  const { events, connected } = useSSE(jobId, { enabled: job?.status === "running" });

  if (!job) {
    return (
      <div className="mx-auto max-w-5xl py-16 text-center">
        <h2 className="text-xl font-bold">Job not found</h2>
        <p className="mt-2 text-sm text-muted-foreground">No job with ID "{jobId}" exists.</p>
        <Link to="/jobs" className="mt-4 inline-flex items-center gap-1 text-sm text-primary hover:underline">
          <ArrowLeft className="h-4 w-4" /> Back to Jobs
        </Link>
      </div>
    );
  }

  const allEvents = [...job.events, ...events];

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <Link to="/jobs" className="mb-3 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" /> Back to Jobs
        </Link>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">{job.title}</h1>
            <p className="mt-1 text-sm text-muted-foreground">{job.id} · Created {new Date(job.createdAt).toLocaleString()}</p>
          </div>
          <div className="flex items-center gap-2">
            <JobStatusBadge status={job.status} />
            <Badge variant="outline">{job.stage}</Badge>
          </div>
        </div>
      </div>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-4">
            <span className="text-sm font-medium">{job.progressPct}%</span>
            <Progress value={job.progressPct} className="flex-1" />
            {connected && (
              <span className="flex items-center gap-1 text-xs text-emerald-500">
                <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-500" /> SSE live
              </span>
            )}
          </div>
          {job.error && <p className="mt-2 text-sm text-destructive">{job.error}</p>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle className="text-sm">Stage Timeline</CardTitle></CardHeader>
        <CardContent><StageTimeline job={job} /></CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle className="text-sm">Event Log</CardTitle></CardHeader>
          <CardContent><EventLog events={allEvents} /></CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-sm">Subagents ({job.subagents.length})</CardTitle></CardHeader>
          <CardContent>
            {job.subagents.length === 0 ? (
              <p className="py-4 text-sm text-muted-foreground italic">No subagents spawned yet.</p>
            ) : (
              <div className="space-y-2">{job.subagents.map((sa) => <SubagentCard key={sa.id} subagent={sa} />)}</div>
            )}
          </CardContent>
        </Card>
      </div>

      <Separator />

      <Card>
        <CardHeader><CardTitle className="text-sm">Scenes</CardTitle></CardHeader>
        <CardContent><SceneTable scenes={job.scenes} /></CardContent>
      </Card>

      <div className="flex gap-3">
        <button onClick={() => window.location.reload()} className="inline-flex items-center gap-1 rounded-md border px-3 py-1.5 text-sm hover:bg-accent">
          <RefreshCw className="h-4 w-4" /> Refresh
        </button>
        <span className="self-center text-xs text-muted-foreground">{allEvents.length} events captured</span>
      </div>
    </div>
  );
}
