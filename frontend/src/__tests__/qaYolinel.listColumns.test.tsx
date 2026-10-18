/**
 * QA-014 · columnas de granja en listados + granja/lote en «Mis pendientes».
 *   Contrato backend: `GET /lots` devuelve `farm_name`; `GET /operations` devuelve
 *   `lot_code`, `farm_name`, `registered_by_name`, `created_at` y `event_date`.
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
import MyPendingPage from '../pages/operations/MyPendingPage'
import { useAuthStore } from '../stores/auth.store'

function setSession(permissions: string[], viewType: 'web' | 'mobile' = 'web') {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 9, username: 'qayf', first_name: 'Q', last_name: 'Y', email: 'q@x.com',
      role_id: 35, view_type: viewType, is_super_admin: false, company_id: 1,
      effective_company_id: 1, permissions,
      company_business_units: [], granted_business_units: [], effective_business_units: [],
    } as any,
  })
}

beforeEach(() => {
  get.mockReset()
  get.mockResolvedValue({ data: [], headers: {} })
  try { sessionStorage.clear() } catch { /* noop */ }
  useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false, token: null })
})

describe('QA-014 · columnas de listados', () => {
  it('QA-014 · lotes: muestra la granja y filtra por granja en el servidor', async () => {
    setSession(['lots:read'])
    get.mockImplementation((url: string) => {
      const u = String(url)
      if (u.startsWith('/lots')) {
        return Promise.resolve({
          data: [{ id: 1, lot_code: 'L-1', bird_type: 'breeder', status: 'active', start_date: '2026-09-01', farm_id: 7, farm_name: 'Granja Norte' }],
          headers: {},
        })
      }
      if (u.startsWith('/masters/farms')) {
        return Promise.resolve({ data: [{ id: 7, name: 'Granja Norte' }] })
      }
      return Promise.resolve({ data: [], headers: {} })
    })
    render(
      <MemoryRouter initialEntries={['/lots']}>
        <Routes><Route path="/lots" element={<LotListPage />} /></Routes>
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getAllByText(/Granja Norte/).length).toBeGreaterThan(0))
    await waitFor(() => expect((screen.getByTestId('lot-filter-farm') as HTMLSelectElement).querySelectorAll('option').length).toBeGreaterThan(1))

    fireEvent.change(screen.getByTestId('lot-filter-farm'), { target: { value: '7' } })
    await waitFor(() => expect(get.mock.calls.some((c) => String(c[0]).includes('/lots') && String(c[0]).includes('farm_id=7'))).toBe(true))
  })

  it('QA-014 · operaciones: muestra lote, granja y registrado por; filtra por granja', async () => {
    setSession(['operations:read'])
    get.mockImplementation((url: string) => {
      const u = String(url)
      if (u === '/operations') {
        return Promise.resolve({
          data: [{
            id: 3, lot_id: 1, lot_code: 'L-1', farm_id: 7, farm_name: 'Granja Norte',
            registered_by_name: 'Ana Pérez', created_at: '2026-10-18T10:00:00Z',
            event_date: '2026-10-18', event_type: 'feed_registration', status: 'registered',
          }],
          headers: {},
        })
      }
      if (u.startsWith('/masters/farms')) {
        return Promise.resolve({ data: [{ id: 7, name: 'Granja Norte' }] })
      }
      return Promise.resolve({ data: [], headers: {} })
    })
    render(
      <MemoryRouter initialEntries={['/operations']}>
        <Routes><Route path="/operations" element={<OperationListPage />} /></Routes>
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getAllByText(/L-1/).length).toBeGreaterThan(0))
    expect(screen.getAllByText(/Granja Norte/).length).toBeGreaterThan(0)
    expect(screen.getByText(/Ana Pérez/)).toBeTruthy()

    fireEvent.change(screen.getByTestId('operation-filter-farm'), { target: { value: '7' } })
    await waitFor(() =>
      expect(get.mock.calls.some((c) => String(c[0]) === '/operations' && String(c[1]?.params?.farm_id) === '7')).toBe(true),
    )
  })

  it('QA-014 · mis pendientes: muestra el lote y la granja de cada tarjeta', async () => {
    setSession(['operations:read'], 'mobile')
    get.mockImplementation((url: string) => {
      const u = String(url)
      if (u === '/operations') {
        return Promise.resolve({
          data: [{
            id: 4, lot_code: 'L-9', farm_name: 'Granja Sur', event_type: 'mortality_recording',
            status: 'draft', event_date: '2026-10-18',
          }],
          headers: {},
        })
      }
      return Promise.resolve({ data: [], headers: {} })
    })
    render(
      <MemoryRouter initialEntries={['/my-pending']}>
        <Routes><Route path="/my-pending" element={<MyPendingPage />} /></Routes>
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getAllByText(/L-9/).length).toBeGreaterThan(0))
    expect(screen.getAllByText(/Granja Sur/).length).toBeGreaterThan(0)
  })
})
