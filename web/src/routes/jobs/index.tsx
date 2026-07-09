import { createFileRoute } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import { PlusCircle } from "lucide-react";
import { useEffect, useState } from "react";
import type { Job, JobStatus } from "@/types/job";
import { fetchJobs } from "@/lib/api";
import { JobCard } from "@/components/jobs/JobCard";
import { Badge } from "@/components/ui/badge";

const FILTERS: (JobStatus | "all")[] = ["all", "running", "queued", "completed", "failed"];

export const Route = createFileRoute("/jobs/")({
  component: JobsPage,
});

function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<JobStatus | "all">("all");

  useEffect(() => {
    fetchJobs().then((data) => {
      setJobs(data);
      setLoading(false);
    });
  }, []);

  const filtered = filter === "all" ? jobs : jobs.filter((j) => j.status === filter);

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Jobs</h1>
          {!loading && (
            <p className="text-sm text-muted-foreground">
              {jobs.length} total · {jobs.filter((j) => j.status === "running").length} active
            </p>
          )}
        </div>
        <Button><PlusCircle className="mr-1 h-4 w-4" /> New Job</Button>
      </div>
      <div className="flex gap-2 overflow-x-auto">
        {FILTERS.map((f) => (
          <button key={f} onClick={() => setFilter(f)}>
            <Badge variant={filter === f ? "default" : "outline"} className="cursor-pointer capitalize">
              {f === "all" ? "All" : f}
            </Badge>
          </button>
        ))}
      </div>
      {loading ? (
        <div className="rounded-lg border p-8 text-center text-sm text-muted-foreground">Loading jobs…</div>
      ) : filtered.length === 0 ? (
        <div className="rounded-lg border p-8 text-center text-sm text-muted-foreground">No jobs yet.</div>
      ) : (
        <div className="space-y-3">{filtered.map((job) => <JobCard key={job.id} job={job} />)}</div>
      )}
    </div>
  );
}
