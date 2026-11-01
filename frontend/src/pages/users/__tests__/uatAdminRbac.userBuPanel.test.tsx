/**
 * SPEC 013 · UAT Admin/RBAC · Lote F1 — panel «Unidades de negocio» del usuario.
 *
 * AC-UI-01 (`AR-13`/Y-1.2): «Revocar» abre un `ConfirmDialog` que, al vivir en un portal sobre
 * `document.body` con `z-[60]`, queda POR ENCIMA del `Modal` (z-50) y su confirmación revoca.
 * AC-UI-02 (`AR-14`/Y-3.2): por unidad se resuelve la concesión VIVA si existe; si no, la
 * revocada MÁS RECIENTE. Tras re-conceder se ve «Concedida» + «Efectiva» y se ofrece «Revocar».
 * AC-UI-03 (`AR-15`/Y-1.1): el panel rotula EMPRESA (con su nombre) y USUARIO (nombre + login).
 * AC-UI-04 (`AR-16`/Y-3.1): la confirmación de revocar nombra al usuario y a la unidad.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'

const get = vi.fn()
const post = vi.fn()
const del = vi.fn()

vi.mock('../../../services/api', () => ({
  default: {
    get: (...a: any[]) => get(...a),
    post: (...a: any[]) => post(...a),
    delete: (...a: any[]) => del(...a),
    put: (...a: any[]) => post(...a),
  },
}))

const toastSuccess = vi.fn()
const toastError = vi.fn()
vi.mock('../../../components/Toast', () => ({
  useToast: () => ({ success: toastSuccess, error: toastError, warning: vi.fn(), info: vi.fn() }),
  getErrorMessage: (_e: any, fallback: string) => fallback,
  ToastProvider: ({ children }: any) => children,
}))

// i18n: el segundo argumento puede ser un fallback (string) o variables de interpolación.
// El mock conserva el comportamiento previo para strings y expone las variables para poder
// afirmar que la confirmación nombra usuario y unidad (AC-UI-04).
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, arg?: unknown) => {
      if (typeof arg === 'string') return arg
      if (arg && typeof arg === 'object') {
        const values = Object.entries(arg as Record<string, unknown>)
          .map(([k, v]) => `${k}=${String(v)}`)
          .join(' · ')
        return `${key} [${values}]`
      }
      return key
    },
  }),
}))

import { ToastProvider } from '../../../components/Toast'
import UserBusinessUnitsButton from '../UserBusinessUnitsButton'
import { useAuthStore } from '../../../stores/auth.store'
import { useCompanyStore } from '../../../stores/company.store'

const CARLOS = {
  id: 9, username: 'carlos', first_name: 'Carlos', last_name: 'Ruiz',
  email: 'c@x.com', role_id: 1, view_type: 'web', is_active: true,
}

const UNITS = [
  { code: 'grandparent', name_key: 'businessUnits.grandparent', is_enabled: true },
  { code: 'breeder', name_key: 'businessUnits.breeder', is_enabled: true },
  { code: 'hatchery', name_key: 'businessUnits.hatchery', is_enabled: true },
  { code: 'broiler', name_key: 'businessUnits.broiler', is_enabled: true },
]

// Historia real del backend tras revocar y volver a conceder: DOS filas para el mismo código,
// ordenadas por id (la revocada es la más antigua). `stateFor` debe elegir la VIVA.
const GRANTS_CARLOS = [
  { user_id: 9, code: 'grandparent', company_id: 1, granted_at: '2026-09-01T00:00:00Z', revoked_at: null, is_effective: true },
  { user_id: 9, code: 'breeder', company_id: 1, granted_at: '2026-08-01T00:00:00Z', revoked_at: '2026-08-10T00:00:00Z', is_effective: false },
  { user_id: 9, code: 'breeder', company_id: 1, granted_at: '2026-09-20T00:00:00Z', revoked_at: null, is_effective: true },
  { user_id: 9, code: 'hatchery', company_id: 1, granted_at: '2026-07-01T00:00:00Z', revoked_at: '2026-07-05T00:00:00Z', is_effective: false },
]

function setSession() {
  useAuthStore.setState({
    user: {
      id: 5, username: 'ana', first_name: 'Ana', last_name: 'Díaz', email: 'ana@x.com',
      role_id: 2, view_type: 'web', is_super_admin: false,
      company_id: 1, effective_company_id: 1,
      permissions: ['business_units:read', 'business_units:create', 'business_units:delete'],
    } as any,
  })
  useCompanyStore.setState({ activeCompanyId: 1, activeCompanyName: 'Empresa Alfa', companies: [], isSwitching: false })
}

function mockApi() {
  get.mockImplementation((url: string) => {
    if (url === '/business-units') return Promise.resolve({ data: UNITS })
    if (/^\/users\/\d+\/business-units$/.test(url)) return Promise.resolve({ data: GRANTS_CARLOS })
    return Promise.resolve({ data: [] })
  })
  post.mockResolvedValue({ data: {} })
  del.mockResolvedValue({ data: {} })
}

beforeEach(() => {
  get.mockReset(); post.mockReset(); del.mockReset()
  toastSuccess.mockReset(); toastError.mockReset()
  setSession()
  mockApi()
})

async function openPanel() {
  render(<ToastProvider><UserBusinessUnitsButton user={CARLOS} /></ToastProvider>)
  fireEvent.click(await screen.findByRole('button', { name: `users.businessUnits.open — carlos` }))
  await screen.findByText('users.businessUnits.title')
}

function rowOf(unitName: string): HTMLElement {
  return screen.getByText(unitName).closest('li') as HTMLElement
}

describe('SPEC 013 · Lote F1 · panel de unidades del usuario', () => {
  it('AC-UI-01: «Revocar» abre la confirmación en un portal sobre el modal y revoca (AR-13)', async () => {
    await openPanel()
    fireEvent.click(within(rowOf('Progenitoras')).getByRole('button', { name: 'admin.grants.revoke' }))

    const dialogs = await screen.findAllByRole('dialog')
    const confirm = dialogs.find(d => within(d).queryByText('admin.grants.revokeConfirmTitle'))
    expect(confirm, 'el diálogo de confirmación debe abrirse').toBeTruthy()
    const panel = dialogs.find(d => d !== confirm) as HTMLElement
    // Portal: la confirmación NO está anidada dentro del Modal (ese anidamiento la dejaba debajo)
    expect(panel.contains(confirm as HTMLElement)).toBe(false)

    let root = confirm as HTMLElement
    while (root.parentElement && root.parentElement !== document.body) root = root.parentElement
    expect(root.parentElement).toBe(document.body)
    expect(root.className).toContain('z-[60]')

    fireEvent.click(within(confirm as HTMLElement).getByRole('button', { name: 'admin.grants.revoke' }))
    await waitFor(() => expect(del).toHaveBeenCalledWith('/users/9/business-units/grandparent'))
    expect(toastSuccess).toHaveBeenCalledWith('admin.grants.revokedSuccess')
  })

  it('AC-UI-02: con historia + concesión viva se resuelve la VIVA (AR-14)', async () => {
    await openPanel()

    // breeder: revocada antigua (id menor) + viva reciente ⇒ Concedida + Efectiva + Revocar
    const breeder = rowOf('Reproductoras')
    expect(within(breeder).getByText('admin.grants.state.granted')).toBeTruthy()
    expect(within(breeder).getByText('admin.grants.state.effective')).toBeTruthy()
    expect(within(breeder).getByRole('button', { name: 'admin.grants.revoke' })).toBeTruthy()
    expect(within(breeder).queryByText('users.businessUnits.revokedHistoric')).toBeNull()
    expect(within(breeder).queryByRole('button', { name: 'admin.grants.grant' })).toBeNull()

    // hatchery: SOLO la revocada ⇒ Revocada (histórica) + Conceder
    const hatchery = rowOf('Incubadora')
    expect(within(hatchery).getByText('users.businessUnits.revokedHistoric')).toBeTruthy()
    expect(within(hatchery).getByRole('button', { name: 'admin.grants.grant' })).toBeTruthy()
    expect(within(hatchery).queryByText('admin.grants.state.granted')).toBeNull()

    // broiler: sin concesión ⇒ No concedida + Conceder
    const broiler = rowOf('Engorde')
    expect(within(broiler).getByText('admin.grants.state.notGranted')).toBeTruthy()
  })

  it('AC-UI-03: el panel identifica EMPRESA (nombre) y USUARIO (nombre + login) (AR-15)', async () => {
    await openPanel()
    // La línea descriptiva del Modal lleva rótulo + valor de empresa y de usuario
    expect(screen.getByText(/users\.businessUnits\.companyLabel/)).toBeTruthy()
    expect(screen.getByText(/users\.businessUnits\.userLabel/)).toBeTruthy()
    expect(screen.getByText(/Empresa Alfa/)).toBeTruthy()
    expect(screen.getByText(/Carlos Ruiz \(carlos\)/)).toBeTruthy()
    // Los rótulos de las dos columnas de ESTADO siguen siendo estados, no identidades
    expect(screen.getByText('users.businessUnits.companyState')).toBeTruthy()
    expect(screen.getByText('users.businessUnits.userState')).toBeTruthy()
  })

  it('AC-UI-04: la confirmación de revocar nombra al usuario y a la unidad (AR-16)', async () => {
    await openPanel()
    fireEvent.click(within(rowOf('Progenitoras')).getByRole('button', { name: 'admin.grants.revoke' }))

    const dialogs = await screen.findAllByRole('dialog')
    const confirm = dialogs.find(d => within(d).queryByText('admin.grants.revokeConfirmTitle'))!
    const message = within(confirm).getByText(/admin\.grants\.revokeConfirmMessage/)
    expect(message.textContent).toMatch(/Carlos Ruiz \(carlos\)/)
    expect(message.textContent).toMatch(/Progenitoras/)
  })
})
