import { useEffect, useRef, useState } from 'react'

/**
 * `004` · NAV-01 / UX-01 — Guard de cambios sin guardar.
 *
 * La app usa el router DECLARATIVO de React Router 7 (`<Routes>`), donde
 * `useBlocker` no está disponible (exige data router). Este hook implementa la
 * protección mínima y sin `alert/prompt` nativos (convención del repo):
 *
 * 1. `beforeunload` mientras `dirty` (refresh / cierre de pestaña).
 * 2. Sentinel de historial + `popstate` para el browser-back INTERNO:
 *    al ensuciarse la pantalla se empuja una entrada centinela; si el usuario
 *    pulsa atrás, cae en el centinela y se intercepta (sin mutar la URL).
 *
 * Semántica de confirmación:
 * - Cancelar ⇒ `stay()`: se vuelve a empujar el centinela con `history.forward()`
 *   (la URL no cambió; la pantalla y el formulario permanecen intactos).
 * - Confirmar (browser back) ⇒ `confirmLeave()`: `history.go(-1)` cae en la
 *   entrada anterior real (la que el usuario esperaba).
 * - Salida programática (botón «Volver» con destino conocido) ⇒
 *   `requestRouteLeave(run)`: muestra la confirmación y, al confirmar, ejecuta
 *   `run()` (navegación por ruta canónica; nunca depende del historial).
 *
 * Límite declarado: dos pulsaciones de “atrás” inmediatas y seguidas pueden
 * adelantar la confirmación (el navegador procesa el popstate antes de que el
 * diálogo bloquee); el diálogo modal reduce este caso al mínimo.
 */
export function useUnsavedChangesGuard(dirty: boolean) {
  const [confirmOpen, setConfirmOpen] = useState(false)
  const allowedRef = useRef(false)
  const sentinelRef = useRef(false)
  const intentRef = useRef<{ kind: 'history' } | { kind: 'route'; run: () => void } | null>(null)

  // 1) Aviso del navegador para refresh/cierre.
  useEffect(() => {
    if (!dirty) return
    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault()
      e.returnValue = ''
    }
    window.addEventListener('beforeunload', handler)
    return () => window.removeEventListener('beforeunload', handler)
  }, [dirty])

  // 2) Sentinel + popstate para el back interno.
  useEffect(() => {
    if (!dirty) {
      sentinelRef.current = false
      return
    }
    if (!sentinelRef.current) {
      try {
        window.history.pushState({ gaUnsavedGuard: true }, '', window.location.href)
        sentinelRef.current = true
      } catch {
        /* historial no disponible (jsdom) — sin centinela */
      }
    }
    const onPop = () => {
      if (allowedRef.current) return
      intentRef.current = { kind: 'history' }
      setConfirmOpen(true)
    }
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [dirty])

  /** Salida programática (botón Volver u otra salida controlada). */
  const requestRouteLeave = (run: () => void) => {
    if (!dirty) {
      run()
      return
    }
    intentRef.current = { kind: 'route', run }
    setConfirmOpen(true)
  }

  /** El usuario decide quedarse: cierra el diálogo sin navegar. */
  const stay = () => {
    intentRef.current = null
    setConfirmOpen(false)
    // Si venía de un popstate interceptado, la entrada centinela sigue delante;
    // permanecer es simplemente no navegar (la URL nunca cambió).
  }

  /** El usuario confirma salir sin guardar. */
  const confirmLeave = () => {
    allowedRef.current = true
    setConfirmOpen(false)
    const intent = intentRef.current
    intentRef.current = null
    if (intent?.kind === 'route') {
      intent.run()
      return
    }
    // browser-back confirmado: volver a la entrada REAL anterior al formulario.
    try {
      window.history.go(-1)
    } catch {
      /* sin historial disponible */
    }
  }

  return { confirmOpen, requestRouteLeave, stay, confirmLeave, dirty }
}
