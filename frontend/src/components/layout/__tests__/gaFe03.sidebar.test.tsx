/**
 * GA-FE-03 · RED comportamental — Sidebar contra el estado actual.
 *
 * Hoy el Sidebar solo filtra las entradas que declaran `permission` (una): D ve Auditoría,
 * Maestros, SAP, Reportes, Revisión, Aprobaciones, Usuarios; Z ve las cuatro unidades. El
 * objetivo es la política completa (RBAC + BU + contexto) con grupos vacíos ocultos.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (k: string, f?: string) => f ?? k }),
}))

import Sidebar from '../Sidebar'
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

function renderSidebar() {
  return render(<MemoryRouter><Sidebar /></MemoryRouter>)
}

beforeEach(() => {
  useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false, token: null })
})

describe('GA-FE-03 · Sidebar derivado del evaluador canónico (§23)', () => {
  it('D (dashboard:read): sin admin/productivo; CORE y perfil presentes; sin grupos vacíos', () => {
    setSession(['dashboard:read'], [], ['grandparent', 'breeder', 'hatchery', 'broiler'])
    renderSidebar()
    for (const texto of [
      'Usuarios y Roles', 'Auditoría', 'Maestros', 'Integración SAP',
      'Reportes', 'Centro de Revisión', 'Aprobaciones', 'Gestión Avícola',
    ]) {
      expect(screen.queryByText(texto), `no debe verse: ${texto}`).toBeNull()
    }
    expect(screen.getByText('Mi Perfil')).toBeTruthy()
    expect(screen.queryByText('OPERATIVO')).toBeNull()
    expect(screen.queryByText('REVISIÓN')).toBeNull()
  })

  it('Z (cero unidades): el área operativa desaparece; Configuración permanece', () => {
    setSession(['dashboard:read'], [], ['grandparent', 'breeder', 'hatchery', 'broiler'])
    renderSidebar()
    expect(screen.queryByText('Gestión Avícola')).toBeNull()
    expect(screen.getByText('Configuración')).toBeTruthy()
    expect(screen.getByText('Mi Perfil')).toBeTruthy()
  })

  it('C con broiler: el área operativa aparece (hub) y el resto no', () => {
    setSession(['operations:read', 'lots:read'], ['broiler'], ['grandparent', 'breeder', 'hatchery', 'broiler'])
    renderSidebar()
    expect(screen.getByText('Gestión Avícola')).toBeTruthy()
    expect(screen.queryByText('Centro de Revisión')).toBeNull()
  })

  it('B (Access Admin): descubre su superficie; sin productivo ni usuarios', () => {
    setSession(
      ['business_units:read', 'business_units:update', 'business_units:create', 'business_units:delete'],
      [], [],
    )
    renderSidebar()
    expect(screen.getByText('Acceso por unidad')).toBeTruthy()
    expect(screen.queryByText('Usuarios y Roles')).toBeNull()
    expect(screen.queryByText('Gestión Avícola')).toBeNull()
  })

  it('A (CBU Admin): igual separación de planos', () => {
    setSession(['business_units:read', 'business_units:update', 'dashboard:read'], [], [])
    renderSidebar()
    expect(screen.getByText('Acceso por unidad')).toBeTruthy()
    expect(screen.queryByText('Usuarios y Roles')).toBeNull()
    expect(screen.queryByText('Auditoría')).toBeNull()
    expect(screen.queryByText('Gestión Avícola')).toBeNull()
  })
})
