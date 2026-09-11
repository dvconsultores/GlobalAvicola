/**
 * GA-FE-04 · RED — SAP Manager: mutaciones por `sap:send_sap`.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

const get = vi.fn()
const post = vi.fn()
vi.mock('../../../services/api', () => ({
  default: { get: (...a: any[]) => get(...a), post: (...a: any[]) => post(...a) },
}))
vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (k: string, f?: string) => f ?? k }) }))
vi.mock('../../../components/Toast', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() }),
  getErrorMessage: (_e: any, f: string) => f,
}))

import SapManagerPage from '../SapManagerPage'
import { useAuthStore } from '../../../stores/auth.store'

function setSession(permissions: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 99, username: 'probe', first_name: 'P', last_name: 'Q', email: 'p@x.com',
      role_id: 3, view_type: 'web', is_super_admin: false, company_id: 1, effective_company_id: 1,
      permissions, company_business_units: [], granted_business_units: [], effective_business_units: [],
    } as any,
  })
}

beforeEach(() => {
  get.mockReset(); post.mockReset()
  get.mockImplementation(() => Promise.resolve({ data: [] }))
})

describe('GA-FE-04 · SapManagerPage — autoridad de acción', () => {
  it('solo sap:read ⇒ sin Consolidar ni Exportar', async () => {
    setSession(['sap:read'])
    render(<MemoryRouter><SapManagerPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByText('Integración SAP')).toBeTruthy())
    expect(screen.queryByRole('button', { name: /Consolidar/ })).toBeNull()
    expect(screen.queryByRole('button', { name: /Exportar/ })).toBeNull()
  })

  it('control: con sap:send_sap ⇒ controles visibles', async () => {
    setSession(['sap:read', 'sap:send_sap'])
    render(<MemoryRouter><SapManagerPage /></MemoryRouter>)
    await waitFor(() => expect(screen.getByText('Integración SAP')).toBeTruthy())
    expect(screen.getAllByRole('button', { name: /Consolidar/ }).length).toBeGreaterThan(0)
    expect(screen.getAllByRole('button', { name: /Exportar/ }).length).toBeGreaterThan(0)
  })
})
