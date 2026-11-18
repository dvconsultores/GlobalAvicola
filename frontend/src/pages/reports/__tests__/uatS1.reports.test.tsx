/**
 * `UAT S1` · `AC-S1-R01` y `AC-S1-R02` (specs/015-breeder-cria-uat-s1 §6).
 *
 *  - R01: la pantalla de reportes no arranca con un lote fijo (antes `useState(2)`): con
 *    lotes visibles selecciona el primero y pide sus KPIs; sin lotes muestra un estado
 *    vacío explicado en vez de un error. «Volver» del reporte de lote regresa al origen.
 *  - R02: los exportes usan `bird_type`, `status`, `farm_name` y `house_name` con los
 *    estados traducidos.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
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

import ReportsPage from '../ReportsPage'
import LotReportPage from '../LotReportPage'
import { lotReportToRows } from '../../../utils/export'
import { useAuthStore } from '../../../stores/auth.store'

function setSession(permissions: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 9, username: 'uatS1rep', first_name: 'U', last_name: 'S', email: 'u@x.com',
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

function renderReports() {
  return render(
    <MemoryRouter initialEntries={['/reports']}>
      <Routes><Route path="/reports" element={<ReportsPage />} /></Routes>
    </MemoryRouter>,
  )
}

const REPORTE = {
  lot: {
    id: 7, lot_code: 'L-7', status: 'active', bird_type: 'breeder',
    start_date: '2026-09-01', end_date: '2026-11-20',
    farm_name: 'Granja Norte', house_name: 'Galpón 3',
  },
  opening_balance: { total_birds: 1000, total_males: 100, total_females: 900 },
  event_summary: { total_events: 4 },
}

describe('UAT S1 · reportes sin lote fijo (AC-S1-R01)', () => {
  it('(1) el lote por defecto es el primero visible: pide sus KPIs y nunca el lote 2', async () => {
    setSession(['reports:read', 'lots:read'])
    get.mockImplementation((url: string) => {
      const u = String(url)
      if (u.startsWith('/lots')) return Promise.resolve({ data: [{ id: 7, lot_code: 'L-7', status: 'active' }], headers: {} })
      if (u.includes('/reports/kpis')) return Promise.resolve({ data: {} })
      if (u.includes('/reports/lot/')) return Promise.resolve({ data: { weeks: [] } })
      return Promise.resolve({ data: [], headers: {} })
    })
    renderReports()

    await waitFor(() => expect(urls().some((u) => u.includes('/reports/kpis?lot_id=7'))).toBe(true))
    expect(urls().some((u) => u.includes('lot_id=2')), 'lote 2 codificado en la petición').toBe(false)
    // el enlace rápido apunta al lote realmente seleccionado y lo nombra por su código
    await waitFor(() => expect(document.querySelector('a[href="/reports/lot/7"]')).toBeTruthy())
    expect(document.querySelector('a[href="/reports/lot/2"]')).toBeNull()
    expect(screen.getByRole('combobox')).toBeTruthy()
  })

  it('(2) sin lotes visibles no pide KPIs ni serie semanal y muestra el estado vacío', async () => {
    setSession(['reports:read', 'lots:read'])
    get.mockImplementation((url: string) => {
      const u = String(url)
      if (u.startsWith('/lots')) return Promise.resolve({ data: [], headers: {} })
      return Promise.resolve({ data: [], headers: {} })
    })
    renderReports()

    await waitFor(() =>
      expect(screen.getByText(/reports\.noLotsTitle|Sin lotes disponibles/)).toBeTruthy())
    expect(screen.getByText(/reports\.noLotsHint|No hay lotes visibles/)).toBeTruthy()
    expect(urls().some((u) => u.includes('/reports/kpis')), 'KPIs pedidos sin lote').toBe(false)
    expect(urls().some((u) => u.includes('/weekly')), 'serie semanal pedida sin lote').toBe(false)
    // no es un error: no hay estado de error ni reintento
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it('(3) «Volver» del reporte de lote va al detalle del lote en enlace directo', async () => {
    setSession(['reports:read', 'lots:read'])
    get.mockImplementation((url: string) => {
      const u = String(url)
      if (u === '/reports/lot/5') return Promise.resolve({ data: { ...REPORTE, lot: { ...REPORTE.lot, id: 5, lot_code: 'L-5' } } })
      return Promise.resolve({ data: [] })
    })
    render(
      <MemoryRouter initialEntries={['/reports/lot/5']}>
        <Routes>
          <Route path="/reports/lot/:id" element={<LotReportPage />} />
          <Route path="/lots/:id" element={<div>DETALLE-LOTE</div>} />
          <Route path="/reports" element={<div>LISTA-REPORTES</div>} />
        </Routes>
      </MemoryRouter>,
    )

    const volver = await screen.findByTestId('back-navigation')
    expect(volver).toBeTruthy()
    // el reporte del lote muestra la ubicación y el tipo traducidos
    await waitFor(() => expect(screen.getByText('Granja Norte')).toBeTruthy())
    expect(screen.getByText('Galpón 3')).toBeTruthy()
    fireEvent.click(volver)
    await waitFor(() => expect(screen.getByText('DETALLE-LOTE')).toBeTruthy())
  })
})

describe('UAT S1 · exportes con estados traducidos (AC-S1-R02)', () => {
  it('(4) lotReportToRows traduce bird_type y status y añade granja/galpón', () => {
    const t = (k: string) => `T:${k}`
    const [fila] = lotReportToRows(REPORTE, t)

    expect(fila.bird_type).toBe('T:birdTypes.breeder')
    expect(fila.status).toBe('T:lotStatus.active')
    expect(fila.farm_name).toBe('Granja Norte')
    expect(fila.house_name).toBe('Galpón 3')
    expect(fila.end_date).toBe('2026-11-20')
    expect(fila.lot_code).toBe('L-7')
  })

  it('(4b) sin traductor conserva los códigos canónicos (compatibilidad)', () => {
    const [fila] = lotReportToRows(REPORTE)
    expect(fila.bird_type).toBe('breeder')
    expect(fila.status).toBe('active')
  })
})
