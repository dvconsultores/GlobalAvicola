/**
 * QA-Yolinel · GREEN de regresión — `MasterListPage`: columna del padre (`QA-012`) y
 * estado explícito de la fila con sus acciones (`QA-002`).
 *
 * Cubre lo que la sesión de QA dio por bueno en pantalla:
 *   (a) en `houses`, la columna del padre pinta el NOMBRE de la granja, nunca el `farm_id`;
 *   (b) una fila con `is_active:false` se rotula «Inactivo» y ofrece Reactivar (no Desactivar);
 *   (c) una fila activa ofrece Desactivar (no Reactivar).
 *
 * El mock de `useTranslation` devuelve el fallback: los textos son los de respaldo en
 * español que la pantalla declara (`t('common.inactive', 'Inactivo')`).
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

if (!window.matchMedia) {
  // jsdom no implementa matchMedia; `SearchSelect` lo consulta al montar.
  // @ts-expect-error polyfill de prueba
  window.matchMedia = (q: string) => ({
    matches: false, media: q, onchange: null,
    addEventListener: () => {}, removeEventListener: () => {},
    addListener: () => {}, removeListener: () => {}, dispatchEvent: () => false,
  })
}
if (!Element.prototype.scrollIntoView) Element.prototype.scrollIntoView = () => {}

import MasterListPage from '../MasterListPage'
import { useAuthStore } from '../../../stores/auth.store'

const COLS_NAME = [{ key: 'name', labelKey: 'masters.fields.name' }]

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

/** Enrutado del mock por prefijo: `/masters/houses` antes que `/masters/farms`. */
function servir(rutas: Record<string, any[]>) {
  get.mockImplementation((url: string) => {
    const u = String(url)
    for (const [prefijo, filas] of Object.entries(rutas)) {
      if (u.startsWith(prefijo)) {
        return Promise.resolve({ data: filas, headers: { 'x-total-count': String(filas.length) } })
      }
    }
    return Promise.resolve({ data: [], headers: {} })
  })
}

const montar = (entity: string) => render(
  <MemoryRouter>
    <MasterListPage entity={entity} titleKey={`masters.${entity}`} columns={COLS_NAME} />
  </MemoryRouter>,
)

beforeEach(() => {
  get.mockReset(); post.mockReset(); put.mockReset(); del.mockReset()
  useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false, token: null })
})

describe('QA-Yolinel · MasterListPage — padre y estado de la fila', () => {
  it('(a) houses: la columna del padre muestra el nombre de la granja', async () => {
    setSession(['masters:read', 'masters:update', 'masters:delete'])
    servir({
      '/masters/houses': [{ id: 1, name: 'G1', farm_id: 7, is_active: true }],
      '/masters/farms': [{ id: 7, name: 'Granja Norte', is_active: true }],
    })
    montar('houses')

    await waitFor(() => expect(screen.getByText('G1')).toBeTruthy())
    // `QA-012`: id→nombre con la lista completa del padre (una granja inactiva también resuelve).
    expect(await screen.findByText('Granja Norte')).toBeTruthy()
  })

  it('(b) farms inactiva: «Inactivo», Reactivar disponible y sin Desactivar', async () => {
    setSession(['masters:read', 'masters:update', 'masters:delete'])
    servir({
      '/masters/farms': [{ id: 3, name: 'Granja Sur', is_active: false }],
    })
    const { container } = montar('farms')

    await waitFor(() => expect(screen.getByText('Granja Sur')).toBeTruthy())
    expect(screen.getByText('Inactivo')).toBeTruthy()
    expect(await screen.findByRole('button', { name: 'Reactivar' })).toBeTruthy()
    expect(screen.queryByRole('button', { name: 'Desactivar' })).toBeNull()
    // La fila dada de baja se atenúa para no confundirse con una vigente.
    await waitFor(() =>
      expect(container.querySelector('tbody tr')?.className).toContain('opacity-60'))
  })

  it('(c) farms activa: Desactivar disponible y sin Reactivar', async () => {
    setSession(['masters:read', 'masters:update', 'masters:delete'])
    servir({
      '/masters/farms': [{ id: 4, name: 'Granja Este', is_active: true }],
    })
    montar('farms')

    await waitFor(() => expect(screen.getByText('Granja Este')).toBeTruthy())
    expect(screen.getByText('Activo')).toBeTruthy()
    expect(await screen.findByRole('button', { name: 'Desactivar' })).toBeTruthy()
    expect(screen.queryByRole('button', { name: 'Reactivar' })).toBeNull()
  })
})
