/**
 * GA-FE-04 · RED — MasterListPage (AC-FE16 en su superficie de origen: maestros).
 * R (`masters:read`): ve filas, NO ve «Nuevo» ni Editar/Eliminar.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

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
vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (k: string, f?: string) => f ?? k }) }))

import MasterListPage from '../MasterListPage'
import { useAuthStore } from '../../../stores/auth.store'

const ROWS = [{ id: 1, name: 'Granja Uno', code: 'G1', location: 'L' }]

function setSession(permissions: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 99, username: 'probe', first_name: 'P', last_name: 'Q', email: 'p@x.com',
      role_id: 3, view_type: 'web', is_super_admin: false, company_id: 1, effective_company_id: 1,
      permissions,
      company_business_units: [], granted_business_units: [], effective_business_units: [],
    } as any,
  })
}

beforeEach(() => {
  get.mockReset()
  get.mockImplementation((url: string) => {
    if (String(url).startsWith('/masters/')) return Promise.resolve({ data: ROWS, headers: { 'x-total-count': '1' } })
    return Promise.resolve({ data: [] })
  })
})

describe('GA-FE-04 · MasterListPage — autoridad de acción', () => {
  it('R (masters:read): sin Nuevo/Editar/Eliminar', async () => {
    setSession(['masters:read'])
    render(
      <MemoryRouter>
        <MasterListPage entity="farms" titleKey="masters.farms" columns={[{ key: 'name', labelKey: 'masters.farms' }]} searchFields={['name']} />
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getByText('Granja Uno')).toBeTruthy())
    expect(screen.queryByText('Nuevo')).toBeNull()
    expect(screen.queryByText('common.edit')).toBeNull()
    expect(screen.queryByText('common.delete')).toBeNull()
  })

  it('control: con masters:* los controles aparecen', async () => {
    setSession(['masters:read', 'masters:create', 'masters:update', 'masters:delete'])
    render(
      <MemoryRouter>
        <MasterListPage entity="farms" titleKey="masters.farms" columns={[{ key: 'name', labelKey: 'masters.farms' }]} searchFields={['name']} />
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getByText('Granja Uno')).toBeTruthy())
    expect(screen.getAllByText('Nuevo').length).toBeGreaterThan(0)
    expect(screen.getAllByText('common.edit').length).toBeGreaterThan(0)
    expect(screen.getAllByText('common.delete').length).toBeGreaterThan(0)
  })
})
