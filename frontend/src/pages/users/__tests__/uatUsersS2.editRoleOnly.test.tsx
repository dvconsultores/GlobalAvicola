/**
 * SPEC 013 · GA-UAT-USERS-S2-01 · UAT SESIÓN 2 · RED jsdom.
 *
 * Hallazgo de Yolinel: editar un usuario cambiando SOLO el rol mostraba
 * «La nueva contraseña debe ser distinta de la actual» sin tocar la clave.
 * Causa (spec §7): el modal de edición conservaba un `input[type=password]`
 * siempre presente que el navegador autocompletaba y `handleSave` enviaba
 * como clave nueva a `POST /users/{id}/password`.
 *
 * Contrato AC-S2-01..03: editar y cambiar clave son operaciones distintas;
 * en edición la clave solo viaja si se activa «Cambiar contraseña».
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
// Igual que `r195.usersEdit`: `t` devuelve el texto de reserva o la clave. Se
// añade la interpolación de `{{detail}}` porque el aviso «datos guardados pero
// la contraseña no se cambió» la usa.
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (k: string, f?: any) => {
      if (typeof f === 'string') return f
      if (f && typeof f === 'object' && typeof f.detail === 'string') return `${k}: ${f.detail}`
      return k
    },
  }),
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

// Contrato `UserUpdate` (`extra=forbid`): ni `password` ni `new_password` ni
// `username`/`company_id` (los resuelve el servidor).
const CLAVES_PUT = [
  'first_name', 'last_name', 'email', 'phone',
  'role_id', 'area_id', 'view_type', 'is_active',
]

const CLAVE_OK = 'Clave-Nueva-12'
function setSession(permissions: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 61, username: 's201', first_name: 'S', last_name: 'U', email: 's@x.com',
      role_id: 35, view_type: 'web', is_super_admin: false, company_id: 1,
      effective_company_id: 1, permissions,
      company_business_units: [], granted_business_units: [], effective_business_units: [],
    } as any,
  })
}

const TODOS = ['users:read', 'users:create', 'users:update', 'users:delete']

const renderPage = () => render(<ToastProvider><UsersPage /></ToastProvider>)
const abrirEdicion = async () => {
  await screen.findAllByText('jperez')
  fireEvent.click(document.querySelectorAll('.lucide-pencil')[0])
  await screen.findByPlaceholderText('users.usernamePlaceholder')
}

const guardar = () => fireEvent.click(screen.getByRole('button', { name: 'common.save' }))

const inputsPassword = () =>
  Array.from(document.querySelectorAll('input[type="password"]')) as HTMLInputElement[]

const toggleClave = () => screen.getByRole('button', { name: 'users.changePasswordToggle' })

const postsPassword = () =>
  post.mock.calls.filter((c) => String(c[0]).includes('/password'))
const activarCambioClave = () => fireEvent.click(toggleClave())

const camposClave = async () => {
  activarCambioClave()
  const nueva = await screen.findByPlaceholderText('users.newPassword')
  const conf = screen.getByPlaceholderText('users.confirmPassword')
  return { nueva, conf }
}

beforeEach(() => {
  get.mockReset(); post.mockReset(); put.mockReset(); del.mockReset()
  toastError.mockReset(); toastSuccess.mockReset()
  get.mockImplementation((url: string) => {
    const u = String(url)
    if (u.startsWith('/users')) return Promise.resolve({ data: [USER_A], headers: {} })
    if (u.startsWith('/roles')) return Promise.resolve({ data: [{ id: 2, name: 'Operador' }, { id: 3, name: 'Supervisor' }] })
    if (u.startsWith('/masters/companies')) return Promise.resolve({ data: [{ id: 1, name: 'Empresa Uno', is_active: true }] })
    return Promise.resolve({ data: [] })
  })
  put.mockResolvedValue({ data: USER_A })
  post.mockResolvedValue({ data: {} })
})

const editarYGuardar = async (aplicar: () => void) => {
  setSession(TODOS)
  renderPage()
  await abrirEdicion()
  // Autofill simulado del navegador (ver FE-01).
  const autofill = inputsPassword()
  if (autofill.length > 0) fireEvent.change(autofill[0], { target: { value: 'ClaveActual-1' } })
  aplicar()
  guardar()
}

const esperarSoloPut = async () => {
  await waitFor(() => expect(put).toHaveBeenCalledTimes(1))
  await waitFor(() => expect(screen.queryByPlaceholderText('users.usernamePlaceholder')).toBeNull())
  expect(put.mock.calls[0][0]).toBe('/users/5')
  expect(postsPassword()).toHaveLength(0)
  expect(toastError).not.toHaveBeenCalled()
}

describe('S2-01 · edición sin cambiar la contraseña', () => {
  it('FE-01 · cambiar SOLO el rol ⇒ un PUT y ninguna petición a /password', async () => {
    setSession(TODOS)
    renderPage()
    await abrirEdicion()

    // Escenario de Yolinel: el navegador AUTORELLENA cualquier campo de
    // contraseña que el modal de edición muestre (fondo azul del autofill).
    // Si no hay ninguno —lo que exige AC-S2-02— no hay nada que rellenar.
    const autofill = inputsPassword()
    if (autofill.length > 0) fireEvent.change(autofill[0], { target: { value: 'ClaveActual-1' } })

    fireEvent.change(document.querySelectorAll('select')[0], { target: { value: '3' } })
    guardar()

    await waitFor(() => expect(put).toHaveBeenCalledTimes(1))
    await waitFor(() => expect(screen.queryByPlaceholderText('users.usernamePlaceholder')).toBeNull())
    expect(put.mock.calls[0][0]).toBe('/users/5')
    expect(postsPassword()).toHaveLength(0)
    expect(toastError).not.toHaveBeenCalled()
  })
    it('FE-02 · el cuerpo del PUT tiene EXACTAMENTE las claves del contrato', async () => {
    setSession(TODOS)
    renderPage()
    await abrirEdicion()
    const autofill = inputsPassword()
    if (autofill.length > 0) fireEvent.change(autofill[0], { target: { value: 'ClaveActual-1' } })
    fireEvent.change(document.querySelectorAll('select')[0], { target: { value: '3' } })
    guardar()

    await waitFor(() => expect(put).toHaveBeenCalledTimes(1))
    const [url, payload] = put.mock.calls[0]
    expect(url).toBe('/users/5')
    expect(Object.keys(payload).sort()).toEqual([...CLAVES_PUT].sort())
    expect(payload).not.toHaveProperty('password')
    expect(payload).not.toHaveProperty('new_password')
    expect(postsPassword()).toHaveLength(0)
  })
  it('FE-03 · cambiar el apellido ⇒ un PUT, ningún POST /password, sin error', async () => {
    await editarYGuardar(() => {
      fireEvent.change(screen.getByPlaceholderText('users.lastNamePlaceholder'), { target: { value: 'Pérez Soto' } })
    })
    await esperarSoloPut()
    expect((put.mock.calls[0][1] as any).last_name).toBe('Pérez Soto')
  })

  it('FE-04 · cambiar el email ⇒ un PUT, ningún POST /password, sin error', async () => {
    await editarYGuardar(() => {
      fireEvent.change(screen.getByPlaceholderText('users.emailPlaceholder'), { target: { value: 'nuevo@example.com' } })
    })
    await esperarSoloPut()
    expect((put.mock.calls[0][1] as any).email).toBe('nuevo@example.com')
  })
    // El modal no expone control de `is_active` (el estado se alterna desde la
  // tabla), así que FE-05 usa el nombre, el otro dato de identidad editable.
  it('FE-05 · cambiar el nombre ⇒ un PUT, ningún POST /password, sin error', async () => {
    await editarYGuardar(() => {
      fireEvent.change(screen.getByPlaceholderText('users.firstNamePlaceholder'), { target: { value: 'Juan Carlos' } })
    })
    await esperarSoloPut()
    expect((put.mock.calls[0][1] as any).first_name).toBe('Juan Carlos')
  })
})
describe('S2-01 · flujo explícito de cambio de contraseña (AC-S2-03)', () => {
  const abrirClave = async () => {
    setSession(TODOS)
    renderPage()
    await abrirEdicion()
    return camposClave()
  }

  it('FE-06a · nueva < 8 ⇒ error de validación y NINGUNA petición', async () => {
    const { nueva, conf } = await abrirClave()
    fireEvent.change(nueva, { target: { value: 'Corta' } })
    fireEvent.change(conf, { target: { value: 'Corta' } })
    guardar()

    await waitFor(() => expect(toastError).toHaveBeenCalled())
    expect(String(toastError.mock.calls[0][0])).toContain('users.passwordTooShort')
    expect(put).not.toHaveBeenCalled()
    expect(post).not.toHaveBeenCalled()
    expect(screen.getByPlaceholderText('users.usernamePlaceholder')).toBeTruthy()
  })
    it('FE-06b · confirmación distinta ⇒ error y NINGUNA petición', async () => {
    const { nueva, conf } = await abrirClave()
    fireEvent.change(nueva, { target: { value: CLAVE_OK } })
    fireEvent.change(conf, { target: { value: 'Otra-Clave-99' } })
    guardar()

    await waitFor(() => expect(toastError).toHaveBeenCalled())
    expect(String(toastError.mock.calls[0][0])).toContain('users.passwordMismatch')
    expect(put).not.toHaveBeenCalled()
    expect(post).not.toHaveBeenCalled()
    expect(screen.getByPlaceholderText('users.usernamePlaceholder')).toBeTruthy()
  })
    it('FE-06c · válida ⇒ PUT y después POST /users/5/password con {new_password}', async () => {
    const { nueva, conf } = await abrirClave()
    fireEvent.change(document.querySelectorAll('select')[0], { target: { value: '3' } })
    fireEvent.change(nueva, { target: { value: CLAVE_OK } })
    fireEvent.change(conf, { target: { value: CLAVE_OK } })
    guardar()

    await waitFor(() => expect(postsPassword()).toHaveLength(1))
    expect(put).toHaveBeenCalledTimes(1)
    expect(put.mock.calls[0][0]).toBe('/users/5')
    const clavesPUT = Object.keys(put.mock.calls[0][1] as any).sort()
    expect(clavesPUT).toEqual([...CLAVES_PUT].sort())
    expect(post.mock.calls[0][0]).toBe('/users/5/password')
    expect(post.mock.calls[0][1]).toEqual({ new_password: CLAVE_OK })
    expect(put.mock.invocationCallOrder[0]).toBeLessThan(post.mock.invocationCallOrder[0])
    expect(toastError).not.toHaveBeenCalled()
  })
    it('FE-06d · POST rechazado ⇒ aviso con el detalle del servidor y PUT ya aplicado', async () => {
    const detalle = 'La nueva contraseña debe ser distinta de la actual'
    post.mockRejectedValueOnce({ response: { status: 422, data: { detail: detalle } } })
    const { nueva, conf } = await abrirClave()
    fireEvent.change(nueva, { target: { value: CLAVE_OK } })
    fireEvent.change(conf, { target: { value: CLAVE_OK } })
    guardar()

    await waitFor(() => expect(toastError).toHaveBeenCalled())
    expect(put).toHaveBeenCalledTimes(1)
    const aviso = String(toastError.mock.calls[0][0])
    expect(aviso).toContain('users.passwordNotChanged')
    expect(aviso).toContain(detalle)
    // el PUT se aplicó: la lista se refresca y el modal no se cierra
    await waitFor(() =>
      expect(get.mock.calls.filter((c) => String(c[0]).startsWith('/users')).length).toBeGreaterThan(1))
    expect(screen.getByPlaceholderText('users.usernamePlaceholder')).toBeTruthy()
  })
})
describe('S2-01 · el campo de contraseña solo existe si se pide (AC-S2-02)', () => {
  it('FE-07a · en edición NO hay input[type=password] hasta activar el cambio', async () => {
    setSession(TODOS)
    renderPage()
    await abrirEdicion()
    expect(document.querySelector('input[type="password"]')).toBeNull()
    expect(toggleClave().getAttribute('aria-pressed')).toBe('false')
  })

  it('FE-07b · activado ⇒ nueva + confirmación con autocomplete="new-password"', async () => {
    setSession(TODOS)
    renderPage()
    await abrirEdicion()
    const { nueva, conf } = await camposClave()
    const campos = inputsPassword()
    expect(campos).toHaveLength(2)
    expect(campos).toContain(nueva)
    expect(campos).toContain(conf)
    for (const c of campos) expect(c.getAttribute('autocomplete')).toBe('new-password')
    expect(toggleClave().getAttribute('aria-pressed')).toBe('true')
  })
    it('FE-07c · desactivar descarta lo escrito y el Guardar posterior no pide clave', async () => {
    setSession(TODOS)
    renderPage()
    await abrirEdicion()
    let { nueva, conf } = await camposClave()
    fireEvent.change(nueva, { target: { value: CLAVE_OK } })
    fireEvent.change(conf, { target: { value: CLAVE_OK } })

    fireEvent.click(toggleClave())
    await waitFor(() => expect(document.querySelectorAll('input[type="password"]').length).toBe(0))

    // Al reactivar los campos vuelven vacíos: lo escrito se descartó.
    const otraVez = await camposClave()
    nueva = otraVez.nueva; conf = otraVez.conf
    expect((nueva as HTMLInputElement).value).toBe('')
    expect((conf as HTMLInputElement).value).toBe('')

    // Y un guardado tras volver a desactivar no envía clave alguna.
    fireEvent.click(toggleClave())
    await waitFor(() => expect(document.querySelectorAll('input[type="password"]').length).toBe(0))
    guardar()
    await esperarSoloPut()
  })
  it('FE-07d · en ALTA el campo de contraseña lleva autocomplete="new-password"', async () => {
    setSession(TODOS)
    renderPage()
    await screen.findAllByText('jperez')
    fireEvent.click(screen.getByRole('button', { name: 'common.create' }))
    const campo = (await screen.findByPlaceholderText('users.passwordPlaceholder')) as HTMLInputElement
    expect(campo.type).toBe('password')
    expect(campo.getAttribute('autocomplete')).toBe('new-password')
    // En alta la clave es obligatoria: no hay conmutador que la oculte.
    expect(screen.queryByRole('button', { name: 'users.changePasswordToggle' })).toBeNull()
  })
})












