/**
 * GA-FE-03 · RED comportamental — barra inferior móvil (paridad semántica §35).
 *
 * Hoy `MobileNav` hardcodea Operativo/Home/KPI sin evaluación. Con cero unidades (Z) la
 * entrada productiva no debe existir tampoco en móvil; sin permiso `dashboard:read` no debe
 * aparecer Home/KPI (D-4 sigue documentado en la página, no en la barra).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (k: string, f?: string) => f ?? k }),
}))

import MobileNav from '../MobileNav'
import { useAuthStore } from '../../../stores/auth.store'

function setSession(permissions: string[], effective: string[], enabled: string[]) {
  useAuthStore.setState({
    isAuthenticated: true,
    isLoading: false,
    token: null,
    user: {
      id: 9, username: 'tester', first_name: 'T', last_name: 'T', email: 't@x.com',
      role_id: 99, view_type: 'mobile', is_super_admin: false,
      company_id: 1, effective_company_id: 1,
      permissions,
      company_business_units: enabled,
      granted_business_units: effective,
      effective_business_units: effective,
    } as any,
  })
}

beforeEach(() => {
  useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false, token: null })
})

describe('GA-FE-03 · MobileNav derivada del evaluador', () => {
  it('Z: sin Operativo; Home y KPI presentes', () => {
    setSession(['dashboard:read'], [], ['grandparent', 'breeder', 'hatchery', 'broiler'])
    render(<MemoryRouter><MobileNav /></MemoryRouter>)
    expect(screen.queryByText('Gestión Avícola')).toBeNull()
    expect(document.querySelector('a[href="/menu/poultry"]')).toBeNull()
    expect(screen.getByText('Home')).toBeTruthy()
    expect(screen.getByText('KPI')).toBeTruthy()
  })

  it('C con broiler: Operativo presente (misma semántica que desktop)', () => {
    setSession(['operations:read', 'lots:read'], ['broiler'], ['broiler'])
    render(<MemoryRouter><MobileNav /></MemoryRouter>)
    expect(screen.getByText('Gestión Avícola')).toBeTruthy()
  })

  it('sin dashboard:read (B) la barra no ofrece Home/KPI', () => {
    setSession(['business_units:read'], [], [])
    render(<MemoryRouter><MobileNav /></MemoryRouter>)
    expect(screen.queryByText('Home')).toBeNull()
    expect(screen.queryByText('KPI')).toBeNull()
  })
})
