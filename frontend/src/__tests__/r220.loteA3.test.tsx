/**
 * R-220 · RED jsdom — Lote A, tercera tanda:
 *   A1 (C#17): fechas `YYYY-MM-DD` de la API pintadas como ISO crudo en listados
 *              (el `new Date('YYYY-MM-DD')` además corre el día en husos negativos).
 *   A2 (C#18): ReportsPage usa un input numérico con lote 2 codificado; debe ser un
 *              selector real alimentado por `/lots`.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
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
import ReportsPage from '../pages/reports/ReportsPage'
import { useAuthStore } from '../stores/auth.store'

function setSession(permissions: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 9, username: 'r220c', first_name: 'R', last_name: 'C', email: 'r@x.com',
      role_id: 35, view_type: 'web', is_super_admin: false, company_id: 1,
      effective_company_id: 1, permissions,
      company_business_units: [], granted_business_units: [], effective_business_units: [],
    } as any,
  })
}

const LOTES = [
  { id: 5, lot_code: 'L-05', status: 'active', start_date: '2026-09-10', bird_type: 'broiler' },
  { id: 6, lot_code: 'L-06', status: 'active', start_date: '2026-09-11', bird_type: 'breeder' },
]

beforeEach(() => {
  get.mockReset()
  get.mockResolvedValue({ data: [], headers: {} })
  useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false, token: null })
})

describe('R-220 · Lote A tercera tanda (RED)', () => {
  it('AC-R220-A·A1 · las fechas se muestran formateadas (nunca el ISO crudo)', async () => {
    setSession(['lots:read'])
    get.mockImplementation((url: string) => {
      const u = String(url)
      if (u.startsWith('/lots')) return Promise.resolve({ data: LOTES, headers: {} })
      return Promise.resolve({ data: [], headers: {} })
    })
    render(
      <MemoryRouter initialEntries={['/lots']}>
        <Routes><Route path="/lots" element={<LotListPage />} /></Routes>
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getAllByText(/L-05/).length).toBeGreaterThan(0))
    // el ISO crudo no debe aparecer en ninguna celda
    expect(screen.queryByText(/^2026-09-10$/), 'fecha ISO cruda visible').toBeNull()
    expect(screen.queryByText(/2026-09-10/), 'fecha ISO cruda visible').toBeNull()
    // y sí una fecha localizada (10/09/2026 o 09/10/2026 según locale del entorno)
    expect(screen.getAllByText(/10[\/.]09[\/.]2026|09[\/.]10[\/.]2026/).length).toBeGreaterThan(0)
  })

  it('AC-R220-A·A2 · ReportsPage ofrece un selector real de lote (no un input con lote fijo)', async () => {
    setSession(['reports:read', 'lots:read'])
    get.mockImplementation((url: string) => {
      const u = String(url)
      if (u.startsWith('/lots')) return Promise.resolve({ data: LOTES, headers: {} })
      if (u.includes('/reports/kpis')) return Promise.resolve({ data: {} })
      if (u.includes('/reports/lot/')) return Promise.resolve({ data: { weeks: [] } })
      return Promise.resolve({ data: [], headers: {} })
    })
    render(
      <MemoryRouter initialEntries={['/reports']}>
        <Routes><Route path="/reports" element={<ReportsPage />} /></Routes>
      </MemoryRouter>,
    )
    const selector = await screen.findByRole('combobox')
    expect(selector).toBeTruthy()
    // opciones reales del listado de lotes
    await waitFor(() => expect(screen.getByRole('option', { name: /L-05/ })).toBeTruthy())
    // el input numérico codificado (lote 2) ya no existe
    expect(screen.queryByRole('spinbutton')).toBeNull()
  })
})
