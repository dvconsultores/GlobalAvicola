/**
 * GA-FE-08 · RED — Descubribilidad de «Lotes» (OBS-UAT-01).
 *
 * Estado pre-fix (`30fe3dc`): `NAV_ITEMS` no contiene ninguna entrada hacia `/lots`;
 * el usuario autorizado solo alcanza la superficie por URL directa. Estas pruebas fijan
 * el contrato deseado de la tranche (SPEC GA-FE-08) y fallan en rojo hasta la implementación.
 *
 * Marco: GA-FE-03 (evaluador único) — `nav.lots` ya existe en ES/EN y se REUSA; sin claves nuevas.
 */
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import {
  NAV_ITEMS,
  getNavItemsForViewType,
  isPathActive,
  isAnyChildActive,
  type NavItem,
} from '../../data/navigationConfig'
import { filterNavItemsBySession } from '../../auth/navigation'

function flatten(items: NavItem[]): NavItem[] {
  return items.flatMap((i) => [i, ...(i.children ? flatten(i.children) : [])])
}
function keys(items: NavItem[]): string[] {
  return flatten(items).map((i) => i.key)
}
function findKey(items: NavItem[], key: string): NavItem | undefined {
  return flatten(items).find((i) => i.key === key)
}

/** Sesiones espejo del contrato `/me` (mismos campos que GA-FE-03). */
const S = {
  /** Autorizado: empresa + unidad efectiva + RBAC de lotes. */
  op: { is_super_admin: false, permissions: ['dashboard:read', 'operations:read', 'lots:read'], effective_company_id: 1, company_business_units: ['grandparent', 'breeder', 'hatchery', 'broiler'], effective_business_units: ['broiler'] },
  /** RBAC-lotes ausente (pero unidades y empresa OK). */
  noLots: { is_super_admin: false, permissions: ['dashboard:read', 'operations:read'], effective_company_id: 1, company_business_units: ['grandparent', 'breeder', 'hatchery', 'broiler'], effective_business_units: ['broiler'] },
  /** Sin concesión de unidad (BU negativa). */
  noGrant: { is_super_admin: false, permissions: ['dashboard:read', 'operations:read', 'lots:read'], effective_company_id: 1, company_business_units: [], effective_business_units: [] },
  /** Empresa con unidades OFF (absoluto OD-16). */
  buOff: { is_super_admin: false, permissions: ['dashboard:read', 'operations:read', 'lots:read'], effective_company_id: 1, company_business_units: [], effective_business_units: [] },
  /** Zero-BU (solo CORE). */
  zeroBu: { is_super_admin: false, permissions: ['dashboard:read'], effective_company_id: 1, company_business_units: ['grandparent', 'breeder', 'hatchery', 'broiler'], effective_business_units: [] },
  /** Access Administrator (control-plane puro). */
  adm: { is_super_admin: false, permissions: ['business_units:read', 'business_units:update', 'business_units:create', 'business_units:delete'], effective_company_id: 1, company_business_units: [], effective_business_units: [] },
  eNoCtx: { is_super_admin: true, permissions: [], effective_company_id: null, company_business_units: [], effective_business_units: [] },
  eOn: { is_super_admin: true, permissions: [], effective_company_id: 1, company_business_units: ['broiler'], effective_business_units: [] },
} as const

describe('GA-FE-08 · contrato de la entrada «Lotes»', () => {
  it('existe una entrada declarativa hacia la ruta existente /lots, con permiso y dependencia de unidad declarados (AC01-04)', () => {
    const lots = findKey(NAV_ITEMS, 'lots')
    expect(lots, 'entrada «lots» ausente en NAV_ITEMS (OBS-UAT-01)').toBeTruthy()
    expect(lots!.to).toBe('/lots')
    expect(lots!.labelKey).toBe('nav.lots')
    expect(lots!.permission).toBe('lots:read')
    expect(lots!.capability).toBe('PRODUCTIVE')
    expect(lots!.requiresUnits).toBe(true)
    expect(lots!.section).toBe('operational')
    // Sin ruta duplicada (AC04).
    expect(flatten(NAV_ITEMS).filter((i) => i.to === '/lots')).toHaveLength(1)
  })

  it('vive bajo Gestión Avícola como primera opción del hub, sin raíz nueva (AC19, AC26)', () => {
    const poultry = findKey(NAV_ITEMS, 'poultry')
    expect(poultry?.children?.[0]?.key).toBe('lots')
  })

  it('el operador autorizado descubre «Lotes» (AC01/02)', () => {
    const filtered = filterNavItemsBySession(NAV_ITEMS, S.op)
    const poultry = findKey(filtered, 'poultry')
    expect(poultry?.children?.some((c) => c.key === 'lots' && c.to === '/lots')).toBe(true)
  })

  it('sin el permiso de lotes no hay entrada (AC11)', () => {
    expect(keys(filterNavItemsBySession(NAV_ITEMS, S.noLots))).not.toContain('lots')
  })

  it('sin unidades efectivas (BU negativa) no hay entrada ni raíz productiva (AC08)', () => {
    const k = keys(filterNavItemsBySession(NAV_ITEMS, S.noGrant))
    expect(k).not.toContain('lots')
    expect(k).not.toContain('poultry')
  })

  it('empresa con BU OFF: sin producto, global incluido (AC07, AC14)', () => {
    expect(keys(filterNavItemsBySession(NAV_ITEMS, S.buOff))).not.toContain('lots')
    const eAllOff = { ...S.eOn, company_business_units: [] }
    expect(keys(filterNavItemsBySession(NAV_ITEMS, eAllOff))).not.toContain('lots')
  })

  it('OD-23: la concesión histórica terminada NO revive; la concesión fresca sí (AC09/10)', () => {
    const historica = { ...S.op, effective_business_units: [] }
    expect(keys(filterNavItemsBySession(NAV_ITEMS, historica))).not.toContain('lots')
    expect(keys(filterNavItemsBySession(NAV_ITEMS, S.op))).toContain('lots')
  })

  it('zero-BU y Access Administrator no obtienen «Lotes» (AC12/13)', () => {
    expect(keys(filterNavItemsBySession(NAV_ITEMS, S.zeroBu))).not.toContain('lots')
    expect(keys(filterNavItemsBySession(NAV_ITEMS, S.adm))).not.toContain('lots')
  })

  it('actor global: sin contexto fail-closed; con unidad habilitada descubre (AC06/14)', () => {
    expect(keys(filterNavItemsBySession(NAV_ITEMS, S.eNoCtx))).not.toContain('lots')
    expect(keys(filterNavItemsBySession(NAV_ITEMS, S.eOn))).toContain('lots')
  })
})

describe('GA-FE-08 · vistas y estado activo', () => {
  it('la entrada viaja en ambas vistas: web completa y móvil bajo Gestión Avícola (AC19/20)', () => {
    expect(flatten(getNavItemsForViewType('web')).some((i) => i.key === 'lots')).toBe(true)
    const mobile = getNavItemsForViewType('mobile')
    const poultry = findKey(mobile, 'poultry')
    expect(poultry?.children?.some((c) => c.key === 'lots')).toBe(true)
  })

  it('la ruta activa cubre lista y detalle y resalta el contenedor (AC05)', () => {
    expect(isPathActive('/lots', '/lots')).toBe(true)
    expect(isPathActive('/lots/54', '/lots')).toBe(true)
    expect(isPathActive('/lotss', '/lots')).toBe(false)
    const poultry = findKey(NAV_ITEMS, 'poultry')!
    expect(isAnyChildActive('/lots', poultry)).toBe(true)
    expect(isAnyChildActive('/lots/54', poultry)).toBe(true)
  })
})

describe('GA-FE-08 · i18n por reuso', () => {
  function load(lang: string): any {
    return JSON.parse(readFileSync(resolve(process.cwd(), `public/locales/${lang}/translation.json`), 'utf-8'))
  }
  it('nav.lots existe en ES («Lotes») y EN («Lots») — clave reusada, sin copy nuevo (AC21-23)', () => {
    expect(load('es').nav.lots).toBe('Lotes')
    expect(load('en').nav.lots).toBe('Lots')
  })
})
