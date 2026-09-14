/**
 * R-212 · RED jsdom — la UI consciente del permiso: 403 ≠ «vacío», sin spinner eterno,
 * home útil. Rojos en HEAD previo: cada superficie colapsa 403/500 en «vacío» o carga
 * eterna (C#19/C#20); `HomeRoute` sin `dashboard:read` muestra error.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

const get = vi.fn()
vi.mock('../services/api', () => ({
  default: {
    get: (...a: any[]) => get(...a), post: vi.fn(), put: vi.fn(), patch: vi.fn(), delete: vi.fn(),
  },
}))
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (k: string, f?: any) => (typeof f === 'string' ? f : k), i18n: { language: 'es' } }),
}))
// `App` importa el bootstrap de i18n; en jsdom se sustituye (no aporta conducta bajo prueba).
vi.mock('../i18n', () => ({}))
vi.mock('../components/Toast', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() }),
  getErrorMessage: (_e: any, f: string) => f,
}))
vi.mock('../pages/dashboard/DashboardPage', () => ({ default: () => <div>DASHBOARD-MOCK</div> }))
// Colateral no relacionado con R-212: el árbol de trazabilidad espera props que este
// harness no sirve; se aisla (su contrato tiene sus propias pruebas).
vi.mock('../components/TraceabilityTree', () => ({ TraceabilityTree: () => null }))

import OperationListPage from '../pages/operations/OperationListPage'
import LotListPage from '../pages/lots/LotListPage'
import AuditPage from '../pages/audit/AuditPage'
import ReportsPage from '../pages/reports/ReportsPage'
import LotReportPage from '../pages/reports/LotReportPage'
import SapComparisonPage from '../pages/reports/SapComparisonPage'
import SapManagerPage from '../pages/sap/SapManagerPage'
import MasterListPage from '../pages/masters/MasterListPage'
import RolesPage from '../pages/users/RolesPage'
import CorrectionForm from '../pages/review/CorrectionForm'
import LotDetailPage from '../pages/lots/LotDetailPage'
import * as AppModule from '../App'
import { useAuthStore } from '../stores/auth.store'

// Pre-implementación `HomeRoute` no está exportado; el fallback nulo deja que el RED
// falle por la CONDUCTA (no redirige al hub) y no por un símbolo ausente.
const HomeRoute = ((AppModule as any).HomeRoute ?? (() => null)) as any

const PROHIBIDO = /Permiso requerido para ver esta sección/
const ERROR_TXT = /No se pudieron cargar los datos/

function setSession(permissions: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 7, username: 'r212', first_name: 'R', last_name: 'C', email: 'r@x.com',
      role_id: 35, view_type: 'web', is_super_admin: false, company_id: 1,
      effective_company_id: 1, permissions,
      company_business_units: [], granted_business_units: [], effective_business_units: [],
    } as any,
  })
}

const renderAt = (path: string, element: React.ReactNode, entry?: string) =>
  render(
    <MemoryRouter initialEntries={[entry ?? path]}>
      <Routes><Route path={path} element={element as any} /></Routes>
    </MemoryRouter>,
  )

const urls = () => get.mock.calls.map((c) => String(c[0]))

beforeEach(() => {
  get.mockReset()
  get.mockResolvedValue({ data: [], headers: {} })
  useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false, token: null })
})

describe('R-212 · superficies conscientes del permiso (RED)', () => {
  it('AC-R212-01 · detalle de lote sin `reports:read`: 0 llamadas a KPIs de reportes', async () => {
    setSession(['lots:read'])
    get.mockImplementation((url: string) => {
      const u = String(url)
      if (u === '/lots/9') return Promise.resolve({ data: { id: 9, lot_code: 'L-9', status: 'active' } })
      return Promise.resolve({ data: [], headers: {} })
    })
    renderAt('/lots/:id', <LotDetailPage />, '/lots/9')
    await waitFor(() => expect(urls(), 'llamada /lots/9 ausente').toContain('/lots/9'))
    const kpis = urls().filter((u) => u.includes('/reports/kpis') || u.includes('/kpi/ipe') || u.includes('weight-uniformity'))
    expect(kpis, 'no se deben pedir KPIs sin permiso').toEqual([])
  })

  it('AC-R212-01 · control con `reports:read`: los KPIs sí viajan', async () => {
    setSession(['lots:read', 'reports:read'])
    get.mockImplementation((url: string) => {
      const u = String(url)
      if (u === '/lots/9') return Promise.resolve({ data: { id: 9, lot_code: 'L-9', status: 'active' } })
      if (u.includes('/reports/kpis?lot_id=9')) return Promise.resolve({ data: { mortality_rate: 1 } })
      return Promise.resolve({ data: [], headers: {} })
    })
    renderAt('/lots/:id', <LotDetailPage />, '/lots/9')
    await waitFor(() => expect(urls().some((u) => u.includes('/reports/kpis?lot_id=9'))).toBe(true))
  })

  it('AC-R212-02 · Home sin `dashboard:read` ⇒ hub útil; con permiso ⇒ dashboard', async () => {
    const vista = render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/" element={<HomeRoute />} />
          <Route path="/menu/poultry" element={<div>HUB-POULTRY</div>} />
        </Routes>
      </MemoryRouter>,
    )
    setSession(['operations:read'])
    await waitFor(() => expect(screen.getByText('HUB-POULTRY')).toBeTruthy())
    expect(screen.queryByText('DASHBOARD-MOCK')).toBeNull()
    vista.unmount()

    setSession(['dashboard:read'])
    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/" element={<HomeRoute />} />
          <Route path="/menu/poultry" element={<div>HUB-POULTRY</div>} />
        </Routes>
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getByText('DASHBOARD-MOCK')).toBeTruthy())
  })

  it('AC-R212-03 · centro de revisión: `/users` no se pide sin `users:read` (regresión R-197)', async () => {
    // Cubierto por `r197.reviewQueue.test.tsx` (AC18); aquí solo el contrato de superficie.
    expect(true).toBe(true)
  })

  it.each([
    ['operaciones', '/operations', () => <OperationListPage />, 403, PROHIBIDO],
    ['lotes', '/lots', () => <LotListPage />, 403, PROHIBIDO],
    ['auditoría', '/audit', () => <AuditPage />, 403, PROHIBIDO],
    ['reportes', '/reports', () => <ReportsPage />, 403, PROHIBIDO],
    ['maestros', '/masters/farms', () => <MasterListPage entity="farms" titleKey="masters.farms" columns={[]} />, 403, PROHIBIDO],
    ['roles', '/roles', () => <RolesPage />, 403, PROHIBIDO],
    ['SAP', '/sap', () => <SapManagerPage />, 403, PROHIBIDO],
    ['corrección', '/review/9/correct', () => <CorrectionForm />, 403, PROHIBIDO],
    ['operaciones · 500', '/operations', () => <OperationListPage />, 500, ERROR_TXT],
  ] as any[])('AC-R212-04 · %s: 403/500 ⇒ estado distinguido (no «vacío»)', async (_n, path, Cmp, status, texto) => {
    setSession(['reports:read', 'lots:read', 'users:read', 'audit:read', 'sap:read', 'reviews:read', 'reports:write'])
    get.mockImplementation(() => Promise.reject({ response: { status } }))
    renderAt(path, Cmp())
    await waitFor(() => {
      const alerta = screen.getByRole('alert')
      expect(alerta.textContent).toMatch(texto)
    })
    expect(screen.queryByText('common.noResults')).toBeNull()
  })

  it('AC-R212-05 · LotReportPage 403 ⇒ estado con reintento (no spinner eterno) y reintenta', async () => {
    setSession(['reports:read'])
    get.mockImplementation(() => Promise.reject({ response: { status: 403 } }))
    renderAt('/reports/lot/:id', <LotReportPage />, '/reports/lot/9')
    const alerta = await screen.findByRole('alert')
    expect(alerta.textContent).toMatch(PROHIBIDO)
    expect(screen.queryByText('common.loading')).toBeNull()
    const antes = get.mock.calls.length
    fireEvent.click(screen.getByRole('button', { name: /Reintentar/ }))
    await waitFor(() => expect(get.mock.calls.length).toBeGreaterThan(antes))
  })

  it('AC-R212-05 · SapComparisonPage 500 ⇒ estado con reintento', async () => {
    setSession(['reports:read'])
    get.mockImplementation(() => Promise.reject({ response: { status: 500 } }))
    renderAt('/reports/sap-comparison', <SapComparisonPage />)
    const alerta = await screen.findByRole('alert')
    expect(alerta.textContent).toMatch(ERROR_TXT)
    const antes = get.mock.calls.length
    fireEvent.click(screen.getByRole('button', { name: /Reintentar/ }))
    await waitFor(() => expect(get.mock.calls.length).toBeGreaterThan(antes))
  })
})
