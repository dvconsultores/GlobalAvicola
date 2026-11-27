/**
 * SPEC 020 (`AC-S2-U01`) · RED jsdom — columna «Lote» del historial de Operaciones.
 *
 * Pre-fix: cualquier evento sin lote decía «Se creará al aprobar», aunque sólo la
 * importación de abuelos (`grandparent_import`) crea lote al aprobar. Una inspección
 * de granja no genera lote: «Sin lote (nivel granja)».
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

const get = vi.fn()
vi.mock('../../../services/api', () => ({
  default: {
    get: (...a: any[]) => get(...a), post: vi.fn(), put: vi.fn(), patch: vi.fn(), delete: vi.fn(),
  },
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

const EVENTOS = [
  { id: 901, event_type: 'farm_inspection', event_date: '2026-09-10', status: 'approved', farm_name: 'Granja Norte' },
  { id: 902, event_type: 'grandparent_import', event_date: '2026-09-10', status: 'approved' },
  { id: 903, event_type: 'mortality_recording', event_date: '2026-09-10', status: 'approved', lot_id: 44, lot_code: 'L-0044' },
  { id: 904, event_type: 'mortality_recording', event_date: '2026-09-10', status: 'approved', lot_id: 42 },
]

function setSession(permissions: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 8, username: 's2l', first_name: 'S', last_name: 'L', email: 's2l@x.com',
      role_id: 35, view_type: 'web', is_super_admin: false, company_id: 1,
      effective_company_id: 1, permissions,
      company_business_units: [], granted_business_units: [], effective_business_units: [],
    } as any,
  })
}

beforeEach(() => {
  get.mockReset()
  try { sessionStorage.clear() } catch { /* noop */ }
  get.mockImplementation((url: string) => {
    const u = String(url)
    if (u === '/operations') {
      return Promise.resolve({ data: EVENTOS, headers: { 'x-total-count': String(EVENTOS.length) } })
    }
    return Promise.resolve({ data: [], headers: {} })
  })
})

const renderLista = async () => {
  setSession(['operations:read'])
  render(<MemoryRouter initialEntries={['/operations']}><OperationListPage /></MemoryRouter>)
  return screen.findByTestId('operation-row-901')
}

describe('SPEC 020 · AC-S2-U01 · columna «Lote» del historial', () => {
  it('farm_inspection sin lote ⇒ «Sin lote (nivel granja)» (ni «Se creará al aprobar» ni «#null»)', async () => {
    const fila = await renderLista()
    expect(within(fila).getByText('Sin lote (nivel granja)')).toBeTruthy()
    expect(within(fila).queryByText(/Se creará al aprobar/)).toBeNull()
    expect(within(fila).queryByText(/#null/)).toBeNull()
  })

  it('grandparent_import sin lote ⇒ «Se creará al aprobar»', async () => {
    await renderLista()
    const fila = await screen.findByTestId('operation-row-902')
    expect(within(fila).getByText('Se creará al aprobar')).toBeTruthy()
    expect(within(fila).queryByText(/Sin lote \(nivel granja\)/)).toBeNull()
  })

  it('evento con `lot_code` ⇒ el código; con sólo `lot_id` ⇒ «#id» (nunca «#null»)', async () => {
    await renderLista()
    const conCodigo = await screen.findByTestId('operation-row-903')
    expect(within(conCodigo).getByText('L-0044')).toBeTruthy()

    const soloId = await screen.findByTestId('operation-row-904')
    expect(within(soloId).getByText('#42')).toBeTruthy()
    expect(screen.queryByText(/#null/)).toBeNull()
  })
})
