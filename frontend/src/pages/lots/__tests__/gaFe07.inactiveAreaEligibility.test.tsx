/**
 * GA-FE-07 · RED — selector de Área: solo áreas activas (OD-21, R-185).
 *
 * La decisión del propietario establece que un maestro dado de baja lógica no puede
 * usarse para NUEVAS referencias: el selector transaccional del formulario de lote
 * no debe ofrecer áreas inactivas. La administración de maestros NO se toca.
 *
 * Estado pre-fix (RED): el selector incluye la inactiva ⇒ este archivo falla.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent, within } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

const get = vi.fn()
vi.mock('../../../services/api', () => ({
  default: {
    get: (...a: any[]) => get(...a),
    post: vi.fn(), put: vi.fn(), patch: vi.fn(), delete: vi.fn(),
  },
}))
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (k: string, f?: any) => (typeof f === 'string' ? f : k) }),
}))
vi.mock('../../../components/Toast', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() }),
  getErrorMessage: (_e: any, f: string) => f,
}))

import LotFormPage from '../LotFormPage'
import { useAuthStore } from '../../../stores/auth.store'

const AREAS = [
  { id: 6, name: 'Nave Activa GA-FE-07', is_active: true },
  { id: 7, name: 'Nave Histórica GA-FE-07', is_active: false },
  { id: 8, name: 'Nave Retirada GA-FE-07', is_active: false },
]

beforeEach(() => {
  get.mockReset()
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 124, username: 'ga7.operador', first_name: 'G', last_name: 'O', email: 'g@x.com',
      role_id: 57, view_type: 'web', is_super_admin: false, company_id: 1, effective_company_id: 1,
      permissions: ['dashboard:read', 'lots:read', 'lots:create', 'masters:read'],
      company_business_units: ['broiler'], granted_business_units: ['broiler'],
      effective_business_units: ['broiler'],
    } as any,
  })
  get.mockImplementation((url: string) => {
    const u = String(url)
    if (u.startsWith('/masters/areas')) return Promise.resolve({ data: AREAS })
    if (u.startsWith('/masters/farms')) return Promise.resolve({ data: [{ id: 1, name: 'Granja Uno' }] })
    if (u.startsWith('/masters/')) return Promise.resolve({ data: [] })
    return Promise.resolve({ data: [] })
  })
})

describe('GA-FE-07 · selector de área — elegibilidad por estado (RED)', () => {
  it('la inactiva no se ofrece; la activa sí (filtro de selección)', async () => {
    render(
      <MemoryRouter initialEntries={['/lots/new']}>
        <Routes><Route path="/lots/new" element={<LotFormPage />} /></Routes>
      </MemoryRouter>,
    )
    const sel = await screen.findByLabelText('Área')
    await waitFor(() => expect(within(sel).getByText('Nave Activa GA-FE-07')).toBeTruthy())

    // Objetivo (falla pre-fix): las inactivas no deben aparecer como opción.
    expect(within(sel).queryByText('Nave Histórica GA-FE-07')).toBeNull()
    expect(within(sel).queryByText('Nave Retirada GA-FE-07')).toBeNull()
    // Control positivo: la activa sí está y es seleccionable.
    fireEvent.change(sel, { target: { value: '6' } })
    expect((sel as HTMLSelectElement).value).toBe('6')
  })

  it('control · el API sí devuelve las inactivas (el filtro es del selector, no de los datos)', async () => {
    render(
      <MemoryRouter initialEntries={['/lots/new']}>
        <Routes><Route path="/lots/new" element={<LotFormPage />} /></Routes>
      </MemoryRouter>,
    )
    await screen.findByLabelText('Área')
    await waitFor(() => expect(get).toHaveBeenCalledWith('/masters/areas?limit=100'))
    // Los datos crudos conservan las inactivas (administración aparte); aquí solo
    // verificamos que la fuente las incluye para que el filtro sea significativo.
    expect(AREAS.filter(a => !a.is_active).length).toBe(2)
  })
})
