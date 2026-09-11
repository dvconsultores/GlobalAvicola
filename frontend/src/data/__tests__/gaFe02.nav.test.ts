/**
 * GA-FE-02 · Navegación mínima administrativa (AC-NAV-01/02/03/05).
 *
 * La entrada de «Acceso por unidad» debe ser descubrible para actores con
 * `business_units:read` e invisible sin él. GA-FE-03 cerró la frontera que esta suite
 * declaraba («el resto del menú no cambia»): ahora TODO el árbol se evalúa con
 * `filterNavItemsBySession` (RBAC + unidades). Las aserciones de GA-FE-02 siguen vigentes.
 */
import { describe, it, expect } from 'vitest'
import { NAV_ITEMS } from '../navigationConfig'
import { filterNavItemsBySession } from '../../auth/navigation'

function flatten(items: any[]): any[] {
  return items.flatMap((i) => [i, ...(i.children ? flatten(i.children) : [])])
}

const unitAccessEntry = () => flatten(NAV_ITEMS).find((i) => i.to === '/admin/unit-access')

describe('GA-FE-02 · navegación admin mínima', () => {
  it('existe una entrada hacia /admin/unit-access con permiso declarado', () => {
    const entry = unitAccessEntry()
    expect(entry).toBeTruthy()
    expect(entry.permission).toBe('business_units:read')
    expect(entry.labelKey).toBe('nav.unitAccess')
  })

  it('un actor con business_units:read ve la entrada', () => {
    const filtered = filterNavItemsBySession(NAV_ITEMS, {
      is_super_admin: false,
      permissions: ['business_units:read'],
      effective_company_id: 1,
      company_business_units: [],
      effective_business_units: [],
    })
    expect(flatten(filtered).some((i) => i.to === '/admin/unit-access')).toBe(true)
  })

  it('el Super Administrador ve la entrada', () => {
    const filtered = filterNavItemsBySession(NAV_ITEMS, {
      is_super_admin: true, permissions: [], effective_company_id: 1,
      company_business_units: [], effective_business_units: [],
    })
    expect(flatten(filtered).some((i) => i.to === '/admin/unit-access')).toBe(true)
  })

  it('un actor sin el permiso NO ve la entrada (AC-NAV-03)', () => {
    const filtered = filterNavItemsBySession(NAV_ITEMS, {
      is_super_admin: false, permissions: ['lots:read'], effective_company_id: 1,
      company_business_units: ['broiler'], effective_business_units: ['broiler'],
    })
    expect(flatten(filtered).some((i) => i.to === '/admin/unit-access')).toBe(false)
  })

  it('sin sesión no se muestra nada', () => {
    expect(filterNavItemsBySession(NAV_ITEMS, null)).toEqual([])
  })

  it('el resto del menú también se evalúa (frontera GA-FE-03 cerrada, AC-NAV-05)', () => {
    const filtered = filterNavItemsBySession(NAV_ITEMS, {
      is_super_admin: false, permissions: ['lots:read'], effective_company_id: 1,
      company_business_units: ['broiler'], effective_business_units: ['broiler'],
    })
    const keys = flatten(filtered).map((i) => i.key)
    expect(keys).not.toContain('users')
    expect(keys).not.toContain('audit')
    expect(keys).not.toContain('sap')
    expect(keys).not.toContain('poultry')
    expect(keys).toContain('settings_profile')
  })
})
