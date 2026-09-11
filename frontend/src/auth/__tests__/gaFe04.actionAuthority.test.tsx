/**
 * GA-FE-04 · Capa de autoridad de acción (RED inicial — módulo objetivo inexistente).
 *
 * Contrato: la autoridad de una ACCIÓN de pantalla usa el MISMO vocabulario y evaluador que
 * la navegación (`auth/navigation.canAccessCapability`), reexpuestos como capa de acción:
 * `canPerformAction(spec, session)` y `<ActionGate spec={…}>` (declarativo).
 * P-13: página ≠ acción · AC-FE16: «quien solo lee no ve acciones de escritura».
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { canPerformAction, ActionGate } from '../actionAuthority'

const SESS = {
  rRead: {
    is_super_admin: false, permissions: ['users:read', 'masters:read'],
    effective_company_id: 1, company_business_units: [], effective_business_units: [],
  },
  rFull: {
    is_super_admin: false, permissions: ['users:read', 'users:create', 'users:update', 'users:delete'],
    effective_company_id: 1, company_business_units: [], effective_business_units: [],
  },
  e: {
    is_super_admin: true, permissions: [],
    effective_company_id: 1, company_business_units: ['broiler'], effective_business_units: [],
  },
  eNoCtx: {
    is_super_admin: true, permissions: [],
    effective_company_id: null, company_business_units: [], effective_business_units: [],
  },
  c: {
    is_super_admin: false, permissions: ['operations:read', 'operations:create'],
    effective_company_id: 1, company_business_units: ['broiler'], effective_business_units: ['broiler'],
  },
  cNoGrant: {
    is_super_admin: false, permissions: ['operations:read', 'operations:create'],
    effective_company_id: 1, company_business_units: ['broiler'], effective_business_units: [],
  },
}

describe('GA-FE-04 · canPerformAction (capa de acción sobre el evaluador GA-FE-03)', () => {
  it('permiso ausente ⇒ acción no permitida; presente ⇒ permitida', () => {
    expect(canPerformAction({ permission: 'users:create' }, SESS.rRead)).toBe(false)
    expect(canPerformAction({ permission: 'users:create' }, SESS.rFull)).toBe(true)
  })

  it('el comodín global es la única autoridad global', () => {
    expect(canPerformAction({ permission: 'users:delete' }, SESS.e)).toBe(true)
    expect(canPerformAction({ permission: 'users:delete' }, SESS.rRead)).toBe(false)
  })

  it('acción productiva: exige permiso ∧ unidad (efectiva normal / habilitada+contexto global)', () => {
    expect(canPerformAction({ permission: 'operations:create', businessUnit: 'broiler' }, SESS.c)).toBe(true)
    expect(canPerformAction({ permission: 'operations:create', businessUnit: 'broiler' }, SESS.cNoGrant)).toBe(false)
    expect(canPerformAction({ permission: 'operations:create', businessUnit: 'broiler' }, SESS.e)).toBe(true)
    expect(canPerformAction({ permission: 'operations:create', businessUnit: 'broiler' }, SESS.eNoCtx)).toBe(false)
  })

  it('sin sesión nada es accionable', () => {
    expect(canPerformAction({ permission: 'users:read' }, null)).toBe(false)
  })
})

describe('GA-FE-04 · ActionGate (declarativo)', () => {
  it('oculta el control cuando falta la autoridad y lo pinta cuando existe', () => {
    const { rerender } = render(
      <ActionGate spec={{ permission: 'users:create' }} session={SESS.rRead}>
        <button>ALTA</button>
      </ActionGate>,
    )
    expect(screen.queryByText('ALTA')).toBeNull()
    rerender(
      <ActionGate spec={{ permission: 'users:create' }} session={SESS.rFull}>
        <button>ALTA</button>
      </ActionGate>,
    )
    expect(screen.getByText('ALTA')).toBeTruthy()
  })
})
