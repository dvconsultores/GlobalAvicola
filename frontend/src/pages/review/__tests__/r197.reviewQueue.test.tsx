/**
 * R-197 · RED jsdom — bandeja de revisión (AC05/07/18/19/20).
 *
 * Rojos en HEAD:
 *   AC05 · faltan pestañas `corrected`/`rejected`; la URL envía `operator_id` (el
 *          backend ignora ese parámetro y espera `registered_by_id`).
 *   AC07 · «Devolver» usa `prompt()` sin longitud mínima (ni en cliente).
 *   AC18 · sin `users:read` la pantalla llama igualmente a `/users`.
 *   AC19 · 403 en la carga muestra «Sin resultados» en lugar de «sin permiso».
 *   AC20 · `prompt()` nativo en pantalla de revisión.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

const get = vi.fn()
const post = vi.fn()
vi.mock('../../../services/api', () => ({
  default: {
    get: (...a: any[]) => get(...a), post: (...a: any[]) => post(...a),
    put: vi.fn(), delete: vi.fn(),
  },
}))
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (k: string, f?: any) => (typeof f === 'string' ? f : k) }),
}))
const toastError = vi.fn()
const toastSuccess = vi.fn()
vi.mock('../../../components/Toast', async (importOriginal) => {
  const actual = await importOriginal<any>()
  return { ...actual, useToast: () => ({ success: toastSuccess, error: toastError, warning: vi.fn(), info: vi.fn() }) }
})

import ReviewCenter from '../ReviewCenter'
import { ToastProvider } from '../../../components/Toast'
import { useAuthStore } from '../../../stores/auth.store'

const EVENTO = {
  id: 301, event_type: 'mortality', event_date: '2026-09-10', status: 'in_review',
  lot_id: 7, farm_id: 1, house_id: 2, registered_by_id: 9, version: 1,
}

function setSession(permissions: string[], userId = 5) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: userId, username: 'r197', first_name: 'R', last_name: 'C', email: 'r@x.com',
      role_id: 35, view_type: 'web', is_super_admin: false, company_id: 1,
      effective_company_id: 1, permissions,
      company_business_units: [], granted_business_units: [], effective_business_units: [],
    } as any,
  })
}

const urlsLlamadas = () => get.mock.calls.map((c) => String(c[0]))

beforeEach(() => {
  get.mockReset(); post.mockReset(); vi.clearAllMocks()
  get.mockImplementation((url: string) => {
    const u = String(url)
    if (u.startsWith('/review/pending')) return Promise.resolve({ data: { events: [EVENTO], total: 1 } })
    if (u.startsWith('/masters/farms')) return Promise.resolve({ data: [] })
    if (u.startsWith('/users')) return Promise.resolve({ data: [{ id: 9, username: 'operador' }] })
    return Promise.resolve({ data: [] })
  })
})

const renderPage = () => render(
  <MemoryRouter initialEntries={['/review?status=in_review']}>
    <ToastProvider><ReviewCenter /></ToastProvider>
  </MemoryRouter>,
)

describe('R-197 · bandeja de revisión (RED)', () => {
  it('AC05 · 7 pestañas (incluye corrected/rejected) y el estado activo viaja en la URL', async () => {
    setSession(['review:read', 'review:review', 'users:read'])
    renderPage()
    await waitFor(() => expect(urlsLlamadas().some((u) => u.includes('/review/pending'))).toBe(true))
    // pestañas solicitadas por el diseño C-03 (las 7 de bandeja)
    for (const etiqueta of ['Devueltos', 'Aprobados', 'Consolidados', 'Corregidos', 'Rechazados']) {
      expect(screen.getAllByRole('button', { name: new RegExp(etiqueta) }).length, etiqueta).toBeGreaterThan(0)
    }
    expect(urlsLlamadas().some((u) => u.includes('status=in_review'))).toBe(true)
  })

  it('AC18/AC04 · sin users:read: no se llama /users y el filtro de operador no existe', async () => {
    setSession(['review:read', 'review:review'])
    renderPage()
    await waitFor(() => expect(urlsLlamadas().some((u) => u.includes('/review/pending'))).toBe(true))
    expect(urlsLlamadas().filter((u) => u.startsWith('/users')).length, 'GET /users sin users:read').toBe(0)
    expect(screen.queryByText(/Operador/)).toBeNull()
  })

  it('AC04 · con users:read el filtro viaja como `registered_by_id` (no `operator_id`)', async () => {
    setSession(['review:read', 'review:review', 'users:read'])
    renderPage()
    await waitFor(() => expect(urlsLlamadas().some((u) => u.includes('/review/pending'))).toBe(true))
    const selector = await screen.findByLabelText(/Operador/) .catch(() => null)
      ?? document.querySelector('select[data-filtro="operador"]')
    expect(selector, 'selector de operador ausente').toBeTruthy()
    fireEvent.change(selector as Element, { target: { value: '9' } })
    await waitFor(() => {
      const conFiltro = urlsLlamadas().filter((u) => u.includes('registered_by_id=9'))
      expect(conFiltro.length, 'registered_by_id no viaja').toBeGreaterThan(0)
    })
    expect(urlsLlamadas().some((u) => u.includes('operator_id=')), 'operator_id prohibido').toBe(false)
  })

  it('AC07/AC20 · «Devolver» no usa prompt nativo y exige ≥10 caracteres', async () => {
    setSession(['review:read', 'review:review'])
    const promptSpy = vi.spyOn(window, 'prompt').mockReturnValue('corto')
    renderPage()
    await screen.findAllByText('mortality')
    fireEvent.click(screen.getAllByRole('button', { name: /Devolver/ })[0])

    // sin diálogo nativo
    expect(promptSpy).not.toHaveBeenCalled()
    // con observación corta no se emite POST
    const caja = await screen.findByRole('textbox', { name: /observaci/i }).catch(() => null)
    expect(caja, 'campo de observaciones ausente').toBeTruthy()
    fireEvent.change(caja as Element, { target: { value: 'corto' } })
    fireEvent.click(screen.getByRole('button', { name: 'Confirmar' }))
    expect(post.mock.calls.filter((c) => String(c[0]).includes('/review/return')).length).toBe(0)
    promptSpy.mockRestore()
  })

  it('AC19 · 403 en la carga ⇒ mensaje de permiso (no «Sin resultados»)', async () => {
    setSession(['review:read', 'review:review'])
    get.mockImplementation((url: string) => {
      const u = String(url)
      if (u.startsWith('/review/pending')) {
        return Promise.reject({ response: { status: 403, data: { detail: 'Forbidden' } } })
      }
      return Promise.resolve({ data: [] })
    })
    renderPage()
    await waitFor(() => expect(screen.getByText(/review\.noPermissionQueue/)).toBeTruthy())
    expect(screen.queryByText('common.noResults')).toBeNull()
  })
})
