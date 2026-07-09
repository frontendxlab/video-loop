import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { act, renderHook, waitFor } from '@testing-library/react'
import { useSSE } from '@/hooks/useSSE'
import type { SSEEvent } from '@/types/sse'

// ─── Mock EventSource for jsdom ─────────────────────────────────────────────

type Listener = EventListenerOrEventListenerObject

class MockEventSource extends EventTarget {
  static readonly CONNECTING = 0
  static readonly OPEN = 1
  static readonly CLOSED = 2
  readyState = MockEventSource.CONNECTING
  url: string
  withCredentials = false
  onopen: ((e: Event) => void) | null = null
  onmessage: ((e: MessageEvent) => void) | null = null
  onerror: ((e: Event) => void) | null = null
  #listeners = new Map<string, Set<Listener>>()

  constructor(url: string) {
    super()
    this.url = url
    instances.push(this)
    setTimeout(() => this.#open(), 0)
  }

  #open(): void {
    this.readyState = MockEventSource.OPEN
    const ev = new Event('open')
    this.onopen?.(ev)
    this.dispatchEvent(ev)
  }

  addEventListener(type: string, handler: Listener): void {
    if (!this.#listeners.has(type)) this.#listeners.set(type, new Set())
    this.#listeners.get(type)!.add(handler)
  }

  removeEventListener(type: string, handler: Listener): void {
    this.#listeners.get(type)?.delete(handler)
  }

  close(): void {
    this.readyState = MockEventSource.CLOSED
  }

  /** Simulate SSE event from backend (named event type). */
  emit(type: string, data: string): void {
    const msg = new MessageEvent(type, { data })
    this.#listeners.get(type)?.forEach((h) => {
      if ('handleEvent' in h) h.handleEvent(msg)
      else h(msg)
    })
    if (this.onmessage) this.onmessage(msg)
  }

  /** Simulate connection error. */
  emitError(): void {
    this.readyState = MockEventSource.CLOSED
    const ev = new Event('error')
    this.onerror?.(ev)
    this.dispatchEvent(ev)
  }
}

/** Build a backend-format SSE data payload. */
function backendEvent(
  type: string,
  overrides: Record<string, unknown> = {},
): string {
  return JSON.stringify({
    id: 'evt_' + Math.random().toString(36).slice(2, 8),
    type,
    jobId: 'job-1',
    timestamp: Date.now() / 1000,
    payload: {},
    ...overrides,
  })
}

let instances: MockEventSource[] = []

beforeEach(() => {
  instances = []
  vi.stubGlobal('EventSource', MockEventSource as unknown as typeof EventSource)
})

afterEach(() => {
  vi.unstubAllGlobals()
})

// ─── Tests ──────────────────────────────────────────────────────────────────

describe('useSSE', () => {
  it('creates EventSource with correct URL', async () => {
    renderHook(() => useSSE('job-1'))
    await waitFor(() => expect(instances.length).toBe(1))
    expect(instances[0].url).toBe('/api/jobs/job-1/stream')
  })

  it('sets connected=true on open', async () => {
    const { result } = renderHook(() => useSSE('job-1'))
    await waitFor(() => expect(result.current.connected).toBe(true))
  })

  it('sets connected=false on error', async () => {
    const { result } = renderHook(() => useSSE('job-1'))
    await waitFor(() => expect(result.current.connected).toBe(true))

    const es = instances[0]
    act(() => { es.emitError() })

    await waitFor(() => expect(result.current.connected).toBe(false))
  })

  it('parses and appends job.started event', async () => {
    const { result } = renderHook(() => useSSE('job-1'))
    await waitFor(() => expect(instances.length).toBe(1))

    const es = instances[0]
    act(() => { es.emit('job.started', backendEvent('job.started', { payload: { title: 'Test job' } })) })

    await waitFor(() => expect(result.current.events.length).toBe(1))
    const event = result.current.events[0]
    expect(event.type).toBe('job.started')
    expect(event.data).toMatchObject({ jobId: 'job-1', title: 'Test job' })
    expect(typeof event.data.timestamp).toBe('string')
  })

  it('parses and appends job.stage event', async () => {
    const { result } = renderHook(() => useSSE('job-1'))
    await waitFor(() => expect(instances.length).toBe(1))

    const es = instances[0]
    act(() => {
      es.emit('job.stage', backendEvent('job.stage', { payload: { stage: 'render', progressPct: 50, phase: 'render' } }))
    })

    await waitFor(() => expect(result.current.events.length).toBe(1))
    expect(result.current.events[0]).toMatchObject({
      type: 'job.stage',
      data: { stage: 'render', progressPct: 50, phase: 'render' },
    })
  })

  it('accumulates multiple events in order', async () => {
    const { result } = renderHook(() => useSSE('job-1'))
    await waitFor(() => expect(instances.length).toBe(1))

    const es = instances[0]
    act(() => {
      es.emit('job.started', backendEvent('job.started', { payload: { title: 'Test' } }))
      es.emit('job.stage', backendEvent('job.stage', { payload: { stage: 'plan', progressPct: 10, phase: 'plan' } }))
    })

    await waitFor(() => expect(result.current.events.length).toBe(2))
    expect(result.current.events[0].type).toBe('job.started')
    expect(result.current.events[1].type).toBe('job.stage')
  })

  it('triggers onEvent callback', async () => {
    const onEvent = vi.fn()
    renderHook(() => useSSE('job-1', { onEvent }))
    await waitFor(() => expect(instances.length).toBe(1))

    const es = instances[0]
    act(() => { es.emit('job.started', backendEvent('job.started', { payload: { title: 'Test' } })) })

    await waitFor(() => expect(onEvent).toHaveBeenCalledWith(
      expect.objectContaining({ type: 'job.started' }),
    ))
  })

  it('does not create EventSource when enabled=false', async () => {
    renderHook(() => useSSE('job-1', { enabled: false }))
    expect(instances.length).toBe(0)
  })

  it('does not create EventSource when jobId is undefined', async () => {
    renderHook(() => useSSE(undefined))
    expect(instances.length).toBe(0)
  })

  it('closes EventSource on unmount', async () => {
    const { unmount } = renderHook(() => useSSE('job-1'))
    await waitFor(() => expect(instances.length).toBe(1))
    const es = instances[0]

    unmount()

    expect(es.readyState).toBe(MockEventSource.CLOSED)
    expect(instances[0].readyState).toBe(MockEventSource.CLOSED)
  })

  it('clear() empties events array', async () => {
    const { result } = renderHook(() => useSSE('job-1'))
    await waitFor(() => expect(instances.length).toBe(1))

    const es = instances[0]
    act(() => { es.emit('job.started', backendEvent('job.started', { payload: { title: 'Test' } })) })
    await waitFor(() => expect(result.current.events.length).toBe(1))

    act(() => { result.current.clear() })

    expect(result.current.events.length).toBe(0)
  })
})
