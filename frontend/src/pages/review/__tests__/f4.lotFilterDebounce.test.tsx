/**
 * `F4` (AC-S1-F01) · RED jsdom — el filtro «Lote» de Revisión y Aprobaciones espera
 * 400 ms antes de pedir y valida el formato en cliente: si no son dígitos no se
 * consulta con ese filtro y se muestra UN único aviso en español.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

const get = vi.fn()
const post = vi.fn()
vi.mock('../../../services/api', () => ({
  default: {
    get: (...a: any[]) => get(...a), post: (...a: any[]) => post(...a),
    put: vi.fn(), patch: vi.fn(), delete: vi.fn(),
  },
}))
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (k: string, f?: any) => (typeof f === 'string' ? f : k) }),
}))
const toastError = vi.fn()
vi.mock('../../../components/Toast', async (importOriginal) => {
  const actual = await importOriginal<any>()
  return { ...actual, useToast: () => ({ success: vi.fn(), error: toastError, warning: vi.fn(), info: vi.fn() }) }
})

import ReviewCenter from '../ReviewCenter'
import ApprovalPanel from '../../approvals/ApprovalPanel'
import { ToastProvider } from '../../../components/Toast'
import { useAuthStore } from '../../../stores/auth.store'

const EVENTO = {
  id: 401, event_type: 'mortality', event_date: '2026-09-10', status: 'in_review',
  lot_id: 12, lot_code: 'LT-12', farm_id: 1, house_id: 2, registered_by_id: 9, version: 1,
}

function setSession(permissions: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 7, username: 'f4', first_name: 'F', last_name: '4', email: 'f4@x.com',
      role_id: 35, view_type: 'web', is_super_admin: false, company_id: 1,
      effective_company_id: 1, permissions,
      company_business_units: [], granted_business_units: [], effective_business_units: [],
    } as any,
  })
}

const urls = () => get.mock.calls.map((c) => String(c[0]))
const llamadasA = (prefijo: string) => urls().filter((u) => u.startsWith(prefijo))

beforeEach(() => {
  get.mockReset(); post.mockReset(); toastError.mockReset()
  try { sessionStorage.clear() } catch { /* noop */ }
  get.mockImplementation((url: string) => {
    const u = String(url)
    if (u.startsWith('/review/pending') || u.startsWith('/approvals/pending')) {
      return Promise.resolve({ data: { events: [EVENTO], total: 1 } })
    }
    if (u.startsWith('/masters/farms')) return Promise.resolve({ data: [] })
    if (u.startsWith('/users')) return Promise.resolve({ data: [] })
    return Promise.resolve({ data: [] })
  })
})

const renderReview = () => render(
  <MemoryRouter initialEntries={['/review?status=in_review']}>
    <ToastProvider><ReviewCenter /></ToastProvider>
  </MemoryRouter>,
)
const renderApprovals = () => render(
  <MemoryRouter>
    <ToastProvider><ApprovalPanel /></ToastProvider>
  </MemoryRouter>,
)

describe('F4 · filtro de lote de Revisión', () => {
  it('texto no numérico ⇒ ninguna petición con `lot_id` y un aviso en español', async () => {
    setSession(['review:read', 'review:review'])
    renderReview()
    await waitFor(() => expect(llamadasA('/review/pending').length).toBe(1))

    fireEvent.change(screen.getByTestId('review-filter-lot'), { target: { value: 'abc' } })

    expect(await screen.findByTestId('lot-filter-hint', {}, { timeout: 2000 })).toBeTruthy()
    expect(screen.getByTestId('lot-filter-hint').textContent).toBe('Escriba el ID numérico del lote (solo dígitos)')
    // El aviso es único (no se duplica uno por carácter).
    expect(screen.getAllByTestId('lot-filter-hint').length).toBe(1)
    expect(screen.queryByText(/Input should be/i)).toBeNull()
    expect(llamadasA('/review/pending').some((u) => u.includes('lot_id=abc'))).toBe(false)
    expect(toastError).not.toHaveBeenCalled()
  })

  it('ID numérico ⇒ se consulta con `lot_id` tras el debounce', async () => {
    setSession(['review:read', 'review:review'])
    renderReview()
    await waitFor(() => expect(llamadasA('/review/pending').length).toBe(1))

    fireEvent.change(screen.getByTestId('review-filter-lot'), { target: { value: '12' } })

    await waitFor(
      () => expect(llamadasA('/review/pending').some((u) => u.includes('lot_id=12'))).toBe(true),
      { timeout: 2000 },
    )
    expect(screen.queryByTestId('lot-filter-hint')).toBeNull()
  })

  it('tres caracteres seguidos ⇒ una sola petición extra (sin ráfaga)', async () => {
    setSession(['review:read', 'review:review'])
    renderReview()
    await waitFor(() => expect(llamadasA('/review/pending').length).toBe(1))
    const antes = llamadasA('/review/pending').length

    const input = screen.getByTestId('review-filter-lot')
    fireEvent.change(input, { target: { value: '1' } })
    fireEvent.change(input, { target: { value: '12' } })
    fireEvent.change(input, { target: { value: '123' } })

    await waitFor(
      () => expect(llamadasA('/review/pending').some((u) => u.includes('lot_id=123'))).toBe(true),
      { timeout: 2000 },
    )
    expect(llamadasA('/review/pending').length - antes, 'peticiones por la ráfaga').toBe(1)
  })
})

describe('F4 · filtro de lote de Aprobaciones', () => {
  it('texto no numérico ⇒ no viaja `lot_id` y se avisa en español una sola vez', async () => {
    setSession(['approvals:approve'])
    renderApprovals()
    await waitFor(() => expect(llamadasA('/approvals/pending').length).toBe(1))

    fireEvent.change(screen.getByTestId('approval-filter-lot'), { target: { value: 'lt-01' } })

    expect(await screen.findByTestId('lot-filter-hint', {}, { timeout: 2000 })).toBeTruthy()
    expect(llamadasA('/approvals/pending').some((u) => u.includes('lot_id=lt-01'))).toBe(false)
    expect(toastError).not.toHaveBeenCalled()
  })

  it('ID numérico ⇒ consulta con `lot_id` tras el debounce', async () => {
    setSession(['approvals:approve'])
    renderApprovals()
    await waitFor(() => expect(llamadasA('/approvals/pending').length).toBe(1))

    fireEvent.change(screen.getByTestId('approval-filter-lot'), { target: { value: '12' } })

    await waitFor(
      () => expect(llamadasA('/approvals/pending').some((u) => u.includes('lot_id=12'))).toBe(true),
      { timeout: 2000 },
    )
  })
})
