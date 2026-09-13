/**
 * `R-208` · RED — botones de lote gateados por `approvals:approve|reject`.
 *
 * La barra de lote («Aprobar todos» / «Rechazar todos») hoy se gatea con
 * `review:review`: un revisor sin capacidad de aprobar ve los botones (rojo).
 * Con `approvals:*` deben seguir viéndose (control). Diseño:
 * `specs/R-208/R-208_RED_E2E_UAT_DESIGN.md §1.2`.
 *
 * Nota: los mocks de `t`/`toast` se definen **estables** (una sola identidad por
 * módulo): con identidades nuevas por render, `fetchEvents` se recrea, el clic
 * dispara un refetch y la selección se pierde antes de poder observar la barra.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

const get = vi.fn()
const post = vi.fn()
vi.mock('../../../services/api', () => ({
  default: { get: (...a: any[]) => get(...a), post: (...a: any[]) => post(...a) },
}))
vi.mock('react-i18next', () => {
  const t = (k: string, f?: string) => f ?? k
  return { useTranslation: () => ({ t, i18n: {} }) }
})
vi.mock('../../../components/Toast', () => {
  const toast = { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() }
  return { useToast: () => toast, getErrorMessage: (_e: any, f: string) => f }
})

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

async function seleccionarPrimerEvento() {
  await waitFor(() => expect(screen.getAllByText(/#11/).length).toBeGreaterThan(0))
  fireEvent.click(screen.getAllByRole('checkbox')[0])
  await waitFor(() => {
    expect(screen.getAllByRole('checkbox').some(c => (c as HTMLInputElement).checked)).toBe(true)
  })
}

describe('R-208 · botones de lote por approvals:*', () => {
  it('revisor sin approvals:* tras seleccionar ⇒ sin «Aprobar todos» ni «Rechazar todos»', async () => {
    setSession(['review:review', 'review:read'])
    render(<MemoryRouter><ApprovalPanel /></MemoryRouter>)
    await seleccionarPrimerEvento()
    expect(screen.queryByRole('button', { name: /Aprobar todos/ })).toBeNull()
    expect(screen.queryByRole('button', { name: /Rechazar todos/ })).toBeNull()
  })

  it('control: con approvals:approve/reject ⇒ botones de lote visibles', async () => {
    setSession(['review:review', 'review:read', 'approvals:approve', 'approvals:reject'])
    render(<MemoryRouter><ApprovalPanel /></MemoryRouter>)
    await seleccionarPrimerEvento()
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Aprobar todos/ })).toBeTruthy()
    })
    expect(screen.getByRole('button', { name: /Rechazar todos/ })).toBeTruthy()
  })
})
