import { useCallback, useRef, useState } from 'react'

interface PanState {
  x: number
  y: number
  scale: number
}

interface UseCanvasPanReturn {
  /** CSS transform string for inner container */
  transform: string
  /** Bind to canvas container element */
  handlers: {
    onMouseDown: (e: React.MouseEvent) => void
    onMouseMove: (e: React.MouseEvent) => void
    onMouseUp: () => void
    onWheel: (e: React.WheelEvent) => void
    onTouchStart: (e: React.TouchEvent) => void
    onTouchMove: (e: React.TouchEvent) => void
    onTouchEnd: () => void
  }
  /** Reset to origin */
  reset: () => void
  /** Programmatic zoom */
  zoomTo: (s: number) => void
  scale: number
}

const MIN_SCALE = 0.1
const MAX_SCALE = 3
const WHEEL_FACTOR = 0.001

export function useCanvasPan(initialScale = 1): UseCanvasPanReturn {
  const [state, setState] = useState<PanState>({ x: 0, y: 0, scale: initialScale })
  const dragging = useRef(false)
  const last = useRef({ x: 0, y: 0 })
  const touchId = useRef<number | null>(null)
  const touchStartDist = useRef(0)
  const touchStartScale = useRef(1)

  const onMouseDown = useCallback((e: React.MouseEvent) => {
    // Only pan on left button, not on interactive elements
    if (e.button !== 0) return
    const target = e.target as HTMLElement
    if (target.closest('[data-stop-propagation]')) return
    dragging.current = true
    last.current = { x: e.clientX, y: e.clientY }
  }, [])

  const onMouseMove = useCallback((e: React.MouseEvent) => {
    if (!dragging.current) return
    const dx = e.clientX - last.current.x
    const dy = e.clientY - last.current.y
    last.current = { x: e.clientX, y: e.clientY }
    setState(prev => ({ ...prev, x: prev.x + dx, y: prev.y + dy }))
  }, [])

  const onMouseUp = useCallback(() => {
    dragging.current = false
  }, [])

  const onWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault()
    const delta = -e.deltaY * WHEEL_FACTOR
    setState(prev => {
      const ns = Math.min(MAX_SCALE, Math.max(MIN_SCALE, prev.scale + delta * prev.scale))
      // Zoom toward cursor
      const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
      const mx = e.clientX - rect.left
      const my = e.clientY - rect.top
      const nx = mx - (mx - prev.x) * (ns / prev.scale)
      const ny = my - (my - prev.y) * (ns / prev.scale)
      return { x: nx, y: ny, scale: ns }
    })
  }, [])

  const onTouchStart = useCallback((e: React.TouchEvent) => {
    if (e.touches.length === 1) {
      touchId.current = e.touches[0].identifier
      last.current = { x: e.touches[0].clientX, y: e.touches[0].clientY }
    } else if (e.touches.length === 2) {
      const dx = e.touches[0].clientX - e.touches[1].clientX
      const dy = e.touches[0].clientY - e.touches[1].clientY
      touchStartDist.current = Math.sqrt(dx * dx + dy * dy)
      touchStartScale.current = state.scale
    }
  }, [state.scale])

  const onTouchMove = useCallback((e: React.TouchEvent) => {
    e.preventDefault()
    if (e.touches.length === 1 && touchId.current !== null) {
      const dx = e.touches[0].clientX - last.current.x
      const dy = e.touches[0].clientY - last.current.y
      last.current = { x: e.touches[0].clientX, y: e.touches[0].clientY }
      setState(prev => ({ ...prev, x: prev.x + dx, y: prev.y + dy }))
    } else if (e.touches.length === 2) {
      const dx = e.touches[0].clientX - e.touches[1].clientX
      const dy = e.touches[0].clientY - e.touches[1].clientY
      const dist = Math.sqrt(dx * dx + dy * dy)
      const s = touchStartScale.current * (dist / touchStartDist.current)
      setState(prev => ({ ...prev, scale: Math.min(MAX_SCALE, Math.max(MIN_SCALE, s)) }))
    }
  }, [])

  const onTouchEnd = useCallback(() => {
    touchId.current = null
  }, [])

  const reset = useCallback(() => setState({ x: 0, y: 0, scale: 1 }), [])
  const zoomTo = useCallback((s: number) => setState(prev => ({ ...prev, scale: Math.min(MAX_SCALE, Math.max(MIN_SCALE, s)) })), [])

  const transform = `translate(${state.x}px, ${state.y}px) scale(${state.scale})`

  return {
    transform,
    handlers: { onMouseDown, onMouseMove, onMouseUp, onWheel, onTouchStart, onTouchMove, onTouchEnd },
    reset,
    zoomTo,
    scale: state.scale,
  }
}
