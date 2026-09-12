/**
 * R-189 (F-01) · RED — el guardado del asistente debe emitir el contrato canónico:
 *   · `egg_storage_records` sin contenido ⇒ `[]` (nunca `[{}]`)
 *   · la OC elegida ⇒ `sap_document_ref` con el CÓDIGO de la referencia (campo que el dominio valida)
 * Camino real: se renderiza el formulario y se pulsa Guardar; se inspecciona el payload del POST.
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
const FARM = { id: 1, name: 'Granja Norte', code: 'GN' }

if (!window.matchMedia) {
  // jsdom no implementa matchMedia; SearchSelect lo consulta al montar.
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
    if (url.startsWith('/masters/farms')) return Promise.resolve({ data: [FARM] })
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
  fireEvent.click(await screen.findByRole('button', { name: boton }))
  const op = await screen.findByText(opcion)
  fireEvent.click(op)
}

const irAImportacion = async () => {
  fireEvent.click(await screen.findByRole('button', { name: /Progenitoras — Cría/ }))
  fireEvent.click(await screen.findByRole('button', { name: /grandparent_import/ }))
  await waitFor(() => expect(porNombre('extra_data.import_plan.origin_country')).toBeTruthy())
}

const llenarPlanDeImportacion = async () => {
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
}

const guardar = async () => {
  fireEvent.click(await screen.findByRole('button', { name: /common\.save/ }))
  await waitFor(() => expect(post).toHaveBeenCalled())
  const llamada = post.mock.calls.find((c) => c[0] === '/operations')
  expect(llamada, 'POST /operations').toBeTruthy()
  return llamada![1]
}

describe('R-189 · payload de importación (F-01)', () => {
  it('AC03/AC04 · sin almacenamiento capturado ⇒ egg_storage_records = [] (nunca [{}])', async () => {
    montar()
    await irAImportacion()
    await llenarPlanDeImportacion()
    const payload = await guardar()
    expect(payload.egg_storage_records).toEqual([])
    expect(payload.bird_movements).toHaveLength(2)
    for (const fila of payload.bird_movements) {
      expect(Number.isFinite(fila.avg_weight) || fila.avg_weight === undefined).toBe(true)
    }
  })

  it('AC08-AC11 · la OC elegida viaja en sap_document_ref con su código canónico', async () => {
    montar()
    await irAImportacion()
    await llenarPlanDeImportacion()
    const payload = await guardar()
    expect(payload.sap_document_ref).toBe('PO-C001-GPR-0001')
    expect(payload.extra_data?.sap_order_ref).toBe('PO-C001-GPR-0001')
    expect(payload.event_type).toBe('grandparent_import')
    expect(payload.lot_id ?? null).toBeNull()
  })
})

describe('R-189 · payload de recepción (F-01)', () => {
  it('AC15 · sin almacenamiento capturado ⇒ egg_storage_records = [] en recepción', async () => {
    montar()
    fireEvent.click(await screen.findByRole('button', { name: /Progenitoras — Cría/ }))
    fireEvent.click(await screen.findByRole('button', { name: /bird_reception/ }))
    await elegirEnSelector(/Seleccionar lote/, /L-GP-2099-01/)
    const granja = screen.queryByRole('button', { name: /Seleccionar granja/ })
    if (granja) await elegirEnSelector(/Seleccionar granja/, /Granja Norte/)
    const q = porNombre('bird_movements.0.quantity')
    if (q) cambio('bird_movements.0.quantity', '10')
    const payload = await guardar()
    expect(payload.egg_storage_records).toEqual([])
    expect(payload.bird_movements).toHaveLength(1)
    expect(payload.bird_movements[0].quantity).toBe(10)
    expect(Number.isFinite(payload.bird_movements[0].avg_weight) || payload.bird_movements[0].avg_weight === undefined).toBe(true)
  })
})
