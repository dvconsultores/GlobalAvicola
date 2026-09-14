/**
 * R-207 · RED jsdom — superficie de reverso: solicitar, seguir y mostrar.
 *
 * Rojos en HEAD:
 *   AC-R207-01 · no existe la acción «Solicitar reverso» en el detalle (gate `reversals:create`).
 *   AC-R207-02 · no hay modal ni POST `/reversals`; sin contrapartida enlazada.
 *   AC-R207-03 · `reversed` cae al gris de fallback (sin mapa/color propio) y `statusColors` no lo declara.
 *   AC-R207-04 · solicitar con motivo <5: sin validación de cliente (no existe el flujo).
 *
 * Contrato (SPEC §11/§19): `POST /reversals {event_id, reason}` ⇒ `ReversalRead`
 * (`reversal_event_id` = contrapartida). Gate `reversals:create`; motivo ≥5; 409/400 legibles.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

const get = vi.fn()
const post = vi.fn()
vi.mock('../../../services/api', () => ({
  default: {
    get: (...a: any[]) => get(...a),
    post: (...a: any[]) => post(...a),
    put: vi.fn(), patch: vi.fn(), delete: vi.fn(),
  },
}))
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (k: string, f?: any) => (typeof f === 'string' ? f : k) }),
}))
const toastError = vi.fn()
const toastSuccess = vi.fn()
vi.mock('../../../components/Toast', () => ({
  useToast: () => ({ success: toastSuccess, error: toastError, warning: vi.fn(), info: vi.fn() }),
  getErrorMessage: (_e: any, f: string) => f,
}))
vi.mock('../../../../src/components/operations/WeightEvaluation', () => ({ default: () => null }))

import OperationDetailPage from '../OperationDetailPage'
import { useAuthStore } from '../../../stores/auth.store'
import { STATUS_STYLES } from '../../../data/statusColors'

function baseEvent(status: string, extra: Record<string, any> = {}) {
  return {
    id: 700, lot_id: 1, event_type: 'weight_recording', event_date: '2026-09-11',
    status, company_id: 1, registered_by_id: 1, version: 1, observations: null,
    bird_movements: [], feed_movements: [], egg_movements: [], evidences: [],
    ...extra,
  }
}

function setSession(permissions: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 9, username: 'r207-c', first_name: 'R', last_name: 'C', email: 'c@x.com',
      role_id: 1, view_type: 'web', is_super_admin: false, company_id: 1, effective_company_id: 1,
      permissions, company_business_units: ['broiler'], granted_business_units: ['broiler'],
      effective_business_units: ['broiler'],
    } as any,
  })
}

const renderPage = () =>
  render(
    <MemoryRouter initialEntries={['/operations/700']}>
      <Routes>
        <Route path="/operations/:id" element={<OperationDetailPage />} />
      </Routes>
    </MemoryRouter>,
  )

const solicitarBtn = () => screen.queryByRole('button', { name: /Solicitar reverso/ })
const esperarDetalle = () => screen.findByText(/operations\.eventDetail/)

beforeEach(() => {
  get.mockReset(); post.mockReset(); toastError.mockReset(); toastSuccess.mockReset()
  useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false, token: null })
})

describe('R-207 · superficie de reverso (RED)', () => {
  it('AC-R207-01 · «Solicitar reverso» visible solo con `reversals:create` (evento approved)', async () => {
    setSession(['operations:read'])
    get.mockResolvedValue({ data: baseEvent('approved') })
    const primera = renderPage()
    await esperarDetalle()
    expect(solicitarBtn(), 'sin permiso no debe ofrecerse la acción').toBeNull()
    primera.unmount()

    setSession(['operations:read', 'reversals:create'])
    get.mockReset()
    get.mockResolvedValue({ data: baseEvent('approved') })
    renderPage()
    await esperarDetalle()
    expect(solicitarBtn(), 'con permiso el botón debe existir').not.toBeNull()
  })

  it('AC-R207-02 · solicitar con motivo ≥5 ⇒ POST /reversals y contrapartida enlazada', async () => {
    setSession(['operations:read', 'reversals:create'])
    get.mockResolvedValue({ data: baseEvent('approved') })
    post.mockResolvedValue({
      data: { id: 88, original_event_id: 700, reversal_event_id: 912, status: 'pending_review' },
    })
    renderPage()
    await esperarDetalle()
    fireEvent.click(solicitarBtn() as Element)

    const motivo = await screen.findByRole('textbox', { name: /Motivo/i })
    fireEvent.change(motivo, { target: { value: 'Necesito neutralizar el registro erróneo' } })
    fireEvent.click(screen.getByRole('button', { name: 'Confirmar' }))

    await waitFor(() => {
      const llamadas = post.mock.calls.filter((c) => String(c[0]).includes('/reversals'))
      expect(llamadas.length, 'POST /reversals ausente').toBe(1)
      expect(llamadas[0][1]).toEqual({
        event_id: 700, reason: 'Necesito neutralizar el registro erróneo',
      })
    })
    // Contrapartida visible y enlazada (`reversal_event_id`).
    await waitFor(() => {
      expect(document.querySelector('a[href="/operations/912"]'), 'enlace a la contrapartida').toBeTruthy()
    })
  })

  it('AC-R207-03 · evento `reversed`: badge con estilo propio (no el gris de fallback) y mapa central', async () => {
    const central = (STATUS_STYLES as any)['reversed']
    expect(central, 'STATUS_STYLES sin `reversed`').toBeTruthy()

    setSession(['operations:read'])
    get.mockResolvedValue({ data: baseEvent('reversed') })
    renderPage()
    await esperarDetalle()
    const badge = screen.getByText('reversed')
    expect(badge.className, 'badge `reversed` en gris de fallback').not.toMatch(/bg-slate-100/)
  })

  it('AC-R207-04 · motivo <5 ⇒ sin POST y aviso visible (validación de cliente)', async () => {
    setSession(['operations:read', 'reversals:create'])
    get.mockResolvedValue({ data: baseEvent('approved') })
    renderPage()
    await esperarDetalle()
    fireEvent.click(solicitarBtn() as Element)

    const motivo = await screen.findByRole('textbox', { name: /Motivo/i })
    fireEvent.change(motivo, { target: { value: 'ok' } })
    fireEvent.click(screen.getByRole('button', { name: 'Confirmar' }))

    expect(post.mock.calls.filter((c) => String(c[0]).includes('/reversals')).length,
      'no debe emitirse POST con motivo corto').toBe(0)
    expect(screen.getByRole('alert'), 'aviso de motivo corto ausente').toBeTruthy()
  })
})
