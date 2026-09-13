/**
 * `R-210` · RED jsdom — el pesaje se captura y rotula en **gramos** (unidad única).
 *
 * La curva (OD-06), la evaluación, el CV de uniformidad y el IPE viven en gramos, y la
 * clave i18n lo dice («(g)»); sin embargo varios rótulos del asistente caían al fallback
 * «(kg)» y algunos inputs conservaban `step="0.001"` (de la época kg). Regla: una sola
 * unidad — gramos — en captura, etiqueta y serialización, sin conversión silenciosa.
 *
 * RED esperado en HEAD: `weight_recording` y `lot_closure` muestran «(kg)» y `step=0.001`.
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

const LOTE = { id: 7, lot_code: 'L-BO-210-01', bird_type: 'broiler', farm_id: 1, house_id: 55, status: 'active' }
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
    if (url.startsWith('/lots')) return Promise.resolve({ data: [LOTE] })
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

describe('R-210 · unidad única en gramos', () => {
  it('AC-R210-01 · weight_recording rotula en gramos (sin «(kg)»)', async () => {
    montar()
    await abrirEvento(/Engorde/, /weight_recording/)
    await waitFor(() => expect(screen.getByText(/Peso prom\. \(g\)/)).toBeTruthy())
    expect(document.body.textContent).not.toContain('(kg)')
  })

  it('AC-R210-01b · lot_closure rotula en gramos (sin «(kg)») — control', async () => {
    montar()
    await abrirEvento(/Engorde/, /lot_closure/)
    await waitFor(() => expect(screen.getByText(/Peso final prom\. \(g\)/)).toBeTruthy())
    expect(document.body.textContent).not.toContain('(kg)')
  })

  it('AC-R210-02 · los inputs de peso no llevan step 0.001 (captura en g)', async () => {
    montar()
    await abrirEvento(/Engorde/, /weight_recording/)
    const input = await waitFor(() => {
      const el = document.querySelector('[name="bird_movements.0.avg_weight"]') as HTMLInputElement | null
      expect(el).toBeTruthy()
      return el!
    })
    expect(input.getAttribute('step')).not.toBe('0.001')
    expect(input.getAttribute('step')).toBe('1')
  })

  it('AC-R210-03 · serialización sin conversión: 2150 g viaja como 2150', async () => {
    montar()
    await abrirEvento(/Engorde/, /weight_recording/)
    const loteSel = await screen.findAllByRole('button', { name: /Seleccionar lote/ })
    fireEvent.click(loteSel[0])
    fireEvent.click((await screen.findAllByRole('button', { name: /L-BO-210-01/ }))[0])
    const cantidad = document.querySelector('[name="bird_movements.0.quantity"]') as HTMLElement | null
    if (cantidad) fireEvent.change(cantidad, { target: { value: '50' } })
    const peso = document.querySelector('[name="bird_movements.0.avg_weight"]') as HTMLElement
    fireEvent.change(peso, { target: { value: '2150' } })
    await waitFor(() => expect((peso as HTMLInputElement).value).toBe('2150'))
    fireEvent.click(await screen.findByRole('button', { name: /common\.save/ }))
    await waitFor(() => expect(post).toHaveBeenCalled())
    const llamada = post.mock.calls.find((c) => c[0] === '/operations')
    const mov = llamada![1]?.bird_movements?.find((m: any) => m?.avg_weight != null)
    expect(mov?.avg_weight, `mov=${JSON.stringify(llamada![1]?.bird_movements)}`).toBe(2150)
  })
})

describe('R-210 · i18n sin kg', () => {
  it('AC-R210-04 · ninguna clave de peso contiene «kg»', () => {
    for (const idioma of ['es', 'en']) {
      const dict = JSON.parse(readFileSync(
        resolve(__dirname, `../../../../public/locales/${idioma}/translation.json`), 'utf8'))
      const ofensivas: string[] = []
      const recorrer = (nodo: any, ruta: string) => {
        if (!nodo || typeof nodo !== 'object') return
        for (const [k, v] of Object.entries(nodo)) {
          const r = ruta ? `${ruta}.${k}` : k
          if (typeof v === 'string') {
            if (/weight|peso|avg/i.test(r) && /\bkg\b|\(kg\)/i.test(v)) ofensivas.push(`${r}=${v}`)
          } else {
            recorrer(v, r)
          }
        }
      }
      recorrer(dict, '')
      expect(ofensivas, `${idioma}: ${ofensivas.join(' | ')}`).toEqual([])
    }
  })
})
