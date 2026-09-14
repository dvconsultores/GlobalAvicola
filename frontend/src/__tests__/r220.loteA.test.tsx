/**
 * R-220 · RED jsdom — Lote A (representativos): A9 (doble clic en Aprobar ⇒ 1 POST)
 * y A4 (`lot_id` nulo no debe rotular «#null»; patrón «Se creará al aprobar»).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

const get = vi.fn()
const post = vi.fn()
vi.mock('../services/api', () => ({
  default: { get: (...a: any[]) => get(...a), post: (...a: any[]) => post(...a), put: vi.fn(), patch: vi.fn(), delete: vi.fn() },
}))
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (k: string, f?: any) => (typeof f === 'string' ? f : k), i18n: { language: 'es' } }),
}))
vi.mock('../components/Toast', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() }),
  getErrorMessage: (_e: any, f: string) => f,
}))

import ApprovalPanel from '../pages/approvals/ApprovalPanel'
import OperationListPage from '../pages/operations/OperationListPage'
import { useAuthStore } from '../stores/auth.store'

function setSession(permissions: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 9, username: 'r220', first_name: 'R', last_name: 'C', email: 'r@x.com',
      role_id: 35, view_type: 'web', is_super_admin: false, company_id: 1,
      effective_company_id: 1, permissions,
      company_business_units: [], granted_business_units: [], effective_business_units: [],
    } as any,
  })
}

const urls = (fn: any) => fn.mock.calls.map((c: any) => String(c[0]))

beforeEach(() => {
  get.mockReset(); post.mockReset()
  get.mockResolvedValue({ data: [], headers: {} })
  post.mockResolvedValue({ data: {} })
  useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false, token: null })
})

describe('R-220 · Lote A (representativos, RED)', () => {
  it('AC-R220-A·A9 · doble clic en «Aprobar» ⇒ un solo POST /approvals/approve', async () => {
    setSession(['review:read', 'approvals:approve', 'approvals:reject'])
    get.mockImplementation((url: string) => {
      const u = String(url)
      if (u.includes('/approvals/pending')) {
        return Promise.resolve({ data: { events: [{ id: 31, status: 'corrected', event_type: 'mortality_recording', event_date: '2026-09-10' }], total: 1 } })
      }
      return Promise.resolve({ data: [], headers: {} })
    })
    render(
      <MemoryRouter initialEntries={['/approvals']}>
        <Routes><Route path="/approvals" element={<ApprovalPanel />} /></Routes>
      </MemoryRouter>,
    )
    const filas = await screen.findAllByRole('button', { name: /^Aprobar$/ })
    fireEvent.click(filas[0])
    // el diálogo añade su propio «Aprobar» (confirmLabel) — el último es su confirmación
    const abiertos = await screen.findAllByRole('button', { name: /^Aprobar$/ })
    const confirmar = abiertos[abiertos.length - 1]
    fireEvent.click(confirmar)
    fireEvent.click(confirmar)
    await waitFor(() => {
      const n = urls(post).filter((u) => u.includes('/approvals/approve')).length
      expect(n, 'doble gesto ⇒ doble POST').toBe(1)
    })
  })

  it('AC-R220-A·A4 · `lot_id` nulo ⇒ «Se creará al aprobar» (nunca «#null»)', async () => {
    setSession(['operations:read'])
    get.mockImplementation((url: string) => {
      const u = String(url)
      if (u.startsWith('/operations')) {
        return Promise.resolve({ data: [{ id: 77, event_type: 'grandparent_import', event_date: '2026-09-10', status: 'approved', lot_id: null }] })
      }
      return Promise.resolve({ data: [], headers: {} })
    })
    render(
      <MemoryRouter initialEntries={['/operations']}>
        <Routes><Route path="/operations" element={<OperationListPage />} /></Routes>
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getAllByText(/Se creará al aprobar/).length).toBeGreaterThan(0))
    expect(screen.queryByText(/#null/)).toBeNull()
  })
})
