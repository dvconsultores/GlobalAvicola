/**
 * R-218 · RED jsdom — serie semanal del lote (opción A: `GET /reports/lot/{id}/weekly`).
 * Rojos en HEAD: la vista semanal y las series de reportes leen sublistas que la LISTA
 * de `/operations` ya no expone (C#4) ⇒ tabla vacía y gráficos planos.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

const get = vi.fn()
vi.mock('../../../services/api', () => ({
  default: { get: (...a: any[]) => get(...a), post: vi.fn(), put: vi.fn(), patch: vi.fn(), delete: vi.fn() },
}))
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (k: string, f?: any) => (typeof f === 'string' ? f : k), i18n: { language: 'es' } }),
}))
vi.mock('../../../components/Toast', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() }),
  getErrorMessage: (_e: any, f: string) => f,
}))
vi.mock('../../../components/TraceabilityTree', () => ({ TraceabilityTree: () => null }))

import LotDetailPage from '../../lots/LotDetailPage'
import ReportsPage from '../ReportsPage'
import { useAuthStore } from '../../../stores/auth.store'

const SERIE = {
  lot_id: 9,
  weeks: [
    { week: 1, mortality: 30, feed_kg: 100.0, water_l: 700.0, weight_g: null },
    { week: 2, mortality: 0, feed_kg: 0.0, water_l: 0.0, weight_g: 1500.0 },
  ],
}

function setSession(permissions: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 9, username: 'r218', first_name: 'R', last_name: 'C', email: 'r@x.com',
      role_id: 35, view_type: 'web', is_super_admin: false, company_id: 1,
      effective_company_id: 1, permissions,
      company_business_units: [], granted_business_units: [], effective_business_units: [],
    } as any,
  })
}

const urls = () => get.mock.calls.map((c) => String(c[0]))

beforeEach(() => {
  get.mockReset()
  get.mockResolvedValue({ data: [], headers: {} })
  useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false, token: null })
})

describe('R-218 · serie semanal del lote (RED)', () => {
  it('AC-R218-03 · la vista semanal del lote se sirve del agregado `/reports/lot/{id}/weekly`', async () => {
    setSession(['lots:read', 'reports:read'])
    get.mockImplementation((url: string) => {
      const u = String(url)
      if (u === '/lots/9') return Promise.resolve({ data: { id: 9, lot_code: 'L-9', status: 'active' } })
      if (u.includes('/reports/lot/9/weekly')) return Promise.resolve({ data: SERIE })
      return Promise.resolve({ data: [], headers: {} })
    })
    render(
      <MemoryRouter initialEntries={['/lots/9']}>
        <Routes><Route path="/lots/:id" element={<LotDetailPage />} /></Routes>
      </MemoryRouter>,
    )
    await waitFor(() => expect(urls().some((u) => u.includes('/reports/lot/9/weekly'))).toBe(true))
    // filas reales de la serie (semana 1: 30 bajas; semana 2: 1500 g)
    await waitFor(() => expect(screen.getAllByText('30').length).toBeGreaterThan(0))
    expect(screen.getAllByText(/1500/).length).toBeGreaterThan(0)
  })

  it('AC-R218-04 · los gráficos de reportes usan la serie real (no la lista sin sublistas)', async () => {
    setSession(['reports:read'])
    get.mockImplementation((url: string) => {
      const u = String(url)
      if (u.includes('/reports/lot/2/weekly')) return Promise.resolve({ data: { ...SERIE, lot_id: 2 } })
      if (u.includes('/reports/kpis?lot_id=2')) return Promise.resolve({ data: {} })
      return Promise.resolve({ data: [], headers: {} })
    })
    render(
      <MemoryRouter initialEntries={['/reports']}>
        <Routes><Route path="/reports" element={<ReportsPage />} /></Routes>
      </MemoryRouter>,
    )
    await waitFor(() => expect(urls().some((u) => u.includes('/reports/lot/2/weekly'))).toBe(true))
    expect(urls().some((u) => u.includes('/operations?lot_id=2&limit=100')), 'la fuente plana ya no debería usarse').toBe(false)
  })
})

