/**
 * GA-FE-02-B · F4 — Selector de empresa alcanzable para la autoridad global (CAP-SES-05).
 *
 * OD-14: la autoridad global sin contexto debe poder ELEGIR empresa desde la UI normal.
 * RED de esta tranche: con `effective_company_id = null` y sin nombre de empresa, el bloque
 * del selector no se renderiza (condición `activeCompanyName || user?.company_name`) y el
 * camino de recuperación queda circular. Controles: usuario sin autoridad ⇒ sin selector.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

const get = vi.fn()
const post = vi.fn()

vi.mock('../../../services/api', () => ({
  default: { get: (...a: any[]) => get(...a), post: (...a: any[]) => post(...a) },
}))

vi.mock('../../notifications/NotificationBell', () => ({ default: () => null }))

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (k: string, f?: string) => f ?? k,
    i18n: { resolvedLanguage: 'es', changeLanguage: vi.fn() },
  }),
}))

vi.mock('../../../i18n', () => ({
  normalizeLanguage: () => 'es',
  nextLanguage: () => 'en',
}))

import Header from '../Header'
import { useAuthStore } from '../../../stores/auth.store'
import { useCompanyStore } from '../../../stores/company.store'

function setUser(over: Record<string, unknown> = {}) {
  useAuthStore.setState({
    user: {
      id: 1, username: 'admin', first_name: 'Admin', last_name: 'Sistema',
      email: 'admin@globalavicola.com', role_id: 1, view_type: 'web',
      is_super_admin: true, company_id: null, company_name: null,
      effective_company_id: null, permissions: ['*:read'],
      ...over,
    } as any,
  })
}

beforeEach(() => {
  get.mockReset(); post.mockReset()
  useAuthStore.setState({ user: null } as any)
  useCompanyStore.setState({ activeCompanyId: null, activeCompanyName: null, companies: [], isSwitching: false } as any)
})

describe('F4 · Header — alcanzabilidad del selector', () => {
  it('autoridad global SIN contexto: el selector es visible (RED antes del fix)', () => {
    setUser({ is_super_admin: true })
    render(<MemoryRouter><Header /></MemoryRouter>)
    expect(screen.getByTitle('company.selector')).toBeInTheDocument()
  })

  it('autoridad global CON empresa activa: selector presente', () => {
    setUser({ is_super_admin: true })
    useCompanyStore.setState({ activeCompanyId: 1, activeCompanyName: 'Avícola Global C.A.' } as any)
    render(<MemoryRouter><Header /></MemoryRouter>)
    expect(screen.getByTitle('company.selector')).toBeInTheDocument()
  })

  it('usuario común con empresa: badge sin selector', () => {
    setUser({ is_super_admin: false, company_id: 1, company_name: 'Avícola Global C.A.' })
    useCompanyStore.setState({ activeCompanyId: 1, activeCompanyName: 'Avícola Global C.A.' } as any)
    render(<MemoryRouter><Header /></MemoryRouter>)
    expect(screen.queryByTitle('company.selector')).toBeNull()
  })

  it('usuario común sin empresa: sin selector', () => {
    setUser({ is_super_admin: false })
    render(<MemoryRouter><Header /></MemoryRouter>)
    expect(screen.queryByTitle('company.selector')).toBeNull()
  })
})

describe('F4 · fetchMe — nombre de la empresa efectiva con persistida nula (bootstrap admin)', () => {
  it('resuelve el nombre por el catálogo cuando la persistida es null', async () => {
    get.mockImplementation((url: string) => {
      if (url === '/me') {
        return Promise.resolve({
          data: {
            id: 1, username: 'admin', first_name: 'Admin', last_name: 'Sistema',
            email: 'admin@globalavicola.com', role_id: 1, view_type: 'web',
            is_active: true, is_super_admin: true, company_id: null,
            company_name: null, effective_company_id: 1, permissions: ['*:read'],
          },
        })
      }
      if (String(url).startsWith('/masters/companies')) {
        return Promise.resolve({ data: [{ id: 1, name: 'Avícola Global C.A.', is_active: true }] })
      }
      return Promise.resolve({ data: [] })
    })
    await useAuthStore.getState().fetchMe()
    expect(useCompanyStore.getState().activeCompanyId).toBe(1)
    expect(useCompanyStore.getState().activeCompanyName).toBe('Avícola Global C.A.')
  })
})
