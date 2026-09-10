/**
 * GA-FE-02 · Navegación mínima administrativa (AC-NAV-01/02/03/05).
 *
 * La entrada de «Acceso por unidad» debe ser descubrible para actores con
 * `business_units:read`, invisible sin él, y el filtrado por permiso debe aplicarse SOLO a las
 * entradas que declaran `permission` (frontera R-98/GA-FE-03: el resto del menú no cambia).
 */
import { describe, it, expect } from 'vitest'
import { NAV_ITEMS, filterNavItemsByPermissions } from '../navigationConfig'

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
    const filtered = filterNavItemsByPermissions(NAV_ITEMS, {
      is_super_admin: false,
      permissions: ['business_units:read'],
    })
    expect(flatten(filtered).some((i) => i.to === '/admin/unit-access')).toBe(true)
  })

  it('el Super Administrador ve la entrada', () => {
    const filtered = filterNavItemsByPermissions(NAV_ITEMS, { is_super_admin: true, permissions: [] })
    expect(flatten(filtered).some((i) => i.to === '/admin/unit-access')).toBe(true)
  })

  it('un actor sin el permiso NO ve la entrada (AC-NAV-03)', () => {
    const filtered = filterNavItemsByPermissions(NAV_ITEMS, { is_super_admin: false, permissions: ['lots:read'] })
    expect(flatten(filtered).some((i) => i.to === '/admin/unit-access')).toBe(false)
  })

  it('sin sesión tampoco se muestra', () => {
    const filtered = filterNavItemsByPermissions(NAV_ITEMS, null)
    expect(flatten(filtered).some((i) => i.to === '/admin/unit-access')).toBe(false)
  })

  it('el resto del menú NO se filtra (frontera R-98/GA-FE-03, AC-NAV-05)', () => {
    const filtered = filterNavItemsByPermissions(NAV_ITEMS, { is_super_admin: false, permissions: ['lots:read'] })
    const before = flatten(NAV_ITEMS).filter((i) => !i.permission)
    const after = flatten(filtered).filter((i) => !i.permission)
    expect(after.map((i) => i.key).sort()).toEqual(before.map((i) => i.key).sort())
  })
})
