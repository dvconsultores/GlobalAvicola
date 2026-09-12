/**
 * R-189 (F-01) · RED — un 4xx gobernado (422 estructurado de FastAPI) no puede romper el render.
 * Se renderiza el formulario, se provoca el rechazo realista del POST y se exige:
 * página montada, mensaje humano visible y ninguna excepción de React.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

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

import OperationFormPage from '../OperationFormPage'
import { ToastProvider } from '../../../components/Toast'

const LOT = { id: 7, lot_code: 'L-GP-2099-01', farm_id: 1, house_id: null, status: 'active' }
const OC = { id: 33, sap_code: 'PO-C001-GPR-0001', description: 'OC abuelas', quantity: 100, extra_data: { vendor_name: 'Cobb' } }

if (!window.matchMedia) {
  // @ts-expect-error polyfill de prueba
  window.matchMedia = (q: string) => ({
    matches: false, media: q, onchange: null,
    addEventListener: () => {}, removeEventListener: () => {},
    addListener: () => {}, removeListener: () => {}, dispatchEvent: () => false,
  })
}
if (!Element.prototype.scrollIntoView) Element.prototype.scrollIntoView = () => {}

beforeEach(() => {
  vi.clearAllMocks()
  get.mockImplementation((url: string) => {
    if (url.startsWith('/lots')) return Promise.resolve({ data: [LOT] })
    if (url.startsWith('/masters/farms')) return Promise.resolve({ data: [{ id: 1, name: 'Granja Norte', code: 'GN' }] })
    if (url.startsWith('/masters/suppliers')) return Promise.resolve({ data: [{ id: 1, name: 'Cobb-Vantress' }] })
    if (url.startsWith('/masters/transports')) return Promise.resolve({ data: [{ id: 1, name: 'Camión', plate: 'ABC-123' }] })
    if (url.startsWith('/sap/references')) {
      return Promise.resolve({ data: { references: url.includes('transfer_order') ? [] : [OC] } })
    }
    return Promise.resolve({ data: [] })
  })
})

const porNombre = (nombre: string) => document.querySelector(`[name="${nombre}"]`) as HTMLElement | null
const cambio = (nombre: string, valor: string) => {
  const el = porNombre(nombre)
  expect(el, `campo ${nombre}`).toBeTruthy()
  fireEvent.change(el!, { target: { value: valor } })
}
const elegirEnSelector = async (boton: RegExp, opcion: RegExp) => {
  fireEvent.click(await screen.findByRole('button', { name: boton }))
  fireEvent.click(await screen.findByText(opcion))
}

describe('R-189 · render seguro de errores (F-01 · React #31)', () => {
  it('AC19-AC26 · 422 estructurado ⇒ mensaje legible y página usable (sin excepción de React)', async () => {
    post.mockRejectedValueOnce({
      response: {
        data: {
          detail: [{ type: 'missing', loc: ['body', 'egg_storage_records', 0, 'arrival_date'], msg: 'Field required', input: {} }],
        },
      },
    })
    render(<MemoryRouter initialEntries={['/operations/new']}><ToastProvider><OperationFormPage /></ToastProvider></MemoryRouter>)

    fireEvent.click(await screen.findByRole('button', { name: /Progenitoras — Cría/ }))
    fireEvent.click(await screen.findByRole('button', { name: /grandparent_import/ }))
    await waitFor(() => expect(porNombre('extra_data.import_plan.origin_country')).toBeTruthy())
    await elegirEnSelector(/Seleccionar orden SAP/, /PO-C001-GPR-0001/)
    await elegirEnSelector(/Seleccionar proveedor/, /Cobb-Vantress/)
    await elegirEnSelector(/Seleccionar transporte/, /Camión/)
    cambio('extra_data.import_plan.origin_country', 'Francia')
    cambio('extra_data.import_plan.purchased_total', '110')
    cambio('extra_data.import_plan.shipped_total', '105')
    cambio('extra_data.import_plan.received_total', '100')
    cambio('extra_data.import_plan.transit_mortality', '5')
    cambio('extra_data.import_plan.departure_date', '2026-09-05')
    cambio('extra_data.import_plan.arrival_date', '2026-09-12')
    cambio('extra_data.import_plan.reception_condition', 'buena')
    cambio('extra_data.import_plan.quarantine_days', '21')
    cambio('extra_data.import_plan.quarantine_end_date', '2026-10-03')
    cambio('extra_data.import_plan.initial_health_inspection', 'sin hallazgos')
    cambio('bird_movements.0.quantity', '40')
    cambio('bird_movements.1.quantity', '60')
    if (porNombre('bird_movements.0.avg_weight')) cambio('bird_movements.0.avg_weight', '3800')
    if (porNombre('bird_movements.1.avg_weight')) cambio('bird_movements.1.avg_weight', '3600')

    fireEvent.click(await screen.findByRole('button', { name: /common\.save/ }))
    await waitFor(() => expect(post).toHaveBeenCalled())

    // La página sigue montada y usable…
    await waitFor(() => expect(screen.getByRole('button', { name: /common\.save/ })).toBeInTheDocument())
    // …y el rechazo se explica en texto humano (con la ubicación del error, sin objetos crudos).
    await waitFor(() => expect(screen.getByText(/Field required/)).toBeInTheDocument())
    expect(screen.getByText(/egg_storage_records\.0\.arrival_date/)).toBeInTheDocument()
  })
})
