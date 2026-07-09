import type { VideoReport } from "@/types/report";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";

interface Props { report: VideoReport }

function SeverityBar({ counts }: { counts: { high: number; medium: number; low: number } }) {
  const total = counts.high + counts.medium + counts.low;
  if (total === 0) return <span className="text-xs text-muted-foreground">none</span>;
  return (
    <div className="flex h-2 w-full max-w-[200px] overflow-hidden rounded-full bg-muted">
      {counts.high > 0 && <div className="bg-red-500 transition-all" style={{ width: `${(counts.high / total) * 100}%` }} title={`${counts.high} high`} />}
      {counts.medium > 0 && <div className="bg-amber-500 transition-all" style={{ width: `${(counts.medium / total) * 100}%` }} title={`${counts.medium} medium`} />}
      {counts.low > 0 && <div className="bg-blue-400 transition-all" style={{ width: `${(counts.low / total) * 100}%` }} title={`${counts.low} low`} />}
    </div>
  );
}

function StatusDot({ passed }: { passed: boolean }) {
  return <span className={cn("inline-block h-2 w-2 rounded-full", passed ? "bg-emerald-500" : "bg-red-500")} />;
}

export function ReportSummaryTab({ report }: Props) {
  const fmt = report.render_format;
  return (
    <div className="space-y-4">
      {/* Render format */}
      <Card>
        <CardHeader><CardTitle className="text-sm">Render Format</CardTitle></CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-2 text-sm sm:grid-cols-3">
            <div><span className="text-muted-foreground">Resolution</span><p>{fmt.width}×{fmt.height}</p></div>
            <div><span className="text-muted-foreground">FPS</span><p>{fmt.fps}</p></div>
            <div><span className="text-muted-foreground">Pixel</span><p>{fmt.pixel_format}</p></div>
            <div><span className="text-muted-foreground">Video</span><p>{fmt.video_codec}</p></div>
            <div><span className="text-muted-foreground">Audio</span><p>{fmt.audio_codec}</p></div>
          </div>
        </CardContent>
      </Card>

      {/* Scenes summary */}
      <Card>
        <CardHeader><CardTitle className="text-sm">Scenes</CardTitle></CardHeader>
        <CardContent>
          <div className="mb-3 grid grid-cols-3 gap-2 text-sm">
            <div><span className="text-muted-foreground">Count</span><p className="text-lg font-semibold">{report.scenes_summary.count}</p></div>
            <div><span className="text-muted-foreground">Engines</span><p className="text-lg font-semibold">{Object.keys(report.scenes_summary.engines).length}</p></div>
            <div><span className="text-muted-foreground">Duration</span><p className="text-lg font-semibold">{(report.scenes_summary.total_duration_frames / fmt.fps).toFixed(1)}s</p></div>
          </div>
          {report.scenes_summary.scenes && report.scenes_summary.scenes.length > 0 && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>#</TableHead>
                  <TableHead>Engine</TableHead>
                  <TableHead className="text-right">Frames</TableHead>
                  <TableHead className="text-right">Time</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {report.scenes_summary.scenes.map((s) => (
                  <TableRow key={s.index}>
                    <TableCell>{s.index}</TableCell>
                    <TableCell><Badge variant="outline" className="text-[10px]">{s.engine}</Badge></TableCell>
                    <TableCell className="text-right">{s.duration_frames}</TableCell>
                    <TableCell className="text-right">{(s.duration_frames / fmt.fps).toFixed(1)}s</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* L0 Summary */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-sm">L0 — Mixed Engine Review</CardTitle>
          <Badge variant={report.l0_summary.passed ? "success" : "destructive"}>{report.l0_summary.status}</Badge>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm">
            <span><StatusDot passed={report.l0_summary.passed} /> {report.l0_summary.total_issues} issues</span>
            <span className="text-muted-foreground">{report.l0_summary.sampled_frames} sampled / {report.l0_summary.total_frames} total</span>
            <span className="text-muted-foreground">{report.l0_summary.duration_seconds.toFixed(1)}s</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-muted-foreground">Severity distribution:</span>
            <SeverityBar counts={report.l0_summary.severity_counts} />
            <span className="text-xs text-muted-foreground">
              {report.l0_summary.severity_counts.high}h / {report.l0_summary.severity_counts.medium}m / {report.l0_summary.severity_counts.low}l
            </span>
          </div>
          {report.l0_summary.issues.length > 0 && (
            <div className="space-y-1">
              {report.l0_summary.issues.map((iss, i) => (
                <div key={i} className="flex items-start gap-2 rounded-md bg-muted/50 p-2 text-xs">
                  <Badge variant={iss.severity === "high" ? "destructive" : iss.severity === "medium" ? "warning" : "outline"} className="shrink-0 text-[9px]">{iss.severity}</Badge>
                  <span className="text-muted-foreground">{iss.type}{iss.detail ? `: ${iss.detail}` : ""}</span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* L1 Summary */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-sm">L1 — Frame Integrity</CardTitle>
          <StatusDot passed={report.l1_summary.passed} />
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 text-sm">
            <span>{report.l1_summary.total_issues} issues</span>
            <span className="text-muted-foreground">{report.l1_summary.total_frames} frames</span>
          </div>
          {report.l1_summary.issues.length > 0 && (
            <div className="mt-2 space-y-1">
              {report.l1_summary.issues.map((iss, i) => (
                <div key={i} className="rounded-md bg-muted/50 p-2 text-xs text-muted-foreground">
                  {iss.type}{iss.detail ? `: ${iss.detail}` : ""}{iss.start !== undefined ? ` [${iss.start}–${iss.end}]` : ""}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* L2 Layout Overlap */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-sm">L2b — Layout Overlap</CardTitle>
          <Badge variant={report.l2_layout_overlap_summary.passed ? "success" : "destructive"}>{report.l2_layout_overlap_summary.status}</Badge>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center gap-3 text-sm">
            <span>{report.l2_layout_overlap_summary.total_issues} issues</span>
            {report.l2_layout_overlap_summary.total_issues > 0 && (
              <>
                <SeverityBar counts={report.l2_layout_overlap_summary.severity_counts} />
                <span className="text-xs text-muted-foreground">
                  {report.l2_layout_overlap_summary.severity_counts.high}h / {report.l2_layout_overlap_summary.severity_counts.medium}m / {report.l2_layout_overlap_summary.severity_counts.low}l
                </span>
              </>
            )}
          </div>
          {report.l2_layout_overlap_summary.issues.length > 0 && (
            <div className="space-y-1">
              {report.l2_layout_overlap_summary.issues.map((iss, i) => (
                <div key={i} className="rounded-md bg-muted/50 p-2 text-xs text-muted-foreground">
                  {iss.type}{iss.detail ? `: ${iss.detail}` : ""}{iss.element ? ` (${iss.element})` : ""}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Coherence summary */}
      {report.coherence_summary && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-sm">Coherence</CardTitle>
            <Badge variant={report.coherence_summary.coherent ? "success" : "destructive"}>
              {report.coherence_summary.coherent ? "Coherent" : "Issues"}
            </Badge>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex gap-4">
              <span>Arc: {report.coherence_summary.has_complete_arc ? "✓" : "✗"}</span>
              <span>Phase order: {report.coherence_summary.phase_order_valid ? "✓" : "✗"}</span>
              <span>{report.coherence_summary.total_issues} issues</span>
            </div>
            {report.coherence_summary.missing_phases.length > 0 && (
              <p className="text-xs text-muted-foreground">Missing: {report.coherence_summary.missing_phases.join(", ")}</p>
            )}
          </CardContent>
        </Card>
      )}

      {report.policy_verdict && (
        <div className="rounded-lg border p-4">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">Policy Verdict:</span>
            <Badge variant={report.policy_verdict === "pass" ? "success" : report.policy_verdict === "warn" ? "warning" : "destructive"}>
              {report.policy_verdict}
            </Badge>
          </div>
        </div>
      )}
    </div>
  );
}
