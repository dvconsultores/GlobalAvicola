/**
 * GA-FE-03 · EVALUADOR CANÓNICO DE NAVEGACIÓN — una sola política compartida.
 *
 * La navegación REFLEJA autoridad; no la sustituye (`R-98`/`R-119`, `T-040-23`,
 * `CAP-ADM-06`). Este módulo es la única implementación de la política de descubribilidad:
 *
 *   RBAC (permiso canónico, espejo de `tiene_permiso`)
 *   ∩ empresa efectiva / unidad habilitada de la empresa (para el actor global)
 *   ∩ unidad efectiva del usuario (concesión ∩ habilitada ∩ activa) para el resto
 *
 * Invariantes (`OD-14`, `OD-16`, fix D-1 `9ffc5ec`):
 *  - `Company BU OFF` es absoluto para lo productivo, **incluido** el actor global.
 *  - El actor global **sin contexto** no obtiene inquilino: falla cerrada.
 *  - Encender una unidad NO concede (`OD-16.d`); la concesión NO habilita una unidad apagada
 *    (`OD-16.e`).
 *  - El backend sigue siendo la autoridad final; esto es UX de descubribilidad.
 *
 * Frontera: `R-98` (acciones de escritura intra-pantalla) excede esta tranche; aquí se cierra
 * la parte de **acciones de navegación** (menú, hubs, atajos accionables).
 */
import { hasPermission } from './permissions'
import type { NavItem } from '../data/navigationConfig'

/** Clasificación de capacidad (SPEC §8). Se deriva del comportamiento del recurso. */
export type NavCapability =
  | 'CORE'
  | 'CONTROL_PLANE'
  | 'PRODUCTIVE'
  | 'REPORTING'
  | 'INTEGRATION'
  | 'GLOBAL_CONTROL'

/** Cuatro unidades productivas canónicas (`OD-16.a`). Sin quinta unidad, sin alias. */
export const PRODUCTIVE_UNITS = ['grandparent', 'breeder', 'hatchery', 'broiler'] as const
export type ProductiveUnit = (typeof PRODUCTIVE_UNITS)[number]

/** La sesión que evalúa la navegación — subconjunto EXACTO del contrato `/me` (fase 8). */
export interface NavSession {
  is_super_admin?: boolean | null
  permissions?: string[] | null
  effective_company_id?: number | null
  company_business_units?: string[] | null
  effective_business_units?: string[] | null
}

/** Especificación evaluable de una capacidad de navegación o de una ruta. */
export interface CapabilitySpec {
  /** Permiso RBAC requerido, en el lenguaje canónico `modulo:accion`. */
  permission?: string
  /** Unidad productiva de la que depende la capacidad (exacta). */
  businessUnit?: string
  /** La capacidad exige un conjunto productivo no vacío (multi-unidad). */
  requiresUnits?: boolean
}

function unitsOf(list?: string[] | null): string[] {
  return Array.isArray(list) ? list.filter((u): u is string => typeof u === 'string') : []
}

/** `is_super_admin` es la capacidad real (comodín `("*", …, "all")`), no un nombre de rol. */
export function isGlobalActor(session: NavSession | null | undefined): boolean {
  return session?.is_super_admin === true
}

function hasCompanyContext(session: NavSession): boolean {
  return session.effective_company_id != null
}

/** ¿Hay AL MENOS una unidad disponible para navegación productiva? */
export function hasAnyUnits(session: NavSession | null | undefined): boolean {
  if (!session) return false
  if (isGlobalActor(session)) {
    return hasCompanyContext(session) && unitsOf(session.company_business_units).length > 0
  }
  return unitsOf(session.effective_business_units).length > 0
}

/** ¿La unidad `bu` está disponible? Normal ⇒ efectiva; global ⇒ habilitada + contexto. */
export function hasUnit(session: NavSession | null | undefined, bu: string): boolean {
  if (!session) return false
  if (isGlobalActor(session)) {
    return hasCompanyContext(session) && unitsOf(session.company_business_units).includes(bu)
  }
  return unitsOf(session.effective_business_units).includes(bu)
}

/**
 * Decisión canónica de una capacidad. Orden de dimensiones:
 * permiso → unidad (exacta) → conjunto no vacío. Sin rol, sin username, sin estado de menú.
 */
export function canAccessCapability(
  cap: CapabilitySpec,
  session: NavSession | null | undefined,
): boolean {
  if (!session) return false
  if (cap.permission && !hasPermission(session, cap.permission)) return false
  if (cap.businessUnit && !hasUnit(session, cap.businessUnit)) return false
  if (cap.requiresUnits && !hasAnyUnits(session)) return false
  return true
}

/** Mapa etapa productiva → unidad canónica (el catálogo de etapas es dominio, no ACL). */
const STAGE_UNIT: Record<string, ProductiveUnit> = {
  grandparent_rearing: 'grandparent',
  grandparent_production: 'grandparent',
  breeder_rearing: 'breeder',
  breeder_production: 'breeder',
  hatchery: 'hatchery',
  broiler: 'broiler',
}

/** Visibilidad de un atajo de etapa (Dashboard móvil y cualquier superficie de proceso). */
export function stageVisibleForSession(
  stageKey: string,
  session: NavSession | null | undefined,
): boolean {
  const bu = STAGE_UNIT[stageKey]
  if (!bu) return false
  return canAccessCapability({ permission: 'operations:read', businessUnit: bu }, session)
}

function specOf(item: NavItem): CapabilitySpec {
  return {
    permission: item.permission,
    businessUnit: item.businessUnit,
    requiresUnits: item.requiresUnits,
  }
}

/**
 * Filtra el árbol de navegación con la política canónica.
 * - Hoja: visible ⇔ `canAccessCapability`.
 * - Contenedor: visible ⇔ su propia especificación pasa Y le queda ≥1 hijo visible
 *   (los grupos vacíos desaparecen — §9F/§30).
 * - Sin sesión: árbol vacío (el login no pinta navegación).
 */
export function filterNavItemsBySession(
  items: NavItem[],
  session: NavSession | null | undefined,
): NavItem[] {
  if (!session) return []
  const result: NavItem[] = []
  for (const item of items) {
    if (item.children) {
      const children = filterNavItemsBySession(item.children, session)
      if (children.length === 0) continue
      if (!canAccessCapability(specOf(item), session)) continue
      result.push({ ...item, children })
    } else if (canAccessCapability(specOf(item), session)) {
      result.push(item)
    }
  }
  return result
}
