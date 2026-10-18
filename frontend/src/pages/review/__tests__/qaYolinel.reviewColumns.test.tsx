/**
 * QA-014/QA-015 — columnas de contexto en las bandejas.
 *
 * - ReviewCenter: la tabla/listado muestran Granja y «Registrado por».
 * - ApprovalPanel: selector de granja que viaja como `farm_id` y muestra autor.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

const get = vi.fn()
const post = vi.fn()
vi.mock('../../../services/api', () => ({
  default: {
    get: (...a: any[]) => get(...a), post: (...a: any[]) => post(...a),
    put: vi.fn(), delete: vi.fn(),
  },
}))
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (k: string, f?: any) => (typeof f === 'string' ? f : k) }),
}))
const toastError = vi.fn()
const toastSuccess = vi.fn()
vi.mock('../../../components/Toast', async (importOriginal) => {
  const actual = await importOriginal<any>()
  return { ...actual, useToast: () => ({ success: toastSuccess, error: toastError, warning: vi.fn(), info: vi.fn() }) }
})

import ReviewCenter from '../ReviewCenter'
import ApprovalPanel from '../../approvals/ApprovalPanel'
import { ToastProvider } from '../../../components/Toast'
import { useAuthStore } from '../../../stores/auth.store'

const EVENTO = {
  id: 1, lot_id: 5, lot_code: 'L-1', farm_id: 7, farm_name: 'Granja Norte',
  registered_by_name: 'Ana Pérez', created_at: '2026-10-18T10:00:00Z',
  event_date: '2026-10-18', event_type: 'feed_registration', status: 'pending_review',
}

function setSession(permissions: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 5, username: 'qa', first_name: 'Q', last_name: 'A', email: 'qa@x.com',
      role_id: 35, view_type: 'web', is_super_admin: false, company_id: 1,
      effective_company_id: 1, permissions,
      company_business_units: [], granted_business_units: [], effective_business_units: [],
    } as any,
  })
}

const urlsLlamadas = () => get.mock.calls.map((c) => String(c[0]))

beforeEach(() => {
  get.mockReset(); post.mockReset(); vi.clearAllMocks()
  get.mockImplementation((url: string) => {
    const u = String(url)
    if (u.startsWith('/review/pending')) return Promise.resolve({ data: { events: [EVENTO], total: 1 } })
    if (u.startsWith('/approvals/pending')) {
      return Promise.resolve({ data: { events: [{ ...EVENTO, status: 'reviewed' }], total: 1 } })
    }
    if (u.startsWith('/masters/farms')) return Promise.resolve({ data: [{ id: 7, name: 'Granja Norte' }] })
    return Promise.resolve({ data: [] })
  })
})

describe('QA-014 · ReviewCenter — columnas de contexto', () => {
  it('muestra granja y registrado por del evento', async () => {
    setSession(['review:read', 'review:review'])
    render(
      <MemoryRouter initialEntries={['/review?status=pending_review']}>
        <ToastProvider><ReviewCenter /></ToastProvider>
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getAllByText(/Granja Norte/).length).toBeGreaterThan(0))
    expect(screen.getAllByText(/Ana Pérez/).length).toBeGreaterThan(0)
    // el lote viaja con su código legible, no solo el id
    expect(screen.getAllByText(/L-1/).length).toBeGreaterThan(0)
  })
})

describe('QA-015 · ApprovalPanel — filtro de granja y columnas', () => {
  it('muestra el autor del registro y envía farm_id al filtrar por granja', async () => {
    setSession(['approvals:approve'])
    render(<MemoryRouter><ApprovalPanel /></MemoryRouter>)
    await waitFor(() => expect(screen.getAllByText(/Ana Pérez/).length).toBeGreaterThan(0))

    const selector = await screen.findByTestId('approval-filter-farm')
    fireEvent.change(selector, { target: { value: '7' } })

    await waitFor(() => {
      const conFiltro = urlsLlamadas().filter((u) => u.includes('/approvals/pending') && u.includes('farm_id=7'))
      expect(conFiltro.length, 'farm_id no viaja a /approvals/pending').toBeGreaterThan(0)
    }, { timeout: 3000 })
  })
})
