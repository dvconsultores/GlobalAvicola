/**
 * R-220 · B1/B2 (F G-03/G-04, R1/R2) — RED:
 * · B1: en web <1024px no hay sidebar (`hidden lg:flex`) NI hamburguesa ⇒ sin navegación.
 * · B2: la cabecera móvil (`lg:hidden`) no ofrece logout ni perfil.
 *
 * Corrección esperada: hamburguesa que monta `MobileDrawer` (patrón ya construido,
 * D3) y acciones de perfil/logout en la cabecera móvil.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, within, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (k: string, f?: string) => f ?? k, i18n: { resolvedLanguage: 'es', language: 'es', changeLanguage: vi.fn() } }),
  initReactI18next: { type: '3rdParty', init: vi.fn() },
}))

vi.mock('../components/notifications/NotificationBell', () => ({
  default: () => <div data-testid="bell-stub" />,
}))

import Header from '../components/layout/Header'
import { useAuthStore } from '../stores/auth.store'

function setSession(viewType: 'web' | 'mobile' = 'web') {
  useAuthStore.setState({
    isAuthenticated: true,
    isLoading: false,
    token: null,
    user: {
      id: 9, username: 'tester', first_name: 'T', last_name: 'T', email: 't@x.com',
      role_id: 99, view_type: viewType, is_super_admin: false,
      company_id: 1, effective_company_id: 1,
      company_name: 'Avícola Test',
      permissions: ['operations:read', 'dashboard:read'],
      company_business_units: ['grandparent', 'breeder', 'hatchery', 'broiler'],
      granted_business_units: ['broiler'],
      effective_business_units: ['broiler'],
    } as any,
  })
}

function renderHeader() {
  return render(
    <MemoryRouter initialEntries={['/']}>
      <Routes>
        <Route path="/" element={<Header />} />
        <Route path="/profile" element={<div>PROFILE-STUB</div>} />
        <Route path="/operations" element={<div>OPS-STUB</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

/** La cabecera móvil es el segundo `<header>` (el primero es la de escritorio). */
function mobileHeader() {
  const banners = screen.getAllByRole('banner')
  expect(banners.length).toBeGreaterThanOrEqual(2)
  return banners[banners.length - 1]
}

beforeEach(() => {
  useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false, token: null })
})

describe('R-220 · B1/B2 · navegación <1024px y acciones de cabecera móvil', () => {
  it('B1 · existe hamburguesa y monta el drawer al pulsarla', async () => {
    setSession('web')
    renderHeader()
    const btn = screen.getByRole('button', { name: /Men[uú]/ })
    expect(btn.getAttribute('aria-expanded')).toBe('false')
    fireEvent.click(btn)
    await waitFor(() => {
      expect(document.querySelector('nav[data-state]')?.getAttribute('data-state')).toBe('open')
    })
  })

  it('B2 · la cabecera móvil ofrece logout', () => {
    setSession('mobile')
    renderHeader()
    within(mobileHeader()).getByRole('button', { name: /auth\.logout|Cerrar sesión/ })
  })

  it('B2 · la cabecera móvil ofrece perfil y navega a /profile', async () => {
    setSession('mobile')
    renderHeader()
    const perfil = within(mobileHeader()).getByRole('button', { name: /Mi Perfil|nav\.profile/ })
    fireEvent.click(perfil)
    expect(await screen.findByText('PROFILE-STUB')).toBeTruthy()
  })
})
