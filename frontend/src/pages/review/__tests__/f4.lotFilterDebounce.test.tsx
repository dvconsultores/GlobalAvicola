/**
 * `F4` (AC-S1-F01) + `SPEC 020` (AC-S2-R03) · RED jsdom — el filtro «Lote» de Revisión
 * y Aprobaciones espera 400 ms antes de pedir y viaja como CÓDIGO parcial (`lot_code`,
 * el backend lo acepta sin distinguir mayúsculas); `lot_id` deja de usarse y ya no hay
 * aviso de formato numérico.
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
const mocks = vi.hoisted(() => {
  const toastError = vi.fn()
  // `t` y `toast` deben ser referencias ESTABLES: si cambian de identidad en cada
  // render, `fetchEvents` (que depende de ellas) se re-dispara en bucle y el conteo
  // de peticiones por ráfaga deja de ser medible.
  const t = (k: string, f?: any) => (typeof f === 'string' ? f : k)
  const toast = { success: vi.fn(), error: toastError, warning: vi.fn(), info: vi.fn() }
  return { toastError, t, toast }
})
const toastError = mocks.toastError
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: mocks.t }),
}))
vi.mock('../../../components/Toast', async (importOriginal) => {
  const actual = await importOriginal<any>()
  return { ...actual, useToast: () => mocks.toast }
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
  it('código no numérico ⇒ se consulta con `lot_code` tras el debounce, sin aviso de formato', async () => {
    setSession(['review:read', 'review:review'])
    renderReview()
    await waitFor(() => expect(llamadasA('/review/pending').length).toBe(1))

    fireEvent.change(screen.getByTestId('review-filter-lot'), { target: { value: 'lt-01' } })

    await waitFor(
      () => expect(llamadasA('/review/pending').some((u) => u.includes('lot_code=lt-01'))).toBe(true),
      { timeout: 2000 },
    )
    // Sin avisos duplicados: el mensaje de formato numérico ya no existe.
    expect(screen.queryByTestId('lot-filter-hint')).toBeNull()
    expect(screen.queryByRole('alert')).toBeNull()
    expect(screen.queryByText(/Input should be/i)).toBeNull()
    expect(llamadasA('/review/pending').some((u) => u.includes('lot_id='))).toBe(false)
    expect(toastError).not.toHaveBeenCalled()
  })

  it('tres caracteres seguidos ⇒ una sola petición extra (sin ráfaga)', async () => {
    setSession(['review:read', 'review:review'])
    renderReview()
    await waitFor(() => expect(llamadasA('/review/pending').length).toBe(1))
    const antes = llamadasA('/review/pending').length

    const input = screen.getByTestId('review-filter-lot')
    fireEvent.change(input, { target: { value: 'l' } })
    fireEvent.change(input, { target: { value: 'lt' } })
    fireEvent.change(input, { target: { value: 'lt-1' } })

    await waitFor(
      () => expect(llamadasA('/review/pending').some((u) => u.includes('lot_code=lt-1'))).toBe(true),
      { timeout: 2000 },
    )
    expect(llamadasA('/review/pending').length - antes, 'peticiones por la ráfaga').toBe(1)
  })
})

describe('F4 · filtro de lote de Aprobaciones', () => {
  it('código no numérico ⇒ viaja `lot_code` tras el debounce y nunca `lot_id`', async () => {
    setSession(['approvals:approve'])
    renderApprovals()
    await waitFor(() => expect(llamadasA('/approvals/pending').length).toBe(1))

    fireEvent.change(screen.getByTestId('approval-filter-lot'), { target: { value: 'lt-01' } })

    await waitFor(
      () => expect(llamadasA('/approvals/pending').some((u) => u.includes('lot_code=lt-01'))).toBe(true),
      { timeout: 2000 },
    )
    expect(screen.queryByTestId('lot-filter-hint')).toBeNull()
    expect(llamadasA('/approvals/pending').some((u) => u.includes('lot_id='))).toBe(false)
    expect(toastError).not.toHaveBeenCalled()
  })

  it('tres caracteres seguidos ⇒ una sola petición extra', async () => {
    setSession(['approvals:approve'])
    renderApprovals()
    await waitFor(() => expect(llamadasA('/approvals/pending').length).toBe(1))
    const antes = llamadasA('/approvals/pending').length

    const input = screen.getByTestId('approval-filter-lot')
    fireEvent.change(input, { target: { value: 'L' } })
    fireEvent.change(input, { target: { value: 'L-' } })
    fireEvent.change(input, { target: { value: 'L-0' } })

    await waitFor(
      () => expect(llamadasA('/approvals/pending').some((u) => u.includes('lot_code=L-0'))).toBe(true),
      { timeout: 2000 },
    )
    expect(llamadasA('/approvals/pending').length - antes).toBe(1)
  })
})
