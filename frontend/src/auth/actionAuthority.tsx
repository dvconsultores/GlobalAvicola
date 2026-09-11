/**
 * GA-FE-04 · R-98 / P-13 · CAPA DE AUTORIDAD DE ACCIÓN (intra-pantalla).
 *
 * P-13: página ≠ acción. Una pantalla puede ser LEGIBLE (`read`) y sus controles de
 * escritura deben responder a la autoridad DE LA ACCIÓN (`create`/`update`/`delete`/
 * `review`/`approve`/`reject`/`correct`/`send_sap`), no al hecho de haber llegado a ella.
 *
 * `AC-FE16`: «La interfaz respeta RBAC: quien solo lee no ve acciones de escritura, y el
 * backend sigue siendo la autoridad —ocultar un botón no es autorizar—».
 *
 * Este módulo NO introduce una segunda política: reexpone el evaluador canónico de la
 * navegación (`auth/navigation.canAccessCapability`, GA-FE-03) con el vocabulario de acción.
 * Invariantes heredadas: comodín global por `is_super_admin`; unidad efectiva (concesión ∩
 * habilitada ∩ activa) para el actor de empresa; unidad habilitada + empresa efectiva para
 * el actor global; sin sesión no hay acción. La autoridad final sigue en el backend.
 */
import type { ReactNode } from 'react'
import { canAccessCapability } from './navigation'
import type { CapabilitySpec, NavSession } from './navigation'
import { useAuthStore } from '../stores/auth.store'

/** Especificación evaluable de una acción de pantalla (mismo vocabulario que la navegación). */
export type ActionSpec = CapabilitySpec

/**
 * Evalúa si la sesión puede EJECUTAR la acción descrita por `spec`.
 * Es la única puerta: úsala (o `<ActionGate>`/`useCan`) antes de pintar un control de escritura.
 */
export function canPerformAction(
  spec: ActionSpec,
  session: NavSession | null | undefined,
): boolean {
  return canAccessCapability(spec, session)
}

/** Hook: devuelve un evaluador ligado a la sesión viva del store (reactivo a logout/logout). */
export function useCan(): (spec: ActionSpec) => boolean {
  const user = useAuthStore(s => s.user)
  return (spec: ActionSpec) => canPerformAction(spec, user)
}

interface ActionGateProps {
  spec: ActionSpec
  /** Sesión explícita (pruebas / contextos no conectados al store). Por defecto, la del store. */
  session?: NavSession | null
  /** Contenido protegido. Sin autoridad no se pinta (o se pinta `fallback` si se provee). */
  children: ReactNode
  fallback?: ReactNode
}

/**
 * Guardia declarativa de acción. Fail-closed: sin autoridad ⇒ nada (salvo `fallback`).
 * No sustituye al backend: es descubribilidad y prevención de error, no autorización.
 */
export function ActionGate({ spec, session, children, fallback = null }: ActionGateProps) {
  const storeUser = useAuthStore(s => s.user)
  const effective = session === undefined ? storeUser : session
  const allowed = canPerformAction(spec, effective)
  return <>{allowed ? children : fallback}</>
}
