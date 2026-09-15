/**
 * R-220 · B7 (F §2.b) — RED: el encabezado de `/poultry` (ProcessHubPage) muestra el
 * contador de procesos FIJO en «6» aunque la sesión vea un subconjunto de procesos
 * (filtro GA-FE-03 §33). Debe ser dinámico: nº de etapas visibles.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (k: string, f?: string) => f ?? k }),
}))

import ProcessHubPage from '../pages/operations/ProcessHubPage'
import { useAuthStore } from '../stores/auth.store'

function setSession(permissions: string[], effective: string[]) {
  useAuthStore.setState({
    isAuthenticated: true,
    isLoading: false,
    token: null,
    user: {
      id: 9, username: 'tester', first_name: 'T', last_name: 'T', email: 't@x.com',
      role_id: 99, view_type: 'web', is_super_admin: false,
      company_id: 1, effective_company_id: 1,
      permissions,
      company_business_units: ['grandparent', 'breeder', 'hatchery', 'broiler'],
      granted_business_units: effective,
      effective_business_units: effective,
    } as any,
  })
}

function renderHub() {
  return render(
    <MemoryRouter initialEntries={['/poultry']}>
      <Routes>
        <Route path="/poultry" element={<ProcessHubPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false, token: null })
})

describe('R-220 · B7 · contador de procesos dinámico en /poultry', () => {
  it('muestra el número de procesos VISIBLES, no un 6 fijo', () => {
    setSession(['operations:read'], ['broiler'])
    renderHub()
    expect(screen.getAllByRole('link').length).toBe(1) // solo la etapa autorizada
    const etiqueta = screen.getByText('Procesos')
    expect(etiqueta.previousElementSibling?.textContent).toBe('1')
  })

  it('con visibilidad completa sigue mostrando el total real (control)', () => {
    setSession(['operations:read'], ['grandparent', 'breeder', 'hatchery', 'broiler'])
    renderHub()
    const etiqueta = screen.getByText('Procesos')
    expect(etiqueta.previousElementSibling?.textContent).toBe(String(screen.getAllByRole('link').length))
  })
})
