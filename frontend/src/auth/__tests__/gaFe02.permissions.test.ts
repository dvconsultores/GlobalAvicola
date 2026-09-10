/**
 * GA-FE-02 · Helper mínimo de permisos — espejo EXACTO de `tiene_permiso` del backend
 * (`backend/app/auth/security.py:199-230`):
 *   - Super Admin (comodín) pasa siempre
 *   - `modulo:accion` exacto, o comodín de módulo `*:accion`
 * Autoridad por PERMISO, nunca por nombre de rol (`OD-09 §3.1`, `AC-UI-06`).
 */
import { describe, it, expect } from 'vitest'
import { hasPermission } from '../permissions'

const admin = { is_super_admin: false, permissions: ['business_units:read', 'business_units:update'] }
const accessAdmin = {
  is_super_admin: false,
  permissions: ['business_units:read', 'business_units:update', 'business_units:create', 'business_units:delete'],
}
const ordinary = { is_super_admin: false, permissions: ['lots:read'] }
const superAdmin = { is_super_admin: true, permissions: ['*:read', '*:create'] }

describe('GA-FE-02 · hasPermission', () => {
  it('permite cuando el permiso exacto está presente', () => {
    expect(hasPermission(admin, 'business_units:read')).toBe(true)
    expect(hasPermission(admin, 'business_units:update')).toBe(true)
  })

  it('deniega cuando falta el permiso', () => {
    expect(hasPermission(admin, 'business_units:create')).toBe(false)
    expect(hasPermission(admin, 'business_units:delete')).toBe(false)
    expect(hasPermission(ordinary, 'business_units:read')).toBe(false)
  })

  it('un actor ordinario con permiso ajeno no obtiene el de unidades', () => {
    expect(hasPermission(ordinary, 'business_units:read')).toBe(false)
  })

  it('el Super Administrador (comodín) pasa siempre', () => {
    expect(hasPermission(superAdmin, 'business_units:read')).toBe(true)
    expect(hasPermission(superAdmin, 'business_units:update')).toBe(true)
  })

  it('admite el comodín de módulo `*:accion`', () => {
    const wildcardRead = { is_super_admin: false, permissions: ['*:read'] }
    expect(hasPermission(wildcardRead, 'business_units:read')).toBe(true)
    expect(hasPermission(wildcardRead, 'business_units:create')).toBe(false)
  })

  it('sin sesión no autoriza nada (fail-closed)', () => {
    expect(hasPermission(null, 'business_units:read')).toBe(false)
    expect(hasPermission(undefined, 'business_units:read')).toBe(false)
    expect(hasPermission({}, 'business_units:read')).toBe(false)
  })

  it('el Administrador de Accesos obtiene exactamente sus cuatro capacidades', () => {
    for (const p of ['business_units:read', 'business_units:update', 'business_units:create', 'business_units:delete']) {
      expect(hasPermission(accessAdmin, p)).toBe(true)
    }
    expect(hasPermission(accessAdmin, 'users:read')).toBe(false)
    expect(hasPermission(accessAdmin, 'lots:write')).toBe(false)
  })
})
