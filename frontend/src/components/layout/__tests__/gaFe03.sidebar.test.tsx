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
  it('D (dashboard:read): sin admin/productivo; CORE y Configuración presentes; sin grupos vacíos', () => {
    setSession(['dashboard:read'], [], ['grandparent', 'breeder', 'hatchery', 'broiler'])
    renderSidebar()
    expect(screen.getByText('Dashboard')).toBeTruthy()
    expect(screen.getByText('Configuración')).toBeTruthy()
    for (const texto of [
      'Gestión Avícola', 'Centro de Revisión', 'Aprobaciones', 'Integración SAP',
      'Reportes', 'Auditoría', 'Maestros', 'Usuarios y Roles', 'OPERATIVO', 'REVISIÓN',
    ]) {
      expect(screen.queryByText(texto), `no debe verse: ${texto}`).toBeNull()
    }
  })

  it('Z (cero unidades): el área operativa desaparece; Configuración permanece', () => {
    setSession(['dashboard:read'], [], ['grandparent', 'breeder', 'hatchery', 'broiler'])
    renderSidebar()
    expect(screen.queryByText('Gestión Avícola')).toBeNull()
    expect(screen.queryByText('OPERATIVO')).toBeNull()
    expect(screen.getByText('Configuración')).toBeTruthy()
    expect(screen.getByText('Dashboard')).toBeTruthy()
  })

  it('C con broiler: el área operativa aparece (hub) y el resto no', () => {
    setSession(['operations:read', 'lots:read'], ['broiler'], ['grandparent', 'breeder', 'hatchery', 'broiler'])
    renderSidebar()
    expect(screen.getByText('Gestión Avícola')).toBeTruthy()
    expect(screen.queryByText('Centro de Revisión')).toBeNull()
    expect(screen.queryByText('Auditoría')).toBeNull()
    expect(screen.queryByText('Integración SAP')).toBeNull()
    expect(screen.queryByText('Reportes')).toBeNull()
  })

  it('B (Access Admin): descubre Configuración; sin productivo, sin dashboard (D-4), sin admin ajeno', () => {
    setSession(
      ['business_units:read', 'business_units:update', 'business_units:create', 'business_units:delete'],
      [], [],
    )
    renderSidebar()
    expect(screen.getByText('Configuración')).toBeTruthy()
    expect(screen.queryByText('Dashboard')).toBeNull()
    expect(screen.queryByText('Gestión Avícola')).toBeNull()
    expect(screen.queryByText('Auditoría')).toBeNull()
    expect(screen.queryByText('Maestros')).toBeNull()
    expect(screen.queryByText('Integración SAP')).toBeNull()
  })

  it('A (CBU Admin): CORE + Configuración; sin planos ajenos', () => {
    setSession(['business_units:read', 'business_units:update', 'dashboard:read'], [], [])
    renderSidebar()
    expect(screen.getByText('Dashboard')).toBeTruthy()
    expect(screen.getByText('Configuración')).toBeTruthy()
    expect(screen.queryByText('Auditoría')).toBeNull()
    expect(screen.queryByText('Maestros')).toBeNull()
    expect(screen.queryByText('Gestión Avícola')).toBeNull()
  })
})
