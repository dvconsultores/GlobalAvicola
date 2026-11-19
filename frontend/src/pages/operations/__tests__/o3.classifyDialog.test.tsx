/**
 * `SPEC 016 §A` · `O-3` — clasificar un pendiente desde la bandeja.
 *
 * Contrato del backend:
 *   `GET /operations/{id}/classification-candidates` ⇒ `[{code, name_key}]` (403 sin
 *   `masters:update`, 404 si ya no está pendiente).
 *   `POST /operations/{id}/classify` `{business_unit_code, reason}` ⇒ 200; 400 con `detail`
 *   en español si la unidad no vale; 404 si ya no está pendiente; 422 si el motivo no vale.
 *
 * Lo que se fija aquí: ver NO es clasificar (sin `masters:update` no hay acción), la unidad se
 * ofrece por CÓDIGO + descripción (nunca ids), el motivo se valida en cliente antes de enviar
 * y ningún error del servidor se pinta como JSON crudo ni con el número de estado.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, within, fireEvent } from '@testing-library/react'
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
// `t` como el resto de la página: valor por defecto en el segundo parámetro + interpolación.
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (k: string, a?: any, b?: any) => {
      const fallback = typeof a === 'string' ? a : undefined
      const opciones = a && typeof a === 'object' ? a : (b && typeof b === 'object' ? b : undefined)
      let salida = fallback ?? k
      if (opciones) {
        for (const [nombre, valor] of Object.entries(opciones)) {
          salida = salida.split(`{{${nombre}}}`).join(String(valor))
        }
      }
      return salida
    },
    i18n: { language: 'es' },
  }),
}))
const toastSuccess = vi.fn()
const toastError = vi.fn()
vi.mock('../../../components/Toast', () => ({
  useToast: () => ({ success: toastSuccess, error: toastError, warning: vi.fn(), info: vi.fn() }),
  getErrorMessage: (_e: any, f: string) => f,
}))

import PendingClassificationPage from '../PendingClassificationPage'
import { useAuthStore } from '../../../stores/auth.store'

function setSession(permissions: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 11, username: 'o3', first_name: 'O', last_name: '3', email: 'o3@x.com',
      role_id: 35, view_type: 'web', is_super_admin: false, company_id: 1,
      effective_company_id: 1, permissions,
      company_business_units: [], granted_business_units: [], effective_business_units: [],
    } as any,
  })
}

const PENDIENTES = [
  {
    id: 901, event_type: 'farm_inspection', event_date: '2026-09-10', status: 'registered',
    farm_id: 4, house_id: 7, farm_name: 'Granja SIN', house_name: 'Galpón SIN',
    registered_by_name: 'Ana Autora',
  },
  {
    id: 902, event_type: 'farm_inspection', event_date: '2026-09-09', status: 'registered',
    farm_id: 5, house_id: 8, farm_name: 'Granja MULTI', house_name: 'Galpón MULTI',
    registered_by_name: 'Ana Autora',
  },
]

const CANDIDATOS = [
  { code: 'breeder', name_key: 'businessUnits.breeder' },
  { code: 'hatchery', name_key: 'businessUnits.hatchery' },
]

/** `api.get` con la lista por tandas (para probar el recargado) y los candidatos fijos. */
function mockGet(listas: any[][], candidatos: any[] = CANDIDATOS) {
  let llamadasLista = 0
  get.mockImplementation((url: string) => {
    const u = String(url)
    if (u.endsWith('/classification-candidates')) return Promise.resolve({ data: candidatos })
    if (u === '/operations/pending-classification') {
      const data = listas[Math.min(llamadasLista, listas.length - 1)]
      llamadasLista += 1
      return Promise.resolve({ data })
    }
    return Promise.resolve({ data: [] })
  })
}

const llamadasLista = () =>
  get.mock.calls.filter((c) => String(c[0]) === '/operations/pending-classification').length
const llamadaCandidatos = () =>
  get.mock.calls.find((c) => String(c[0]).includes('/classification-candidates'))

const renderPage = () =>
  render(<MemoryRouter><PendingClassificationPage /></MemoryRouter>)

const abrirDialogo = async () => {
  await waitFor(() => expect(screen.getAllByTestId('classify-btn').length).toBeGreaterThan(0))
  fireEvent.click(screen.getAllByTestId('classify-btn')[0])
  return screen.findByTestId('classify-dialog')
}

const elegirUnidad = async (code: string) => {
  const select = await screen.findByTestId('classify-unit') as HTMLSelectElement
  fireEvent.change(select, { target: { value: code } })
  return select
}

beforeEach(() => {
  get.mockReset()
  post.mockReset()
  toastSuccess.mockReset()
  toastError.mockReset()
  try { sessionStorage.clear() } catch { /* noop */ }
  setSession(['operations:read'])
})

describe('SPEC 016 §A · O-3 · clasificar un pendiente', () => {
  it('sin `masters:update` no hay acción de clasificar (ver ≠ clasificar)', async () => {
    setSession(['operations:read'])
    mockGet([PENDIENTES])
    renderPage()

    await waitFor(() => expect(screen.getAllByTestId('pending-row')).toHaveLength(2))
    expect(screen.queryAllByTestId('classify-btn')).toHaveLength(0)
    expect(screen.queryByTestId('classify-dialog')).toBeNull()
  })

  it('con `masters:update` cada fila ofrece «Clasificar»', async () => {
    setSession(['operations:read', 'masters:update'])
    mockGet([PENDIENTES])
    renderPage()

    await waitFor(() => expect(screen.getAllByTestId('pending-row')).toHaveLength(2))
    expect(screen.getAllByTestId('classify-btn')).toHaveLength(2)
  })

  it('abrir el diálogo muestra el contexto del registro y pide los candidatos', async () => {
    setSession(['operations:read', 'masters:update'])
    mockGet([PENDIENTES])
    renderPage()

    const dialogo = await abrirDialogo()
    const dentro = within(dialogo)
    expect(dentro.getByText('Granja SIN')).toBeTruthy()
    expect(dentro.getByText('Galpón SIN')).toBeTruthy()
    expect(dentro.getByText('Ana Autora')).toBeTruthy()

    await waitFor(() => expect(llamadaCandidatos()).toBeTruthy())
    expect(String(llamadaCandidatos()![0])).toBe('/operations/901/classification-candidates')
  })

  it('el selector ofrece «código — descripción» y ningún id numérico', async () => {
    setSession(['operations:read', 'masters:update'])
    mockGet([PENDIENTES])
    renderPage()
    await abrirDialogo()

    const select = await screen.findByTestId('classify-unit') as HTMLSelectElement
    const opciones = Array.from(select.options)
    expect(opciones[0].value).toBe('')
    expect(opciones[0].textContent).toBe('Seleccione una unidad')
    expect(opciones.map(o => o.textContent)).toContain('breeder — Reproductoras')
    expect(opciones.map(o => o.textContent)).toContain('hatchery — Incubadora')
    expect(opciones.map(o => o.value)).toEqual(['', 'breeder', 'hatchery'])
    for (const o of opciones) {
      expect(o.value, 'el valor de la opción nunca es un id').not.toMatch(/^\d+$/)
      expect(String(o.textContent), 'la etiqueta no lleva ids').not.toMatch(/#\d+/)
    }
  })

  it('«Clasificar» está deshabilitado con motivo vacío, de 2 caracteres o solo espacios', async () => {
    setSession(['operations:read', 'masters:update'])
    mockGet([PENDIENTES])
    renderPage()
    await abrirDialogo()
    await elegirUnidad('hatchery')

    const submit = () => screen.getByTestId('classify-submit') as HTMLButtonElement
    expect(submit().disabled).toBe(true)

    const motivo = screen.getByTestId('classify-reason') as HTMLTextAreaElement
    fireEvent.change(motivo, { target: { value: 'ok' } })
    expect(submit().disabled).toBe(true)
    expect(screen.getAllByText('El motivo debe tener al menos 3 caracteres').length).toBeGreaterThan(0)

    fireEvent.change(motivo, { target: { value: '   ' } })
    expect(submit().disabled).toBe(true)

    fireEvent.change(motivo, { target: { value: '  tres o más  ' } })
    expect(submit().disabled).toBe(false)
    expect(post).not.toHaveBeenCalled()
  })

  it('envía el cuerpo EXACTO a `/classify` y recarga la lista', async () => {
    setSession(['operations:read', 'masters:update'])
    mockGet([PENDIENTES, [PENDIENTES[1]]])
    post.mockResolvedValue({ data: {} })
    renderPage()
    await abrirDialogo()
    await elegirUnidad('hatchery')

    fireEvent.change(screen.getByTestId('classify-reason'), {
      target: { value: '  Inspección de granja multi-cadena  ' },
    })
    fireEvent.click(screen.getByTestId('classify-submit'))

    await waitFor(() => expect(post).toHaveBeenCalledTimes(1))
    expect(post.mock.calls[0][0]).toBe('/operations/901/classify')
    expect(post.mock.calls[0][1]).toEqual({
      business_unit_code: 'hatchery',
      reason: 'Inspección de granja multi-cadena',
    })

    await waitFor(() => expect(llamadasLista()).toBe(2))
    await waitFor(() => expect(screen.getAllByTestId('pending-row')).toHaveLength(1))
    expect(screen.queryByTestId('classify-dialog')).toBeNull()
    expect(toastSuccess).toHaveBeenCalledTimes(1)
    expect(String(toastSuccess.mock.calls[0][0])).toBe('Registro clasificado en Incubadora')
  })

  it('404 ⇒ «El registro ya no está pendiente de clasificar» y recarga la lista', async () => {
    setSession(['operations:read', 'masters:update'])
    mockGet([PENDIENTES, [PENDIENTES[1]]])
    post.mockRejectedValue({ response: { status: 404, data: { detail: 'Registro pendiente no encontrado' } } })
    renderPage()
    await abrirDialogo()
    await elegirUnidad('hatchery')
    fireEvent.change(screen.getByTestId('classify-reason'), { target: { value: 'cadena incubadora' } })
    fireEvent.click(screen.getByTestId('classify-submit'))

    await waitFor(() => expect(
      screen.getByText('El registro ya no está pendiente de clasificar')).toBeTruthy())
    await waitFor(() => expect(llamadasLista()).toBe(2))
    expect(screen.queryByText(/Request failed/)).toBeNull()
    expect(screen.queryByText(/422/)).toBeNull()
  })

  it('400 ⇒ muestra el `detail` del servidor (en español)', async () => {
    setSession(['operations:read', 'masters:update'])
    mockGet([PENDIENTES])
    post.mockRejectedValue({
      response: {
        status: 400,
        data: { detail: 'la unidad no existe o no esta habilitada para la empresa' },
      },
    })
    renderPage()
    await abrirDialogo()
    await elegirUnidad('breeder')
    fireEvent.change(screen.getByTestId('classify-reason'), { target: { value: 'cadena reproductoras' } })
    fireEvent.click(screen.getByTestId('classify-submit'))

    await waitFor(() => expect(screen.getByTestId('classify-error')).toBeTruthy())
    expect(screen.getByTestId('classify-error').textContent)
      .toBe('la unidad no existe o no esta habilitada para la empresa')
    expect(screen.queryByText(/Request failed/)).toBeNull()
  })

  it('422 ⇒ mensaje propio en español, sin JSON crudo ni el número de estado', async () => {
    setSession(['operations:read', 'masters:update'])
    mockGet([PENDIENTES])
    post.mockRejectedValue({
      response: {
        status: 422,
        data: {
          detail: [{
            loc: ['body', 'reason'], msg: 'String should have at least 3 characters',
            type: 'string_too_short',
          }],
        },
      },
    })
    renderPage()
    await abrirDialogo()
    await elegirUnidad('hatchery')
    fireEvent.change(screen.getByTestId('classify-reason'), { target: { value: 'motivo válido' } })
    fireEvent.click(screen.getByTestId('classify-submit'))

    await waitFor(() => expect(screen.getByTestId('classify-error')).toBeTruthy())
    expect(screen.getByTestId('classify-error').textContent).toBe('No se pudo clasificar el registro')
    const texto = document.body.textContent ?? ''
    expect(texto).not.toMatch(/Request failed/)
    expect(texto).not.toMatch(/string_too_short/)
    expect(texto).not.toMatch(/422/)
  })

  it('«Cancelar» cierra el diálogo sin enviar nada', async () => {
    setSession(['operations:read', 'masters:update'])
    mockGet([PENDIENTES])
    renderPage()
    await abrirDialogo()
    await elegirUnidad('hatchery')
    fireEvent.change(screen.getByTestId('classify-reason'), { target: { value: 'motivo suficiente' } })

    fireEvent.click(screen.getByRole('button', { name: 'Cancelar' }))

    await waitFor(() => expect(screen.queryByTestId('classify-dialog')).toBeNull())
    expect(post).not.toHaveBeenCalled()
  })
})
