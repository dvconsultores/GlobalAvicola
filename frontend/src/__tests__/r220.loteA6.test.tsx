/**
 * R-220 · RED jsdom — Lote A, sexta tanda: A8 (C#33) paginación real.
 *   Listados con «Cargar más» usando `X-Total-Count` del backend: hoy piden una
 *   sola página de 100 sin saber cuántos hay (lote/operaciones).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

const get = vi.fn()
vi.mock('../services/api', () => ({
  default: { get: (...a: any[]) => get(...a), post: vi.fn(), put: vi.fn(), patch: vi.fn(), delete: vi.fn() },
}))
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (k: string, f?: any) => (typeof f === 'string' ? f : k), i18n: { language: 'es' } }),
}))
vi.mock('../components/Toast', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() }),
  getErrorMessage: (_e: any, f: string) => f,
}))

import LotListPage from '../pages/lots/LotListPage'
import OperationListPage from '../pages/operations/OperationListPage'
import { useAuthStore } from '../stores/auth.store'

function setSession(permissions: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 9, username: 'r220f', first_name: 'R', last_name: 'C', email: 'r@x.com',
      role_id: 35, view_type: 'web', is_super_admin: false, company_id: 1,
      effective_company_id: 1, permissions,
      company_business_units: [], granted_business_units: [], effective_business_units: [],
    } as any,
  })
}

beforeEach(() => {
  get.mockReset()
  get.mockResolvedValue({ data: [], headers: {} })
  useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false, token: null })
})

describe('R-220 · Lote A sexta tanda (RED)', () => {
  it('AC-R220-A·A8 · lotes: «Cargar más» usa X-Total-Count y trae la página siguiente', async () => {
    setSession(['lots:read'])
    get.mockImplementation((url: string) => {
      const u = String(url)
      if (u.startsWith('/lots?limit=100&skip=0')) {
        return Promise.resolve({ data: [{ id: 5, lot_code: 'L-05', status: 'active', start_date: '2026-09-10', bird_type: 'broiler' }], headers: { 'x-total-count': '2' } })
      }
      if (u.startsWith('/lots?limit=100&skip=1')) {
        return Promise.resolve({ data: [{ id: 6, lot_code: 'L-06', status: 'active', start_date: '2026-09-11', bird_type: 'broiler' }], headers: { 'x-total-count': '2' } })
      }
      return Promise.resolve({ data: [], headers: {} })
    })
    render(
      <MemoryRouter initialEntries={['/lots']}>
        <Routes><Route path="/lots" element={<LotListPage />} /></Routes>
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getAllByText(/L-05/).length).toBeGreaterThan(0))
    const mas = await screen.findByRole('button', { name: /Cargar más/ })
    fireEvent.click(mas)
    await waitFor(() => expect(screen.getAllByText(/L-06/).length).toBeGreaterThan(0))
    expect(screen.queryByRole('button', { name: /Cargar más/ }), '2/2 ⇒ ya no hay más').toBeNull()
    expect(get.mock.calls.some((c) => String(c[0]).startsWith('/lots?limit=100&skip=1'))).toBe(true)
  })

  it('AC-R220-A·A8 · operaciones: «Cargar más» pagina con skip según lo cargado', async () => {
    setSession(['operations:read'])
    get.mockImplementation((url: string, cfg?: any) => {
      const u = String(url)
      if (u === '/operations' && (cfg?.params?.skip ?? 0) === 0) {
        return Promise.resolve({ data: [
          { id: 1, event_type: 'mortality_recording', event_date: '2026-09-10', status: 'approved', lot_id: 5 },
          { id: 2, event_type: 'mortality_recording', event_date: '2026-09-11', status: 'approved', lot_id: 5 },
        ], headers: { 'x-total-count': '3' } })
      }
      if (u === '/operations' && cfg?.params?.skip === 2) {
        return Promise.resolve({ data: [
          { id: 3, event_type: 'mortality_recording', event_date: '2026-09-12', status: 'approved', lot_id: 5 },
        ], headers: { 'x-total-count': '3' } })
      }
      return Promise.resolve({ data: [], headers: {} })
    })
    render(
      <MemoryRouter initialEntries={['/operations']}>
        <Routes><Route path="/operations" element={<OperationListPage />} /></Routes>
      </MemoryRouter>,
    )
    const mas = await screen.findByRole('button', { name: /Cargar más/ })
    fireEvent.click(mas)
    await waitFor(() => expect(get.mock.calls.some((c) => c[1]?.params?.skip === 2)).toBe(true))
    expect(screen.queryByRole('button', { name: /Cargar más/ }), '3/3 ⇒ ya no hay más').toBeNull()
  })
})
