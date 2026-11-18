/**
 * `spec 015 §5` · `AC-S1-T02` (F7) — bandeja de **pendientes de clasificar**: solo lectura,
 * con NOMBRES (granja/galpón/registrado por) en lugar de ids, vacío distinguible de la
 * denegación (`R-212`) y acceso desde el Historial.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

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

import PendingClassificationPage from '../PendingClassificationPage'
import OperationListPage from '../OperationListPage'
import { useAuthStore } from '../../../stores/auth.store'

function setSession(permissions: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 11, username: 'f7', first_name: 'F', last_name: '7', email: 'f7@x.com',
      role_id: 35, view_type: 'web', is_super_admin: false, company_id: 1,
      effective_company_id: 1, permissions,
      company_business_units: [], granted_business_units: [], effective_business_units: [],
    } as any,
  })
}

const PENDIENTES = [
  {
    id: 901, event_type: 'farm_inspection', event_date: '2026-09-10', status: 'registered',
    farm_id: 4, house_id: 7, farm_name: 'Granja SIN', house_name: 'Galpón SIN',
    registered_by_name: 'Ana Autora',
  },
  {
    id: 902, event_type: 'farm_inspection', event_date: '2026-09-09', status: 'registered',
    farm_id: 5, house_id: 8, farm_name: 'Granja MULTI', house_name: 'Galpón MULTI',
    registered_by_name: 'Ana Autora',
  },
]

const llamadaBandeja = () =>
  get.mock.calls.find((c) => String(c[0]) === '/operations/pending-classification')

beforeEach(() => {
  get.mockReset()
  try { sessionStorage.clear() } catch { /* noop */ }
})

describe('F7 · bandeja de pendientes de clasificar', () => {
  it('AC-S1-T02 · lista los pendientes con NOMBRES de granja y galpón (no ids)', async () => {
    setSession(['operations:read'])
    get.mockResolvedValue({ data: PENDIENTES })
    render(<MemoryRouter><PendingClassificationPage /></MemoryRouter>)

    await waitFor(() => expect(screen.getAllByTestId('pending-row')).toHaveLength(2))
    expect(screen.getByText('Granja SIN')).toBeTruthy()
    expect(screen.getByText('Galpón SIN')).toBeTruthy()
    expect(screen.getByText('Granja MULTI')).toBeTruthy()
    expect(screen.getByText('Galpón MULTI')).toBeTruthy()
    expect(screen.getAllByText('Ana Autora')).toHaveLength(2)
    expect(screen.queryByText('#901'), 'no debe mostrarse el id crudo').toBeNull()

    const [url, cfg] = llamadaBandeja()!
    expect(url).toBe('/operations/pending-classification')
    expect(cfg?.params).toMatchObject({ limit: 100 })
    // Decisión de seguridad `GA-REM-040`: esta pantalla NO clasifica.
    expect(get.mock.calls.some((c) => String(c[0]).includes('/classify'))).toBe(false)
  })

  it('lista vacía ⇒ texto de vacío, no error', async () => {
    setSession(['operations:read'])
    get.mockResolvedValue({ data: [] })
    render(<MemoryRouter><PendingClassificationPage /></MemoryRouter>)

    await screen.findByTestId('pending-classification-page')
    await waitFor(() => expect(
      screen.getByText('No hay registros pendientes de clasificar.')).toBeTruthy())
    expect(screen.queryAllByTestId('pending-row')).toHaveLength(0)
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it('403 ⇒ ErrorState de «prohibido» (denegación ≠ vacío)', async () => {
    setSession(['operations:read'])
    get.mockRejectedValue({ response: { status: 403 } })
    render(<MemoryRouter><PendingClassificationPage /></MemoryRouter>)

    await waitFor(() => expect(screen.getByRole('alert')).toBeTruthy())
    expect(screen.getByRole('alert').getAttribute('data-estado')).toBe('prohibido')
    expect(screen.queryByText('No hay registros pendientes de clasificar.')).toBeNull()
  })

  it('el Historial ofrece el enlace a la bandeja', async () => {
    setSession(['operations:read'])
    get.mockImplementation((url: string) => {
      const u = String(url)
      if (u === '/operations') return Promise.resolve({ data: [], headers: {} })
      return Promise.resolve({ data: [], headers: {} })
    })
    render(<MemoryRouter><OperationListPage /></MemoryRouter>)

    const enlace = await screen.findByTestId('pending-classification-link')
    expect(enlace.getAttribute('href')).toBe('/operations/pending-classification')
  })
})
