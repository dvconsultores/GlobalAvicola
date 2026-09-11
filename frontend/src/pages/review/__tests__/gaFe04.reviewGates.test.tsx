/**
 * GA-FE-04 · RED — ReviewCenter: acciones de revisión por `review:review`.
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

import ReviewCenter from '../ReviewCenter'
import { useAuthStore } from '../../../stores/auth.store'

const EVENTS = [{ id: 21, lot_id: 21, event_type: 'x', status: 'pending_review', event_date: '2026-09-11', operator: { username: 'op' }, farm: { name: 'F' } }]

function setSession(permissions: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 99, username: 'probe', first_name: 'P', last_name: 'Q', email: 'p@x.com',
      role_id: 3, view_type: 'web', is_super_admin: false, company_id: 1, effective_company_id: 1,
      permissions, company_business_units: ['broiler'], granted_business_units: ['broiler'], effective_business_units: ['broiler'],
    } as any,
  })
}

beforeEach(() => {
  get.mockReset(); post.mockReset()
  get.mockImplementation((url: string) => {
    if (String(url).startsWith('/review/pending')) return Promise.resolve({ data: { events: EVENTS, total: 1 } })
    if (String(url).startsWith('/masters') || String(url).startsWith('/users')) return Promise.resolve({ data: [] })
    return Promise.resolve({ data: { events: [], total: 0 } })
  })
})

describe('GA-FE-04 · ReviewCenter — autoridad de acción', () => {
  it('solo review:read ⇒ sin Iniciar/Completar/Devolver', async () => {
    setSession(['review:read'])
    render(<MemoryRouter><ReviewCenter /></MemoryRouter>)
    await waitFor(() => expect(screen.getAllByText(/#21/).length).toBeGreaterThan(0))
    expect(screen.queryByRole('button', { name: /Iniciar/ })).toBeNull()
    expect(screen.queryByRole('button', { name: /Completar/ })).toBeNull()
    expect(screen.queryByRole('button', { name: /Devolver/ })).toBeNull()
  })

  it('control: con review:review ⇒ acción de inicio visible', async () => {
    setSession(['review:read', 'review:review'])
    render(<MemoryRouter><ReviewCenter /></MemoryRouter>)
    await waitFor(() => expect(screen.getAllByText(/#21/).length).toBeGreaterThan(0))
    expect(screen.getAllByRole('button', { name: /Iniciar/ }).length).toBeGreaterThan(0)
  })
})
