/**
 * SPEC `020` §7 · O-23 — un valor de maestro vacío (`null`) se lee «Sin valor» (nunca `null`,
 * `undefined` ni un hueco), el selector de corrección solo ofrece registros ACTIVOS del catálogo
 * y con etiqueta funcional (`código — nombre`, nunca el `id` solo), y el historial de correcciones
 * usa la misma regla: «Sin valor» donde no había dato y el nombre donde lo hay.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

const get = vi.fn()
const post = vi.fn()
vi.mock('../../../services/api', () => ({
  default: {
    get: (...a: any[]) => get(...a), post: (...a: any[]) => post(...a),
    put: vi.fn(), delete: vi.fn(),
  },
}))

// Traducciones mínimas: `t` devuelve el texto es y la clave si no está en el diccionario.
const DICC: Record<string, string> = {
  'corrections.fields.observations': 'Observaciones',
  'corrections.fields.supplier_id': 'Proveedor',
  'corrections.fields.sample_size': 'Tamaño de muestra',
  'corrections.fields.bird_movements.avg_weight': 'Peso promedio',
  'corrections.row': 'fila {{id}}',
  'corrections.sex.male': 'Macho',
  'corrections.noFields': 'Este evento no admite correcciones en su estado actual.',
  'corrections.correctedRequired': 'Indique el valor corregido.',
  'corrections.valueNumeric': 'El valor debe ser un número.',
  'corrections.reasonMin': 'El motivo debe tener al menos 5 caracteres.',
  'corrections.typeRequired': 'Seleccione el tipo de corrección',
  // `020` · §7 `AC-O23-07`: valor ausente.
  'corrections.noValue': 'Sin valor',
  'common.select': 'Seleccione',
  'review.saveCorrection': 'Guardar Corrección',
  'review.reasonPlaceholder': 'Explica por qué se corrige este valor...',
}
const t = (k: string, o?: any) => String(DICC[k] ?? k).replace(/\{\{(\w+)\}\}/g, (_m, p) => String(o?.[p] ?? ''))
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t, i18n: { language: 'es', resolvedLanguage: 'es' } }),
}))

const toastError = vi.fn()
const toastSuccess = vi.fn()
vi.mock('../../../components/Toast', async (importOriginal) => {
  const actual = await importOriginal<any>()
  return { ...actual, useToast: () => ({ success: toastSuccess, error: toastError, warning: vi.fn(), info: vi.fn() }) }
})

import CorrectionForm from '../CorrectionForm'
import ReviewDetail from '../ReviewDetail'
import { ToastProvider } from '../../../components/Toast'
import { useAuthStore } from '../../../stores/auth.store'

const EVENTO = {
  id: 55, event_type: 'daily_weights', event_date: '2026-09-10', status: 'in_review',
  lot_id: 7, farm_id: 1, house_id: 2, version: 1, observations: 'sin novedad',
  bird_movements: [], feed_movements: [], egg_movements: [], sap_document_ref: null,
}

// `020` · §7 `AC-O23-07`: un maestro SIN valor asignado (`current_value`/`current_display` nulos).
const CAMPO_MAESTRO_NULO = {
  field_name: 'supplier_id', label_key: 'corrections.fields.supplier_id',
  current_value: null, row_id: null, row_label: null, value_type: 'integer',
  master: 'suppliers', current_display: null,
}
const CATALOGO_PROVEEDORES = [
  { id: 7, name: 'Proveedor ABC', sap_code: 'PROV-001', is_active: true },
  { id: 9, name: 'Proveedor Sin Código', sap_code: null, is_active: true },
  { id: 11, name: 'Proveedor Retirado', sap_code: 'PROV-011', is_active: false },
]

function setSession(permissions: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 5, username: 'uatS2o23', first_name: 'U', last_name: 'S', email: 'u@x.com',
      role_id: 35, view_type: 'web', is_super_admin: false, company_id: 1,
      effective_company_id: 1, permissions,
      company_business_units: [], granted_business_units: [], effective_business_units: [],
    } as any,
  })
}

const montarForm = (campos: any[], catalogo: any[] = CATALOGO_PROVEEDORES) => {
  get.mockImplementation((url: string) => {
    const u = String(url)
    if (u === '/operations/55') return Promise.resolve({ data: { ...EVENTO } })
    if (u === '/corrections/events/55/correctable-fields') return Promise.resolve({ data: campos })
    if (u === '/masters/suppliers?limit=100') return Promise.resolve({ data: catalogo })
    if (u.startsWith('/masters/correction-types')) return Promise.resolve({ data: [{ id: 1, name: 'Error de digitación' }] })
    return Promise.resolve({ data: [] })
  })
  return render(
    <MemoryRouter initialEntries={['/review/55/correct']}>
      <Routes>
        <Route path="/review/:id/correct" element={<ToastProvider><CorrectionForm /></ToastProvider>} />
        <Route path="/review/:id" element={<div>detalle</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

const selectorMaestro = () => screen.getByTestId('correction-corrected-master') as HTMLSelectElement
const textoOriginal = () => (screen.getByTestId('correction-original') as HTMLInputElement).value

beforeEach(() => {
  get.mockReset(); post.mockReset(); vi.clearAllMocks()
  post.mockResolvedValue({ data: {} })
  setSession(['review:read', 'corrections:correct'])
})

describe('O-23 · spec 020 §7', () => {
  it('F01 · el valor original de un maestro vacío se lee «Sin valor»', async () => {
    montarForm([CAMPO_MAESTRO_NULO])
    await waitFor(() => expect(textoOriginal()).toBe('Sin valor'))

    const texto = textoOriginal()
    expect(texto).not.toContain('null')
    expect(texto).not.toContain('undefined')
    expect(texto).not.toContain('0')
  })

  it('F02 · un maestro vacío sigue siendo corregible con selector, no con texto libre', async () => {
    montarForm([CAMPO_MAESTRO_NULO])
    await waitFor(() => expect(selectorMaestro()).toBeTruthy())
    expect(screen.queryByTestId('correction-corrected')).toBeNull()
  })

  it('F03 · el selector solo ofrece los registros activos del catálogo', async () => {
    montarForm([CAMPO_MAESTRO_NULO])
    await waitFor(() => expect(selectorMaestro().options.length).toBe(3))

    const opciones = Array.from(selectorMaestro().options)
    // opción vacía + los dos registros activos (el `is_active: false` queda fuera)
    expect(opciones[0].value).toBe('')
    expect(opciones[0].textContent).toContain('--')
    expect(opciones.map((o) => o.value)).toEqual(['', '7', '9'])
    expect(opciones.map((o) => o.textContent)).not.toContain('Proveedor Retirado')
  })

  it('F04 · la etiqueta funcional del proveedor es «código — nombre»', async () => {
    montarForm([CAMPO_MAESTRO_NULO])
    await waitFor(() => expect(selectorMaestro().options.length).toBe(3))

    const opciones = Array.from(selectorMaestro().options)
    expect(opciones[1].textContent).toBe('PROV-001 — Proveedor ABC')
  })

  it('F05 · sin código se ofrece el nombre y ninguna opción es solo el id', async () => {
    montarForm([CAMPO_MAESTRO_NULO])
    await waitFor(() => expect(selectorMaestro().options.length).toBe(3))

    const opciones = Array.from(selectorMaestro().options)
    expect(opciones[2].textContent).toBe('Proveedor Sin Código')
    expect(opciones.map((o) => String(o.textContent))).not.toContain('7')
    expect(opciones.map((o) => String(o.textContent))).not.toContain('9')
  })

  it('F06 · guardar envía el id del proveedor elegido y refresca el detalle', async () => {
    montarForm([CAMPO_MAESTRO_NULO])
    await waitFor(() => expect(selectorMaestro().options.length).toBe(3))

    fireEvent.change(selectorMaestro(), { target: { value: '7' } })
    fireEvent.change(screen.getByTestId('correction-type'), { target: { value: '1' } })
    fireEvent.change(screen.getByPlaceholderText(/Explica por qué/), { target: { value: 'proveedor mal seleccionado' } })
    fireEvent.click(screen.getByRole('button', { name: /Guardar Corrección/ }))

    await waitFor(() => expect(post).toHaveBeenCalledTimes(1))
    expect(post).toHaveBeenCalledWith('/corrections', expect.objectContaining({
      event_id: 55,
      field_name: 'supplier_id',
      corrected_value: '7',
      correction_type_id: 1,
      reason: 'proveedor mal seleccionado',
    }))
    // navega a `/review/55` (se vuelve a cargar el detalle del evento)
    await waitFor(() => expect(screen.getByText('detalle')).toBeTruthy())
  })

  it('F07 · el historial de un maestro vacío dice «Sin valor» y muestra el nombre corregido', async () => {
    const HISTORIAL = [
      {
        id: 8, event_id: 55, field_name: 'supplier_id',
        original_value: null, original_display: null,
        corrected_value: '7', corrected_display: 'Proveedor ABC',
        reason: 'proveedor mal seleccionado', created_at: '2026-09-10T09:00:00Z',
        corrected_by_name: 'María Ruiz',
      },
    ]
    get.mockImplementation((url: string) => {
      const u = String(url)
      if (u === '/operations/55') return Promise.resolve({ data: { ...EVENTO } })
      if (u === '/corrections/event/55') return Promise.resolve({ data: HISTORIAL })
      return Promise.resolve({ data: [] })
    })
    render(
      <MemoryRouter initialEntries={['/review/55']}>
        <Routes>
          <Route path="/review/:id" element={<ToastProvider><ReviewDetail /></ToastProvider>} />
        </Routes>
      </MemoryRouter>,
    )

    await waitFor(() => expect(screen.getByTestId('correction-no-value')).toBeTruthy())
    expect(screen.getByTestId('correction-no-value').textContent).toBe('Sin valor')

    const linea = screen.getByTestId('correction-no-value').closest('p') as HTMLParagraphElement
    const texto = linea.textContent || ''
    expect(texto).toContain('Sin valor')
    expect(texto).toContain('"Proveedor ABC"')
    expect(texto).not.toContain('null')
    expect(texto).not.toContain('"7"')
  })
})
