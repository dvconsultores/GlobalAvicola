/**
 * R-220 · RED jsdom — Lote A, segunda tanda:
 *   A3 (C#25): KPIs del panel de aprobación siempre 0 sobre datos que no pueden contarlos
 *              (la lista es de pendientes) ⇒ se retiran los ficticios.
 *   A5 (C#28): el `reason` del 400/evaluación no se muestra (WeightEvaluation).
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

import ApprovalPanel from '../pages/approvals/ApprovalPanel'
import WeightEvaluation from '../components/operations/WeightEvaluation'
import { useAuthStore } from '../stores/auth.store'

function setSession(permissions: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 9, username: 'r220b', first_name: 'R', last_name: 'C', email: 'r@x.com',
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

describe('R-220 · Lote A segunda tanda (RED)', () => {
  it('AC-R220-A·A3 · el panel no muestra KPIs que no puede contar (Aprobados/Rechazados ficticios)', async () => {
    setSession(['review:read', 'approvals:approve', 'approvals:reject'])
    get.mockImplementation((url: string) => {
      const u = String(url)
      if (u.includes('/approvals/pending')) {
        return Promise.resolve({ data: { events: [{ id: 31, status: 'corrected', event_type: 'mortality_recording', event_date: '2026-09-10' }], total: 1 } })
      }
      return Promise.resolve({ data: [], headers: {} })
    })
    render(
      <MemoryRouter initialEntries={['/approvals']}>
        <Routes><Route path="/approvals" element={<ApprovalPanel />} /></Routes>
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getAllByText(/Aprobar/).length).toBeGreaterThan(0))
    expect(screen.queryByText('Aprobados'), 'KPI ficticio «Aprobados» siempre 0').toBeNull()
    expect(screen.queryByText('Rechazados'), 'KPI ficticio «Rechazados» siempre 0').toBeNull()
    expect(screen.getAllByText('Pendientes').length).toBeGreaterThan(0)
  })

  it('AC-R220-A·A5 · la evaluación muestra el `reason` cuando el motor lo declara', async () => {
    get.mockImplementation((url: string) => {
      const u = String(url)
      if (u.includes('/weight-evaluation')) {
        return Promise.resolve({
          data: {
            event_id: 5, lot_id: 1, age_days: 12, curve_version_label: null,
            reason: 'Sin curva declarada para la edad del lote',
            evaluations: [{ avg_weight: 1200, status: 'no_reference', expected_min: null, expected_target: null, expected_max: null }],
          },
        })
      }
      return Promise.resolve({ data: [], headers: {} })
    })
    render(<WeightEvaluation eventId={5} />)
    await waitFor(() =>
      expect(screen.getByText(/Sin curva declarada para la edad del lote/)).toBeTruthy())
  })
})
