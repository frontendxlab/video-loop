import type { SceneReport } from "@/types/report";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Film, Hash } from "lucide-react";

interface Props { scenes: SceneReport[] }

export function ReportScenesTab({ scenes }: Props) {
  if (scenes.length === 0) {
    return (
      <div className="rounded-lg border p-12 text-center text-sm text-muted-foreground">
        <Film className="mx-auto mb-3 h-8 w-8 text-muted-foreground/50" />
        <p>No per-scene report artifacts found.</p>
        <p className="mt-1 text-xs">Scene reports appear alongside rendered scene files as <code className="rounded bg-muted px-1">*.mp4.scene.report.json</code>.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader><CardTitle className="text-sm">Per-Scene Reports ({scenes.length})</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>#</TableHead>
                <TableHead>Engine</TableHead>
                <TableHead className="text-right">Duration</TableHead>
                <TableHead>Hash</TableHead>
                <TableHead>Format</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {scenes.map((s) => (
                <TableRow key={s.scene_index}>
                  <TableCell className="font-medium">{s.scene_index}</TableCell>
                  <TableCell><Badge variant="outline" className="text-[10px]">{s.engine}</Badge></TableCell>
                  <TableCell className="text-right">
                    {s.duration_frames}f ({(s.duration_frames / s.render_format.fps).toFixed(1)}s)
                  </TableCell>
                  <TableCell>
                    <code className="flex items-center gap-1 rounded bg-muted px-1 text-[10px]">
                      <Hash className="h-3 w-3" /> {s.content_hash || "—"}
                    </code>
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {s.render_format.width}×{s.render_format.height} @ {s.render_format.fps}fps
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Engine breakdown */}
      <Card>
        <CardHeader><CardTitle className="text-sm">Engine Breakdown</CardTitle></CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            {Object.entries(
              scenes.reduce<Record<string, number>>((acc, s) => {
                acc[s.engine] = (acc[s.engine] || 0) + 1;
                return acc;
              }, {})
            ).map(([engine, count]) => (
              <div key={engine} className="flex items-center gap-2 rounded-md border px-3 py-2">
                <Badge variant="outline">{engine}</Badge>
                <span className="text-sm font-semibold">{count}</span>
                <span className="text-xs text-muted-foreground">scene{count !== 1 ? "s" : ""}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
