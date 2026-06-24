import { useState, useEffect } from 'react'

type Breakpoint = 'mobile' | 'tablet' | 'desktop'

const BREAKPOINTS = {
  mobile: 640,
  tablet: 768,
  desktop: 1024,
}

/**
 * Hook that tracks the current responsive breakpoint.
 * Returns 'mobile' (<640px), 'tablet' (640-1023px), or 'desktop' (1024px+).
 */
export function useMediaQuery(): Breakpoint {
  const [breakpoint, setBreakpoint] = useState<Breakpoint>(() => {
    if (typeof window === 'undefined') return 'desktop'
    const w = window.innerWidth
    if (w < BREAKPOINTS.mobile) return 'mobile'
    if (w < BREAKPOINTS.desktop) return 'tablet'
    return 'desktop'
  })

  useEffect(() => {
    const handler = () => {
      const w = window.innerWidth
      if (w < BREAKPOINTS.mobile) setBreakpoint('mobile')
      else if (w < BREAKPOINTS.desktop) setBreakpoint('tablet')
      else setBreakpoint('desktop')
    }

    handler()
    window.addEventListener('resize', handler)
    return () => window.removeEventListener('resize', handler)
  }, [])

  return breakpoint
}

/**
 * Specific media query matcher.
 * @example const isMobile = useMediaQueryMin(640) // true if viewport >= 640px
 */
export function useMediaQueryMin(minWidth: number): boolean {
  const [matches, setMatches] = useState(() => {
    if (typeof window === 'undefined') return false
    return window.innerWidth >= minWidth
  })

  useEffect(() => {
    const mq = window.matchMedia(`(min-width: ${minWidth}px)`)
    const handler = (e: MediaQueryListEvent) => setMatches(e.matches)
    setMatches(mq.matches)
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [minWidth])

  return matches
}
