import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowLeft, BarChart3, GitBranch, Film, FileText } from "lucide-react";
import { getReport, getProvenance, getSceneReports } from "@/data/mock";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { ReportSummaryTab } from "@/components/reports/ReportSummary";
import { ReportProvenanceTab } from "@/components/reports/ReportProvenance";
import { ReportScenesTab } from "@/components/reports/ReportScenes";

export const Route = createFileRoute("/reports/$reportName")({
  component: ReportDetailPage,
});

function ReportDetailPage() {
  const { reportName } = Route.useParams();
  const report = getReport(reportName);
  const provenance = getProvenance(reportName);
  const scenes = getSceneReports(reportName);

  if (!report) {
    return (
      <div className="mx-auto max-w-4xl py-16 text-center">
        <FileText className="mx-auto mb-3 h-10 w-10 text-muted-foreground/50" />
        <h2 className="text-xl font-bold">Report not found</h2>
        <p className="mt-2 text-sm text-muted-foreground">No report with name "{reportName}" exists.</p>
        <Link to="/reports" className="mt-4 inline-flex items-center gap-1 text-sm text-primary hover:underline">
          <ArrowLeft className="h-4 w-4" /> Back to Reports
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <Link to="/reports" className="mb-3 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" /> Back to Reports
        </Link>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">{reportName}</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              {report.engine_mix.join(", ")} · {report.scenes_summary.count} scenes ·{" "}
              {report.render_format.width}×{report.render_format.height} ·{" "}
              {report.render_format.fps}fps
            </p>
          </div>
          <Badge variant="outline" className="text-xs">
            <span className="mr-1">v</span>{report.version}
          </Badge>
        </div>
      </div>

      <Tabs defaultValue="summary" className="w-full">
        <TabsList>
          <TabsTrigger value="summary" className="gap-1.5">
            <BarChart3 className="h-4 w-4" /> Summary
          </TabsTrigger>
          <TabsTrigger value="provenance" className="gap-1.5" disabled={!provenance}>
            <GitBranch className="h-4 w-4" /> Provenance
          </TabsTrigger>
          <TabsTrigger value="scenes" className="gap-1.5">
            <Film className="h-4 w-4" /> Scenes ({scenes.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="summary" className="mt-4">
          <ReportSummaryTab report={report} />
        </TabsContent>

        <TabsContent value="provenance" className="mt-4">
          {provenance ? (
            <ReportProvenanceTab provenance={provenance} />
          ) : (
            <p className="py-8 text-center text-sm text-muted-foreground">No provenance graph available for this report.</p>
          )}
        </TabsContent>

        <TabsContent value="scenes" className="mt-4">
          <ReportScenesTab scenes={scenes} />
        </TabsContent>
      </Tabs>

      <div className="rounded-lg border bg-muted/30 p-3">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <FileText className="h-3.5 w-3.5" />
          <span>Report timestamp:</span>
          <code className="rounded bg-muted px-1">{report.report_timestamp}</code>
          <span className="ml-auto">Content hash: <code className="rounded bg-muted px-1">{report.content_hash || "—"}</code></span>
        </div>
      </div>
    </div>
  );
}
