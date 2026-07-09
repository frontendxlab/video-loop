import { createFileRoute, Link } from "@tanstack/react-router";
import { getReports } from "@/data/mock";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BarChart3, FileText, AlertTriangle, CheckCircle2, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ReportSummary } from "@/types/report";

export const Route = createFileRoute("/reports/")({
  component: ReportsIndexPage,
});

function VerdictBadge({ verdict }: { verdict: string }) {
  const map: Record<string, { label: string; variant: "success" | "warning" | "destructive" | "outline"; icon: typeof CheckCircle2 }> = {
    pass: { label: "Pass", variant: "success", icon: CheckCircle2 },
    warn: { label: "Warn", variant: "warning", icon: AlertTriangle },
    fail: { label: "Fail", variant: "destructive", icon: XCircle },
  };
  const m = map[verdict] || { label: verdict, variant: "outline" as const, icon: FileText };
  const Icon = m.icon;
  return (
    <Badge variant={m.variant} className="gap-1">
      <Icon className="h-3 w-3" /> {m.label}
    </Badge>
  );
}

function ReportCard({ report }: { report: ReportSummary }) {
  const framesToSec = (f: number) => `${(f / 30).toFixed(1)}s`;
  return (
    <Link to="/reports/$reportName" params={{ reportName: report.name }}>
      <Card className="transition-colors hover:bg-accent/50">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-3">
            <CardTitle className="text-sm font-medium leading-tight">{report.name}</CardTitle>
            <VerdictBadge verdict={report.policy_verdict} />
          </div>
        </CardHeader>
        <CardContent className="space-y-2 text-xs text-muted-foreground">
          <div className="flex flex-wrap gap-x-4 gap-y-1">
            <span>Hash: <code className="rounded bg-muted px-1 text-[10px]">{report.content_hash || "—"}</code></span>
            <span>{report.scenes_count} scenes</span>
            <span>{framesToSec(report.total_duration_frames)}</span>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {report.engine_mix.map((e) => (
              <Badge key={e} variant="outline" className="text-[10px]">{e}</Badge>
            ))}
            {report.has_provenance && (
              <Badge variant="secondary" className="text-[10px]">provenance</Badge>
            )}
          </div>
          <div className="flex gap-4">
            <span>L0: <span className={cn(report.l0_status === "pass" ? "text-emerald-500" : report.l0_status === "warn" ? "text-amber-500" : "text-red-500")}>{report.l0_status}</span></span>
            <span>L1: {report.l1_passed === null ? "?" : report.l1_passed ? "✓" : "✗"}</span>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}

function ReportsIndexPage() {
  const reports = getReports();

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Reports</h1>
        <p className="text-sm text-muted-foreground">Video reports, provenance, and per-scene results</p>
      </div>

      {reports.length === 0 ? (
        <div className="rounded-lg border p-12 text-center text-sm text-muted-foreground">
          <BarChart3 className="mx-auto mb-3 h-8 w-8 text-muted-foreground/50" />
          <p>No reports yet. Reports appear here after video review completes.</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {reports.map((r) => <ReportCard key={r.name} report={r} />)}
        </div>
      )}
    </div>
  );
}
