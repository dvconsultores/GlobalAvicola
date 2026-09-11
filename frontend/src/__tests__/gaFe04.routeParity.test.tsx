/**
 * GA-FE-04 · RED — Paridad de rutas (§“ROUTE/SCREEN/API PERMISSION PARITY”).
 * R (solo lectura administrativa) escribe la URL directa de una pantalla de alta:
 * debe recibir la negativa visual (guarda independiente) — hoy renderiza la página.
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
    get: (...a: any[]) => get(...a), post: (...a: any[]) => post(...a),
    put: (...a: any[]) => put(...a), patch: (...a: any[]) => patch(...a), delete: (...a: any[]) => del(...a),
  },
}))
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (k?: string, f?: string) => f ?? k, i18n: { resolvedLanguage: 'es', language: 'es', changeLanguage: vi.fn() } }),
}))
vi.mock('../i18n', () => ({ normalizeLanguage: () => 'es', nextLanguage: () => 'en' }))
vi.mock('../hooks/useTelegram', () => ({
  useTelegram: () => ({ enableClosingConfirmation: vi.fn(), isAvailable: false }),
  useTelegramBackHandler: () => undefined,
}))
vi.mock('../components/notifications/NotificationBell', () => ({ default: () => null }))

import App from '../App'
import { useAuthStore } from '../stores/auth.store'

function setSession(permissions: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 99, username: 'probe', first_name: 'P', last_name: 'Q', email: 'p@x.com',
      role_id: 3, view_type: 'web', is_super_admin: false, company_id: 1, effective_company_id: 1,
      permissions, company_business_units: ['broiler'], granted_business_units: [], effective_business_units: [],
    } as any,
  })
}

function renderAt(path: string) {
  return render(<MemoryRouter initialEntries={[path]}><App /></MemoryRouter>)
}
const denied = () => screen.queryByText('common.noPermission')

beforeEach(() => {
  get.mockClear(); post.mockClear()
  useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false, token: null })
})

describe('GA-FE-04 · Paridad ruta↔acción (deep links de alta)', () => {
  it('R: /lots/new ⇒ negativa visual', async () => {
    setSession(['users:read', 'masters:read'])
    renderAt('/lots/new')
    expect(denied()).not.toBeNull()
  })

  it('R: /operations/new ⇒ negativa visual', async () => {
    setSession(['users:read', 'masters:read'])
    renderAt('/operations/new')
    expect(denied()).not.toBeNull()
  })

  it('R: /review/1/correct ⇒ negativa visual (sin corrections:correct)', async () => {
    setSession(['users:read', 'masters:read', 'review:read', 'review:review'])
    renderAt('/review/1/correct')
    expect(denied()).not.toBeNull()
  })

  it('control: C con create en su unidad ⇒ /lots/new permitido', async () => {
    setSession(['lots:read', 'lots:create', 'operations:read', 'operations:create', 'dashboard:read'])
    useAuthStore.setState({
      user: {
        ...(useAuthStore.getState().user as any),
        effective_business_units: ['broiler'], granted_business_units: ['broiler'],
      },
    })
    renderAt('/lots/new')
    expect(denied()).toBeNull()
  })
})
