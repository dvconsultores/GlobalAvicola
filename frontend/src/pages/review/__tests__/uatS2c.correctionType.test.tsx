/**
 * SPEC `020` §6 · `RR-27` — el formulario de corrección exige el TIPO de corrección antes de
 * enviar: sin tipo no hay POST a `/corrections` y se avisa inline (`corrections.typeRequired`);
 * con tipo elegido el payload lleva `correction_type_id` numérico.
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
  'corrections.noFields': 'Este evento no admite correcciones en su estado actual.',
  'corrections.correctedRequired': 'Indique el valor corregido.',
  'corrections.valueNumeric': 'El valor debe ser un número.',
  'corrections.reasonMin': 'El motivo debe tener al menos 5 caracteres.',
  'corrections.typeRequired': 'Seleccione el tipo de corrección',
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
import { ToastProvider } from '../../../components/Toast'
import { useAuthStore } from '../../../stores/auth.store'

const EVENTO = {
  id: 55, event_type: 'daily_weights', event_date: '2026-09-10', status: 'in_review',
  lot_id: 7, farm_id: 1, house_id: 2, version: 1, observations: 'sin novedad',
  bird_movements: [], feed_movements: [], egg_movements: [], sap_document_ref: null,
}

const CAMPO_TEXTO = {
  field_name: 'observations', label_key: 'corrections.fields.observations',
  current_value: 'sin novedad', row_id: null, row_label: null, value_type: 'text',
  master: null, current_display: null,
}

function setSession(permissions: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 5, username: 'uatS2cType', first_name: 'U', last_name: 'S', email: 'u@x.com',
      role_id: 35, view_type: 'web', is_super_admin: false, company_id: 1,
      effective_company_id: 1, permissions,
      company_business_units: [], granted_business_units: [], effective_business_units: [],
    } as any,
  })
}

const TIPOS_POR_DEFECTO = [{ id: 1, name: 'Error de digitación' }, { id: 2, name: 'Dato incompleto' }]
const montarForm = (campos: any[], tipos: any[] = TIPOS_POR_DEFECTO) => {
  get.mockImplementation((url: string) => {
    const u = String(url)
    if (u === '/operations/55') return Promise.resolve({ data: { ...EVENTO } })
    if (u === '/corrections/events/55/correctable-fields') return Promise.resolve({ data: campos })
    if (u.startsWith('/masters/correction-types')) {
      return Promise.resolve({ data: tipos })
    }
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

const selectorTipo = () => screen.getByTestId('correction-type') as HTMLSelectElement

beforeEach(() => {
  get.mockReset(); post.mockReset(); vi.clearAllMocks()
  post.mockResolvedValue({ data: {} })
  setSession(['review:read', 'corrections:correct'])
})

describe('SPEC 020 §6 · RR-27 · tipo de corrección obligatorio', () => {
  it('a · sin tipo de corrección el envío se bloquea: no hay POST y se ve el aviso', async () => {
    montarForm([CAMPO_TEXTO])
    await waitFor(() => expect(selectorTipo().options.length).toBe(3))

    fireEvent.change(screen.getByTestId('correction-corrected'), { target: { value: 'con novedad' } })
    fireEvent.change(screen.getByPlaceholderText(/Explica por qué/), { target: { value: 'observación mal digitada' } })
    fireEvent.click(screen.getByRole('button', { name: /Guardar Corrección/ }))

    await waitFor(() => expect(screen.getByTestId('correction-error')).toBeTruthy())
    expect(screen.getByTestId('correction-error').textContent).toBe('Seleccione el tipo de corrección')
    expect(screen.queryAllByTestId('correction-error').length).toBe(1)
    expect(post).not.toHaveBeenCalled()
  })

  it('b · con tipo elegido se envía correction_type_id numérico', async () => {
    montarForm([CAMPO_TEXTO])
    await waitFor(() => expect(selectorTipo().options.length).toBe(3))

    fireEvent.change(screen.getByTestId('correction-corrected'), { target: { value: 'con novedad' } })
    fireEvent.change(selectorTipo(), { target: { value: '2' } })
    fireEvent.change(screen.getByPlaceholderText(/Explica por qué/), { target: { value: 'observación mal digitada' } })
    fireEvent.click(screen.getByRole('button', { name: /Guardar Corrección/ }))

    await waitFor(() => expect(post).toHaveBeenCalledTimes(1))
    expect(post).toHaveBeenCalledWith('/corrections', expect.objectContaining({
      event_id: 55,
      field_name: 'observations',
      corrected_value: 'con novedad',
      reason: 'observación mal digitada',
      correction_type_id: 2,
    }))
    const enviado = (post.mock.calls[0][1] as any).correction_type_id
    expect(typeof enviado).toBe('number')
  })

  it('c · un tipo de corrección inactivo no se ofrece (el servidor lo rechazaría)', async () => {
    montarForm([CAMPO_TEXTO], [
      { id: 1, name: 'Tipo retirado', is_active: false },
      { id: 2, name: 'Dato incompleto', is_active: true },
    ])
    await waitFor(() => expect(selectorTipo().options.length).toBe(2))
    const nombres = Array.from(selectorTipo().options).map(o => o.textContent)
    expect(nombres).not.toContain('Tipo retirado')
    expect(nombres).toContain('Dato incompleto')
  })
})
