import type { ProvenanceGraph } from "@/types/report";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { GitBranch, FileText, Hash, FolderOpen, Film } from "lucide-react";

interface Props { provenance: ProvenanceGraph }

export function ReportProvenanceTab({ provenance }: Props) {
  return (
    <div className="space-y-4">
      {/* Overview */}
      <Card>
        <CardHeader><CardTitle className="text-sm">Provenance Overview</CardTitle></CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
            <div>
              <span className="flex items-center gap-1 text-muted-foreground"><Hash className="h-3 w-3" /> Content Hash</span>
              <code className="rounded bg-muted px-1 text-xs">{provenance.content_hash || "—"}</code>
            </div>
            <div>
              <span className="flex items-center gap-1 text-muted-foreground"><GitBranch className="h-3 w-3" /> Engines</span>
              <div className="mt-0.5 flex flex-wrap gap-1">
                {provenance.engines.map((e) => <Badge key={e} variant="outline" className="text-[10px]">{e}</Badge>)}
              </div>
            </div>
            <div>
              <span className="flex items-center gap-1 text-muted-foreground"><Film className="h-3 w-3" /> Scenes</span>
              <p>{provenance.scenes.length}</p>
            </div>
            <div>
              <span className="flex items-center gap-1 text-muted-foreground"><FileText className="h-3 w-3" /> Report</span>
              <code className="block truncate text-xs text-muted-foreground" title={provenance.reports.video_report}>
                {provenance.reports.video_report.split("/").pop()}
              </code>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Scene Lineage */}
      <Card>
        <CardHeader><CardTitle className="text-sm">Scene Lineage</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Scene ID</TableHead>
                <TableHead>Kind</TableHead>
                <TableHead>Engine</TableHead>
                <TableHead>Hash</TableHead>
                <TableHead className="text-right">Duration</TableHead>
                <TableHead>Assets</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {provenance.scenes.map((s) => (
                <TableRow key={s.id}>
                  <TableCell className="font-medium text-xs">{s.id}</TableCell>
                  <TableCell>{s.kind}</TableCell>
                  <TableCell><Badge variant="outline" className="text-[10px]">{s.engine}</Badge></TableCell>
                  <TableCell><code className="rounded bg-muted px-1 text-[10px]">{s.content_hash}</code></TableCell>
                  <TableCell className="text-right">{s.duration_frames}f</TableCell>
                  <TableCell>
                    {Object.keys(s.assets).length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {Object.entries(s.assets).map(([k, v]) => (
                          <Badge key={k} variant="secondary" className="text-[9px]" title={v}>
                            {k}
                          </Badge>
                        ))}
                      </div>
                    ) : (
                      <span className="text-xs text-muted-foreground">—</span>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Report paths */}
      <Card>
        <CardHeader><CardTitle className="text-sm">Artifact Paths</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-2 text-xs">
            {Object.entries(provenance.reports).map(([key, path]) => (
              <div key={key} className="flex items-center gap-2 rounded-md bg-muted/50 p-2">
                <FolderOpen className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                <span className="min-w-[100px] font-medium">{key}:</span>
                <code className="truncate text-[10px] text-muted-foreground" title={path}>{path}</code>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
