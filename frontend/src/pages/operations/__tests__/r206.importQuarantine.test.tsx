/**
 * `R-206` · RED jsdom — importación de abuelas con «Cuarentena (fecha fin)» en blanco.
 *
 * El campo es opcional; en blanco viaja como `''` y `PlanDeImportacion` lo rechaza
 * (400 BR-22 «Input should be a valid date»). El payload canónico debe **omitir** la clave.
 *
 * RED esperado en HEAD: el POST lleva `quarantine_end_date: ''` ⇒ la aserción de ausencia
 * falla.
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

const LOTE = { id: 7, lot_code: 'L-GP-2099-01', farm_id: 1, house_id: null, status: 'active' }
const FARM = { id: 1, name: 'Granja Norte', code: 'GN' }
const GALPON = { id: 11, name: 'Galpón 1', farm_id: 1, capacity: 5000 }
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
    if (url.startsWith('/lots')) return Promise.resolve({ data: [LOTE] })
    if (url.startsWith('/masters/farms')) return Promise.resolve({ data: [FARM] })
    if (url.startsWith('/masters/houses')) return Promise.resolve({ data: [GALPON] })
    if (url.startsWith('/masters/suppliers')) return Promise.resolve({ data: [{ id: 1, name: 'Cobb-Vantress' }] })
    if (url.startsWith('/masters/transports')) return Promise.resolve({ data: [{ id: 1, name: 'Camión', plate: 'ABC-123' }] })
    if (url.startsWith('/sap/references')) {
      return Promise.resolve({ data: { references: url.includes('transfer_order') ? [] : [OC] } })
    }
    return Promise.resolve({ data: [] })
  })
  post.mockResolvedValue({ data: { id: 999 } })
})

const montar = () => render(
  <MemoryRouter initialEntries={['/operations/new']}>
    <ToastProvider><OperationFormPage /></ToastProvider>
  </MemoryRouter>)

const porNombre = (nombre: string) => document.querySelector(`[name="${nombre}"]`) as HTMLElement | null
const cambio = (nombre: string, valor: string) => {
  const el = porNombre(nombre)
  expect(el, `campo ${nombre}`).toBeTruthy()
  fireEvent.change(el!, { target: { value: valor } })
}

const elegirEnSelector = async (boton: RegExp, opcion: RegExp) => {
  const botones = await screen.findAllByRole('button', { name: boton })
  fireEvent.click(botones[0])
  const opciones = await screen.findAllByRole('button', { name: opcion })
  fireEvent.click(opciones[0])
}

describe('R-206 · importación con fecha de cuarentena en blanco', () => {
  it('el payload omite quarantine_end_date (canónico: vacío ⇒ ausencia)', async () => {
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
    // «Cuarentena (fecha fin)» queda en blanco — el caso del hallazgo.

    fireEvent.click(await screen.findByRole('button', { name: /common\.save/ }))
    await waitFor(() => expect(post).toHaveBeenCalled())
    const llamada = post.mock.calls.find((c) => c[0] === '/operations')
    expect(llamada, 'POST /operations').toBeTruthy()
    const plan = llamada![1]?.extra_data?.import_plan ?? {}
    expect('quarantine_end_date' in plan, `plan=${JSON.stringify(plan)}`).toBe(false)
  })
})
