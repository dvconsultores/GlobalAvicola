/**
 * SPEC 020 (`AC-S2-R03` / `AC-S2-U01`) · RED jsdom — Centro de Revisión y Panel de
 * Aprobaciones: el filtro de lote viaja por CÓDIGO (`lot_code`, coincidencia parcial;
 * NUNCA `lot_id`) tras 400 ms y el rango de fechas se valida en cliente (inicio > fin
 * ⇒ no se consulta el backend y se muestra UN único aviso).
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent, act } from '@testing-library/react'
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
  // Referencias estables (ver `f4.lotFilterDebounce`): evita el bucle de `fetchEvents`.
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
  id: 501, event_type: 'mortality', event_date: '2026-09-10', status: 'in_review',
  lot_id: 12, lot_code: 'LT-12', farm_id: 1, house_id: 2, registered_by_id: 9, version: 1,
}

function setSession(permissions: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 7, username: 's2', first_name: 'S', last_name: '2', email: 's2@x.com',
      role_id: 35, view_type: 'web', is_super_admin: false, company_id: 1,
      effective_company_id: 1, permissions,
      company_business_units: [], granted_business_units: [], effective_business_units: [],
    } as any,
  })
}

const urls = () => get.mock.calls.map((c) => String(c[0]))
const llamadasA = (prefijo: string) => urls().filter((u) => u.startsWith(prefijo))
const params = (url: string) => new URLSearchParams(url.split('?')[1] ?? '')
const ultimaA = (prefijo: string) => {
  const l = llamadasA(prefijo)
  return params(l[l.length - 1] ?? '')
}

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

afterEach(() => { vi.useRealTimers() })

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

describe('SPEC 020 · filtro por código de lote en Revisión', () => {
  it('REV-S2-UI-01 · teclear «L-0001» envía `lot_code` tras 400 ms y nunca `lot_id`', async () => {
    setSession(['review:read', 'review:review'])
    renderReview()
    await waitFor(() => expect(llamadasA('/review/pending').length).toBe(1))
    const antes = llamadasA('/review/pending').length

    vi.useFakeTimers()
    const campo = screen.getByTestId('review-filter-lot')
    fireEvent.change(campo, { target: { value: 'L-0' } })
    fireEvent.change(campo, { target: { value: 'L-0001' } })

    await act(async () => { vi.advanceTimersByTime(399) })
    expect(llamadasA('/review/pending').length - antes, 'sin petición antes de los 400 ms').toBe(0)

    await act(async () => { vi.advanceTimersByTime(1) })

    const ultima = ultimaA('/review/pending')
    expect(ultima.get('lot_code')).toBe('L-0001')
    expect(ultima.get('lot_id')).toBeNull()
    expect(llamadasA('/review/pending').length - antes, 'una sola petición por la ráfaga').toBe(1)
    expect(llamadasA('/review/pending').every((u) => params(u).get('lot_id') === null), 'prohibido `lot_id`').toBe(true)
  })

  it('REV-S2-UI-02 · un texto no numérico no muestra ningún aviso de formato', async () => {
    setSession(['review:read', 'review:review'])
    renderReview()
    await waitFor(() => expect(llamadasA('/review/pending').length).toBe(1))

    fireEvent.change(screen.getByTestId('review-filter-lot'), { target: { value: 'lt-01' } })

    await waitFor(
      () => expect(llamadasA('/review/pending').some((u) => params(u).get('lot_code') === 'lt-01')).toBe(true),
      { timeout: 2000 },
    )
    expect(screen.queryByTestId('lot-filter-hint')).toBeNull()
    expect(screen.queryByRole('alert')).toBeNull()
    expect(screen.queryByText(/solo dígitos/i)).toBeNull()
    expect(toastError).not.toHaveBeenCalled()
  })
})

describe('SPEC 020 · validación del rango de fechas en Revisión', () => {
  it('REV-S2-UI-03 · inicio > fin ⇒ no se consulta y aparece un único `role="alert"`', async () => {
    setSession(['review:read', 'review:review'])
    renderReview()
    await waitFor(() => expect(llamadasA('/review/pending').length).toBe(1))

    const desde = screen.getByTestId('review-filter-date-from')
    const hasta = screen.getByTestId('review-filter-date-to')
    fireEvent.change(desde, { target: { value: '2026-09-20' } })
    await waitFor(() => expect(ultimaA('/review/pending').get('date_from')).toBe('2026-09-20'))
    const antes = llamadasA('/review/pending').length

    fireEvent.change(hasta, { target: { value: '2026-09-10' } })

    const alertas = await screen.findAllByRole('alert')
    expect(alertas.length, 'un solo mensaje de rango').toBe(1)
    expect(alertas[0].textContent).toBe('La fecha inicial no puede ser posterior a la fecha final')
    await waitFor(() => expect(desde.getAttribute('aria-invalid')).toBe('true'))
    expect(hasta.getAttribute('aria-invalid')).toBe('true')

    expect(llamadasA('/review/pending').length - antes, 'el rango inválido no se consulta').toBe(0)
    expect(
      llamadasA('/review/pending').slice(antes).filter((u) => params(u).has('date_from') || params(u).has('date_to')),
    ).toEqual([])
  })

  it('REV-S2-UI-04 · solo inicio, solo fin y mismo día envían los parámetros correctos', async () => {
    setSession(['review:read', 'review:review'])
    renderReview()
    await waitFor(() => expect(llamadasA('/review/pending').length).toBe(1))

    const desde = screen.getByTestId('review-filter-date-from')
    const hasta = screen.getByTestId('review-filter-date-to')

    fireEvent.change(desde, { target: { value: '2026-09-10' } })
    await waitFor(() => {
      const p = ultimaA('/review/pending')
      expect(p.get('date_from')).toBe('2026-09-10')
      expect(p.get('date_to')).toBeNull()
    })

    fireEvent.change(hasta, { target: { value: '2026-09-20' } })
    await waitFor(() => {
      const p = ultimaA('/review/pending')
      expect(p.get('date_from')).toBe('2026-09-10')
      expect(p.get('date_to')).toBe('2026-09-20')
    })

    fireEvent.change(desde, { target: { value: '' } })
    await waitFor(() => {
      const p = ultimaA('/review/pending')
      expect(p.get('date_from')).toBeNull()
      expect(p.get('date_to')).toBe('2026-09-20')
    })

    // Mismo día: `from == to` es válido (límites inclusivos del backend).
    fireEvent.change(desde, { target: { value: '2026-09-20' } })
    await waitFor(() => {
      const p = ultimaA('/review/pending')
      expect(p.get('date_from')).toBe('2026-09-20')
      expect(p.get('date_to')).toBe('2026-09-20')
    })
    expect(screen.queryByRole('alert')).toBeNull()
    expect(desde.getAttribute('aria-invalid')).toBe('false')
  })
})

describe('SPEC 020 · filtro por código de lote en Aprobaciones', () => {
  it('REV-S2-UI-05 · ApprovalPanel envía `lot_code` a /approvals/pending', async () => {
    setSession(['approvals:approve'])
    renderApprovals()
    await waitFor(() => expect(llamadasA('/approvals/pending').length).toBe(1))

    fireEvent.change(screen.getByTestId('approval-filter-lot'), { target: { value: 'L-0001' } })

    await waitFor(
      () => expect(llamadasA('/approvals/pending').some((u) => params(u).get('lot_code') === 'L-0001')).toBe(true),
      { timeout: 2000 },
    )
    expect(llamadasA('/approvals/pending').every((u) => params(u).get('lot_id') === null), 'prohibido `lot_id`').toBe(true)
    expect(screen.queryByTestId('lot-filter-hint')).toBeNull()
    expect(screen.queryByRole('alert')).toBeNull()
  })
})
