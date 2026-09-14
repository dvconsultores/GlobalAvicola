/**
 * R-220 · RED jsdom — Lote A, cuarta tanda: A6 (C#29).
 * El detalle de operación no pinta campos presentes (agua, sanos/débiles, params de
 * incubadora, inspecciones) — el dato viaja y se pierde en pantalla.
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
vi.mock('../components/TraceabilityTree', () => ({ TraceabilityTree: () => null }))

import OperationDetailPage from '../pages/operations/OperationDetailPage'
import { useAuthStore } from '../stores/auth.store'

function setSession() {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 9, username: 'r220d', first_name: 'R', last_name: 'C', email: 'r@x.com',
      role_id: 35, view_type: 'web', is_super_admin: false, company_id: 1,
      effective_company_id: 1, permissions: ['operations:read'],
      company_business_units: [], granted_business_units: [], effective_business_units: [],
    } as any,
  })
}

beforeEach(() => {
  get.mockReset()
  useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false, token: null })
})

describe('R-220 · Lote A cuarta tanda (RED)', () => {
  it('AC-R220-A·A6 · el detalle pinta agua, sanos/débiles, params de incubadora e inspecciones', async () => {
    setSession()
    get.mockImplementation((url: string) => {
      const u = String(url)
      if (u === '/operations/55') {
        return Promise.resolve({
          data: {
            id: 55, event_type: 'birth_registration', event_date: '2026-09-10', status: 'approved',
            lot_id: 1, farm_id: 1, house_id: 2, version: 1, observations: null,
            bird_movements: [], feed_movements: [], egg_movements: [], evidences: [],
            water_liters: 700,
            chicks_healthy: 300, chicks_weak: 4,
            hatchery_params: [{ quantity_loaded: 500 }],
            inspection_details: [{ value_numeric: 7 }],
          },
        })
      }
      return Promise.resolve({ data: [], headers: {} })
    })
    render(
      <MemoryRouter initialEntries={['/operations/55']}>
        <Routes><Route path="/operations/:id" element={<OperationDetailPage />} /></Routes>
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getByText(/birth_registration/)).toBeTruthy())
    expect(screen.getByText(/Agua:? 700/), 'agua omitida').toBeTruthy()
    expect(screen.getByText(/Sanos:? 300/), 'sanos/débiles omitidos').toBeTruthy()
    expect(screen.getByText(/Cargados:? 500/), 'params de incubadora omitidos').toBeTruthy()
    expect(screen.getByText(/Inspección:? 7/), 'inspecciones omitidas').toBeTruthy()
  })
})
