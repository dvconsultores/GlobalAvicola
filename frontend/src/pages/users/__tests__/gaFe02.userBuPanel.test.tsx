/**
 * GA-FE-02 · Panel «Unidades de negocio» dentro de la administración de usuarios (AC-UBU).
 *
 * Separación dura (AC-UBU-04): estado de la EMPRESA (habilitada/inactiva) y estado del USUARIO
 * (concedida / efectiva / revocada / no concedida) son indicadores distintos, nunca fusionados.
 * La concesión y la revocación usan los endpoints exactos del contrato.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'

const get = vi.fn()
const post = vi.fn()
const del = vi.fn()
const put = vi.fn()

vi.mock('../../../services/api', () => ({
  default: {
    get: (...a: any[]) => get(...a),
    post: (...a: any[]) => post(...a),
    delete: (...a: any[]) => del(...a),
    put: (...a: any[]) => put(...a),
  },
}))

const toastSuccess = vi.fn()
const toastError = vi.fn()
vi.mock('../../../components/Toast', () => ({
  useToast: () => ({ success: toastSuccess, error: toastError, warning: vi.fn(), info: vi.fn() }),
  getErrorMessage: (_e: any, fallback: string) => fallback,
  // `R-215`: UsersPage usa `useToast`; el provider real existe en App.
  ToastProvider: ({ children }: any) => children,
}))

vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (k: string, f?: string) => f ?? k }),
}))

import { ToastProvider } from '../../../components/Toast'
import UsersPage from '../UsersPage'
import { useAuthStore } from '../../../stores/auth.store'
import { useCompanyStore } from '../../../stores/company.store'

const CARLOS = {
  id: 9, username: 'carlos', first_name: 'Carlos', last_name: 'Ruiz',
  email: 'c@x.com', role_id: 1, view_type: 'web', is_active: true,
}
const SELF = {
  id: 5, username: 'ana', first_name: 'Ana', last_name: 'Díaz',
  email: 'ana@x.com', role_id: 2, view_type: 'web', is_active: true,
}

const UNITS = [
  { code: 'grandparent', name_key: 'businessUnits.grandparent', is_enabled: true },
  { code: 'breeder', name_key: 'businessUnits.breeder', is_enabled: true },
  { code: 'hatchery', name_key: 'businessUnits.hatchery', is_enabled: true },
  { code: 'broiler', name_key: 'businessUnits.broiler', is_enabled: false },
]

const GRANTS_CARLOS = [
  { user_id: 9, code: 'grandparent', company_id: 1, granted_at: '2026-09-01T00:00:00Z', revoked_at: null, is_effective: true },
  { user_id: 9, code: 'breeder', company_id: 1, granted_at: '2026-08-01T00:00:00Z', revoked_at: '2026-08-15T00:00:00Z', is_effective: false },
]

function setSession(permissions: string[]) {
  useAuthStore.setState({
    user: {
      id: 5, username: 'ana', first_name: 'Ana', last_name: 'Díaz', email: 'ana@x.com',
      role_id: 2, view_type: 'web', is_super_admin: false,
      company_id: 1, effective_company_id: 1, permissions,
    } as any,
  })
  useCompanyStore.setState({ activeCompanyId: 1, activeCompanyName: 'Empresa Alfa', companies: [], isSwitching: false })
}

function mockApi() {
  get.mockImplementation((url: string) => {
    if (url === '/users') return Promise.resolve({ data: [CARLOS, SELF] })
    if (url === '/business-units') return Promise.resolve({ data: UNITS })
    if (/^\/users\/\d+\/business-units$/.test(url)) {
      return Promise.resolve({ data: url.includes('/9/') ? GRANTS_CARLOS : [] })
    }
    return Promise.resolve({ data: [] })
  })
  post.mockResolvedValue({ data: {} })
  del.mockResolvedValue({ data: {} })
}

beforeEach(() => {
  get.mockReset(); post.mockReset(); del.mockReset(); put.mockReset()
  toastSuccess.mockReset(); toastError.mockReset()
  setSession(['business_units:read', 'business_units:create', 'business_units:delete'])
  mockApi()
})

async function openPanel(username: string) {
  render(<ToastProvider><UsersPage /></ToastProvider>)
  const openBtn = await screen.findByRole('button', { name: `users.businessUnits.open — ${username}` })
  fireEvent.click(openBtn)
  await screen.findByText('users.businessUnits.title')
}

describe('GA-FE-02 · Panel de unidades del usuario', () => {
  it('muestra identidad, y EMPRESA vs USUARIO como estados separados (AC-UBU-02/03/04)', async () => {
    await openPanel('carlos')
    expect(screen.getByText('users.businessUnits.companyState')).toBeTruthy()
    expect(screen.getByText('users.businessUnits.userState')).toBeTruthy()

    // Empresa: broiler inactivo; el resto activo → al menos un "Activa" y un "Inactiva"
    expect(screen.getAllByText('admin.units.state.enabled').length).toBeGreaterThanOrEqual(3)
    expect(screen.getByText('admin.units.state.disabled')).toBeTruthy()

    // Usuario: grandparent concedida y efectiva; breeder revocada (histórica); dos sin concesión
    expect(screen.getByText('admin.grants.state.granted')).toBeTruthy()
    expect(screen.getByText('admin.grants.state.effective')).toBeTruthy()
    expect(screen.getByText('users.businessUnits.revokedHistoric')).toBeTruthy()
    expect(screen.getAllByText('admin.grants.state.notGranted')).toHaveLength(2)
  })

  it('conceder llama POST exacto y refetchea las concesiones (AC-UBU-05/06)', async () => {
    await openPanel('carlos')
    const broilerRow = screen.getByText('Engorde').closest('li')!
    // broiler está inactiva: sin acción de concesión (contrato 409 no se provoca)
    expect(within(broilerRow).queryByRole('button', { name: 'admin.grants.grant' })).toBeNull()

    const hatcheryRow = screen.getByText('Incubadora').closest('li')!
    fireEvent.click(within(hatcheryRow).getByRole('button', { name: 'admin.grants.grant' }))

    await waitFor(() => expect(post).toHaveBeenCalledWith('/users/9/business-units', { code: 'hatchery' }))
    expect(toastSuccess).toHaveBeenCalledWith('admin.grants.grantedSuccess')
    await waitFor(() =>
      expect(get.mock.calls.filter(([u]) => String(u) === '/users/9/business-units').length).toBeGreaterThanOrEqual(2),
    )
  })

  it('revocar pide confirmación, llama DELETE y refetchea (AC-UBU-08/09)', async () => {
    await openPanel('carlos')
    const gpRow = screen.getByText('Progenitoras').closest('li')!
    fireEvent.click(within(gpRow).getByRole('button', { name: 'admin.grants.revoke' }))

    const dialogs = await screen.findAllByRole('dialog')
    const confirm = dialogs.find(d => within(d).queryByText('admin.grants.revokeConfirmTitle'))!
    fireEvent.click(within(confirm).getByRole('button', { name: 'admin.grants.revoke' }))

    await waitFor(() => expect(del).toHaveBeenCalledWith('/users/9/business-units/grandparent'))
    expect(toastSuccess).toHaveBeenCalledWith('admin.grants.revokedSuccess')
  })

  it('sobre uno mismo: sin acción de concesión y nota visible (AC-UBU-11 UI)', async () => {
    await openPanel('ana')
    expect(screen.getByText('users.businessUnits.selfNote')).toBeTruthy()
    expect(screen.queryByRole('button', { name: 'admin.grants.grant' })).toBeNull()
  })

  it('fallo al cargar concesiones: error claro, no silencio (AC-UBU-19)', async () => {
    get.mockImplementation((url: string) => {
      if (url === '/users') return Promise.resolve({ data: [CARLOS, SELF] })
      if (url === '/business-units') return Promise.resolve({ data: UNITS })
      if (/^\/users\/\d+\/business-units$/.test(url)) return Promise.reject(new Error('boom'))
      return Promise.resolve({ data: [] })
    })
    await openPanel('carlos')
    await waitFor(() => expect(toastError).toHaveBeenCalledWith('users.businessUnits.loadError'))
  })

  it('sin business_units:read no hay entrada al panel en la tabla (AC-NAV-03)', async () => {
    setSession(['users:read'])
    render(<ToastProvider><UsersPage /></ToastProvider>)
    await screen.findAllByText('carlos')
    expect(screen.queryByRole('button', { name: /users.businessUnits.open/ })).toBeNull()
  })
})
