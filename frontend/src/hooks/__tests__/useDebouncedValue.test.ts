/**
 * `F4` (AC-S1-F01) — el valor sólo se propaga tras `delayMs` sin cambios.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useDebouncedValue } from '../useDebouncedValue'

describe('useDebouncedValue', () => {
  beforeEach(() => { vi.useFakeTimers() })
  afterEach(() => { vi.useRealTimers() })

  it('devuelve el valor inicial y lo propaga tras el retardo', () => {
    const { result } = renderHook(() => useDebouncedValue('abc', 400))
    expect(result.current).toBe('abc')

    act(() => { vi.advanceTimersByTime(400) })
    expect(result.current).toBe('abc')
  })

  it('sólo propaga el último valor de una ráfaga', () => {
    const { result, rerender } = renderHook(
      ({ valor }: { valor: string }) => useDebouncedValue(valor, 400),
      { initialProps: { valor: '' } },
    )

    rerender({ valor: 'l' })
    act(() => { vi.advanceTimersByTime(200) })
    rerender({ valor: 'lt' })
    act(() => { vi.advanceTimersByTime(200) })
    rerender({ valor: 'lt-01' })

    // Aún no pasaron 400 ms desde la última tecla.
    expect(result.current).toBe('')

    act(() => { vi.advanceTimersByTime(400) })
    expect(result.current).toBe('lt-01')
  })

  it('respeta un retardo propio', () => {
    const { result, rerender } = renderHook(
      ({ valor }: { valor: string }) => useDebouncedValue(valor, 100),
      { initialProps: { valor: 'a' } },
    )
    rerender({ valor: 'ab' })
    act(() => { vi.advanceTimersByTime(100) })
    expect(result.current).toBe('ab')
  })
})
