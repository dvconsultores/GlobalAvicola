/**
 * AR-23 · RED jsdom — bucle de redirección infinito `/` ⇄ `/menu/poultry`.
 *
 * Un usuario SIN `dashboard:read` y SIN hub «poultry» alcanzable (p. ej. rol con solo
 * {audit:read, lots:read} y ninguna unidad productiva efectiva) rebotaba entre las dos
 * rutas: `HomeRoute` enviaba a `/menu/poultry` y `MenuHubPage` —fail-closed— devolvía a `/`,
 * ~300 navegaciones por segundo con `<main>` vacío. Rojo en HEAD previo: `HomeRoute` redirige
 * siempre y no hay ningún aviso neutro (`role="status"` con `home.noLanding`).
 *
 * Montaje/mocks tomados de `r212.permissionAwareness.test.tsx` (mismo `setSession`, mismo
 * mock de `DashboardPage` y de i18n: `t(k)` devuelve la clave).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { useEffect } from 'react'
import { MemoryRouter, Routes, Route, useLocation } from 'react-router-dom'

vi.mock('../services/api', () => ({
  default: {
    get: vi.fn(), post: vi.fn(), put: vi.fn(), patch: vi.fn(), delete: vi.fn(),
  },
}))
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (k: string, f?: any) => (typeof f === 'string' ? f : k), i18n: { language: 'es' } }),
}))
// `App` importa el bootstrap de i18n; en jsdom se sustituye (no aporta conducta bajo prueba).
vi.mock('../i18n', () => ({}))
vi.mock('../components/Toast', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() }),
  getErrorMessage: (_e: any, f: string) => f,
}))
vi.mock('../pages/dashboard/DashboardPage', () => ({ default: () => <div>DASHBOARD-MOCK</div> }))
// Colateral no relacionado con AR-23: el árbol de trazabilidad espera props que este
// harness no sirve; se aisla (su contrato tiene sus propias pruebas).
vi.mock('../components/TraceabilityTree', () => ({ TraceabilityTree: () => null }))

import MenuHubPage from '../pages/operations/MenuHubPage'
import { HomeRoute } from '../App'
import { useAuthStore } from '../stores/auth.store'
/**
 * Espía de navegación: cuenta cada cambio de `location.key`. Un bucle de redirección lo
 * dispara cientos de veces por segundo; una navegación legítima, una o dos.
 *
 * El bucle es síncrono (efectos de `<Navigate>` encadenados), así que AHOGA los timers: si
 * se dejara correr, la espera de abajo nunca vencería y la prueba colgaría en vez de fallar.
 * El tope duro convierte el bucle en un fallo inmediato y legible.
 */
let navCount = 0

const NAV_LIMITE = 20

function Spy() {
  const { key } = useLocation()
  useEffect(() => { navCount += 1 }, [key])
  if (navCount > NAV_LIMITE) throw new Error(`bucle de redirección: ${navCount} navegaciones`)
  return null
}

function setSession(permissions: string[], units: string[] = []) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 7, username: 'ar23', first_name: 'A', last_name: 'R', email: 'ar23@x.com',
      role_id: 36, view_type: 'web', is_super_admin: false, company_id: 1,
      effective_company_id: 1, permissions,
      company_business_units: [], granted_business_units: units, effective_business_units: units,
    } as any,
  })
}

const ESPERA_MS = 300
const esperar = () => new Promise((r) => setTimeout(r, ESPERA_MS))

beforeEach(() => {
  navCount = 0
  useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false, token: null })
})
describe('AR-23 · home sin `dashboard:read` y sin hub alcanzable (no bucle)', () => {
  it('AC-AR23-01 · sesión {audit:read, lots:read} sin unidades: aviso neutro, sin bucle', async () => {
    // Sin `dashboard:read` y sin unidad productiva efectiva, la raíz `poultry` no sobrevive
    // al filtro canónico: es exactamente la sesión que hacía ping-pong con `MenuHubPage`.
    setSession(['audit:read', 'lots:read'])
    render(
      <MemoryRouter initialEntries={['/']}>
        <Spy />
        <Routes>
          <Route path="/" element={<HomeRoute />} />
          <Route path="/menu/:menuKey" element={<MenuHubPage />} />
        </Routes>
      </MemoryRouter>,
    )

    await esperar()

    expect(navCount, 'bucle de redirección / ⇄ /menu/poultry').toBeLessThanOrEqual(3)
    const aviso = screen.getByRole('status')
    expect(aviso.textContent).toBe('home.noLanding')
    expect(screen.queryByText('DASHBOARD-MOCK')).toBeNull()
  }, 5000)
  it('AC-AR23-02 · con `operations:read` y unidad: sigue yendo al hub (sin cambio)', async () => {
    setSession(['operations:read'], ['broiler'])
    render(
      <MemoryRouter initialEntries={['/']}>
        <Spy />
        <Routes>
          <Route path="/" element={<HomeRoute />} />
          <Route path="/menu/poultry" element={<div>HUB-POULTRY</div>} />
        </Routes>
      </MemoryRouter>,
    )

    expect(await screen.findByText('HUB-POULTRY')).toBeTruthy()
    expect(screen.queryByText('DASHBOARD-MOCK')).toBeNull()
    expect(screen.queryByRole('status')).toBeNull()
    expect(navCount).toBeLessThanOrEqual(3)
  })

  it('AC-AR23-03 · con `dashboard:read` se pinta el dashboard (sin cambio)', async () => {
    setSession(['dashboard:read'])
    render(
      <MemoryRouter initialEntries={['/']}>
        <Spy />
        <Routes>
          <Route path="/" element={<HomeRoute />} />
          <Route path="/menu/poultry" element={<div>HUB-POULTRY</div>} />
        </Routes>
      </MemoryRouter>,
    )

    expect(await screen.findByText('DASHBOARD-MOCK')).toBeTruthy()
    expect(screen.queryByText('HUB-POULTRY')).toBeNull()
    expect(screen.queryByRole('status')).toBeNull()
  })
})



