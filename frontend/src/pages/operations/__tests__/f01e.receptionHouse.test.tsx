/**
 * R-189 (F-01e) · RED — el galpón capturado en la recepción debe viajar como `house_id` del evento
 * cuando el lote no lo declara (lotes autocreados `R-153`/`OD-25`, sin galpón).
 *
 * Camino real: se renderiza el formulario de recepción, se elige el lote y el galpón de la fila
 * de distribución y se pulsa Guardar; se inspecciona el payload del POST.
 *
 * Hallazgo F-01e (GA-UAT-09 retry): con el lote sin galpón, el payload hoy sale **sin** `house_id`
 * y el backend responde 400 `BR-08` «requiere un galpón asignado» — la recepción por UI queda
 * bloqueada para el camino canónico de `OD-25 (B)`.
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

const LOTE_SIN_GALPON = { id: 7, lot_code: 'L-GP-2099-01', farm_id: 1, house_id: null, status: 'active' }
const LOTE_CON_GALPON = { id: 8, lot_code: 'L-GP-2099-02', farm_id: 1, house_id: 55, status: 'active' }
const GALPON = { id: 11, name: 'Galpón 1', farm_id: 1, capacity: 5000 }
const GALPON_55 = { id: 55, name: 'Galpón 55', farm_id: 1, capacity: 5000 }
const FARM = { id: 1, name: 'Granja Norte', code: 'GN' }
const OC = { id: 33, sap_code: 'PO-C001-GPR-0001', description: 'OC abuelas', quantity: 5600, extra_data: { vendor_name: 'Cobb' } }

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
    if (url.startsWith('/lots')) return Promise.resolve({ data: [LOTE_SIN_GALPON, LOTE_CON_GALPON] })
    if (url.startsWith('/masters/farms')) return Promise.resolve({ data: [FARM] })
    if (url.startsWith('/masters/houses')) return Promise.resolve({ data: [GALPON, GALPON_55] })
    if (url.startsWith('/masters/suppliers')) return Promise.resolve({ data: [{ id: 1, name: 'Cobb-Vantress' }] })
    if (url.startsWith('/masters/transports')) return Promise.resolve({ data: [{ id: 1, name: 'Camión', plate: 'ABC-123' }] })
    if (url.startsWith('/sap/references')) {
      return Promise.resolve({ data: { references: url.includes('transfer_order') ? [] : [OC] } })
    }
    return Promise.resolve({ data: [] })
  })
  post.mockResolvedValue({ data: { id: 999 } })
})

const montar = () => render(<MemoryRouter initialEntries={['/operations/new']}><ToastProvider><OperationFormPage /></ToastProvider></MemoryRouter>)

const porNombre = (nombre: string) => document.querySelector(`[name="${nombre}"]`) as HTMLElement | null
const cambio = (nombre: string, valor: string) => {
  const el = porNombre(nombre)
  expect(el, `campo ${nombre}`).toBeTruthy()
  fireEvent.change(el!, { target: { value: valor } })
}

const elegirEnSelector = async (boton: RegExp, opcion: RegExp) => {
  const botones = await screen.findAllByRole('button', { name: boton })
  fireEvent.click(botones[0])
  // La opción es un <button> del desplegable; la etiqueta «Galpón N» de la fila es un <span> (no debe elegirse).
  const opciones = await screen.findAllByRole('button', { name: opcion })
  fireEvent.click(opciones[0])
}

const irARecepcion = async () => {
  fireEvent.click(await screen.findByRole('button', { name: /Progenitoras — Cría/ }))
  fireEvent.click(await screen.findByRole('button', { name: /bird_reception/ }))
  await waitFor(() => expect(porNombre('bird_movements.0.quantity')).toBeTruthy())
}

const guardar = async () => {
  fireEvent.click(await screen.findByRole('button', { name: /common\.save/ }))
  await waitFor(() => expect(post).toHaveBeenCalled())
  const llamada = post.mock.calls.find((c) => c[0] === '/operations')
  expect(llamada, 'POST /operations').toBeTruthy()
  return llamada![1]
}

describe('R-189 · F-01e · galpón de la recepción (house_id del evento)', () => {
  it('AC-F01E-01 · lote SIN galpón + galpón elegido en la fila ⇒ house_id del evento = galpón de la fila', async () => {
    montar()
    await irARecepcion()
    await elegirEnSelector(/Seleccionar lote/, /L-GP-2099-01/)
    await elegirEnSelector(/Seleccionar galpón/, /Galpón 1/)
    cambio('bird_movements.0.quantity', '40')
    const payload = await guardar()
    expect(payload.lot_id).toBe(7)
    expect(payload.bird_movements[0].target_house_id).toBe(11)
    expect(payload.house_id).toBe(11)
  })

  it('AC-F01E-02 · lote CON galpón ⇒ el house_id del lote se conserva (sin regresión)', async () => {
    montar()
    await irARecepcion()
    await elegirEnSelector(/Seleccionar lote/, /L-GP-2099-02/)
    await elegirEnSelector(/Seleccionar galpón/, /Galpón 1/)
    cambio('bird_movements.0.quantity', '50')
    const payload = await guardar()
    expect(payload.lot_id).toBe(8)
    expect(payload.house_id).toBe(55)
  })

  it('AC-F01E-03 · sin galpón en el lote NI en las filas ⇒ house_id ausente (sin inventar)', async () => {
    montar()
    await irARecepcion()
    await elegirEnSelector(/Seleccionar lote/, /L-GP-2099-01/)
    cambio('bird_movements.0.quantity', '30')
    const payload = await guardar()
    expect(payload.house_id ?? null).toBeNull()
  })

  it('AC-F01E-04 · frontera: la importación no cambia (sin fallback de galpón)', async () => {
    montar()
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
    cambio('bird_movements.0.quantity', '40')
    cambio('bird_movements.1.quantity', '60')
    const payload = await guardar()
    expect(payload.event_type).toBe('grandparent_import')
    expect(payload.house_id ?? null).toBeNull()
  })
})
