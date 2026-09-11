/**
 * GA-FE-03 · Evaluador canónico de navegación — especificación ejecutable (RED inicial).
 *
 * Objetivo: UNA definición declarativa + UN evaluador compartido (`auth/navigation.ts`).
 * Estas pruebas fijan el contrato EXACTO que la implementación debe cumplir; contra el estado
 * actual de `main` fallan en rojo (módulo inexistente / semántica ausente).
 *
 * Dimensiones (SPEC §9): permiso RBAC · unidad de empresa habilitada · unidad efectiva de
 * usuario · contexto de empresa · autoridad global. `R-98`/`R-119` — frontera GA-FE-03.
 */
import { describe, it, expect } from 'vitest'
import { canAccessCapability, filterNavItemsBySession, stageVisibleForSession } from '../navigation'
import { NAV_ITEMS, type NavItem } from '../../data/navigationConfig'

function flatten(items: NavItem[]): NavItem[] {
  return items.flatMap((i) => [i, ...(i.children ? flatten(i.children) : [])])
}
function keys(items: NavItem[]): string[] {
  return flatten(items).map((i) => i.key)
}
function findKey(items: NavItem[], key: string): NavItem | undefined {
  return flatten(items).find((i) => i.key === key)
}

const SESSIONS = {
  eNoCtx: {
    is_super_admin: true, permissions: [], effective_company_id: null,
    company_business_units: [], effective_business_units: [],
  },
  eAllOff: {
    is_super_admin: true, permissions: [], effective_company_id: 1,
    company_business_units: [], effective_business_units: [],
  },
  eBroilerOn: {
    is_super_admin: true, permissions: [], effective_company_id: 1,
    company_business_units: ['broiler'], effective_business_units: [],
  },
  aCbu: {
    is_super_admin: false, permissions: ['business_units:read', 'business_units:update', 'dashboard:read'],
    effective_company_id: 1, company_business_units: [], effective_business_units: [],
  },
  bAccess: {
    is_super_admin: false,
    permissions: ['business_units:read', 'business_units:update', 'business_units:create', 'business_units:delete'],
    effective_company_id: 1, company_business_units: [], effective_business_units: [],
  },
  cFull: {
    is_super_admin: false, permissions: ['operations:read', 'lots:read', 'dashboard:read'],
    effective_company_id: 1, company_business_units: ['grandparent', 'breeder', 'hatchery', 'broiler'],
    effective_business_units: ['broiler'],
  },
  cNoGrant: {
    is_super_admin: false, permissions: ['operations:read', 'lots:read', 'dashboard:read'],
    effective_company_id: 1, company_business_units: ['grandparent', 'breeder', 'hatchery', 'broiler'],
    effective_business_units: [],
  },
  cBuOff: {
    is_super_admin: false, permissions: ['operations:read', 'lots:read', 'dashboard:read'],
    effective_company_id: 1, company_business_units: [], effective_business_units: [],
  },
  dNoAuth: {
    is_super_admin: false, permissions: ['dashboard:read'],
    effective_company_id: 1, company_business_units: ['grandparent', 'breeder', 'hatchery', 'broiler'],
    effective_business_units: [],
  },
  zZeroBu: {
    is_super_admin: false, permissions: ['dashboard:read'],
    effective_company_id: 1, company_business_units: ['grandparent', 'breeder', 'hatchery', 'broiler'],
    effective_business_units: [],
  },
  pNoRbac: {
    is_super_admin: false, permissions: ['dashboard:read'],
    effective_company_id: 1, company_business_units: ['grandparent', 'breeder', 'hatchery', 'broiler'],
    effective_business_units: ['broiler'],
  },
} as const

describe('GA-FE-03 · canAccessCapability — dimensiones de autoridad', () => {
  it('un permiso ausente deniega SIEMPRE (aunque tenga unidades)', () => {
    expect(canAccessCapability({ permission: 'users:read' }, SESSIONS.pNoRbac)).toBe(false)
    expect(canAccessCapability({ permission: 'users:read' }, SESSIONS.bAccess)).toBe(false)
    expect(canAccessCapability({ permission: 'users:read' }, SESSIONS.eBroilerOn)).toBe(true)
  })

  it('unidad productiva: normal exige EFECTIVA, global exige HABILITADA + contexto', () => {
    expect(canAccessCapability({ permission: 'operations:read', businessUnit: 'broiler' }, SESSIONS.cFull)).toBe(true)
    expect(canAccessCapability({ permission: 'operations:read', businessUnit: 'breeder' }, SESSIONS.cFull)).toBe(false)
    expect(canAccessCapability({ permission: 'operations:read', businessUnit: 'broiler' }, SESSIONS.cNoGrant)).toBe(false)
    expect(canAccessCapability({ permission: 'operations:read', businessUnit: 'broiler' }, SESSIONS.cBuOff)).toBe(false)
    expect(canAccessCapability({ permission: 'operations:read', businessUnit: 'broiler' }, SESSIONS.eBroilerOn)).toBe(true)
    expect(canAccessCapability({ permission: 'operations:read', businessUnit: 'broiler' }, SESSIONS.eAllOff)).toBe(false)
    expect(canAccessCapability({ permission: 'operations:read', businessUnit: 'broiler' }, SESSIONS.eNoCtx)).toBe(false)
  })

  it('conjunto productivo «cualquiera»: exige ≥1 unidad disponible', () => {
    expect(canAccessCapability({ permission: 'reports:read', requiresUnits: true }, SESSIONS.eBroilerOn)).toBe(true)
    expect(canAccessCapability({ permission: 'reports:read', requiresUnits: true }, SESSIONS.eAllOff)).toBe(false)
    expect(canAccessCapability({ permission: 'reports:read', requiresUnits: true }, SESSIONS.eNoCtx)).toBe(false)
    expect(canAccessCapability({ permission: 'review:read', requiresUnits: true }, SESSIONS.cNoGrant)).toBe(false)
    expect(canAccessCapability({ permission: 'review:read', requiresUnits: true }, SESSIONS.cFull)).toBe(true)
  })

  it('el comodín global (is_super_admin) es la única vía de permiso global', () => {
    expect(canAccessCapability({ permission: 'audit:read' }, SESSIONS.eNoCtx)).toBe(true)
    expect(canAccessCapability({ permission: 'audit:read' }, SESSIONS.aCbu)).toBe(false)
  })
})

describe('GA-FE-03 · filterNavItemsBySession — política sobre el árbol real', () => {
  it('C con broiler: ve broiler, no las demás unidades; review/reports ocultos sin permiso', () => {
    const filtered = filterNavItemsBySession(NAV_ITEMS, SESSIONS.cFull)
    const k = keys(filtered)
    expect(k).toContain('broiler')
    expect(k).not.toContain('grandparent')
    expect(k).not.toContain('breeder')
    expect(k).not.toContain('hatchery')
    expect(k).not.toContain('review')
    expect(k).not.toContain('reports')
    expect(k).not.toContain('sap')
    expect(k).toContain('settings_profile')
  })

  it('Z (cero unidades): sin producto, sin grupos vacíos, CORE intacto', () => {
    const filtered = filterNavItemsBySession(NAV_ITEMS, SESSIONS.zZeroBu)
    const k = keys(filtered)
    expect(k).toContain('dashboard')
    expect(k).toContain('settings_profile')
    expect(k).not.toContain('poultry')
    expect(k).not.toContain('review')
    expect(k).not.toContain('approvals')
    expect(k).not.toContain('reports')
    expect(k).not.toContain('users')
    expect(findKey(filtered, 'settings')!.children!.map((c) => c.key)).toEqual(['settings_profile'])
  })

  it('E sin contexto: inquilino fail-closed; control global intacto', () => {
    const k = keys(filterNavItemsBySession(NAV_ITEMS, SESSIONS.eNoCtx))
    expect(k).not.toContain('poultry')
    expect(k).not.toContain('reports')
    expect(k).not.toContain('review')
    expect(k).toContain('users')
    expect(k).toContain('masters')
    expect(k).toContain('audit')
    expect(k).toContain('settings_unit_access')
  })

  it('E con broiler ON: solo la unidad habilitada + productivo multi-unidad', () => {
    const k = keys(filterNavItemsBySession(NAV_ITEMS, SESSIONS.eBroilerOn))
    expect(k).toContain('broiler')
    expect(k).not.toContain('grandparent')
    expect(k).not.toContain('breeder')
    expect(k).not.toContain('hatchery')
    expect(k).toContain('review')
    expect(k).toContain('reports')
  })

  it('E con TODO OFF: cero producto (BU OFF absoluto, global incluido)', () => {
    const k = keys(filterNavItemsBySession(NAV_ITEMS, SESSIONS.eAllOff))
    expect(k).not.toContain('poultry')
    expect(k).not.toContain('review')
    expect(k).not.toContain('reports')
    expect(k).toContain('dashboard')
  })

  it('D y B: sin superficies ajenas a su autoridad', () => {
    const kd = keys(filterNavItemsBySession(NAV_ITEMS, SESSIONS.dNoAuth))
    expect(kd).not.toContain('users')
    expect(kd).not.toContain('audit')
    expect(kd).not.toContain('masters')
    expect(kd).not.toContain('sap')
    const kb = keys(filterNavItemsBySession(NAV_ITEMS, SESSIONS.bAccess))
    expect(kb).toContain('settings_unit_access')
    expect(kb).not.toContain('users')
    expect(kb).not.toContain('poultry')
  })

  it('A: descubribilidad de su superficie y nada más', () => {
    const k = keys(filterNavItemsBySession(NAV_ITEMS, SESSIONS.aCbu))
    expect(k).toContain('settings_unit_access')
    expect(k).not.toContain('users')
    expect(k).not.toContain('poultry')
    expect(k).not.toContain('masters')
  })

  it('sin sesión: árbol vacío (el login no pinta navegación)', () => {
    expect(filterNavItemsBySession(NAV_ITEMS, null)).toEqual([])
  })
})

describe('GA-FE-03 · atajos del Dashboard derivan del mismo evaluador (§33)', () => {
  it('Z no ve atajos de unidades productivas; C ve solo su unidad; global solo habilitadas', () => {
    expect(stageVisibleForSession('broiler', SESSIONS.zZeroBu)).toBe(false)
    expect(stageVisibleForSession('broiler', SESSIONS.cFull)).toBe(true)
    expect(stageVisibleForSession('breeder', SESSIONS.cFull)).toBe(false)
    expect(stageVisibleForSession('hatchery', SESSIONS.cNoGrant)).toBe(false)
    expect(stageVisibleForSession('hatchery', SESSIONS.eBroilerOn)).toBe(false)
    expect(stageVisibleForSession('broiler', SESSIONS.eBroilerOn)).toBe(true)
  })
})

describe('GA-FE-03 · metadatos de la definición canónica', () => {
  it('todas las entradas declaran clase de capacidad', () => {
    for (const item of flatten(NAV_ITEMS)) {
      expect(item.capability, `capability ausente en ${item.key}`).toBeTruthy()
    }
  })

  it('las entradas productivas declaran su dependencia de unidad', () => {
    const productive = flatten(NAV_ITEMS).filter(
      (i) => i.capability === 'PRODUCTIVE' || i.capability === 'REPORTING',
    )
    expect(productive.length).toBeGreaterThan(0)
    for (const item of productive) {
      expect(
        item.businessUnit || item.requiresUnits,
        `dependencia BU ausente en ${item.key}`,
      ).toBeTruthy()
    }
  })

  it('ninguna entrada declara gating por nombre de rol/usuario (metadatos)', () => {
    for (const item of flatten(NAV_ITEMS)) {
      expect((item as any).roleName).toBeUndefined()
      expect((item as any).username).toBeUndefined()
    }
  })
})
