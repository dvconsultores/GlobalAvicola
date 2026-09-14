/**
 * `R-194` · RED jsdom — cadena de incubadora por UI (recepción → carga → nacimiento → despacho).
 *
 * Cinco defectos de contrato en la etapa incubadora: (a) `farm_id` forzado a `undefined`
 * ⇒ 400 BR-08; (b) los fértiles viajan en `egg_storage_records` y no como
 * `egg_movements[fertile]` ⇒ saldo BR-03 en 0; (c) `arrival_date` no capturado ⇒ 422;
 * (d) `dosage_per_bird` sin `valueAsNumber` ⇒ envío silencioso; (e) el selector de
 * incubadora no llega al payload (`hatchery_params[0].hatchery_id`).
 *
 * RED esperado en HEAD: AC-01/02/03/04/06 rojos.
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

const LOTE_HAT = { id: 30, lot_code: 'L-HAT-194-01', bird_type: 'hatchery', farm_id: 1, house_id: 80, status: 'active' }
const PLANTA = { id: 1, name: 'Planta Incubadora', code: 'PI', farm_id: 1 }
const GALPON_80 = { id: 80, name: 'Galpón 80', farm_id: 1, capacity: 100000 }
const INCUBADORA = { id: 1, name: 'Setter 1', code: 'SET1' }

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
    if (url.startsWith('/lots')) return Promise.resolve({ data: [LOTE_HAT] })
    if (url.startsWith('/masters/farms')) return Promise.resolve({ data: [PLANTA] })
    if (url.startsWith('/masters/houses')) return Promise.resolve({ data: [GALPON_80] })
    if (url.startsWith('/masters/hatcheries')) return Promise.resolve({ data: [PLANTA] })
    if (url.startsWith('/masters/incubators')) return Promise.resolve({ data: [INCUBADORA] })
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

const elegirEnSelector = async (boton: RegExp, opcion: RegExp) => {
  const botones = await screen.findAllByRole('button', { name: boton })
  fireEvent.click(botones[0])
  const opciones = await screen.findAllByRole('button', { name: opcion })
  fireEvent.click(opciones[0])
}

const abrirEvento = async (evento: RegExp) => {
  fireEvent.click(await screen.findByRole('button', { name: /Incubadora/ }))
  fireEvent.click(await screen.findByRole('button', { name: evento }))
}

const guardar = async () => {
  fireEvent.click(await screen.findByRole('button', { name: /common\.save/ }))
  await waitFor(() => expect(post).toHaveBeenCalled())
  const llamada = post.mock.calls.find((c) => c[0] === '/operations')
  expect(llamada, 'POST /operations').toBeTruthy()
  return llamada![1]
}

describe('R-194 · cadena de incubadora por UI', () => {
  it('AC-R194-01 · recepción con ubicación y arrival_date en el payload', async () => {
    montar()
    await abrirEvento(/egg_reception_hatchery/)
    await elegirEnSelector(/Seleccionar lote/, /L-HAT-194-01/)
    cambio('egg_storage_records.0.eggs_received', '1000')
    const payload = await guardar()
    expect(payload.farm_id).toBe(1)
    expect(payload.house_id).toBe(80)
    expect(payload.egg_storage_records?.[0]?.arrival_date).toBeTruthy()
  })

  it('AC-R194-02 · los fértiles viajan como egg_movements[fertile]', async () => {
    montar()
    await abrirEvento(/egg_reception_hatchery/)
    await elegirEnSelector(/Seleccionar lote/, /L-HAT-194-01/)
    cambio('egg_storage_records.0.eggs_received', '1000')
    const payload = await guardar()
    const fertiles = (payload.egg_movements || []).find((m: any) => m?.egg_type === 'fertile')
    expect(fertiles?.quantity).toBe(1000)
  })

  it('AC-R194-03 · carga de incubadora envía petición', async () => {
    montar()
    await abrirEvento(/incubation_load/)
    await elegirEnSelector(/Seleccionar lote/, /L-HAT-194-01/)
    cambio('hatchery_params.0.quantity_loaded', '500')
    await guardar()
  })

  it('AC-R194-04a · nacimiento: dosis válida envía', async () => {
    montar()
    await abrirEvento(/birth_registration/)
    await elegirEnSelector(/Seleccionar lote/, /L-HAT-194-01/)
    cambio('dosage_per_bird', '0.2')
    cambio('bird_movements.0.quantity', '300')
    await guardar()
  })

  it('AC-R194-04b · nacimiento: dosis negativa ⇒ sin POST y operations.dosageInvalid', async () => {
    montar()
    await abrirEvento(/birth_registration/)
    await elegirEnSelector(/Seleccionar lote/, /L-HAT-194-01/)
    cambio('dosage_per_bird', '-1')
    cambio('bird_movements.0.quantity', '300')
    fireEvent.click(await screen.findByRole('button', { name: /common\.save/ }))
    await waitFor(() => {
      expect(screen.getByText('La dosis debe ser un número ≥ 0')).toBeTruthy()
    })
    expect(post).not.toHaveBeenCalled()
  })

  it('AC-R194-06 · hatchery_id viaja en la fila', async () => {
    montar()
    await abrirEvento(/egg_reception_hatchery/)
    // El selector de incubadora acota el catálogo de lotes: primero la incubadora.
    await elegirEnSelector(/Seleccionar incubadora/, /Planta Incubadora/)
    await elegirEnSelector(/Seleccionar lote/, /L-HAT-194-01/)
    cambio('egg_storage_records.0.eggs_received', '1000')
    const payload = await guardar()
    expect(payload.hatchery_params?.[0]?.hatchery_id).toBe(1)
  })
})
