/**
 * GA-FE-03 · RED comportamental — MenuHub (`D-2`) contra el estado actual.
 *
 * Hoy `MenuHubPage` consume `NAV_ITEMS` CRUDOS (`findNavItem` sobre el árbol sin filtrar):
 * D (sin `business_units:read`) ve la tarjeta «Acceso por unidad»; Z (cero unidades) ve las
 * cuatro unidades productivas. El objetivo es que el hub evalúe el MISMO árbol filtrado que el
 * Sidebar y que una raíz no visible redirija a home.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (k: string, f?: string) => f ?? k }),
}))

import MenuHubPage from '../MenuHubPage'
import { useAuthStore } from '../../../stores/auth.store'

function setSession(permissions: string[], effective: string[], enabled: string[], isSuper = false) {
  useAuthStore.setState({
    isAuthenticated: true,
    isLoading: false,
    token: null,
    user: {
      id: 9, username: 'tester', first_name: 'T', last_name: 'T', email: 't@x.com',
      role_id: 99, view_type: 'web', is_super_admin: isSuper,
      company_id: 1, effective_company_id: 1,
      permissions,
      company_business_units: enabled,
      granted_business_units: effective,
      effective_business_units: effective,
    } as any,
  })
}

function renderHub(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/menu/:menuKey" element={<MenuHubPage />} />
        <Route path="/" element={<div>HOME-STUB</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false, token: null })
})

describe('GA-FE-03 · MenuHub obedece la misma política (§34, NAV-AC07/44)', () => {
  it('D (dashboard:read) NO ve la tarjeta «Acceso por unidad» en /menu/settings', () => {
    setSession(['dashboard:read'], [], ['grandparent', 'breeder', 'hatchery', 'broiler'])
    renderHub('/menu/settings')
    expect(screen.queryByText('Acceso por unidad')).toBeNull()
    expect(screen.queryByText('Usuarios y Roles')).toBeNull()
    expect(screen.getByText('Mi Perfil')).toBeTruthy()
  })

  it('Z (cero unidades) no ve unidades productivas en /menu/poultry (raíz no visible → home)', () => {
    setSession(['dashboard:read'], [], ['grandparent', 'breeder', 'hatchery', 'broiler'])
    renderHub('/menu/poultry')
    expect(screen.queryByText('Progenitoras')).toBeNull()
    expect(screen.queryByText('Incubadora')).toBeNull()
    expect(screen.getByText('HOME-STUB')).toBeTruthy()
  })

  it('C con broiler ve la unidad concedida en /menu/poultry', () => {
    setSession(['operations:read', 'lots:read'], ['broiler'], ['grandparent', 'breeder', 'hatchery', 'broiler'])
    renderHub('/menu/poultry')
    expect(screen.getByText('Pollo de Engorde')).toBeTruthy()
    expect(screen.queryByText('Progenitoras')).toBeNull()
  })

  it('B (Access Admin) sí ve su tarjeta en /menu/settings', () => {
    setSession(
      ['business_units:read', 'business_units:update', 'business_units:create', 'business_units:delete'],
      [], [],
    )
    renderHub('/menu/settings')
    expect(screen.getByText('Acceso por unidad')).toBeTruthy()
    expect(screen.queryByText('Usuarios y Roles')).toBeNull()
  })
})
