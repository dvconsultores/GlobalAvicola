/**
 * R-219 · RED jsdom — `AuditPage` lee el contrato real de la auditoría.
 *
 * Diseño: `specs/R-219/R-219_AC_RED_E2E_UAT.md` (AC-01…05).
 *
 * Rojo en HEAD:
 *   01 · el usuario se muestra como id numérico (`user_name` no existe en el esquema).
 *   02 · la pestaña Correcciones no muestra el diff (`old_value/new_value` no existen;
 *        los reales son `previous_values/new_values` y `previous_state/new_state`).
 *   03 · `comments` se ignora (solo viaja `change_reason`).
 *   04 · `limit=50` fijo sin paginador aunque el contador muestra `total`.
 *   05 · acciones/módulos se pintan crudos (sin i18n `audit.actions/modules`).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

const get = vi.fn()
vi.mock('../../../services/api', () => ({
  default: {
    get: (...a: any[]) => get(...a),
    post: vi.fn(), put: vi.fn(), patch: vi.fn(), delete: vi.fn(),
  },
}))
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (k: string, f?: any) => {
      if (k.startsWith('audit.actions.')) return `TR-${k.split('.').pop()}`
      if (k.startsWith('audit.modules.')) return `TM-${k.split('.').pop()}`
      return typeof f === 'string' ? f : k
    },
  }),
}))

import AuditPage from '../AuditPage'
import { useAuthStore } from '../../../stores/auth.store'

function setSession(permissions: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 9, username: 'r219-c', first_name: 'R', last_name: 'C', email: 'c@x.com',
      role_id: 1, view_type: 'web', is_super_admin: false, company_id: 1, effective_company_id: 1,
      permissions, company_business_units: ['broiler'], granted_business_units: ['broiler'],
      effective_business_units: ['broiler'],
    } as any,
  })
}

const USUARIO = { id: 7, username: 'ana', first_name: 'Ana', last_name: 'Pérez' }

const LOG_BASE = {
  id: 1, created_at: '2026-09-14T10:00:00Z', action: 'review_started',
  entity_type: 'operational_event', entity_id: '55', user_id: 7,
  module: 'review', previous_values: null, new_values: null,
  previous_state: null, new_state: null, change_reason: null, comments: null,
}

const renderPage = () =>
  render(
    <MemoryRouter>
      <AuditPage />
    </MemoryRouter>,
  )

beforeEach(() => {
  get.mockReset()
  useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false, token: null })
})

describe('R-219 · AuditPage contra el contrato real (RED)', () => {
  it('01 · muestra el nombre del usuario (con permiso users:read)', async () => {
    setSession(['audit:read', 'users:read'])
    get.mockImplementation((url: string) => {
      if (String(url).startsWith('/users')) return Promise.resolve({ data: { users: [USUARIO], total: 1 } })
      return Promise.resolve({ data: { logs: [LOG_BASE], total: 1 } })
    })
    renderPage()
    await waitFor(() => expect(screen.getByText('Ana Pérez')).toBeTruthy())
  })

  it('02 · Correcciones muestra el diff real (previous_values → new_values)', async () => {
    setSession(['audit:read'])
    get.mockResolvedValue({ data: { logs: [{
      ...LOG_BASE, id: 2, action: 'corrected',
      previous_values: { quantity: 10 }, new_values: { quantity: 20 },
    }], total: 1 } })
    renderPage()
    fireEvent.click(await screen.findByRole('button', { name: 'audit.corrections' }))
    await waitFor(() => expect(screen.getByText(/10\s*→\s*20/)).toBeTruthy())
  })

  it('03 · motivo y comentario visibles cuando existen', async () => {
    setSession(['audit:read'])
    get.mockResolvedValue({ data: { logs: [{
      ...LOG_BASE, id: 3,
      change_reason: 'Motivo: error de digitación',
      comments: 'Nota del auditor',
    }], total: 1 } })
    renderPage()
    await waitFor(() => expect(screen.getByText(/Motivo: error de digitación/)).toBeTruthy())
    expect(screen.getByText(/Nota del auditor/)).toBeTruthy()
  })

  it('04 · paginador con total (50 por página)', async () => {
    setSession(['audit:read'])
    const pagina2 = { ...LOG_BASE, id: 99, action: 'login' }
    get.mockImplementation((url: string) => {
      if (String(url).includes('offset=50')) return Promise.resolve({ data: { logs: [pagina2], total: 120 } })
      return Promise.resolve({ data: { logs: [LOG_BASE], total: 120 } })
    })
    renderPage()
    const siguiente = await screen.findByRole('button', { name: /Siguiente/ })
    fireEvent.click(siguiente)
    await waitFor(() => expect(
      get.mock.calls.some((c) => String(c[0]).includes('offset=50')),
    ).toBe(true))
    await waitFor(() => expect(screen.getByText('TR-login')).toBeTruthy())
  })

  it('05 · acciones traducidas (sin crudos)', async () => {
    setSession(['audit:read'])
    get.mockResolvedValue({ data: { logs: [LOG_BASE], total: 1 } })
    renderPage()
    await waitFor(() => expect(screen.getByText('TR-review_started')).toBeTruthy())
    expect(screen.queryByText('review_started')).toBeNull()
  })
})
