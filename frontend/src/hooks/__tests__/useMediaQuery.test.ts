import { describe, it, expect, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useMediaQuery } from '../useMediaQuery'

describe('useMediaQuery', () => {
  const originalInnerWidth = window.innerWidth

  afterEach(() => {
    Object.defineProperty(window, 'innerWidth', { writable: true, value: originalInnerWidth })
  })

  it('returns mobile when width < 640', () => {
    Object.defineProperty(window, 'innerWidth', { writable: true, value: 375 })
    const { result } = renderHook(() => useMediaQuery())
    expect(result.current).toBe('mobile')
  })

  it('returns tablet when width between 640-1023', () => {
    Object.defineProperty(window, 'innerWidth', { writable: true, value: 768 })
    const { result } = renderHook(() => useMediaQuery())
    expect(result.current).toBe('tablet')
  })

  it('returns desktop when width >= 1024', () => {
    Object.defineProperty(window, 'innerWidth', { writable: true, value: 1440 })
    const { result } = renderHook(() => useMediaQuery())
    expect(result.current).toBe('desktop')
  })

  it('responds to window resize', () => {
    Object.defineProperty(window, 'innerWidth', { writable: true, value: 500 })
    const { result } = renderHook(() => useMediaQuery())
    expect(result.current).toBe('mobile')

    act(() => {
      Object.defineProperty(window, 'innerWidth', { writable: true, value: 1024 })
      window.dispatchEvent(new Event('resize'))
    })
    expect(result.current).toBe('desktop')
  })
})

