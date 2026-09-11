/**
 * GA-FE-03 · RED comportamental — guardas de ruta independientes del menú (§24/§36).
 *
 * Hoy solo `/admin/unit-access` valida permiso. El objetivo: TODA ruta con permiso canónico
 * inequívoco falla cerrada visualmente para quien no lo tiene, y las rutas productivas que
 * nombran unidad fallan cerradas por elegibilidad BU (efectiva normal / habilitada global con
 * contexto). La autoridad final sigue siendo el backend (403/404) — aquí se prueba la capa UI.
 *
 * `t(k, f) => f ?? k` ⇒ el mensaje fail-closed se lee como la clave `admin.forbidden`.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

const get = vi.fn(() => Promise.resolve({ data: [] }))
const post = vi.fn(() => Promise.resolve({ data: {} }))
const put = vi.fn(() => Promise.resolve({ data: {} }))
const patch = vi.fn(() => Promise.resolve({ data: {} }))
const del = vi.fn(() => Promise.resolve({ data: {} }))

vi.mock('../services/api', () => ({
  default: {
    get: (...a: any[]) => get(...a),
    post: (...a: any[]) => post(...a),
    put: (...a: any[]) => put(...a),
    patch: (...a: any[]) => patch(...a),
    delete: (...a: any[]) => del(...a),
  },
}))

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (k?: string, f?: string) => f ?? k,
    i18n: { resolvedLanguage: 'es', language: 'es', changeLanguage: vi.fn() },
  }),
}))

vi.mock('../i18n', () => ({
  normalizeLanguage: () => 'es',
  nextLanguage: () => 'en',
}))

vi.mock('../hooks/useTelegram', () => ({
  useTelegram: () => ({ enableClosingConfirmation: vi.fn(), isAvailable: false }),
  useTelegramBackHandler: () => undefined,
}))

vi.mock('../components/notifications/NotificationBell', () => ({ default: () => null }))

import App from '../App'
import { useAuthStore } from '../stores/auth.store'

function setSession(permissions: string[], effective: string[], enabled: string[], opts: { isSuper?: boolean; ctx?: number | null } = {}) {
  useAuthStore.setState({
    isAuthenticated: true,
    isLoading: false,
    token: null,
    user: {
      id: 9, username: 'tester', first_name: 'T', last_name: 'T', email: 't@x.com',
      role_id: 99, view_type: 'web', is_super_admin: opts.isSuper ?? false,
      company_id: 1, effective_company_id: opts.ctx === undefined ? 1 : opts.ctx,
      permissions,
      company_business_units: enabled,
      granted_business_units: effective,
      effective_business_units: effective,
    } as any,
  })
}

function renderAt(path: string) {
  return render(<MemoryRouter initialEntries={[path]}><App /></MemoryRouter>)
}

const forbidden = () => screen.queryByText('admin.forbidden')

beforeEach(() => {
  useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false, token: null })
})

describe('GA-FE-03 · guardas de ruta (fail-closed visual, sin depender del menú)', () => {
  it('D: /users, /roles, /audit, /masters/farms, /sap → denegadas', () => {
    const paths = ['/users', '/roles', '/audit', '/masters/farms', '/sap']
    for (const p of paths) {
      setSession(['dashboard:read'], [], ['broiler'])
      const { unmount } = renderAt(p)
      expect(forbidden(), `debe denegar ${p}`).not.toBeNull()
      unmount()
    }
  })

  it('Z: /review, /approvals, /reports → denegadas (sin permiso y sin unidades)', () => {
    for (const p of ['/review', '/approvals', '/reports']) {
      setSession(['dashboard:read'], [], ['broiler'])
      const { unmount } = renderAt(p)
      expect(forbidden(), `debe denegar ${p}`).not.toBeNull()
      unmount()
    }
  })

  it('D: /lots → denegada (sin lots:read)', () => {
    setSession(['dashboard:read'], [], ['broiler'])
    renderAt('/lots')
    expect(forbidden()).not.toBeNull()
  })

  it('D: /poultry/breeder → denegada (sin operations:read)', () => {
    setSession(['dashboard:read'], [], ['broiler'])
    renderAt('/poultry/breeder')
    expect(forbidden()).not.toBeNull()
  })

  it('D: /poultry (hub web) → denegada; C con broiler → permitida', () => {
    setSession(['dashboard:read'], [], ['broiler'])
    const first = renderAt('/poultry')
    expect(forbidden()).not.toBeNull()
    first.unmount()

    setSession(['operations:read', 'lots:read'], ['broiler'], ['broiler'])
    renderAt('/poultry')
    expect(forbidden()).toBeNull()
  })

  it('C con concesión solo de broiler: /poultry/breeder denegada por unidad; /poultry/broiler permitida', () => {
    setSession(['operations:read', 'lots:read'], ['broiler'], ['grandparent', 'breeder', 'hatchery', 'broiler'])
    const first = renderAt('/poultry/breeder')
    expect(forbidden()).not.toBeNull()
    first.unmount()

    setSession(['operations:read', 'lots:read'], ['broiler'], ['grandparent', 'breeder', 'hatchery', 'broiler'])
    renderAt('/poultry/broiler')
    expect(forbidden()).toBeNull()
  })

  it('E sin contexto: /poultry/broiler falla cerrada; el control global sigue accesible', () => {
    setSession([], [], [], { isSuper: true, ctx: null })
    const first = renderAt('/poultry/broiler')
    expect(forbidden()).not.toBeNull()
    first.unmount()

    setSession([], [], [], { isSuper: true, ctx: null })
    renderAt('/masters/farms')
    expect(forbidden()).toBeNull()
  })

  it('control verde existente: /admin/unit-access ya deniega para D (referencia)', () => {
    setSession(['dashboard:read'], [], [])
    renderAt('/admin/unit-access')
    expect(forbidden()).not.toBeNull()
  })
})
