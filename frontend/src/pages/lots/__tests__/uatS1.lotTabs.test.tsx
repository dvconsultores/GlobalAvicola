/**
 * F3 · AC-S1-B01 / AC-S1-I01 — pestañas de lotes por unidad EFECTIVA y filtro de tipo
 * en el servidor.
 *
 * Contrato:
 *  - Sólo se pintan las pestañas de las unidades disponibles en la sesión
 *    (`effective_business_units`; `company_business_units` para el actor global).
 *  - Sin unidades: estado vacío explícito (`lots.noUnitsTitle`/`lots.noUnitsHint`) y
 *    NINGUNA petición a `/lots`.
 *  - El tipo viaja al servidor (`&bird_type=`) para que `X-Total-Count` y «Cargar más»
 *    sean coherentes con el filtro.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

const get = vi.fn()
vi.mock('../../../services/api', () => ({
  default: { get: (...a: any[]) => get(...a) },
}))
vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (k: string, f?: string) => f ?? k }) }))

import LotListPage from '../LotListPage'
import { useAuthStore } from '../../../stores/auth.store'

const LOTS = [
  { id: 1, lot_code: 'L-BR-2026-01', bird_type: 'breeder', status: 'active', farm_name: 'Granja Norte' },
]

function setSession(effective: string[], isSuperAdmin = false) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 99, username: 'f3probe', first_name: 'F', last_name: '3', email: 'f3@x.com',
      role_id: 3, view_type: 'web', is_super_admin: isSuperAdmin, company_id: 1,
      effective_company_id: 1, permissions: ['lots:read'],
      company_business_units: effective, granted_business_units: effective,
      effective_business_units: effective,
    } as any,
  })
}

const lotCalls = () => get.mock.calls.map(c => String(c[0])).filter(u => u.startsWith('/lots'))

beforeEach(() => {
  get.mockReset()
  get.mockImplementation((url: string) => {
    if (String(url).startsWith('/lots')) return Promise.resolve({ data: LOTS, headers: { 'x-total-count': '1' } })
    return Promise.resolve({ data: [] })
  })
  try { sessionStorage.clear() } catch { /* storage no disponible */ }
  useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false, token: null })
})

const renderPage = () => render(<MemoryRouter><LotListPage /></MemoryRouter>)

describe('F3 · LotListPage — pestañas por unidad efectiva', () => {
  it('AC-S1-B01 · sesión con sólo `breeder` ⇒ pestañas «Todos» y «breeder», sin las demás', async () => {
    setSession(['breeder'])
    renderPage()
    await waitFor(() => expect(lotCalls().length).toBeGreaterThan(0))

    expect(screen.queryByTestId('lot-filter-all'), '«Todos» debe existir con ≥1 unidad').not.toBeNull()
    expect(screen.queryByTestId('lot-filter-breeder')).not.toBeNull()
    expect(screen.queryByTestId('lot-filter-grandparent'), 'unidad no concedida').toBeNull()
    expect(screen.queryByTestId('lot-filter-broiler'), 'unidad no concedida').toBeNull()
    expect(screen.queryByTestId('lot-filter-hatchery'), 'unidad no concedida').toBeNull()
  })

  it('AC-S1-B01 · sesión con breeder+hatchery ⇒ también aparece la pestaña de incubadora', async () => {
    setSession(['breeder', 'hatchery'])
    renderPage()
    await waitFor(() => expect(lotCalls().length).toBeGreaterThan(0))

    expect(screen.queryByTestId('lot-filter-hatchery')).not.toBeNull()
    expect(screen.queryByTestId('lot-filter-breeder')).not.toBeNull()
    expect(screen.queryByTestId('lot-filter-all')).not.toBeNull()
  })

  it('AC-S1-B01 · sesión sin unidades ⇒ estado vacío explícito y ninguna petición a /lots', async () => {
    setSession([])
    renderPage()

    await waitFor(() => expect(screen.queryByTestId('lots-no-units')).not.toBeNull())
    expect(screen.getByText('lots.noUnitsTitle')).toBeTruthy()
    expect(screen.getByText('lots.noUnitsHint')).toBeTruthy()
    expect(screen.queryByText('lots.noLots'), 'no debe confundirse con «Sin lotes»').toBeNull()
    expect(screen.queryByTestId('lot-filter-all'), 'sin unidades no hay pestañas').toBeNull()
    expect(lotCalls(), 'sin unidades no se piden lotes').toEqual([])
  })

  it('AC-S1-I01 · al pulsar la pestaña `breeder` la siguiente petición lleva bird_type=breeder', async () => {
    setSession(['breeder'])
    renderPage()
    await waitFor(() => expect(lotCalls().length).toBeGreaterThan(0))
    expect(lotCalls()[0]).not.toContain('bird_type=')

    fireEvent.click(screen.getByTestId('lot-filter-breeder'))
    await waitFor(() =>
      expect(lotCalls().some(u => u.includes('bird_type=breeder'))).toBe(true),
    )
  })

  it('AC-S1-I01 · defensa en profundidad: si el backend ignora bird_type, sólo se pintan los del tipo activo', async () => {
    setSession(['breeder'])
    // El backend simulado IGNORA `bird_type` y devuelve lotes de dos tipos distintos.
    const mixtos = [
      { id: 1, lot_code: 'L-BR-2026-01', bird_type: 'breeder', status: 'active', farm_name: 'Granja Norte' },
      { id: 2, lot_code: 'L-GP-2026-01', bird_type: 'grandparent', status: 'active', farm_name: 'Granja Sur' },
    ]
    get.mockImplementation((url: string) => {
      if (String(url).startsWith('/lots')) return Promise.resolve({ data: mixtos, headers: { 'x-total-count': '2' } })
      return Promise.resolve({ data: [] })
    })

    renderPage()
    // La tabla y las tarjetas móviles se pintan ambas en el DOM: se cuenta, no se busca uno solo.
    await waitFor(() => expect(screen.queryAllByText('L-GP-2026-01').length).toBeGreaterThan(0))

    fireEvent.click(screen.getByTestId('lot-filter-breeder'))
    await waitFor(() =>
      expect(lotCalls().some(u => u.includes('bird_type=breeder'))).toBe(true),
    )
    await waitFor(() =>
      expect(screen.queryAllByText('L-GP-2026-01'), 'el lote de otro tipo no debe pintarse').toEqual([]),
    )
    expect(
      screen.getAllByText('L-BR-2026-01').length,
      'el lote del tipo activo se sigue pintando',
    ).toBeGreaterThan(0)
  })
})
