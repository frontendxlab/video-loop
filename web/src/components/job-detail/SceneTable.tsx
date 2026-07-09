import { useState } from 'react'
import type { SceneInfo } from '@/types/job'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { SceneArtifactPanel } from './SceneArtifactPanel'

interface Props { scenes: SceneInfo[]; jobId?: string }

export function SceneTable({ scenes, jobId }: Props) {
  const [selectedId, setSelectedId] = useState<string | null>(null)

  if (scenes.length === 0) {
    return <p className="py-4 text-sm text-muted-foreground italic">No scenes yet</p>
  }

  const selected = scenes.find(s => s.id === selectedId) ?? null

  return (
    <div className="space-y-3">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Scene</TableHead>
            <TableHead>Kind</TableHead>
            <TableHead>Engine</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">Issues</TableHead>
            <TableHead className="text-right">Retries</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {scenes.map((s) => (
            <TableRow
              key={s.id}
              onClick={() => setSelectedId(selectedId === s.id ? null : s.id)}
              className={cn(
                'cursor-pointer transition-colors',
                selectedId === s.id && 'bg-muted/50'
              )}
            >
              <TableCell className="font-medium">{s.id}</TableCell>
              <TableCell>{s.kind}</TableCell>
              <TableCell><Badge variant="outline" className="text-[10px]">{s.engine}</Badge></TableCell>
              <TableCell><Badge variant="outline">{s.status}</Badge></TableCell>
              <TableCell className={cn('text-right', s.reviewIssues > 0 && 'text-amber-400')}>{s.reviewIssues}</TableCell>
              <TableCell className="text-right">{s.retryCount}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {selected && (
        <SceneArtifactPanel scene={selected} jobId={jobId ?? ''} onClose={() => setSelectedId(null)} />
      )}
    </div>
  )
}
