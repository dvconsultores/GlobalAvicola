/**
 * `R-190` (F-01e generalizado) · RED jsdom camino real — el `house_id` del evento en los
 * 7 tipos de `location_events` restantes.
 *
 * Hallazgo: sólo la recepción (`R-189`) derivaba su galpón; en distribución, traslado,
 * salida, recolección, despacho, inspección de granja y de transporte el payload salía sin
 * `house_id` (o sin `farm_id`) y el backend respondía 400 `BR-08` — el eslabón visible de
 * P-01/P-03 quedaba roto para los lotes autocreados sin galpón (`OD-25 (B)`).
 *
 * RED esperado en HEAD: 01/02/03/04a/07/08a/08b/09/11 rojos; 04b/05 controles verdes.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

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
const GALPON_11 = { id: 11, name: 'Galpón 1', farm_id: 1, capacity: 5000 }
const GALPON_12 = { id: 12, name: 'Galpón 2', farm_id: 1, capacity: 5000 }
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
    if (url.startsWith('/lots')) return Promise.resolve({ data: [LOTE_SIN_GALPON, LOTE_CON_GALPON] })
    if (url.startsWith('/masters/farms')) return Promise.resolve({ data: [FARM] })
    if (url.startsWith('/masters/houses')) return Promise.resolve({ data: [GALPON_11, GALPON_12, GALPON_55] })
    if (url.startsWith('/masters/transports')) return Promise.resolve({ data: [{ id: 1, name: 'Camión', plate: 'ABC-123' }] })
    if (url.startsWith('/sap/references')) return Promise.resolve({ data: { references: [] } })
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

const elegirEnSelector = async (boton: RegExp, opcion: RegExp, indice = 0) => {
  const botones = await screen.findAllByRole('button', { name: boton })
  fireEvent.click(botones[indice])
  const opciones = await screen.findAllByRole('button', { name: opcion })
  fireEvent.click(opciones[0])
}

const abrirEvento = async (etapa: RegExp, evento: RegExp) => {
  fireEvent.click(await screen.findByRole('button', { name: etapa }))
  fireEvent.click(await screen.findByRole('button', { name: evento }))
}

const guardar = async () => {
  fireEvent.click(await screen.findByRole('button', { name: /common\.save/ }))
  await waitFor(() => expect(post).toHaveBeenCalled())
  const llamada = post.mock.calls.find((c) => c[0] === '/operations')
  expect(llamada, 'POST /operations').toBeTruthy()
  return llamada![1]
}

describe('R-190 · galpón del evento en location_events (sin recepción)', () => {
  it('AC-R190-01 · distribución · lote sin galpón + galpón de fila ⇒ house_id del evento', async () => {
    montar()
    await abrirEvento(/Progenitoras — Cría/, /bird_distribution/)
    await elegirEnSelector(/Seleccionar lote/, /L-GP-2099-01/)
    await elegirEnSelector(/Seleccionar galpón/, /Galpón 1/)
    cambio('bird_movements.0.quantity', '40')
    const payload = await guardar()
    expect(payload.lot_id).toBe(7)
    expect(payload.bird_movements[0].target_house_id).toBe(11)
    expect(payload.house_id).toBe(11)
  })

  it('AC-R190-02 · salida · lote sin galpón ⇒ selector «Galpón del evento» y house_id', async () => {
    montar()
    await abrirEvento(/Progenitoras — Cría/, /bird_exit/)
    await elegirEnSelector(/Seleccionar lote/, /L-GP-2099-01/)
    await elegirEnSelector(/Galpón del evento/, /Galpón 1/)
    const payload = await guardar()
    expect(payload.house_id).toBe(11)
  })

  it('AC-R190-03 · recolección · lote sin galpón ⇒ house_id del evento', async () => {
    montar()
    await abrirEvento(/Progenitoras — Producción/, /egg_collection/)
    await elegirEnSelector(/Seleccionar lote/, /L-GP-2099-01/)
    await elegirEnSelector(/Galpón del evento/, /Galpón 1/)
    cambio('egg_movements.0.quantity', '100')
    const payload = await guardar()
    expect(payload.house_id).toBe(11)
  })

  it('AC-R190-04a · inspección de granja sin granja ni galpón en filas ⇒ sin POST y operations.farmRequired', async () => {
    montar()
    await abrirEvento(/Progenitoras — Cría/, /farm_inspection/)
    fireEvent.click(await screen.findByRole('button', { name: /Añadir galpón/ }))
    cambio('house_inspections.0.temperature', '25')
    fireEvent.click(await screen.findByRole('button', { name: /common\.save/ }))
    await waitFor(() => {
      expect(screen.getByText('operations.farmRequired')).toBeTruthy()
    })
    expect(post).not.toHaveBeenCalled()
  })

  it('AC-R190-04b · inspección de granja con granja y galpón de fila ⇒ farm_id y house_id (control)', async () => {
    montar()
    await abrirEvento(/Progenitoras — Cría/, /farm_inspection/)
    await elegirEnSelector(/Seleccionar granja/, /Granja Norte/)
    fireEvent.click(await screen.findByRole('button', { name: /Añadir galpón/ }))
    await elegirEnSelector(/Seleccionar galpón/, /Galpón 1/)
    cambio('house_inspections.0.temperature', '25')
    const payload = await guardar()
    expect(payload.farm_id).toBe(1)
    expect(payload.house_id).toBe(11)
  })

  it('AC-R190-05 · lote CON galpón ⇒ el house_id del lote manda (control)', async () => {
    montar()
    await abrirEvento(/Progenitoras — Cría/, /bird_distribution/)
    await elegirEnSelector(/Seleccionar lote/, /L-GP-2099-02/)
    await elegirEnSelector(/Seleccionar galpón/, /Galpón 2/)
    cambio('bird_movements.0.quantity', '30')
    const payload = await guardar()
    expect(payload.house_id).toBe(55)
  })

  it('AC-R190-07 · traslado · lote sin galpón ⇒ house_id = galpón origen de la fila 0', async () => {
    montar()
    await abrirEvento(/Progenitoras — Cría/, /bird_transfer/)
    await elegirEnSelector(/Seleccionar lote/, /L-GP-2099-01/)
    await elegirEnSelector(/Seleccionar galpón/, /Galpón 1/, 0)
    await elegirEnSelector(/Seleccionar galpón/, /Galpón 2/)
    const payload = await guardar()
    expect(payload.house_id).toBe(11)
  })

  it('AC-R190-08a · despacho de huevos ⇒ house_id del selector', async () => {
    montar()
    await abrirEvento(/Progenitoras — Producción/, /egg_dispatch/)
    await elegirEnSelector(/Seleccionar lote/, /L-GP-2099-01/)
    await elegirEnSelector(/Galpón del evento/, /Galpón 1/)
    const payload = await guardar()
    expect(payload.house_id).toBe(11)
  })

  it('AC-R190-08b · inspección de transporte ⇒ house_id del selector', async () => {
    montar()
    await abrirEvento(/Progenitoras — Cría/, /transport_inspection/)
    await elegirEnSelector(/Seleccionar lote/, /L-GP-2099-01/)
    await elegirEnSelector(/Galpón del evento/, /Galpón 1/)
    const payload = await guardar()
    expect(payload.house_id).toBe(11)
  })

  it('AC-R190-09 · salida sin galpón elegido ⇒ sin POST y operations.eventHouseRequired', async () => {
    montar()
    await abrirEvento(/Progenitoras — Cría/, /bird_exit/)
    await elegirEnSelector(/Seleccionar lote/, /L-GP-2099-01/)
    fireEvent.click(await screen.findByRole('button', { name: /common\.save/ }))
    await waitFor(() => {
      expect(screen.getByText('operations.eventHouseRequired')).toBeTruthy()
    })
    expect(post).not.toHaveBeenCalled()
  })
})

describe('R-190 · i18n de ubicación', () => {
  it('AC-R190-11 · claves es/en presentes', () => {
    for (const idioma of ['es', 'en']) {
      const ruta = resolve(__dirname, `../../../../public/locales/${idioma}/translation.json`)
      const dict = JSON.parse(readFileSync(ruta, 'utf8'))
      expect(dict.operations?.farmRequired, `${idioma}.operations.farmRequired`).toBeTruthy()
      expect(dict.operations?.eventHouseRequired, `${idioma}.operations.eventHouseRequired`).toBeTruthy()
      expect(dict.operations?.eventHouse, `${idioma}.operations.eventHouse`).toBeTruthy()
    }
  })
})
