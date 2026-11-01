/**
 * SPEC 013 · UAT Admin/RBAC · Lote F2 — Usuarios, Roles y Perfil (`AC-UI-05`, `AC-UI-06`,
 * `AC-RL-04`, `AC-RL-05`).
 *
 * Usuarios (`AC-UI-05` · AR-17/Y-1.3): la papelera ejecuta una BAJA LÓGICA reversible, así que
 * se rotula «Desactivar usuario» (título, confirmación y `aria-label`) y se oculta sobre la
 * propia fila — cortesía de UI; el backend sigue decidiendo.
 *
 * Roles (`AC-UI-06` · AR-20): «Desactivar» se gatea por `users:update` (lo que exige el backend,
 * no `users:delete`), usa `ConfirmDialog` y toasts en vez de `confirm()`/`alert()`, y el `409`
 * por usuarios activos asignados se muestra legible con el `detail` del servidor.
 *
 * Roles (`AC-RL-05` · AR-18/DR-2): sin permisos no se puede guardar y se explica por qué.
 *
 * Roles (`AC-RL-04` · AR-20): «Mostrar inactivos» pide `?include_inactive=true`, los inactivos
 * llevan insignia y se reactivan con `PUT {is_active:true}`.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'

const get = vi.fn()
const post = vi.fn()
const put = vi.fn()
const del = vi.fn()

vi.mock('../../../services/api', () => ({
  default: {
    get: (...a: any[]) => get(...a),
    post: (...a: any[]) => post(...a),
    put: (...a: any[]) => put(...a),
    delete: (...a: any[]) => del(...a),
  },
}))

const toastSuccess = vi.fn()
const toastError = vi.fn()
// `getErrorMessage` se conserva REAL: la prueba del 409 afirma que se muestra el `detail`
// del servidor, y esa normalización (lista/objeto/str) es precisamente la conducta bajo prueba.
vi.mock('../../../components/Toast', async (importOriginal) => {
  const actual = await importOriginal<any>()
  return {
    ...actual,
    useToast: () => ({ success: toastSuccess, error: toastError, warning: vi.fn(), info: vi.fn() }),
  }
})

// `t` devuelve la clave (ignora fallbacks): así los nombres accesibles se afirman por CLAVE y
// la prueba no depende de qué literal se haya escrito como respaldo.
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (k: string) => k }),
}))

import { ToastProvider } from '../../../components/Toast'
import UsersPage from '../UsersPage'
import RolesPage from '../RolesPage'
import { useAuthStore } from '../../../stores/auth.store'

const SELF = {
  id: 5, username: 'ana', first_name: 'Ana', last_name: 'Díaz',
  email: 'ana@x.com', role_id: 2, view_type: 'web', is_active: true,
}
const CARLOS = {
  id: 9, username: 'carlos', first_name: 'Carlos', last_name: 'Ruiz',
  email: 'c@x.com', role_id: 2, view_type: 'web', is_active: true,
}

/** `rolesData`/`usersData` son mutables: cada prueba sirve el escenario que necesita. */
let rolesData: any[] = []
let usersData: any[] = []

function setSession(permissions: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: SELF.id, username: 'ana', first_name: 'Ana', last_name: 'Díaz', email: 'ana@x.com',
      role_id: 2, view_type: 'web', is_super_admin: false, company_id: 1, effective_company_id: 1,
      permissions,
      company_business_units: [], granted_business_units: [], effective_business_units: [],
    } as any,
  })
}

const TODOS = ['users:read', 'users:create', 'users:update', 'users:delete']

beforeEach(() => {
  get.mockReset(); post.mockReset(); put.mockReset(); del.mockReset()
  toastSuccess.mockReset(); toastError.mockReset()
  usersData = [SELF, CARLOS]
  rolesData = [{ id: 2, name: 'Operador', description: 'Opera', permissions: [{ module: 'lots', action: 'read' }], is_active: true }]
  get.mockImplementation((url: string) => {
    const u = String(url)
    // AR-22: la pantalla pide `?limit=100` (y `search` cuando se busca).
    if (u.startsWith('/users?')) return Promise.resolve({ data: usersData })
    if (u.startsWith('/roles/permissions-catalog')) {
      return Promise.resolve({ data: { modules: ['users'], actions: ['read', 'update'] } })
    }
    if (u.startsWith('/roles')) return Promise.resolve({ data: rolesData })
    return Promise.resolve({ data: [] })
  })
  post.mockResolvedValue({ data: {} })
  put.mockResolvedValue({ data: {} })
  del.mockResolvedValue({ data: {} })
})

const urlsPedidas = () => get.mock.calls.map((c) => String(c[0]))

// ─────────────────────────────────── Usuarios ───────────────────────────────────

describe('SPEC 013 · Lote F2 · UsersPage — la papelera es una baja lógica (AC-UI-05)', () => {
  it('la papelera se rotula «Desactivar usuario» (aria-label + title) y confirma con users.deactivate', async () => {
    setSession(TODOS)
    render(<ToastProvider><UsersPage /></ToastProvider>)
    await screen.findAllByText('carlos')

    const papeleras = screen.getAllByLabelText('users.deleteUserTitle')
    // Solo la del OTRO usuario: la propia fila no ofrece baja.
    expect(papeleras).toHaveLength(1)
    expect(papeleras[0].getAttribute('title')).toBe('users.deleteUserTitle')

    fireEvent.click(papeleras[0])
    const dialogo = await screen.findByRole('dialog')
    expect(within(dialogo).getByText('users.deleteUserTitle')).toBeTruthy()
    expect(within(dialogo).getByText(/users\.deleteConfirm/)).toBeTruthy()

    fireEvent.click(within(dialogo).getByRole('button', { name: 'users.deactivate' }))
    await waitFor(() => expect(del).toHaveBeenCalledWith('/users/9'))
  })

  it('sobre la propia fila no hay papelera y el chip de estado NO es interactivo', async () => {
    setSession(TODOS)
    render(<ToastProvider><UsersPage /></ToastProvider>)
    const nombres = await screen.findAllByText('ana')

    // Fila de escritorio (la tabla precede a las tarjetas móviles en el DOM).
    const fila = nombres[0].closest('tr') as HTMLElement
    expect(within(fila).queryByLabelText('users.deleteUserTitle')).toBeNull()
    expect(within(fila).getByText('users.active').tagName).toBe('SPAN')
    expect(within(fila).queryByRole('button', { name: 'users.active' })).toBeNull()

    // Tarjeta móvil de la propia fila: tampoco ofrece la acción.
    const tarjeta = nombres[1].closest('.bg-white') as HTMLElement
    expect(within(tarjeta).queryByText('users.deleteUser')).toBeNull()

    // Control: sobre OTRO usuario el chip sí es un botón (users:update) y la baja existe.
    const filaCarlos = screen.getAllByText('carlos')[0].closest('tr') as HTMLElement
    expect(within(filaCarlos).getByRole('button', { name: 'users.active' })).toBeTruthy()
    expect(within(filaCarlos).getByLabelText('users.deleteUserTitle')).toBeTruthy()
  })
})

/**
 * `AC-ID-05`: el chip de estado es un botón solo si el permiso de la ACCIÓN que dispara está
 * concedido. Desactivar exige `users:delete` (el backend responde `403` sin él) y reactivar
 * exige `users:update`. Antes el chip se gateaba por `users:update` en ambos sentidos, así que
 * quien podía editar pero no borrar veía «Activo» como botón y recibía un `403` al pulsarlo.
 */
describe('SPEC 013 · AC-ID-05 · UsersPage — el chip de estado respeta el permiso de su acción', () => {
  it('con users:update pero SIN users:delete el chip de un usuario ACTIVO no es un botón', async () => {
    setSession(['users:read', 'users:create', 'users:update'])
    render(<ToastProvider><UsersPage /></ToastProvider>)
    const nombres = await screen.findAllByText('carlos')

    // Fila de escritorio: mismo texto, pero no interactivo.
    const fila = nombres[0].closest('tr') as HTMLElement
    expect(within(fila).getByText('users.active').tagName).toBe('SPAN')
    expect(within(fila).queryByRole('button', { name: 'users.active' })).toBeNull()

    // Tarjeta móvil: tampoco ofrece la acción.
    const tarjeta = nombres[1].closest('.bg-white') as HTMLElement
    expect(within(tarjeta).getByText('users.active').tagName).toBe('SPAN')
    expect(within(tarjeta).queryByRole('button', { name: 'users.active' })).toBeNull()

    // No se ofrece lo que el servidor rechazaría: ni baja ni PUT de estado.
    expect(put).not.toHaveBeenCalled()
  })

  it('con users:update y users:delete el chip SÍ es botón y desactivar manda PUT {is_active:false}', async () => {
    setSession(TODOS)
    render(<ToastProvider><UsersPage /></ToastProvider>)
    const fila = (await screen.findAllByText('carlos'))[0].closest('tr') as HTMLElement

    fireEvent.click(within(fila).getByRole('button', { name: 'users.active' }))
    await waitFor(() => expect(put).toHaveBeenCalledWith('/users/9', { is_active: false }))
  })

  it('con users:update sin users:delete el chip de un usuario INACTIVO SÍ es botón (reactivar)', async () => {
    usersData = [...usersData, {
      id: 11, username: 'beatriz', first_name: 'Beatriz', last_name: 'Núñez',
      email: 'b@x.com', role_id: 2, view_type: 'web', is_active: false,
    }]
    setSession(['users:read', 'users:update'])
    render(<ToastProvider><UsersPage /></ToastProvider>)
    const nombres = await screen.findAllByText('beatriz')

    // Reactivar exige `users:update`, que sí tiene: el chip es un botón en ambas vistas.
    const fila = nombres[0].closest('tr') as HTMLElement
    const chip = within(fila).getByRole('button', { name: 'users.inactive' })
    expect(chip.tagName).toBe('BUTTON')

    const tarjeta = nombres[1].closest('.bg-white') as HTMLElement
    expect(within(tarjeta).getByRole('button', { name: 'users.inactive' })).toBeTruthy()

    fireEvent.click(chip)
    await waitFor(() => expect(put).toHaveBeenCalledWith('/users/11', { is_active: true }))
  })
})

// ─────────────────────────────────── Roles ───────────────────────────────────

const abrirNuevoRol = async () => {
  fireEvent.click(await screen.findByRole('button', { name: 'roles.createRole' }))
  await screen.findByLabelText('roles.name')
}

describe('SPEC 013 · Lote F2 · RolesPage — sin permisos no hay rol (AC-RL-05)', () => {
  it('guardar queda deshabilitado y se explica mientras no haya permisos', async () => {
    setSession(TODOS)
    render(<ToastProvider><RolesPage /></ToastProvider>)
    await abrirNuevoRol()

    fireEvent.change(screen.getByLabelText('roles.name'), { target: { value: 'Auditor' } })

    const guardar = screen.getByRole('button', { name: 'common.save' }) as HTMLButtonElement
    expect(guardar.disabled).toBe(true)
    const alerta = screen.getByRole('alert')
    expect(alerta.textContent).toMatch(/roles\.permissionsRequired/)
    expect(post).not.toHaveBeenCalled()
  })

  it('con un permiso marcado se guarda y viaja ese permiso', async () => {
    setSession(TODOS)
    render(<ToastProvider><RolesPage /></ToastProvider>)
    await abrirNuevoRol()

    fireEvent.change(screen.getByLabelText('roles.name'), { target: { value: 'Auditor' } })
    fireEvent.click(screen.getByRole('checkbox', { name: 'users:update' }))

    const guardar = screen.getByRole('button', { name: 'common.save' }) as HTMLButtonElement
    expect(guardar.disabled).toBe(false)
    expect(screen.queryByRole('alert')).toBeNull()

    fireEvent.click(guardar)
    await waitFor(() => expect(post).toHaveBeenCalled())
    expect(post).toHaveBeenCalledWith('/roles', {
      name: 'Auditor', description: '',
      permissions: [{ module: 'users', action: 'update', scope_type: 'all' }],
    })
  })
})

describe('SPEC 013 · Lote F2 · RolesPage — desactivar sin diálogos nativos (AC-UI-06)', () => {
  it('«Desactivar» abre ConfirmDialog y al confirmar hace PUT {is_active:false}', async () => {
    setSession(TODOS)
    render(<ToastProvider><RolesPage /></ToastProvider>)

    fireEvent.click(await screen.findByRole('button', { name: 'roles.deactivate' }))
    const dialogo = await screen.findByRole('dialog')
    expect(within(dialogo).getByText('roles.deactivateTitle')).toBeTruthy()

    fireEvent.click(within(dialogo).getByRole('button', { name: 'roles.deactivate' }))
    await waitFor(() => expect(put).toHaveBeenCalledWith('/roles/2', { is_active: false }))
    expect(toastSuccess).toHaveBeenCalledWith('roles.deactivated')
  })

  it('un 409 por usuarios activos se muestra legible por toast y NUNCA por alert nativo', async () => {
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})
    const detalle = 'El rol tiene 3 usuario(s) activo(s) y no puede desactivarse'
    put.mockRejectedValueOnce({ response: { status: 409, data: { detail: detalle } } })
    setSession(TODOS)
    render(<ToastProvider><RolesPage /></ToastProvider>)

    fireEvent.click(await screen.findByRole('button', { name: 'roles.deactivate' }))
    const dialogo = await screen.findByRole('dialog')
    fireEvent.click(within(dialogo).getByRole('button', { name: 'roles.deactivate' }))

    await waitFor(() => expect(toastError).toHaveBeenCalled())
    expect(String(toastError.mock.calls[0][0])).toBe(detalle)
    expect(alertSpy).not.toHaveBeenCalled()
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
    alertSpy.mockRestore()
  })

  it('con users:delete pero SIN users:update no aparece «Desactivar» (el backend exige users:update)', async () => {
    setSession(['users:read', 'users:create', 'users:delete'])
    render(<ToastProvider><RolesPage /></ToastProvider>)
    await screen.findByText('Operador')

    // El nombre accesible puede venir de la clave o de un fallback: la negación cubre ambos.
    expect(screen.queryByRole('button', { name: /roles\.deactivate|Desactivar rol/ })).toBeNull()
    expect(screen.queryByRole('button', { name: /roles\.editRole|Editar rol/ })).toBeNull()
  })
})

describe('SPEC 013 · Lote F2 · RolesPage — inactivos y reactivación (AC-RL-04)', () => {
  it('«Mostrar inactivos» pide include_inactive, marca el inactivo y permite reactivarlo', async () => {
    rolesData = [
      { id: 2, name: 'Operador', description: 'Opera', permissions: [], is_active: true },
      { id: 4, name: 'Antiguo', description: 'Retirado', permissions: [], is_active: false },
    ]
    setSession(TODOS)
    render(<ToastProvider><RolesPage /></ToastProvider>)
    await screen.findByText('Operador')

    // Primera carga: sin inactivos ⇒ no se piden.
    expect(urlsPedidas()).toContain('/roles')
    expect(urlsPedidas()).not.toContain('/roles?include_inactive=true')

    fireEvent.click(screen.getByRole('checkbox', { name: 'roles.showInactive' }))
    await waitFor(() => expect(urlsPedidas()).toContain('/roles?include_inactive=true'))

    const filaInactivo = (await screen.findByText('Antiguo')).closest('tr') as HTMLElement
    expect(within(filaInactivo).getByText('roles.inactive')).toBeTruthy()
    expect(within(filaInactivo).queryByRole('button', { name: 'roles.deactivate' })).toBeNull()

    // El activo, en cambio, no lleva insignia ni ofrece reactivar.
    const filaActivo = screen.getByText('Operador').closest('tr') as HTMLElement
    expect(within(filaActivo).queryByText('roles.inactive')).toBeNull()
    expect(within(filaActivo).queryByRole('button', { name: 'roles.reactivate' })).toBeNull()

    fireEvent.click(within(filaInactivo).getByRole('button', { name: 'roles.reactivate' }))
    await waitFor(() => expect(put).toHaveBeenCalledWith('/roles/4', { is_active: true }))
    expect(toastSuccess).toHaveBeenCalledWith('roles.reactivated')
  })
})
