import { useCallback, useEffect, useRef, useState } from 'react'
import type { SSEEvent } from '@/types/sse'

export interface UseSSEOptions {
  onEvent?: (event: SSEEvent) => void
  enabled?: boolean
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
    setConnected(true)
    import('@/data/mock').then(({ subscribeToJobEvents }) => {
      cleanupRef.current = subscribeToJobEvents(jobId, (event) => addEvent(event), () => setConnected(false))
    })
    return () => { cleanupRef.current?.(); cleanupRef.current = null; setConnected(false) }
  }, [jobId, enabled, addEvent])

  return { events, connected, clear: () => setEvents([]) }
}
