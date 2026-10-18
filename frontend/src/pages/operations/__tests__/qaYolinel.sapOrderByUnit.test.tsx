/**
 * `QA-007` · `BR-23` · RED jsdom — la OC de una recepción de aves se filtra por la cadena
 * del lote y la cadena desconocida se rotula «sin cadena».
 *
 * El selector cargaba **todas** las OC (`/sap/references?ref_type=purchase_order`) y no
 * había forma de saber a qué cadena pertenecía cada una: podía recepcionarse una OC de
 * Engorde dentro de Reproductoras. Regla (`FR-01` · `AC-01.5`): el selector pide las OC con
 * `&business_unit=<lots.bird_type>` en cuanto hay lote, espera al lote cuando no lo hay y
 * rotula `business_unit_code = null` como «sin cadena» (cadena desconocida ⇒ se permite).
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

const LOTE_BREEDER = { id: 1, lot_code: 'L-BR', bird_type: 'breeder', status: 'active', farm_id: 1, house_id: 1 }
const FARM = { id: 1, name: 'Granja Norte', code: 'GN' }
const GALPON_1 = { id: 1, name: 'Galpón 1', farm_id: 1, capacity: 5000 }

const OC_BREEDER = {
  id: 11, sap_code: '4500001111', ref_type: 'purchase_order', quantity: 100,
  description: 'OC reproductoras', business_unit_code: 'breeder', extra_data: {},
}
const OC_SIN_CADENA = {
  id: 12, sap_code: '4500002222', ref_type: 'purchase_order', quantity: 50,
  description: 'OC sin centros', business_unit_code: null, extra_data: {},
}

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
    if (url.startsWith('/lots')) return Promise.resolve({ data: [LOTE_BREEDER] })
    if (url.startsWith('/masters/farms')) return Promise.resolve({ data: [FARM] })
    if (url.startsWith('/masters/houses')) return Promise.resolve({ data: [GALPON_1] })
    if (url.startsWith('/sap/references')) {
      return Promise.resolve({
        data: {
          references: url.includes('transfer_order') ? [] : [OC_BREEDER, OC_SIN_CADENA],
        },
      })
    }
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
  const botones = await screen.findAllByRole('button', { name: boton })
  fireEvent.click(botones[0])
  const opciones = await screen.findAllByRole('button', { name: opcion })
  fireEvent.click(opciones[0])
}

const urlsPedidas = () => get.mock.calls.map((c) => String(c[0]))

describe('QA-007 · la OC de la recepción se filtra por la cadena del lote', () => {
  it('AC-01.5 · con lote breeder, las OC se piden con business_unit=breeder', async () => {
    montar()
    await abrirEvento(/Reproductoras — Cría/, /bird_reception/)
    await elegirEnSelector(/Seleccionar lote/, /L-BR/)
    await waitFor(() => {
      const urls = urlsPedidas()
      expect(
        urls.some((u) => u.includes('ref_type=purchase_order') && u.includes('business_unit=breeder')),
        `urls=${JSON.stringify(urls)}`,
      ).toBe(true)
    })
  })

  it('AC-01.5b · sin lote no se pide ninguna OC filtrada por cadena y el selector espera al lote', async () => {
    montar()
    await abrirEvento(/Reproductoras — Cría/, /bird_reception/)
    await screen.findByRole('button', { name: /Seleccionar lote/ })
    const conCadena = urlsPedidas().filter((u) => u.includes('business_unit='))
    expect(conCadena, `urls=${JSON.stringify(urlsPedidas())}`).toEqual([])
    const espera = await screen.findAllByRole('button', { name: /Seleccione el lote primero/ })
    expect((espera[0] as HTMLButtonElement).disabled).toBe(true)
  })

  it('AC-01.3 · la OC de cadena desconocida se rotula «sin cadena» en el selector', async () => {
    montar()
    await abrirEvento(/Reproductoras — Cría/, /bird_reception/)
    await elegirEnSelector(/Seleccionar lote/, /L-BR/)
    fireEvent.click((await screen.findAllByRole('button', { name: /Seleccionar orden SAP/ }))[0])
    await waitFor(() => expect(screen.getByText(/OC sin centros · sin cadena/)).toBeTruthy())
    // control: la OC con cadena conocida sí la muestra
    expect(screen.getByText(/OC reproductoras · breeder/)).toBeTruthy()
  })
})
