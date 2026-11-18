/**
 * `F4` (AC-S1-F01 / AC-S1-I02) · RED jsdom — Historial filtra por CÓDIGO de lote
 * (`lot_code`, ya aceptado por el backend), espera 400 ms y nunca envía `lot_id`.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

const get = vi.fn()
vi.mock('../../../services/api', () => ({
  default: { get: (...a: any[]) => get(...a), post: vi.fn(), put: vi.fn(), patch: vi.fn(), delete: vi.fn() },
}))
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (k: string, f?: any) => (typeof f === 'string' ? f : k) }),
}))
vi.mock('../../../components/Toast', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() }),
  getErrorMessage: (_e: any, f: string) => f,
}))

import OperationListPage from '../OperationListPage'
import { useAuthStore } from '../../../stores/auth.store'

function setSession(permissions: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 8, username: 'f4h', first_name: 'F', last_name: 'H', email: 'f4h@x.com',
      role_id: 35, view_type: 'web', is_super_admin: false, company_id: 1,
      effective_company_id: 1, permissions,
      company_business_units: [], granted_business_units: [], effective_business_units: [],
    } as any,
  })
}

/** Llamadas a `GET /operations` con sus parámetros (`api.get(url, { params })`). */
const llamadasOperaciones = () =>
  get.mock.calls
    .filter((c) => String(c[0]) === '/operations')
    .map((c) => (c[1]?.params ?? {}) as Record<string, any>)

beforeEach(() => {
  get.mockReset()
  try { sessionStorage.clear() } catch { /* noop */ }
  get.mockImplementation((url: string) => {
    const u = String(url)
    if (u === '/operations') {
      return Promise.resolve({
        data: [{ id: 900, lot_code: 'LT-01', event_type: 'mortality', event_date: '2026-09-10', status: 'approved' }],
        headers: { 'x-total-count': '1' },
      })
    }
    if (u.startsWith('/masters/farms')) return Promise.resolve({ data: [] })
    return Promise.resolve({ data: [], headers: {} })
  })
})

describe('F4 · Historial · filtro por código de lote', () => {
  it('el campo es de texto, con tope de 50 y placeholder «Código de lote»', async () => {
    setSession(['operations:read'])
    render(<MemoryRouter><OperationListPage /></MemoryRouter>)
    await waitFor(() => expect(llamadasOperaciones().length).toBeGreaterThan(0))

    const campo = screen.getByTestId('operation-filter-lot-code') as HTMLInputElement
    expect(campo.getAttribute('maxlength')).toBe('50')
    expect(campo.placeholder).toBe('Código de lote')
    expect((campo as HTMLInputElement).type).toBe('text')
  })

  it('escribir «lt-01» ⇒ una sola petición con `lot_code` tras el debounce y nunca `lot_id`', async () => {
    setSession(['operations:read'])
    render(<MemoryRouter><OperationListPage /></MemoryRouter>)
    await waitFor(() => expect(llamadasOperaciones().length).toBe(1))
    const antes = llamadasOperaciones().length

    fireEvent.change(screen.getByTestId('operation-filter-lot-code'), { target: { value: 'lt-01' } })

    await waitFor(
      () => expect(llamadasOperaciones().some((p) => p.lot_code === 'lt-01')).toBe(true),
      { timeout: 2000 },
    )
    expect(llamadasOperaciones().length - antes, 'una sola petición por la ráfaga').toBe(1)
    expect(llamadasOperaciones().every((p) => p.lot_id === undefined), 'prohibido `lot_id`').toBe(true)
  })

  it('tres caracteres seguidos ⇒ una sola petición extra', async () => {
    setSession(['operations:read'])
    render(<MemoryRouter><OperationListPage /></MemoryRouter>)
    await waitFor(() => expect(llamadasOperaciones().length).toBe(1))
    const antes = llamadasOperaciones().length

    const campo = screen.getByTestId('operation-filter-lot-code')
    fireEvent.change(campo, { target: { value: 'l' } })
    fireEvent.change(campo, { target: { value: 'lt' } })
    fireEvent.change(campo, { target: { value: 'lt-0' } })

    await waitFor(
      () => expect(llamadasOperaciones().some((p) => p.lot_code === 'lt-0')).toBe(true),
      { timeout: 2000 },
    )
    expect(llamadasOperaciones().length - antes).toBe(1)
  })
})
