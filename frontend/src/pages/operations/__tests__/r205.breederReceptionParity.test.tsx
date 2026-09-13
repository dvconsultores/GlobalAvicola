/**
 * `R-205` · RED jsdom camino real — paridad del asistente para la recepción de
 * reproductoras (BR-20 · `B01`).
 *
 * El cuadre (`received_total`/`dead_on_arrival`/`rejected_on_arrival`) sólo se renderizaba
 * con `stage === 'breeder_rearing'`, y `stage` sólo se fijaba al atravesar el paso 1.
 * Cualquier enlace profundo (`?type=bird_reception`) saltaba al formulario con `stage=null`:
 * la recepción canónica por hub nacía **sin cuadre** y el backend respondía 400 BR-20.
 *
 * RED esperado en HEAD: 01/02/05 rojos; 03/04 controles verdes.
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

const LOTE_BREEDER = { id: 1, lot_code: 'L-BR-205-01', bird_type: 'breeder', farm_id: 1, house_id: 55, status: 'active' }
const LOTE_BROILER = { id: 2, lot_code: 'L-BO-205-01', bird_type: 'broiler', farm_id: 1, house_id: 55, status: 'active' }
const GALPON_55 = { id: 55, name: 'Galpón 55', farm_id: 1, capacity: 5000 }
const FARM = { id: 1, name: 'Granja Norte', code: 'GN' }

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
    if (url.startsWith('/lots')) return Promise.resolve({ data: [LOTE_BREEDER, LOTE_BROILER] })
    if (url.startsWith('/masters/farms')) return Promise.resolve({ data: [FARM] })
    if (url.startsWith('/masters/houses')) return Promise.resolve({ data: [GALPON_55] })
    if (url.startsWith('/sap/references')) return Promise.resolve({ data: { references: [] } })
    return Promise.resolve({ data: [] })
  })
  post.mockResolvedValue({ data: { id: 999 } })
})

const montar = (entrada: string) => render(
  <MemoryRouter initialEntries={[entrada]}>
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

const guardar = async () => {
  fireEvent.click(await screen.findByRole('button', { name: /common\.save/ }))
  await waitFor(() => expect(post).toHaveBeenCalled())
  const llamada = post.mock.calls.find((c) => c[0] === '/operations')
  expect(llamada, 'POST /operations').toBeTruthy()
  return llamada![1]
}

const llenarCuadre = (recibidas: string, muertas: string, rechazadas: string) => {
  cambio('received_total', recibidas)
  cambio('dead_on_arrival', muertas)
  cambio('rejected_on_arrival', rechazadas)
  cambio('sample_size', '10')
  cambio('bird_movements.0.quantity', '95')
}

const CUADRE = /Cuadre de la recepción/

describe('R-205 · recepción de reproductoras — paridad hub/detalle/URL', () => {
  it('AC-R205-01 · hub con deep link (type+lot) ⇒ cuadre visible y payload completo', async () => {
    montar('/operations/new?type=bird_reception&lot_id=1')
    await waitFor(() => expect(porNombre('received_total')).toBeTruthy())
    expect(screen.getByText(CUADRE)).toBeTruthy()
    llenarCuadre('100', '2', '3')
    const payload = await guardar()
    expect(payload.lot_id).toBe(1)
    expect(payload.received_total).toBe(100)
    expect(payload.dead_on_arrival).toBe(2)
    expect(payload.rejected_on_arrival).toBe(3)
  })

  it('AC-R205-02 · deep link con ?stage= explícito ⇒ paridad total', async () => {
    montar('/operations/new?type=bird_reception&lot_id=1&stage=breeder_rearing')
    await waitFor(() => expect(porNombre('received_total')).toBeTruthy())
    llenarCuadre('100', '2', '3')
    const payload = await guardar()
    expect(payload.received_total).toBe(100)
    expect(payload.dead_on_arrival).toBe(2)
    expect(payload.rejected_on_arrival).toBe(3)
  })

  it('AC-R205-05 · cuadre incompleto ⇒ sin POST y mensaje operations.cuadreRequired', async () => {
    montar('/operations/new?type=bird_reception&lot_id=1')
    await waitFor(() => expect(porNombre('received_total')).toBeTruthy())
    cambio('bird_movements.0.quantity', '95')
    fireEvent.click(await screen.findByRole('button', { name: /common\.save/ }))
    await waitFor(() => {
      expect(screen.getByText('operations.cuadreRequired')).toBeTruthy()
    })
    expect(post).not.toHaveBeenCalled()
  })

  it('AC-R205-03 · URL directa por pasos (control) ⇒ cuadre y payload', async () => {
    montar('/operations/new')
    fireEvent.click(await screen.findByRole('button', { name: /Reproductoras — Cría/ }))
    fireEvent.click(await screen.findByRole('button', { name: /bird_reception/ }))
    await waitFor(() => expect(porNombre('received_total')).toBeTruthy())
    expect(screen.getByText(CUADRE)).toBeTruthy()
    await elegirEnSelector(/Seleccionar lote/, /L-BR-205-01/)
    llenarCuadre('100', '2', '3')
    const payload = await guardar()
    expect(payload.received_total).toBe(100)
  })

  it('AC-R205-04 · lote broiler ⇒ sin cuadre (control)', async () => {
    montar('/operations/new?type=bird_reception&lot_id=2')
    await waitFor(() => expect(porNombre('bird_movements.0.quantity')).toBeTruthy())
    expect(screen.queryByText(CUADRE)).toBeNull()
  })
})
