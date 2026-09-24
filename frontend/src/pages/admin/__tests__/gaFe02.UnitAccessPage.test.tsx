/**
 * GA-FE-02 · Página «Acceso por unidad» — RED de la superficie ausente (AC-CBU, AC-UBU, AC-COMP).
 *
 * Contratos ejercitados (exactos, `GA_FE_02_BACKEND_CONTRACT_MATRIX.md`):
 *   GET   /business-units                            → las cuatro unidades con estado
 *   PATCH /business-units/{code}/enable|disable      → mutación + refetch (reconciliación)
 *   GET   /business-units/{code}/grant-candidates    → candidatos (solo con unidad habilitada)
 *   POST  /users/{id}/business-units {code}          → conceder
 *   DELETE/users/{id}/business-units/{code}          → revocar
 *
 * Reglas duras: habilitar NO concede (ninguna llamada de concesión) · sin empresa → fail-closed ·
 * unidad OFF → sin candidatos (409 del contrato no se provoca) · sin permiso → sin acciones.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, within, act } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

const get = vi.fn()
const patch = vi.fn()
const post = vi.fn()
const del = vi.fn()

vi.mock('../../../services/api', () => ({
  default: {
    get: (...a: any[]) => get(...a),
    patch: (...a: any[]) => patch(...a),
    post: (...a: any[]) => post(...a),
    delete: (...a: any[]) => del(...a),
  },
}))

const toastSuccess = vi.fn()
const toastError = vi.fn()
vi.mock('../../../components/Toast', () => ({
  useToast: () => ({ success: toastSuccess, error: toastError, warning: vi.fn(), info: vi.fn() }),
  getErrorMessage: (_e: any, fallback: string) => fallback,
}))

vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (k: string, f?: string) => f ?? k }),
}))

import UnitAccessPage from '../UnitAccessPage'
import { useAuthStore } from '../../../stores/auth.store'
import { useCompanyStore } from '../../../stores/company.store'

const ALL_PERMS = ['business_units:read', 'business_units:update', 'business_units:create', 'business_units:delete']

const UNITS = [
  { code: 'grandparent', name_key: 'businessUnits.grandparent', is_enabled: true },
  { code: 'breeder', name_key: 'businessUnits.breeder', is_enabled: false },
  { code: 'hatchery', name_key: 'businessUnits.hatchery', is_enabled: true },
  { code: 'broiler', name_key: 'businessUnits.broiler', is_enabled: false },
]

const CANDIDATES = [
  { user_id: 9, username: 'carlos', display_name: 'Carlos Ruiz', already_granted: false },
  { user_id: 10, username: 'lucia', display_name: 'Lucía Márquez', already_granted: true },
]

function setSession(permissions: string[] = ALL_PERMS, effectiveCompanyId: number | null = 1) {
  useAuthStore.setState({
    user: {
      id: 5, username: 'ana', first_name: 'Ana', last_name: 'Díaz', email: 'a@x.com',
      role_id: 2, view_type: 'web', is_super_admin: false,
      company_id: 1, effective_company_id: effectiveCompanyId,
      permissions,
    } as any,
  })
  useCompanyStore.setState({
    activeCompanyId: effectiveCompanyId,
    activeCompanyName: effectiveCompanyId ? 'Empresa Alfa' : null,
    companies: [],
    isSwitching: false,
  })
}

function mockApi() {
  get.mockImplementation((url: string) => {
    if (url === '/business-units') return Promise.resolve({ data: UNITS })
    if (String(url).endsWith('/grant-candidates')) return Promise.resolve({ data: CANDIDATES })
    return Promise.resolve({ data: [] })
  })
  patch.mockResolvedValue({ data: {} })
  post.mockResolvedValue({ data: {} })
  del.mockResolvedValue({ data: {} })
}

beforeEach(() => {
  get.mockReset(); patch.mockReset(); post.mockReset(); del.mockReset()
  toastSuccess.mockReset(); toastError.mockReset()
  setSession()
  mockApi()
})

function unitCard(name: string) {
  const list = screen.getByRole('list', { name: 'admin.units.heading' })
  return within(list).getByText(name).closest('li')!
}

async function renderReady() {
  render(<MemoryRouter><UnitAccessPage /></MemoryRouter>)
  await screen.findByRole('list', { name: 'admin.units.heading' })
}

async function confirmDialog(confirmLabel: string) {
  const dialog = await screen.findByRole('dialog')
  fireEvent.click(within(dialog).getByRole('button', { name: confirmLabel }))
}

describe('GA-FE-02 · Acceso por unidad — render', () => {
  it('muestra las CUATRO unidades canónicas con estados mixtos independientes (AC-CBU-02/03)', async () => {
    await renderReady()
    const cards = screen.getByRole('list', { name: 'admin.units.heading' })
    for (const n of ['Progenitoras', 'Reproductoras', 'Incubadora', 'Engorde']) {
      expect(within(cards).getByText(n)).toBeTruthy()
    }
    expect(screen.getAllByText('admin.units.state.enabled')).toHaveLength(2)
    expect(screen.getAllByText('admin.units.state.disabled')).toHaveLength(2)
  })

  it('sin empresa efectiva: fail-closed, sin ninguna llamada (AC-COMP-06, OD-14.d)', async () => {
    setSession(ALL_PERMS, null)
    render(<MemoryRouter><UnitAccessPage /></MemoryRouter>)
    await screen.findByText('admin.context.none')
    expect(screen.getByText('admin.context.noneHint')).toBeTruthy()
    expect(get).not.toHaveBeenCalled()
  })

  it('muestra la empresa efectiva en el contexto (AC-COMP-01)', async () => {
    await renderReady()
    expect(screen.getByText('Empresa Alfa')).toBeTruthy()
  })
})

describe('GA-FE-02 · Acceso por unidad — mutaciones', () => {
  it('habilitar llama PATCH enable, refetchea y confirma éxito (AC-CBU-04/06)', async () => {
    await renderReady()
    const card = unitCard('Reproductoras')
    fireEvent.click(within(card).getByRole('button', { name: 'admin.units.enable' }))
    await confirmDialog('admin.units.enable')

    await waitFor(() => expect(patch).toHaveBeenCalledWith('/business-units/breeder/enable'))
    await waitFor(() => expect(get.mock.calls.filter(([u]) => u === '/business-units').length).toBeGreaterThanOrEqual(2))
    expect(toastSuccess).toHaveBeenCalledWith('admin.units.enabledSuccess')
  })

  it('deshabilitar pide confirmación y llama PATCH disable (AC-CBU-05)', async () => {
    await renderReady()
    const card = unitCard('Incubadora')
    fireEvent.click(within(card).getByRole('button', { name: 'admin.units.disable' }))
    await confirmDialog('admin.units.disable')

    await waitFor(() => expect(patch).toHaveBeenCalledWith('/business-units/hatchery/disable'))
    expect(toastSuccess).toHaveBeenCalledWith('admin.units.disabledSuccess')
  })

  it('habilitar NO dispara ninguna llamada de concesión (AC-CBU-08)', async () => {
    await renderReady()
    const card = unitCard('Reproductoras')
    fireEvent.click(within(card).getByRole('button', { name: 'admin.units.enable' }))
    await confirmDialog('admin.units.enable')
    await waitFor(() => expect(patch).toHaveBeenCalled())
    expect(post).not.toHaveBeenCalled()
    expect(del).not.toHaveBeenCalled()
  })

  it('fallo de mutación: error + reconciliación con refetch, sin falso éxito (AC-CBU-15)', async () => {
    patch.mockRejectedValue(new Error('boom'))
    await renderReady()
    const card = unitCard('Reproductoras')
    fireEvent.click(within(card).getByRole('button', { name: 'admin.units.enable' }))
    await confirmDialog('admin.units.enable')

    await waitFor(() => expect(toastError).toHaveBeenCalledWith('admin.units.saveError'))
    expect(toastSuccess).not.toHaveBeenCalled()
    await waitFor(() => expect(get.mock.calls.filter(([u]) => u === '/business-units').length).toBeGreaterThanOrEqual(2))
  })

  it('sin business_units:update: sin acciones de mutación (AC-CBU-12)', async () => {
    setSession(['business_units:read'])
    await renderReady()
    expect(screen.queryByRole('button', { name: 'admin.units.enable' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'admin.units.disable' })).toBeNull()
  })
})

describe('GA-FE-02 · Acceso por unidad — concesiones', () => {
  async function selectUnit(value: string) {
    const select = await screen.findByLabelText('admin.grants.unitLabel')
    fireEvent.change(select, { target: { value } })
  }

  it('unidad deshabilitada: aviso y SIN llamada a candidatos (contrato 409 evitado)', async () => {
    await renderReady()
    await selectUnit('breeder')
    await screen.findByText('admin.grants.unitDisabledNotice')
    expect(get.mock.calls.some(([u]) => String(u).includes('grant-candidates'))).toBe(false)
  })

  it('unidad habilitada: candidatos con estado y acciones por permiso (AC-UBU-05)', async () => {
    await renderReady()
    await selectUnit('grandparent')
    await screen.findByText('carlos')
    expect(screen.getByText('Lucía Márquez')).toBeTruthy()
    expect(screen.getByText('admin.grants.state.notGranted')).toBeTruthy()
    expect(screen.getByText('admin.grants.state.granted')).toBeTruthy()
    // carlos: no concedida → Conceder; lucia: concedida → Revocar
    const carlosRow = screen.getByText('carlos').closest('li')!
    const luciaRow = screen.getByText('lucia').closest('li')!
    expect(within(carlosRow).getByRole('button', { name: 'admin.grants.grant' })).toBeTruthy()
    expect(within(luciaRow).getByRole('button', { name: 'admin.grants.revoke' })).toBeTruthy()
  })

  it('conceder llama POST /users/{id}/business-units {code} y refetchea (AC-UBU-05/06)', async () => {
    await renderReady()
    await selectUnit('grandparent')
    await screen.findByText('carlos')
    const carlosRow = screen.getByText('carlos').closest('li')!
    fireEvent.click(within(carlosRow).getByRole('button', { name: 'admin.grants.grant' }))

    await waitFor(() => expect(post).toHaveBeenCalledWith('/users/9/business-units', { code: 'grandparent' }))
    expect(toastSuccess).toHaveBeenCalledWith('admin.grants.grantedSuccess')
    await waitFor(() =>
      expect(get.mock.calls.filter(([u]) => String(u).endsWith('/grant-candidates')).length).toBeGreaterThanOrEqual(2),
    )
  })

  it('revocar pide confirmación y llama DELETE con code (AC-UBU-08/09)', async () => {
    await renderReady()
    await selectUnit('grandparent')
    await screen.findByText('lucia')
    const luciaRow = screen.getByText('lucia').closest('li')!
    fireEvent.click(within(luciaRow).getByRole('button', { name: 'admin.grants.revoke' }))
    await confirmDialog('admin.grants.revoke')

    await waitFor(() => expect(del).toHaveBeenCalledWith('/users/10/business-units/grandparent'))
    expect(toastSuccess).toHaveBeenCalledWith('admin.grants.revokedSuccess')
  })

  it('sin business_units:create|delete: sin botones de concesión (AC-UBU-13 UI)', async () => {
    setSession(['business_units:read', 'business_units:update'])
    await renderReady()
    await selectUnit('grandparent')
    await screen.findByText('carlos')
    expect(screen.queryByRole('button', { name: 'admin.grants.grant' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'admin.grants.revoke' })).toBeNull()
  })

  it('el actor (self) no gestiona concesiones desde esta lista si apareciera (AC-UBU-11 UI)', async () => {
    // El contrato excluye al actor de los candidatos; si el backend lo devolviera por error,
    // la UI no debe ofrecer acciones sobre self.
    get.mockImplementation((url: string) => {
      if (url === '/business-units') return Promise.resolve({ data: UNITS })
      if (String(url).endsWith('/grant-candidates'))
        return Promise.resolve({ data: [{ user_id: 5, username: 'ana', display_name: 'Ana Díaz', already_granted: false }] })
      return Promise.resolve({ data: [] })
    })
    await renderReady()
    await selectUnit('grandparent')
    await screen.findByText('ana')
    const selfRow = screen.getByText('ana').closest('li')!
    expect(within(selfRow).queryByRole('button', { name: 'admin.grants.grant' })).toBeNull()
  })
})

describe('GA-FE-02 · Acceso por unidad — cambio de empresa', () => {
  it('al cambiar la empresa refetchea y limpia la selección (AC-COMP-04/05)', async () => {
    await renderReady()
    const select = await screen.findByLabelText('admin.grants.unitLabel')
    fireEvent.change(select, { target: { value: 'grandparent' } })
    await screen.findByText('carlos')
    const candidateCallsBefore = get.mock.calls.filter(([u]) => String(u).endsWith('/grant-candidates')).length

    act(() => {
      // El cambio de empresa real pasa por `switchCompany` → `fetchMe`: la sesión queda con
      // el nuevo `effective_company_id` y la tienda de empresa refleja el nombre elegido.
      const u: any = useAuthStore.getState().user
      useAuthStore.setState({ user: { ...u, effective_company_id: 2 } })
      useCompanyStore.setState({ activeCompanyId: 2, activeCompanyName: 'Empresa Beta' })
    })

    await waitFor(() => expect(get.mock.calls.filter(([u]) => u === '/business-units').length).toBeGreaterThanOrEqual(2))
    // La selección se limpia: no se piden candidatos de la empresa anterior
    await waitFor(() => {
      const candidateCallsAfter = get.mock.calls.filter(([u]) => String(u).endsWith('/grant-candidates')).length
      expect(candidateCallsAfter).toBe(candidateCallsBefore)
    })
    expect((screen.getByLabelText('admin.grants.unitLabel') as HTMLSelectElement).value).toBe('')
  })
})
