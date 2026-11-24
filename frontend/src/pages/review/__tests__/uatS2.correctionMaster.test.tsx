/**
 * SPEC `020` · UAT-S2 (AC-S2-C04/C05 parcial, AC-S2-C07) — el formulario de corrección de un
 * campo de maestro pide el catálogo real, ofrece un selector controlado (el valor corregido es
 * el `id` del registro, nunca texto libre) y muestra el NOMBRE del valor original en lugar del
 * `id`. El historial de correcciones muestra los nombres (`original_display`/`corrected_display`)
 * cuando el backend los entrega.
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

// Campo de maestro: `current_value` es el `id` y `current_display` el nombre del registro.
const CAMPO_MAESTRO = {
  field_name: 'supplier_id', label_key: 'corrections.fields.supplier_id',
  current_value: '27', row_id: null, row_label: null, value_type: 'integer',
  master: 'suppliers', current_display: 'Avícola Norte',
}
const CAMPO_TEXTO = {
  field_name: 'sample_size', label_key: 'corrections.fields.sample_size',
  current_value: '5', row_id: null, row_label: null, value_type: 'integer',
  master: null, current_display: null,
}
const CATALOGO_PROVEEDORES = [
  { id: 27, name: 'Avícola Norte' },
  { id: 31, name: 'Avícola Sur' },
]

function setSession(permissions: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 5, username: 'uatS2c', first_name: 'U', last_name: 'S', email: 'u@x.com',
      role_id: 35, view_type: 'web', is_super_admin: false, company_id: 1,
      effective_company_id: 1, permissions,
      company_business_units: [], granted_business_units: [], effective_business_units: [],
    } as any,
  })
}

const montarForm = (campos: any[]) => {
  get.mockImplementation((url: string) => {
    const u = String(url)
    if (u === '/operations/55') return Promise.resolve({ data: { ...EVENTO } })
    if (u === '/corrections/events/55/correctable-fields') return Promise.resolve({ data: campos })
    if (u === '/masters/suppliers?limit=100') return Promise.resolve({ data: CATALOGO_PROVEEDORES })
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

/** Rutas de catálogo de maestro pedidas por el formulario. */
const pedidosCatalogo = () => get.mock.calls
  .map((c) => String(c[0]))
  .filter((u) => /^\/masters\/(?!correction-types)/.test(u))

const selectorCampo = () => screen.getAllByRole('combobox')[0] as HTMLSelectElement
const selectorMaestro = () => screen.getByTestId('correction-corrected-master') as HTMLSelectElement

beforeEach(() => {
  get.mockReset(); post.mockReset(); vi.clearAllMocks()
  post.mockResolvedValue({ data: {} })
  setSession(['review:read', 'corrections:correct'])
})

describe('SPEC 020 · UAT-S2 · corrección de campos de maestro con selector controlado', () => {
  it('C04 · el valor original de un maestro muestra el NOMBRE, no el id', async () => {
    montarForm([CAMPO_MAESTRO])
    await waitFor(() => expect(selectorCampo().options.length).toBe(1))

    const original = screen.getByTestId('correction-original') as HTMLInputElement
    expect(original.value).toBe('Avícola Norte')
    expect(original.value).not.toBe('27')
  })

  it('C04 · pide el catálogo del maestro y ofrece un select sin el registro actual', async () => {
    montarForm([CAMPO_MAESTRO])
    await waitFor(() => expect(pedidosCatalogo()).toEqual(['/masters/suppliers?limit=100']))

    await waitFor(() => expect(selectorMaestro().options.length).toBe(2))
    const opciones = Array.from(selectorMaestro().options)
    // primera opción vacía + una por registro del catálogo, excluyendo el valor actual (`27`)
    expect(opciones[0].value).toBe('')
    expect(opciones[0].textContent).toContain('Seleccione')
    expect(opciones.map((o) => o.value)).toEqual(['', '31'])
    expect(opciones[1].textContent).toBe('Avícola Sur')
    // en un campo de maestro no se ofrece el input de texto libre
    expect(screen.queryByTestId('correction-corrected')).toBeNull()
  })

  it('C04 · guardar envía el id del registro elegido como string', async () => {
    montarForm([CAMPO_MAESTRO])
    await waitFor(() => expect(selectorMaestro().options.length).toBe(2))
    fireEvent.change(selectorMaestro(), { target: { value: '31' } })
    fireEvent.change(screen.getByPlaceholderText(/Explica por qué/), { target: { value: 'proveedor mal seleccionado' } })
    fireEvent.click(screen.getByRole('button', { name: /Guardar Corrección/ }))

    await waitFor(() => expect(post).toHaveBeenCalledTimes(1))
    expect(post).toHaveBeenCalledWith('/corrections', expect.objectContaining({
      event_id: 55,
      field_name: 'supplier_id',
      corrected_value: '31',
      reason: 'proveedor mal seleccionado',
    }))
    const enviado = (post.mock.calls[0][1] as any).corrected_value
    expect(typeof enviado).toBe('string')
  })

  it('C07 · un campo que no es de maestro conserva el input y no pide catálogo', async () => {
    montarForm([CAMPO_TEXTO])
    await waitFor(() => expect(selectorCampo().options.length).toBe(1))

    const corregido = screen.getByTestId('correction-corrected') as HTMLInputElement
    expect(corregido.getAttribute('type')).toBe('number')
    expect(screen.queryByTestId('correction-corrected-master')).toBeNull()
    expect(pedidosCatalogo()).toEqual([])
  })

  it('C04 · sin selección en un campo de maestro no envía y avisa con un único mensaje', async () => {
    montarForm([CAMPO_MAESTRO])
    await waitFor(() => expect(selectorMaestro().options.length).toBe(2))
    fireEvent.change(screen.getByPlaceholderText(/Explica por qué/), { target: { value: 'proveedor mal seleccionado' } })
    fireEvent.click(screen.getByRole('button', { name: /Guardar Corrección/ }))

    await waitFor(() => expect(screen.getByTestId('correction-error')).toBeTruthy())
    expect(screen.getByTestId('correction-error').textContent).toBe('Indique el valor corregido.')
    expect(screen.queryAllByTestId('correction-error').length).toBe(1)
    expect(post).not.toHaveBeenCalled()
  })
})

describe('SPEC 020 · UAT-S2 · CORR-S2-HIST: el historial muestra nombres, no ids', () => {
  const HISTORIAL = [
    {
      id: 3, event_id: 55, field_name: 'supplier_id',
      original_value: '27', corrected_value: '31',
      original_display: 'Avícola Norte', corrected_display: 'Avícola Sur',
      reason: 'proveedor mal seleccionado', created_at: '2026-09-10T09:00:00Z',
      corrected_by_name: 'María Ruiz',
    },
    {
      id: 4, event_id: 55, field_name: 'bird_movements[5].avg_weight',
      original_value: '2.0', corrected_value: '2.5',
      original_display: null, corrected_display: null,
      reason: 'pesaje mal digitado', created_at: '2026-09-10T10:00:00Z',
      corrected_by_name: 'María Ruiz',
    },
  ]

  const montarDetalle = () => {
    get.mockImplementation((url: string) => {
      const u = String(url)
      if (u === '/operations/55') return Promise.resolve({ data: { ...EVENTO } })
      if (u === '/corrections/event/55') return Promise.resolve({ data: HISTORIAL })
      return Promise.resolve({ data: [] })
    })
    return render(
      <MemoryRouter initialEntries={['/review/55']}>
        <Routes>
          <Route path="/review/:id" element={<ToastProvider><ReviewDetail /></ToastProvider>} />
        </Routes>
      </MemoryRouter>,
    )
  }

  it('C05 · campo de maestro: original_display → corrected_display', async () => {
    montarDetalle()
    await waitFor(() => expect(document.body.textContent).toContain('Avícola Norte'))
    const texto = document.body.textContent || ''
    expect(texto).toContain('"Avícola Norte" → "Avícola Sur"')
    expect(texto).toContain('Proveedor')
  })

  it('C05 · campo que no es de maestro: original_value → corrected_value', async () => {
    montarDetalle()
    await waitFor(() => expect(document.body.textContent).toContain('Peso promedio'))
    const texto = document.body.textContent || ''
    expect(texto).toContain('"2.0" → "2.5"')
  })
})
