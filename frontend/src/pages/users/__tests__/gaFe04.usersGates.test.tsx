/**
 * GA-FE-04 · RED — UsersPage (P-13: página ≠ acción).
 * R = solo lectura administrativa (`users:read`): VE el listado, NO ve controles de escritura.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

const get = vi.fn()
const post = vi.fn()
const put = vi.fn()
const del = vi.fn()
vi.mock('../../../services/api', () => ({
  default: {
    get: (...a: any[]) => get(...a), post: (...a: any[]) => post(...a),
    put: (...a: any[]) => put(...a), delete: (...a: any[]) => del(...a),
  },
}))
vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (k: string, f?: string) => f ?? k }) }))

import UsersPage from '../UsersPage'
import { useAuthStore } from '../../../stores/auth.store'

const USERS = [{ id: 7, username: 'ana', first_name: 'Ana', last_name: 'D', email: 'a@x.com', role_id: 2, view_type: 'web', is_active: true }]
const ROLES = [{ id: 2, name: 'Operador' }]

function setSession(permissions: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 99, username: 'probe', first_name: 'P', last_name: 'Q', email: 'p@x.com',
      role_id: 3, view_type: 'web', is_super_admin: false, company_id: 1, effective_company_id: 1,
      permissions,
      company_business_units: [], granted_business_units: [], effective_business_units: [],
    } as any,
  })
}

beforeEach(() => {
  get.mockReset(); post.mockReset(); put.mockReset(); del.mockReset()
  get.mockImplementation((url: string) => {
    if (url.includes('/users')) return Promise.resolve({ data: USERS })
    if (url.includes('/roles')) return Promise.resolve({ data: ROLES })
    return Promise.resolve({ data: [] })
  })
})

describe('GA-FE-04 · UsersPage — autoridad de acción', () => {
  it('R (users:read): ve el listado y NINGÚN control de escritura', async () => {
    setSession(['users:read'])
    render(<MemoryRouter><UsersPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getAllByText('ana').length).toBeGreaterThan(0))
    expect(screen.queryByText('common.create')).toBeNull()
    expect(document.querySelectorAll('.lucide-pencil').length).toBe(0)
    expect(document.querySelectorAll('.lucide-trash-2').length).toBe(0)
  })

  it('control: con users:* los controles aparecen', async () => {
    setSession(['users:read', 'users:create', 'users:update', 'users:delete'])
    render(<MemoryRouter><UsersPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getAllByText('ana').length).toBeGreaterThan(0))
    expect(screen.getByText('common.create')).toBeTruthy()
    expect(document.querySelectorAll('.lucide-pencil').length).toBeGreaterThan(0)
    expect(document.querySelectorAll('.lucide-trash-2').length).toBeGreaterThan(0)
  })
})
