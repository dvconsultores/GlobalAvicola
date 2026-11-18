/**
 * `F6` · spec 015 §4 — RED jsdom del asistente de operaciones: los obligatorios del servidor
 * se exigen EN CLIENTE (sin petición y con mensaje inline). Arnés reutilizado de
 * `r190.locationEventsHouse.test.tsx` / `f01e.receptionHouse.test.tsx` (mocks de api, i18n y router).
 *
 * La matriz completa vive en `uatS1.requiredRules.test.ts` (regla pura); aquí 3 casos
 * representativos: cantidad, galpón de la inspección y el positivo del pesaje.
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

const LOTE_CRIA = { id: 7, lot_code: 'L-S1-0001', bird_type: 'breeder', farm_id: 1, house_id: 55, status: 'active' }
const LOTE_ENGORDE = { id: 9, lot_code: 'L-S1-0002', bird_type: 'broiler', farm_id: 1, house_id: 55, status: 'active' }
const FARM = { id: 1, name: 'Granja Norte', code: 'GN' }
const GALPON_55 = { id: 55, name: 'Galpón 55', farm_id: 1, capacity: 5000 }

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
    if (url.startsWith('/lots')) return Promise.resolve({ data: [LOTE_CRIA, LOTE_ENGORDE] })
    if (url.startsWith('/masters/farms')) return Promise.resolve({ data: [FARM] })
    if (url.startsWith('/masters/houses')) return Promise.resolve({ data: [GALPON_55] })
    if (url.startsWith('/sap/references')) return Promise.resolve({ data: { references: [] } })
    return Promise.resolve({ data: [] })
  })
  post.mockResolvedValue({ data: { id: 999 } })
})

const montar = () => render(
  <MemoryRouter initialEntries={['/operations/new']}>
    <ToastProvider><OperationFormPage /></ToastProvider>
  </MemoryRouter>)

const abrirEvento = async (etapa: RegExp, evento: RegExp) => {
  fireEvent.click(await screen.findByRole('button', { name: etapa }))
  fireEvent.click(await screen.findByRole('button', { name: evento }))
}

const elegirEnSelector = async (boton: RegExp, opcion: RegExp) => {
  fireEvent.click((await screen.findAllByRole('button', { name: boton }))[0])
  fireEvent.click((await screen.findAllByRole('button', { name: opcion }))[0])
}

const guardar = async () => {
  fireEvent.click(await screen.findByRole('button', { name: /common\.save/ }))
}

describe('F6 · obligatorios de operación en el formulario', () => {
  it('AC-S1-F6-01 · mortalidad con lote y cantidad vacía ⇒ sin POST y operations.quantityRequired', async () => {
    montar()
    await abrirEvento(/Progenitoras — Cría/, /mortality_recording/)
    await elegirEnSelector(/Seleccionar lote/, /L-S1-0001/)
    await guardar()
    await waitFor(() => expect(screen.getByText('operations.quantityRequired')).toBeTruthy())
    expect(post).not.toHaveBeenCalled()
  })

  it('AC-S1-F6-02 · inspección con granja y sin galpón ⇒ sin POST y operations.eventHouseRequired', async () => {
    montar()
    await abrirEvento(/Progenitoras — Cría/, /farm_inspection/)
    await elegirEnSelector(/Seleccionar granja/, /Granja Norte/)
    await guardar()
    await waitFor(() => expect(screen.getByText('operations.eventHouseRequired')).toBeTruthy())
    expect(post).not.toHaveBeenCalled()
  })

  it('AC-S1-F6-03 · pesaje con peso y SIN cantidad ⇒ POST con la fila de aves que lleva avg_weight', async () => {
    montar()
    await abrirEvento(/Engorde/, /weight_recording/)
    await elegirEnSelector(/Seleccionar lote/, /L-S1-0002/)
    const peso = document.querySelector('[name="bird_movements.0.avg_weight"]') as HTMLElement | null
    expect(peso, 'campo bird_movements.0.avg_weight').toBeTruthy()
    fireEvent.change(peso!, { target: { value: '2150' } })
    await guardar()

    await waitFor(() => expect(post).toHaveBeenCalled())
    const llamada = post.mock.calls.find((c) => c[0] === '/operations')
    expect(llamada, 'POST /operations').toBeTruthy()
    const filas = llamada![1]?.bird_movements ?? []
    expect(filas.length).toBeGreaterThan(0)
    expect(filas[0].avg_weight, `filas=${JSON.stringify(filas)}`).toBe(2150)
    // vacío = ausente: no se rellena la cantidad con 0
    expect(filas[0].quantity ?? null).toBeNull()
  })
})
