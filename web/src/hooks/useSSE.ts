import { useCallback, useEffect, useRef, useState } from 'react'
import type { SSEEvent, SSEEventType } from '@/types/sse'

export interface UseSSEOptions {
  onEvent?: (event: SSEEvent) => void
  enabled?: boolean
}

/* All SSE event types — register named EventSource listeners per backend event: lines */
const SSE_EVENT_TYPES: SSEEventType[] = [
  'job.started', 'job.stage', 'job.todo', 'prompt.grilled',
  'director.scene_planned', 'director.scene_routed',
  'subagent.started', 'subagent.token', 'subagent.completed', 'subagent.failed',
  'render.scene_started', 'render.scene_completed',
  'review.issue', 'repair.plan', 'retry.started',
  'artifact.ready', 'job.completed', 'job.failed',
]

/* Parse backend SSE JSON into frontend SSEEvent shape.
   Backend data: line contains:
     {"id":"evt_xxx","type":"job.started","jobId":"j1","timestamp":<unix_float>,"payload":{...}}
   Frontend SSEEvent expects:
     { type: "job.started", data: { jobId: "j1", timestamp: "<ISO>", ...payload } }
   Returns null on parse failure (skip malformed messages). */
function parseBackendPayload(raw: string): SSEEvent | null {
  try {
    const parsed = JSON.parse(raw)
    if (!parsed || typeof parsed !== 'object') return null
    const type = parsed.type as string
    if (!type) return null

    const timestamp = typeof parsed.timestamp === 'number'
      ? new Date(parsed.timestamp * 1000).toISOString()
      : String(parsed.timestamp ?? '')

    return {
      type: type as SSEEventType,
      data: { jobId: parsed.jobId, timestamp, ...parsed.payload },
    } as SSEEvent
  } catch {
    return null
  }
}

export function useSSE(jobId: string | undefined, options: UseSSEOptions = {}) {
  const { onEvent, enabled = true } = options
  const [events, setEvents] = useState<SSEEvent[]>([])
  const [connected, setConnected] = useState(false)
  const cleanupRef = useRef<(() => void) | null>(null)

  const addEvent = useCallback((event: SSEEvent) => {
    setEvents((prev: SSEEvent[]) => [...prev, event])
    onEvent?.(event)
  }, [onEvent])

  useEffect(() => {
    if (!jobId || !enabled) return

    /* Browser environments (prod, dev, test-with-mock) have EventSource */
    if (typeof EventSource !== 'undefined') {
      const es = new EventSource(`/api/jobs/${encodeURIComponent(jobId)}/stream`)
      let closed = false

      const onMessage = (e: MessageEvent) => {
        if (closed) return
        const event = parseBackendPayload(e.data)
        if (event) addEvent(event)
      }

      for (const type of SSE_EVENT_TYPES) {
        es.addEventListener(type, onMessage)
      }
      es.addEventListener('message', onMessage) // fallback for unnamed events

      es.onopen = () => { if (!closed) setConnected(true) }
      es.onerror = () => { if (!closed) setConnected(false) }

      return () => {
        closed = true
        es.close()
        setConnected(false)
      }
    }

    /* Dev/test fallback when EventSource unavailable (jsdom, non-browser) */
    let cancelled = false
    setConnected(true)
    import('@/data/mock').then(({ subscribeToJobEvents }) => {
      if (cancelled) return
      cleanupRef.current = subscribeToJobEvents(
        jobId,
        (event) => { if (!cancelled) addEvent(event) },
        () => { if (!cancelled) setConnected(false) },
      )
    })

    return () => {
      cancelled = true
      cleanupRef.current?.()
      cleanupRef.current = null
      setConnected(false)
    }
  }, [jobId, enabled, addEvent])

  return { events, connected, clear: () => setEvents([]) }
}
