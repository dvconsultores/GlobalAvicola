/**
 * `R-209` · RED jsdom — los selectores SAP guardan el **código** de la referencia, no su id.
 *
 * `bird_exit` guardaba `String(id)` en `sap_document_ref` y `feed_registration` en
 * `feed_movements[0].sap_order_id`: el comparativo SAP quedaba en `'12'`/`'9'` en vez de
 * `'4500001234'`/`'4500009'`, y una referencia sin código escribía el id en la clave.
 * Canónico (`R-189 §2`): `identificadorDeOrdenSap` (doc_number → ref_id → sap_code);
 * sin código ⇒ ausente, nunca `String(id)`.
 *
 * RED esperado en HEAD: 01/02/03 rojos.
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

const LOTE = { id: 7, lot_code: 'L-BR-209-01', bird_type: 'breeder', farm_id: 1, house_id: 55, status: 'active' }
const FARM = { id: 1, name: 'Granja Norte', code: 'GN' }
const GALPON_55 = { id: 55, name: 'Galpón 55', farm_id: 1, capacity: 5000 }

const OC_CON_CODIGO = { id: 12, sap_code: '4500001234', doc_number: '4500001234', description: 'OC salida', extra_data: {} }
const OC_SIN_CODIGO = { id: 5, sap_code: null, doc_number: null, ref_id: null, description: 'REFERENCIA-VACIA', extra_data: {} }
const OT_CON_CODIGO = { id: 9, sap_code: '4500009', doc_number: '4500009', description: 'OT alimento' }

if (!window.matchMedia) {
  // @ts-expect-error polyfill de prueba
  window.matchMedia = (q: string) => ({
    matches: false, media: q, onchange: null,
    addEventListener: () => {}, removeEventListener: () => {},
    addListener: () => {}, removeListener: () => {}, dispatchEvent: () => false,
  })
}
if (!Element.prototype.scrollIntoView) Element.prototype.scrollIntoView = () => {}

function mockCatalogo(oc: any) {
  get.mockImplementation((url: string) => {
    if (url.startsWith('/lots')) return Promise.resolve({ data: [LOTE] })
    if (url.startsWith('/masters/farms')) return Promise.resolve({ data: [FARM] })
    if (url.startsWith('/masters/houses')) return Promise.resolve({ data: [GALPON_55] })
    if (url.startsWith('/masters/transports')) return Promise.resolve({ data: [{ id: 1, name: 'Camión', plate: 'ABC-123' }] })
    if (url.startsWith('/sap/references')) {
      return Promise.resolve({ data: { references: url.includes('transfer_order') ? [OT_CON_CODIGO] : [oc] } })
    }
    return Promise.resolve({ data: [] })
  })
}

beforeEach(() => {
  vi.clearAllMocks()
  mockCatalogo(OC_CON_CODIGO)
  post.mockResolvedValue({ data: { id: 999 } })
})

const montar = () => render(
  <MemoryRouter initialEntries={['/operations/new']}>
    <ToastProvider><OperationFormPage /></ToastProvider>
  </MemoryRouter>)

const elegirEnSelector = async (boton: RegExp, opcion: RegExp) => {
  const botones = await screen.findAllByRole('button', { name: boton })
  fireEvent.click(botones[0])
  const opciones = await screen.findAllByRole('button', { name: opcion })
  fireEvent.click(opciones[0])
}

const abrirEvento = async (evento: RegExp) => {
  fireEvent.click(await screen.findByRole('button', { name: /Progenitoras — Cría/ }))
  fireEvent.click(await screen.findByRole('button', { name: evento }))
}

const guardar = async () => {
  fireEvent.click(await screen.findByRole('button', { name: /common\.save/ }))
  await waitFor(() => expect(post).toHaveBeenCalled())
  const llamada = post.mock.calls.find((c) => c[0] === '/operations')
  expect(llamada, 'POST /operations').toBeTruthy()
  return llamada![1]
}

describe('R-209 · selectores SAP guardan el código canónico', () => {
  it('AC-R209-01 · bird_exit guarda el código de la OC', async () => {
    montar()
    await abrirEvento(/bird_exit/)
    await elegirEnSelector(/Seleccionar lote/, /L-BR-209-01/)
    await elegirEnSelector(/Seleccionar orden SAP/, /4500001234/)
    const payload = await guardar()
    expect(payload.sap_document_ref).toBe('4500001234')
  })

  it('AC-R209-02 · feed_registration guarda el código de la OT', async () => {
    montar()
    await abrirEvento(/feed_registration/)
    await elegirEnSelector(/Seleccionar lote/, /L-BR-209-01/)
    await elegirEnSelector(/Sin orden/, /4500009/)
    const campo = document.querySelector('[name="feed_movements.0.quantity_kg"]') as HTMLElement | null
    if (campo) fireEvent.change(campo, { target: { value: '100' } })
    const payload = await guardar()
    expect(payload.feed_movements?.[0]?.sap_order_id).toBe('4500009')
  })

  it('AC-R209-03 · referencia sin código ⇒ clave ausente (nunca String(id))', async () => {
    mockCatalogo(OC_SIN_CODIGO)
    montar()
    await abrirEvento(/bird_exit/)
    await elegirEnSelector(/Seleccionar lote/, /L-BR-209-01/)
    await elegirEnSelector(/Seleccionar orden SAP/, /REFERENCIA-VACIA/)
    const payload = await guardar()
    expect(payload.sap_document_ref ?? null).toBeNull()
  })
})
