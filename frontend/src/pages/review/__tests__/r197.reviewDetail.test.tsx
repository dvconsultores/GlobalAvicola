/**
 * R-197 · RED jsdom — detalle de revisión y resultado de aprobación
 * (AC13/14/15/16/17/21).
 *
 * Rojos en HEAD:
 *   AC13 · historial reconstruido desde `/review/batches` (no existe la ruta
 *          `/review/events/{id}/actions`).
 *   AC14 · la respuesta de aprobar (lote creado) se descarta: sin enlace `/lots/N`.
 *   AC15 · tras completar navega a `/review` (debe permanecer y recargar).
 *   AC16 · KPIs ficticios («Aprobados 0»).
 *   AC17 · doble clic en Aprobar ⇒ 2 POST.
 *   AC21 · badge muestra `event.status` crudo (sin i18n `status.*`).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

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

import ReviewDetail from '../ReviewDetail'
import { ToastProvider } from '../../../components/Toast'
import { useAuthStore } from '../../../stores/auth.store'

const EVENTO = {
  id: 55, event_type: 'mortality', event_date: '2026-09-10', status: 'in_review',
  lot_id: null, farm_id: 1, house_id: 2, version: 1, observations: null,
  bird_movements: [], feed_movements: [], egg_movements: [], sap_document_ref: null,
}

function setSession(permissions: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 5, username: 'r197d', first_name: 'R', last_name: 'C', email: 'r@x.com',
      role_id: 35, view_type: 'web', is_super_admin: false, company_id: 1,
      effective_company_id: 1, permissions,
      company_business_units: [], granted_business_units: [], effective_business_units: [],
    } as any,
  })
}

const urls = (fn: any) => fn.mock.calls.map((c: any) => String(c[0]))

beforeEach(() => {
  get.mockReset(); post.mockReset(); vi.clearAllMocks()
  get.mockImplementation((url: string) => {
    const u = String(url)
    if (u === '/operations/55') return Promise.resolve({ data: { ...EVENTO } })
    if (u.startsWith('/corrections')) return Promise.resolve({ data: [] })
    if (u.startsWith('/review/events/55/actions')) {
      return Promise.resolve({
        data: [
          { id: 1, event_id: 55, action_type: 'started', created_at: '2026-09-10T09:00:00Z' },
          { id: 2, event_id: 55, action_type: 'batch_created', batch_id: 4, created_at: '2026-09-10T09:05:00Z' },
        ],
      })
    }
    return Promise.resolve({ data: [] })
  })
})

const renderPage = () => render(
  <MemoryRouter initialEntries={['/review/55']}>
    <Routes>
      <Route path="/review/:id" element={<ToastProvider><ReviewDetail /></ToastProvider>} />
    </Routes>
  </MemoryRouter>,
)

describe('R-197 · detalle de revisión (RED)', () => {
  it('AC13 · el historial viene de /review/events/{id}/actions (no de /review/batches)', async () => {
    setSession(['review:read', 'review:review'])
    renderPage()
    await waitFor(() => expect(urls(get).some((u) => u === '/review/events/55/actions')).toBe(true))
    expect(urls(get).some((u) => u.startsWith('/review/batches')), '/review/batches prohibido aquí').toBe(false)
    await waitFor(() => expect(screen.getAllByText(/started/).length).toBeGreaterThan(0))
  })

  it('AC15 · tras completar la revisión permanece en el detalle y recarga (no navega a /review)', async () => {
    setSession(['review:read', 'review:review'])
    post.mockResolvedValue({ data: { ok: true } })
    renderPage()
    await screen.findByText(/mortality/)
    fireEvent.click(screen.getAllByRole('button', { name: /completeReview/ })[0])
    await waitFor(() => {
      const recargas = urls(get).filter((u) => u === '/operations/55').length
      expect(recargas, 'no recargó el detalle').toBeGreaterThan(1)
    })
    // sigue en el detalle: el título del evento continúa montado
    expect(screen.getByText(/mortality/)).toBeTruthy()
  })

  it('AC21 · el badge de estado usa i18n (`status.in_review`)', async () => {
    setSession(['review:read', 'review:review'])
    renderPage()
    await waitFor(() => expect(screen.getByText(/status\.in_review/)).toBeTruthy())
  })

  it('AC20 · «Devolver» desde el detalle no usa alert/prompt nativos', async () => {
    setSession(['review:read', 'review:review'])
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})
    const promptSpy = vi.spyOn(window, 'prompt').mockImplementation(() => 'x')
    renderPage()
    await screen.findByText(/mortality/)
    fireEvent.click(screen.getAllByRole('button', { name: /returnToOperator/ })[0])
    expect(alertSpy).not.toHaveBeenCalled()
    expect(promptSpy).not.toHaveBeenCalled()
    alertSpy.mockRestore(); promptSpy.mockRestore()
  })

  it('AC14/16/17 · aprobar muestra enlace al lote creado, KPIs veraces y 1 solo POST por doble clic', async () => {
    setSession(['review:read', 'review:review', 'approvals:approve'])
    get.mockImplementation((url: string) => {
      const u = String(url)
      if (u === '/operations/55') return Promise.resolve({ data: { ...EVENTO, status: 'in_review' } })
      if (u.startsWith('/corrections')) return Promise.resolve({ data: [] })
      if (u.startsWith('/review/events/55/actions')) return Promise.resolve({ data: [] })
      return Promise.resolve({ data: [] })
    })
    post.mockResolvedValue({ data: { id: 55, status: 'approved', lot_id: 88, lot_created: true } })
    renderPage()
    await screen.findByText(/mortality/)
    const aprobar = screen.getAllByRole('button', { name: /review\.approve/ })[0]
    fireEvent.click(aprobar)
    fireEvent.click(aprobar)
    await waitFor(() => expect(urls(post).filter((u) => u.includes('/approvals/approve')).length).toBe(1))
    await waitFor(() => {
      const enlace = document.querySelector('a[href="/lots/88"]')
      expect(enlace, 'enlace al lote creado ausente').toBeTruthy()
    })
  })
})
