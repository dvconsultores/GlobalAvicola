/**
 * GA-FE-06 · RED — R-182: contrato de alta de lote (fecha prevista de cierre + área).
 *
 * Verdad canónica (reconciliación GA-FE-06):
 *   El formulario YA tiene control `planned_close_date` pero NO lo envía;
 *   `area_id` está declarado en zod y aceptado por backend/DB pero NO tiene control ni viaja.
 *   El defecto es pérdida silenciosa: la fecha prevista nunca llega ⇒ el aviso SLA
 *   «lote próximo a cierre» (ventana 0..3 días) queda sin datos de origen.
 *
 * Contrato esperado tras GA-FE-06:
 *   - PLD capturada ⇒ viaja en POST /lots como `planned_close_date` (YYYY-MM-DD)
 *   - Selector «Área» alimentado por GET /masters/areas?limit=100 (nombres, sin IDs crudos)
 *   - Área elegida ⇒ viaja como `area_id`
 *   - Sin fecha / sin área ⇒ `null` explícito (opcionalidad real; nada inventado)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent, within } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

const get = vi.fn()
const post = vi.fn()
vi.mock('../../../services/api', () => ({
  default: {
    get: (...a: any[]) => get(...a),
    post: (...a: any[]) => post(...a),
    put: vi.fn(), patch: vi.fn(), delete: vi.fn(),
  },
}))
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (k: string, f?: any) => (typeof f === 'string' ? f : k) }),
}))
const toastError = vi.fn()
const toastSuccess = vi.fn()
vi.mock('../../../components/Toast', () => ({
  useToast: () => ({ success: toastSuccess, error: toastError, warning: vi.fn(), info: vi.fn() }),
  getErrorMessage: (_e: any, f: string) => f,
}))

import LotFormPage from '../LotFormPage'
import { useAuthStore } from '../../../stores/auth.store'

function setSession() {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 61, username: 'ga06-c', first_name: 'GA', last_name: 'C', email: 'c@x.com',
      role_id: 35, view_type: 'web', is_super_admin: false, company_id: 1, effective_company_id: 1,
      permissions: ['dashboard:read', 'lots:read', 'lots:create', 'masters:read'],
      company_business_units: ['broiler'], granted_business_units: ['broiler'],
      effective_business_units: ['broiler'],
    } as any,
  })
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/lots/new']}>
      <Routes>
        <Route path="/lots/new" element={<LotFormPage />} />
        <Route path="*" element={<div>navegado</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

const AREAS = [
  { id: 7, name: 'Nave Norte (GA-FE-06)' },
  { id: 8, name: 'Nave Sur (GA-FE-06)' },
]

beforeEach(() => {
  get.mockReset(); post.mockReset(); toastError.mockReset(); toastSuccess.mockReset()
  useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false, token: null })
  get.mockImplementation((url: string) => {
    const u = String(url)
    if (u.startsWith('/masters/farms')) return Promise.resolve({ data: [{ id: 1, name: 'Granja Uno' }] })
    if (u.startsWith('/masters/areas')) return Promise.resolve({ data: AREAS })
    if (u.startsWith('/masters/')) return Promise.resolve({ data: [] })
    return Promise.resolve({ data: [] })
  })
  post.mockResolvedValue({ data: { id: 123 } })
})

/** Rellena los obligatorios del alta (código, tipo, granja). */
function fillRequired() {
  return (async () => {
    fireEvent.change(screen.getByLabelText(/Código/), { target: { value: 'GA6-T1' } })
    const combos = screen.getAllByRole('combobox')
    fireEvent.change(combos[0], { target: { value: 'broiler' } }) // tipo de ave
    // La granja está deshabilitada hasta que cargan los maestros.
    await waitFor(() => expect((screen.getAllByRole('combobox')[1] as HTMLSelectElement).disabled).toBe(false))
    fireEvent.change(screen.getAllByRole('combobox')[1], { target: { value: '1' } }) // granja
    await waitFor(() => expect(screen.getByRole('button', { name: 'Crear Lote' })).toBeTruthy())
  })()
}

const submit = () => fireEvent.click(screen.getByRole('button', { name: 'Crear Lote' }))

describe('GA-FE-06 · R-182 · contrato de alta de lote (RED)', () => {
  it('PLD capturada ⇒ viaja en POST /lots como planned_close_date (YYYY-MM-DD)', async () => {
    setSession()
    renderPage()
    await fillRequired()

    fireEvent.change(screen.getByLabelText('lots.plannedClose'), { target: { value: '2026-10-01' } })
    submit()

    await waitFor(() => expect(post).toHaveBeenCalled())
    const [url, payload] = post.mock.calls[0]
    expect(url).toBe('/lots')
    expect(payload.planned_close_date).toBe('2026-10-01')
  })

  it('selector «Área» alimentado por /masters/areas (nombres, sin IDs crudos)', async () => {
    setSession()
    renderPage()
    await fillRequired()

    // RED: hoy no existe el control ni la consulta.
    const areaSelect = await screen.findByLabelText('Área')
    await waitFor(() => expect(get).toHaveBeenCalledWith('/masters/areas?limit=100'))
    expect(within(areaSelect).getByText('Nave Norte (GA-FE-06)')).toBeTruthy()
    expect(within(areaSelect).queryByText(/#7\b/)).toBeNull()
  })

  it('área elegida ⇒ viaja en POST /lots como area_id', async () => {
    setSession()
    renderPage()
    await fillRequired()

    const areaSelect = await screen.findByLabelText('Área')
    fireEvent.change(areaSelect, { target: { value: '8' } })
    submit()

    await waitFor(() => expect(post).toHaveBeenCalled())
    const [, payload] = post.mock.calls[0]
    expect(payload.area_id).toBe(8)
  })

  it('sin fecha y sin área ⇒ null explícito en el payload (opcionalidad real)', async () => {
    setSession()
    renderPage()
    await fillRequired()
    submit()

    await waitFor(() => expect(post).toHaveBeenCalled())
    const [, payload] = post.mock.calls[0]
    expect(payload).toHaveProperty('planned_close_date', null)
    expect(payload).toHaveProperty('area_id', null)
  })

  it('control · alta mínima sigue funcionando tras el cambio (código/tipo/granja + éxito)', async () => {
    setSession()
    renderPage()
    await fillRequired()
    submit()

    await waitFor(() => expect(post).toHaveBeenCalled())
    const [, payload] = post.mock.calls[0]
    expect(payload.lot_code).toBe('GA6-T1')
    expect(payload.bird_type).toBe('broiler')
    expect(payload.farm_id).toBe(1)
    await waitFor(() => expect(toastSuccess).toHaveBeenCalled())
  })
})
