/**
 * R-220 · RED jsdom — Lote B, segunda tanda: B4 (F G-18).
 *   - ReportsPage tenía el enlace al reporte de lote **fijo en 2**.
 *   - LotDetailPage no ofrecía el reporte del propio lote (ruta casi huérfana).
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
vi.mock('../components/TraceabilityTree', () => ({ TraceabilityTree: () => null }))

import ReportsPage from '../pages/reports/ReportsPage'
import LotDetailPage from '../pages/lots/LotDetailPage'
import { useAuthStore } from '../stores/auth.store'

function setSession(permissions: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 9, username: 'r220j', first_name: 'R', last_name: 'C', email: 'r@x.com',
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

describe('R-220 · Lote B segunda tanda (RED)', () => {
  it('AC-R220-B·B4 · el enlace al reporte sigue al lote elegido (no el 2 fijo)', async () => {
    setSession(['reports:read', 'lots:read'])
    get.mockImplementation((url: string) => {
      const u = String(url)
      if (u.startsWith('/lots')) return Promise.resolve({ data: [{ id: 6, lot_code: 'L-06', status: 'active' }], headers: {} })
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
    fireEvent.change(selector, { target: { value: '6' } })
    await waitFor(() => {
      expect(document.querySelector('a[href="/reports/lot/6"]'), 'enlace al reporte del lote elegido').toBeTruthy()
    })
    expect(document.querySelector('a[href="/reports/lot/2"]'), 'lote 2 codificado').toBeNull()
  })

  it('AC-R220-B·B4 · el detalle del lote ofrece su reporte (gate reports:read)', async () => {
    setSession(['lots:read', 'reports:read'])
    get.mockImplementation((url: string) => {
      const u = String(url)
      if (u === '/lots/9') return Promise.resolve({ data: { id: 9, lot_code: 'L-9', status: 'active', start_date: '2026-09-10' } })
      return Promise.resolve({ data: [], headers: {} })
    })
    render(
      <MemoryRouter initialEntries={['/lots/9']}>
        <Routes><Route path="/lots/:id" element={<LotDetailPage />} /></Routes>
      </MemoryRouter>,
    )
    await waitFor(() =>
      expect(document.querySelector('a[href="/reports/lot/9"]'), 'reporte del lote enlazable').toBeTruthy())
  })
})
