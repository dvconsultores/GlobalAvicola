/**
 * GA-FE-04 · RED — ApprovalPanel: aprobar ≠ rechazar (permisos separados del contrato).
 * - Con solo `review:review`: sin botones de aprobación.
 * - Con `approvals:approve` y sin `approvals:reject`: Aprobar visible, Rechazar NO.
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

import ApprovalPanel from '../ApprovalPanel'
import { useAuthStore } from '../../../stores/auth.store'

const EVENTS = [{ id: 11, lot_id: 11, event_type: 'x', status: 'corrected', event_date: '2026-09-11', operator: { username: 'op' } }]

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
    if (String(url).startsWith('/approvals/pending')) return Promise.resolve({ data: { events: EVENTS, total: 1 } })
    return Promise.resolve({ data: { events: [], total: 0 } })
  })
})

describe('GA-FE-04 · ApprovalPanel — autoridad de acción', () => {
  it('sin permisos de revisión ni aprobación ⇒ sin Aprobar ni Rechazar', async () => {
    setSession(['masters:read'])
    render(<MemoryRouter><ApprovalPanel /></MemoryRouter>)
    await waitFor(() => expect(screen.getAllByText(/#11/).length).toBeGreaterThan(0))
    expect(screen.queryByRole('button', { name: /Aprobar/ })).toBeNull()
    expect(screen.queryByRole('button', { name: /Rechazar/ })).toBeNull()
  })

  it('approvals:approve sin approvals:reject ⇒ Aprobar sí, Rechazar no', async () => {
    setSession(['approvals:approve'])
    render(<MemoryRouter><ApprovalPanel /></MemoryRouter>)
    await waitFor(() => expect(screen.getAllByText(/#11/).length).toBeGreaterThan(0))
    expect(screen.getAllByRole('button', { name: /^Aprobar$/ }).length).toBeGreaterThan(0)
    expect(screen.queryByRole('button', { name: /^Rechazar$/ })).toBeNull()
  })

  it('control: approvals:approve+reject+review:review ⇒ ambos visibles', async () => {
    setSession(['approvals:approve', 'approvals:reject', 'review:review'])
    render(<MemoryRouter><ApprovalPanel /></MemoryRouter>)
    await waitFor(() => expect(screen.getAllByText(/#11/).length).toBeGreaterThan(0))
    expect(screen.getAllByRole('button', { name: /^Aprobar$/ }).length).toBeGreaterThan(0)
    expect(screen.getAllByRole('button', { name: /^Rechazar$/ }).length).toBeGreaterThan(0)
  })
})
