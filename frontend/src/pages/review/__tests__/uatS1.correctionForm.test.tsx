/**
 * `015` · UAT-S1 (AC-S1-C01..C04) — el formulario de corrección ofrece los campos REALES
 * del evento (columnas + submovimientos), muestra el valor original en solo lectura, elige
 * el control por tipo de valor y valida en cliente (sin `alert`).
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
  'corrections.row': 'fila {{id}}',
  'corrections.fields.bird_movements.avg_weight': 'Peso promedio',
  'corrections.sex.male': 'Macho',
  'corrections.noFields': 'Este evento no admite correcciones en su estado actual.',
  'corrections.correctedRequired': 'Indique el valor corregido.',
  'corrections.valueNumeric': 'El valor debe ser un número.',
  'corrections.reasonMin': 'El motivo debe tener al menos 5 caracteres.',
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
import { ToastProvider } from '../../../components/Toast'
import { useAuthStore } from '../../../stores/auth.store'

const EVENTO = {
  id: 55, event_type: 'daily_weights', event_date: '2026-09-10', status: 'in_review',
  lot_id: 7, farm_id: 1, house_id: 2, version: 1, observations: 'sin novedad',
  bird_movements: [], feed_movements: [], egg_movements: [], sap_document_ref: null,
}

const CAMPOS = [
  { field_name: 'observations', label_key: 'corrections.fields.observations', current_value: 'sin novedad', row_id: null, row_label: null, value_type: 'text' },
  { field_name: 'bird_movements[5].avg_weight', label_key: 'corrections.fields.bird_movements.avg_weight', current_value: '2.0', row_id: 5, row_label: 'male', value_type: 'decimal' },
]

function setSession(permissions: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 5, username: 'uatS1c', first_name: 'U', last_name: 'S', email: 'u@x.com',
      role_id: 35, view_type: 'web', is_super_admin: false, company_id: 1,
      effective_company_id: 1, permissions,
      company_business_units: [], granted_business_units: [], effective_business_units: [],
    } as any,
  })
}

const montar = (campos: any[]) => {
  get.mockImplementation((url: string) => {
    const u = String(url)
    if (u === '/operations/55') return Promise.resolve({ data: { ...EVENTO } })
    if (u === '/corrections/events/55/correctable-fields') return Promise.resolve({ data: campos })
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

const selectorCampo = () => screen.getAllByRole('combobox')[0] as HTMLSelectElement

beforeEach(() => {
  get.mockReset(); post.mockReset(); vi.clearAllMocks()
  post.mockResolvedValue({ data: {} })
  setSession(['review:read', 'corrections:correct'])
})

describe('015 · UAT-S1 · formulario de corrección con campos reales', () => {
  it('AC-S1-C01/C02/C03 · lista los campos corregibles con etiqueta traducida y tipo correcto', async () => {
    montar(CAMPOS)
    await waitFor(() => expect(selectorCampo().options.length).toBe(2))
    const etiquetas = Array.from(selectorCampo().options).map((o) => o.textContent)
    expect(etiquetas[0]).toBe('Observaciones')
    expect(etiquetas[1]).toBe('Peso promedio · fila 5 (Macho)')
    // sin nombres crudos del backend en la interfaz
    expect(etiquetas.join(' | ')).not.toContain('bird_movements[')

    // el campo por defecto es `observations`
    expect(selectorCampo().value).toBe('observations')

    fireEvent.change(selectorCampo(), { target: { value: 'bird_movements[5].avg_weight' } })

    const original = screen.getByTestId('correction-original') as HTMLInputElement
    expect(original.value).toBe('2.0')
    expect(original.readOnly).toBe(true)
    const corregido = screen.getByTestId('correction-corrected') as HTMLInputElement
    expect(corregido.getAttribute('type')).toBe('number')
    expect(corregido.value).toBe('')
  })

  it('AC-S1-C04 · motivo de 3 caracteres: no envía, muestra error inline y no usa alert()', async () => {
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})
    montar(CAMPOS)
    await waitFor(() => expect(selectorCampo().options.length).toBe(2))
    fireEvent.change(selectorCampo(), { target: { value: 'bird_movements[5].avg_weight' } })
    fireEvent.change(screen.getByTestId('correction-corrected'), { target: { value: '2.5' } })
    fireEvent.change(screen.getByPlaceholderText(/Explica por qué/), { target: { value: 'abc' } })
    fireEvent.click(screen.getByRole('button', { name: /Guardar Corrección/ }))

    await waitFor(() => expect(screen.getByTestId('correction-error')).toBeTruthy())
    expect(screen.getByTestId('correction-error').textContent).toBe('El motivo debe tener al menos 5 caracteres.')
    expect(post).not.toHaveBeenCalled()
    expect(alertSpy).not.toHaveBeenCalled()
    alertSpy.mockRestore()
  })

  it('AC-S1-C02/C03 · el POST lleva el field_name del submovimiento tal cual y el valor corregido', async () => {
    montar(CAMPOS)
    await waitFor(() => expect(selectorCampo().options.length).toBe(2))
    fireEvent.change(selectorCampo(), { target: { value: 'bird_movements[5].avg_weight' } })
    fireEvent.change(screen.getByTestId('correction-corrected'), { target: { value: '2.5' } })
    fireEvent.change(screen.getByPlaceholderText(/Explica por qué/), { target: { value: 'pesaje mal digitado' } })
    fireEvent.click(screen.getByRole('button', { name: /Guardar Corrección/ }))

    await waitFor(() => expect(post).toHaveBeenCalledTimes(1))
    expect(post).toHaveBeenCalledWith('/corrections', expect.objectContaining({
      event_id: 55,
      field_name: 'bird_movements[5].avg_weight',
      original_value: '2.0',
      corrected_value: '2.5',
      reason: 'pesaje mal digitado',
    }))
  })

  it('AC-S1-C01 · sin campos corregibles muestra `corrections.noFields` y ningún formulario', async () => {
    montar([])
    await waitFor(() => expect(screen.getByText(/no admite correcciones/)).toBeTruthy())
    expect(screen.queryAllByRole('combobox').length).toBe(0)
    expect(screen.queryByRole('button', { name: /Guardar Corrección/ })).toBeNull()
  })
})
