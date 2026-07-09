import { useEffect, useRef } from 'react'
import type { SSEEvent } from '@/types/sse'
import { ScrollArea } from '@/components/ui/scroll-area'
import { cn } from '@/lib/utils'

interface Props { events: SSEEvent[] }

function iconClass(type: string): string {
  if (type.endsWith('.failed')) return 'text-destructive'
  if (type.endsWith('.completed') || type.endsWith('.started')) return 'text-emerald-400'
  if (type.startsWith('review') || type.startsWith('repair')) return 'text-amber-400'
  if (type.endsWith('.token')) return 'text-muted-foreground'
  return 'text-primary'
}

function eventLabel(event: SSEEvent): string {
  const d = event.data as any
  const ts = d.timestamp ? new Date(d.timestamp).toLocaleTimeString() : ''
  const p = `[${ts}]`
  switch (event.type) {
    case 'job.started': return `${p} Job started: ${d.title}`
    case 'job.stage': return `${p} Stage → ${d.stage} (${d.progressPct}%)`
    case 'job.completed': return `${p} Job completed`
    case 'job.failed': return `${p} Job failed: ${d.error}`
    case 'subagent.started': return `${p} ▶ ${d.name} (${d.engine}) — ${d.task}`
    case 'subagent.completed': return `${p} ✓ ${d.name} done in ${d.durationMs}ms`
    case 'subagent.failed': return `${p} ✗ ${d.name} failed: ${d.error}`
    case 'subagent.token': return `${p}   ${d.token}`
    case 'director.scene_planned': return `${p} Scene planned: ${d.sceneKind} (${d.sceneId})`
    case 'director.scene_routed': return `${p} Scene routed: ${d.sceneKind} → ${d.engine}`
    case 'render.scene_started': return `${p} Rendering ${d.sceneId} (${d.sceneKind})`
    case 'render.scene_completed': return `${p} Render done: ${d.sceneId}`
    case 'review.issue': return `${p} ⚠ Review issue (${d.severity}): ${d.issue}`
    case 'repair.plan': return `${p} 🔧 Repair #${d.retryCount}: ${d.plan}`
    case 'retry.started': return `${p} Retry #${d.attempt}: ${d.reason}`
    case 'artifact.ready': return `${p} Artifact: ${d.artifactType} @ ${d.path}`
    case 'job.todo': return `${p} ${d.done ? '☑' : '☐'} ${d.item}`
    default: return `${p} ${event.type}`
  }
}

export function EventLog({ events }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [events.length])
  return (
    <ScrollArea className="h-80 rounded-lg border bg-black/30 p-3 font-mono text-xs leading-relaxed">
      {events.length === 0 ? (
        <p className="text-muted-foreground italic">Waiting for events…</p>
      ) : (
        events.map((ev, i) => (
          <div key={i} className={cn('py-0.5', iconClass(ev.type))}>{eventLabel(ev)}</div>
        ))
      )}
      <div ref={bottomRef} />
    </ScrollArea>
  )
}
