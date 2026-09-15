/**
 * R-220 · B6 (F G-20) — RED: `ProcessStagePage` pinta tiles (grid) y timeline
 * (secuencia) que navegan a `/operations/new` — ruta con gate `operations:create` —
 * aunque la sesión solo tenga `operations:read` ⇒ callejón sin salida.
 *
 * Corrección esperada: sin autoridad de ACCIÓN (`operations:create`) los tiles se
 * pintan read-only y la timeline no ofrece «Registrar operación». La página sigue
 * legible (operaciones:read). Control: con `operations:create` el flujo sigue vivo.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (k: string, f?: string) => f ?? k }),
}))

import ProcessStagePage from '../pages/operations/ProcessStagePage'
import { useAuthStore } from '../stores/auth.store'

function setSession(permissions: string[]) {
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
      granted_business_units: ['broiler'],
      effective_business_units: ['broiler'],
    } as any,
  })
}

function renderStage() {
  return render(
    <MemoryRouter initialEntries={['/poultry/broiler']}>
      <Routes>
        <Route path="/poultry/:stage" element={<ProcessStagePage />} />
        <Route path="/operations/new" element={<div>FORM-STUB</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

function expandirPrimerPaso() {
  fireEvent.click(screen.getByRole('button', { name: /Secuencia/ }))
  const tarjetas = screen.getAllByRole('button').filter((b) => b.getAttribute('aria-expanded') !== null)
  expect(tarjetas.length).toBeGreaterThan(0)
  fireEvent.click(tarjetas[0])
}

beforeEach(() => {
  useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false, token: null })
})

describe('R-220 · B6 · sin operations:create no hay callejón hacia /operations/new', () => {
  it('solo-lectura: el grid no renderiza enlaces al formulario de operación', () => {
    setSession(['operations:read'])
    const { container } = renderStage()
    expect(container.querySelectorAll('a[href^="/operations/new"]').length).toBe(0)
  })

  it('solo-lectura: la vista Secuencia no ofrece «Registrar operación»', () => {
    setSession(['operations:read'])
    renderStage()
    expandirPrimerPaso()
    expect(screen.queryByRole('button', { name: /Registrar operación/ })).toBeNull()
  })

  it('con operations:create el flujo de registro sigue disponible (control)', () => {
    setSession(['operations:read', 'operations:create'])
    const { container } = renderStage()
    expect(container.querySelectorAll('a[href^="/operations/new"]').length).toBeGreaterThan(0)
    expandirPrimerPaso()
    expect(screen.getByRole('button', { name: /Registrar operación/ })).toBeTruthy()
  })
})
