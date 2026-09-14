/**
 * R-215 · RED jsdom — render seguro de errores estructurados (422 lista de FastAPI)
 * en las 5 superficies fuera del asistente, y `ErrorBoundary` global.
 *
 * Diseño: `specs/R-215/R-215_RED_E2E_UAT_DESIGN.md §1` (AC-01…04).
 *
 * Rojo en HEAD:
 *   01 · MasterListPage pinta `detail` crudo ⇒ React #31 (pantalla rota).
 *   02 · LotFormPage pasa `detail` crudo al toast (no normaliza).
 *   03 · TraceabilityTree pinta `linkError` crudo ⇒ React #31.
 *   04 · ProfilePage pinta `message` crudo ⇒ React #31.
 *   05 · UsersPage usa `alert(detail)` ⇒ «[object Object]».
 *   06 · No existe `ErrorBoundary` (import dinámico falla en HEAD).
 *
 * El helper `getErrorMessage` (real) se mantiene activo; solo `useToast` va mockeado.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

const get = vi.fn()
const post = vi.fn()
const put = vi.fn()
const del = vi.fn()
vi.mock('../../services/api', () => ({
  default: {
    get: (...a: any[]) => get(...a),
    post: (...a: any[]) => post(...a),
    put: (...a: any[]) => put(...a),
    patch: vi.fn(),
    delete: (...a: any[]) => del(...a),
  },
}))
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (k: string, f?: any) => (typeof f === 'string' ? f : k) }),
}))
const toastError = vi.fn()
const toastSuccess = vi.fn()
vi.mock('../Toast', async (importOriginal) => {
  const actual = await importOriginal<any>()
  return {
    ...actual,
    useToast: () => ({ success: toastSuccess, error: toastError, warning: vi.fn(), info: vi.fn() }),
  }
})

import MasterListPage from '../../pages/masters/MasterListPage'
import LotFormPage from '../../pages/lots/LotFormPage'
import { TraceabilityTree } from '../../components/TraceabilityTree'
import ProfilePage from '../../pages/users/ProfilePage'
import UsersPage from '../../pages/users/UsersPage'
import { ToastProvider } from '../../components/Toast'
import { useAuthStore } from '../../stores/auth.store'

/** 422 estructurado canónico de FastAPI (el que rompía React #31). */
const E422 = {
  response: {
    data: {
      detail: [
        { type: 'missing', loc: ['body', 'name'], msg: 'String should have at least 1 character', input: {} },
      ],
    },
  },
}

function setSession(permissions: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 61, username: 'r215-c', first_name: 'R', last_name: 'C', email: 'c@x.com',
      role_id: 35, view_type: 'web', is_super_admin: false, company_id: 1, effective_company_id: 1,
      permissions, company_business_units: ['broiler'], granted_business_units: ['broiler'],
      effective_business_units: ['broiler'],
    } as any,
  })
}

beforeEach(() => {
  vi.clearAllMocks()
  useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false, token: null })
  get.mockResolvedValue({ data: [], headers: {} })
})

describe('R-215 · render seguro de errores (RED)', () => {
  it('01 · maestros: 422 lista ⇒ texto legible, sin React #31', async () => {
    setSession(['masters:create', 'masters:update', 'masters:delete', 'masters:read'])
    post.mockRejectedValueOnce(E422)
    render(
      <MemoryRouter>
        <ToastProvider>
          <MasterListPage entity="farms" titleKey="masters.farms"
                          columns={[{ key: 'name', labelKey: 'name' }]} />
        </ToastProvider>
      </MemoryRouter>,
    )
    fireEvent.click(await screen.findByRole('button', { name: 'Nuevo' }))
    const campos = await screen.findAllByRole('textbox')
    fireEvent.change(campos[campos.length - 1], { target: { value: 'Granja R215' } })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar' }))

    await waitFor(() => expect(
      screen.getByText(/name: String should have at least 1 character/),
    ).toBeTruthy())
  })

  it('02 · lotes: 422 lista ⇒ toast legible (cadena, no objeto)', async () => {
    setSession(['lots:read', 'lots:create', 'masters:read', 'dashboard:read'])
    get.mockImplementation((url: string) => {
      const u = String(url)
      if (u.startsWith('/masters/farms')) return Promise.resolve({ data: [{ id: 1, name: 'Granja Uno' }] })
      return Promise.resolve({ data: [] })
    })
    post.mockRejectedValueOnce(E422)
    render(
      <MemoryRouter initialEntries={['/lots/new']}>
        <LotFormPage />
      </MemoryRouter>,
    )
    fireEvent.change(await screen.findByLabelText(/Código/), { target: { value: 'R215-01' } })
    const combos = screen.getAllByRole('combobox')
    fireEvent.change(combos[0], { target: { value: 'broiler' } })
    fireEvent.change(combos[1], { target: { value: '1' } })
    fireEvent.click(screen.getByRole('button', { name: 'Crear Lote' }))

    await waitFor(() => expect(toastError).toHaveBeenCalledTimes(1))
    const mensaje = toastError.mock.calls[0][0]
    expect(typeof mensaje).toBe('string')
    expect(String(mensaje)).toMatch(/name: String should have at least 1 character/)
  })

  it('03 · trazabilidad: 422 lista al vincular ⇒ texto en línea, sin React #31', async () => {
    setSession(['lots:read', 'lots:create'])
    get.mockResolvedValue({
      data: {
        lot: { id: 55, lot_code: 'R215-L', status: 'active', bird_type: 'breeder' },
        egg_batches_sent: [], egg_batches_received: [],
        chick_batches_sent: [],
        chick_batches_received: [
          { id: 9, quantity_dispatched: 120, dispatch_date: '2026-09-01T00:00:00', hatchery_lot: null },
        ],
      },
    })
    post.mockRejectedValueOnce(E422)
    render(
      <MemoryRouter>
        <TraceabilityTree lotId={55} birdType="hatchery" />
      </MemoryRouter>,
    )
    fireEvent.click(await screen.findByRole('button', { name: /Vincular pollitos a engorde/ }))
    const numericos = await screen.findAllByRole('spinbutton')
    fireEvent.change(numericos[0], { target: { value: '77' } })
    fireEvent.change(numericos[1], { target: { value: '120' } })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar' }))

    await waitFor(() => expect(post).toHaveBeenCalled())
    await waitFor(() => expect(
      screen.getByText(/name: String should have at least 1 character/),
    ).toBeTruthy())
  })

  it('04 · perfil: 422 lista al cambiar contraseña ⇒ texto, sin React #31', async () => {
    setSession([])
    post.mockRejectedValueOnce(E422)
    const { container } = render(
      <MemoryRouter>
        <ProfilePage />
      </MemoryRouter>,
    )
    const claves = container.querySelectorAll('input[type="password"]')
    expect(claves.length).toBe(3)
    fireEvent.change(claves[0], { target: { value: 'actual' } })
    fireEvent.change(claves[1], { target: { value: 'nueva12345' } })
    fireEvent.change(claves[2], { target: { value: 'nueva12345' } })
    fireEvent.click(screen.getByRole('button', { name: /profile.updatePassword/ }))

    await waitFor(() => expect(post).toHaveBeenCalled())
    await waitFor(() => expect(
      screen.getByText(/name: String should have at least 1 character/),
    ).toBeTruthy())
  })

  it('05 · usuarios: 422 ⇒ sin «[object Object]» y con mensaje legible', async () => {
    setSession(['users:create', 'users:update', 'users:delete'])
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})
    get.mockImplementation((url: string) => {
      if (String(url).startsWith('/users')) return Promise.resolve({ data: [] })
      return Promise.resolve({ data: [] })
    })
    post.mockRejectedValueOnce(E422)
    render(
      <MemoryRouter>
        <ToastProvider>
          <UsersPage />
        </ToastProvider>
      </MemoryRouter>,
    )
    fireEvent.click(await screen.findByRole('button', { name: 'common.create' }))
    const rellenar = async (clave: string, valor: string) => {
      const campos = await screen.findAllByPlaceholderText(clave)
      campos.forEach((campo) => fireEvent.change(campo, { target: { value: valor } }))
    }
    await rellenar('users.usernamePlaceholder', 'r215u')
    await rellenar('users.firstNamePlaceholder', 'Uno')
    await rellenar('users.emailPlaceholder', 'r215u@example.com')
    await rellenar('users.passwordPlaceholder', 'Clave12345')
    fireEvent.click(screen.getByRole('button', { name: 'common.save' }))

    await waitFor(() => expect(post).toHaveBeenCalledTimes(1))
    await waitFor(() => {
      const noString = alertSpy.mock.calls.filter((c) => typeof c[0] !== 'string')
      expect(noString.length, 'alert con detalle no-string ([object Object])').toBe(0)
    })
    await waitFor(() => expect(toastError).toHaveBeenCalled())
    expect(typeof toastError.mock.calls[0][0]).toBe('string')
    expect(toastError.mock.calls[0][0]).toMatch(/name: String should have at least 1 character/)
    alertSpy.mockRestore()
  })

  it('06 · ErrorBoundary global con recuperación (no existe en HEAD)', async () => {
    const errSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    // `import.meta.glob` no rompe la carga del archivo si el módulo no existe (HEAD).
    const modulos: any = import.meta.glob('../ErrorBoundary.tsx')
    const claves = Object.keys(modulos)
    expect(claves.length, 'ErrorBoundary no existe todavía (R-215 AC-04)').toBeGreaterThan(0)
    const mod: any = await modulos[claves[0]]()
    expect(mod?.ErrorBoundary, 'ErrorBoundary sin export nombrado').toBeTruthy()

    const Bomb = () => { throw new Error('boom de prueba') }
    render(
      <MemoryRouter>
        <mod.ErrorBoundary><Bomb /></mod.ErrorBoundary>
      </MemoryRouter>,
    )
    expect(await screen.findByRole('button', { name: /Reintentar/ })).toBeTruthy()
    expect(screen.getByRole('button', { name: /Recargar/ })).toBeTruthy()
    expect(screen.getByText(/boundary|error/i)).toBeTruthy()
    expect(screen.queryByText(/boom de prueba/)).toBeNull()
    errSpy.mockRestore()
  })
})
