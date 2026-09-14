/**
 * R-195 · RED jsdom — edición de usuario con el subconjunto permitido y errores
 * legibles.
 *
 * Diseño: `specs/R-195/R-195_RED_E2E_UAT_DESIGN.md §1.1` (AC-01/02/03/05/06).
 *
 * Rojos en HEAD (causas previstas):
 *   AC-01 · el PUT de edición incluye `username`/`company_id` ⇒ 422 «Extra inputs» (DTO obsoleto).
 *   AC-02 · 422 ⇒ `alert` con objeto crudo (sin mensaje humano/toast).
 *   AC-03 · alta sin `last_name` ⇒ no hay validación cliente (B-28): el POST se emite.
 *   AC-05 · baja fallida ⇒ modal mudo / `alert` nativo sin mensaje normalizado.
 *   AC-06 · el flujo usa `alert`/`confirm` nativos (C-02: prohibidos).
 *
 * Hallazgo de cabeza: el modal renderiza DOS veces el bloque de datos personales
 * (inputs duplicados de nombre/apellido/email/teléfono/contraseña). El C2 lo
 * deduplica; el RED usa los selectores [0] para no depender de ello.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'

const get = vi.fn()
const post = vi.fn()
const put = vi.fn()
const del = vi.fn()
vi.mock('../../../services/api', () => ({
  default: {
    get: (...a: any[]) => get(...a), post: (...a: any[]) => post(...a),
    put: (...a: any[]) => put(...a), delete: (...a: any[]) => del(...a),
  },
}))
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (k: string, f?: string) => f ?? k }),
}))
const toastError = vi.fn()
const toastSuccess = vi.fn()
vi.mock('../../../components/Toast', async (importOriginal) => {
  const actual = await importOriginal<any>()
  return {
    ...actual,
    useToast: () => ({ success: toastSuccess, error: toastError, warning: vi.fn(), info: vi.fn() }),
  }
})

import UsersPage from '../UsersPage'
import { ToastProvider } from '../../../components/Toast'
import { useAuthStore } from '../../../stores/auth.store'

const USER_A = {
  id: 5, username: 'jperez', first_name: 'Juan', last_name: 'Pérez',
  email: 'jperez@example.com', phone: '', role_id: 2, area_id: null,
  company_id: 1, view_type: 'web', is_active: true,
}

const SUBCONJUNTO = ['first_name', 'last_name', 'email', 'phone', 'role_id', 'is_active', 'view_type', 'area_id']

const E422 = {
  response: {
    data: {
      detail: [{ type: 'value_error', loc: ['body', 'email'], msg: 'value is not a valid email address', input: {} }],
    },
  },
}

function setSession(permissions: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 61, username: 'r195', first_name: 'R', last_name: 'C', email: 'r@x.com',
      role_id: 35, view_type: 'web', is_super_admin: false, company_id: 1,
      effective_company_id: 1, permissions,
      company_business_units: [], granted_business_units: [], effective_business_units: [],
    } as any,
  })
}

const renderPage = () => render(
  <ToastProvider><UsersPage /></ToastProvider>,
)

const abrirEdicion = async () => {
  await screen.findAllByText('jperez')
  fireEvent.click(document.querySelectorAll('.lucide-pencil')[0])
  await screen.findByPlaceholderText('users.usernamePlaceholder')
}

const guardar = () => fireEvent.click(screen.getByRole('button', { name: 'common.save' }))

beforeEach(() => {
  get.mockReset(); post.mockReset(); put.mockReset(); del.mockReset()
  vi.clearAllMocks()
  get.mockImplementation((url: string) => {
    const u = String(url)
    if (u.startsWith('/users')) return Promise.resolve({ data: [USER_A], headers: {} })
    if (u.startsWith('/roles')) return Promise.resolve({ data: [{ id: 2, name: 'Operador' }, { id: 3, name: 'Supervisor' }] })
    if (u.startsWith('/masters/companies')) return Promise.resolve({ data: [{ id: 1, name: 'Empresa Uno', is_active: true }] })
    return Promise.resolve({ data: [] })
  })
})

describe('R-195 · edición de usuario (RED)', () => {
  it('AC-01 · el PUT envía SOLO el subconjunto permitido (sin username/company_id)', async () => {
    setSession(['users:read', 'users:create', 'users:update', 'users:delete'])
    put.mockResolvedValueOnce({ data: { ...USER_A, first_name: 'Juan Carlos', role_id: 3 } })
    renderPage()
    await abrirEdicion()

    const nombres = screen.getAllByPlaceholderText('users.firstNamePlaceholder')
    fireEvent.change(nombres[0], { target: { value: 'Juan Carlos' } })
    const selects = document.querySelectorAll('select')
    fireEvent.change(selects[0], { target: { value: '3' } })
    guardar()

    await waitFor(() => expect(put).toHaveBeenCalled())
    const [url, payload] = put.mock.calls[0]
    expect(url).toBe('/users/5')
    expect(payload.first_name).toBe('Juan Carlos')
    expect(payload.role_id).toBe(3)
    expect(payload).not.toHaveProperty('username')
    expect(payload).not.toHaveProperty('company_id')
    for (const k of SUBCONJUNTO) expect(Object.keys(payload)).toContain(k)
  })

  it('AC-02 · 422 ⇒ mensaje humano por toast (sin objeto crudo)', async () => {
    setSession(['users:read', 'users:create', 'users:update', 'users:delete'])
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})
    put.mockRejectedValueOnce(E422)
    renderPage()
    await abrirEdicion()
    guardar()

    await waitFor(() => expect(toastError).toHaveBeenCalled())
    expect(typeof toastError.mock.calls[0][0]).toBe('string')
    expect(toastError.mock.calls[0][0]).toMatch(/email: value is not a valid email address/)
    expect(alertSpy.mock.calls.filter((c) => typeof c[0] !== 'string').length).toBe(0)
    alertSpy.mockRestore()
  })

  it('AC-03 · alta sin last_name ⇒ validación cliente (no se emite el POST)', async () => {
    setSession(['users:read', 'users:create', 'users:update', 'users:delete'])
    renderPage()
    await screen.findAllByText('jperez')
    fireEvent.click(screen.getByRole('button', { name: 'common.create' }))

    fireEvent.change(await screen.findByPlaceholderText('users.usernamePlaceholder'), { target: { value: 'nuevo' } })
    const nombres = screen.getAllByPlaceholderText('users.firstNamePlaceholder')
    fireEvent.change(nombres[0], { target: { value: 'Nuevo' } })
    fireEvent.change(screen.getAllByPlaceholderText('users.emailPlaceholder')[0], { target: { value: 'nuevo@example.com' } })
    fireEvent.change(screen.getAllByPlaceholderText('users.passwordPlaceholder')[0], { target: { value: 'Clave12345' } })
    guardar()

    await waitFor(() => expect(toastError).toHaveBeenCalled())
    expect(post).not.toHaveBeenCalled()
  })

  it('AC-05 · baja fallida ⇒ mensaje humano (y sin confirm nativo)', async () => {
    setSession(['users:read', 'users:create', 'users:update', 'users:delete'])
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)
    del.mockRejectedValueOnce({
      response: { data: { detail: 'No se puede dar de baja: el usuario tiene registros asociados' } },
    })
    renderPage()
    await screen.findAllByText('jperez')
    fireEvent.click(document.querySelectorAll('.lucide-trash-2')[0])

    const confirmaciones = screen.queryAllByRole('button', { name: /^(Eliminar|Confirmar|Sí)/ })
    if (confirmaciones.length > 0) fireEvent.click(confirmaciones[0])

    await waitFor(() => expect(toastError).toHaveBeenCalled())
    expect(String(toastError.mock.calls[0][0])).toMatch(/No se puede dar de baja/)
    expect(confirmSpy).not.toHaveBeenCalled()
    alertSpy.mockRestore(); confirmSpy.mockRestore()
  })

  it('AC-06 · validación de alta sin diálogos nativos', async () => {
    setSession(['users:read', 'users:create', 'users:update', 'users:delete'])
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})
    renderPage()
    await screen.findAllByText('jperez')
    fireEvent.click(screen.getByRole('button', { name: 'common.create' }))
    await screen.findByPlaceholderText('users.usernamePlaceholder')
    guardar()

    await waitFor(() => expect(toastError).toHaveBeenCalled())
    expect(alertSpy).not.toHaveBeenCalled()
    alertSpy.mockRestore()
  })
})
