/**
 * GA-FE-05 · RED — R-181: envío/reenvío a revisión en el detalle de operación.
 *
 * Contrato canónico (verificado en código):
 *   POST /operations/{id}/submit · permiso operations:create · respuesta OperationalEventRead
 *   reenviables: registered | returned | rejected  ->  pending_review · 400 en otro estado
 *   guarda operativa (CBU/unidad): 403
 *
 * CTA esperado: «Enviar a revisión» (registered) · «Reenviar a revisión» (returned/rejected),
 * visible ⇔ permiso ∧ unidad disponible ∧ estado reenviable; tras éxito: GET fresco + CTA
 * recomputado; fallo: sin éxito falso y reconciliación por GET.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
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

function baseEvent(status: string) {
  return {
    id: 55, lot_id: 1, event_type: 'weight_recording', event_date: '2026-09-11',
    status, company_id: 1, registered_by_id: 1, version: 1, observations: null,
    bird_movements: [], feed_movements: [], egg_movements: [], evidences: [],
  }
}

function setSession(permissions: string[], effectiveUnits: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 9, username: 'ga05-c', first_name: 'GA', last_name: 'C', email: 'c@x.com',
      role_id: 1, view_type: 'web', is_super_admin: false, company_id: 1, effective_company_id: 1,
      permissions, company_business_units: ['broiler'], granted_business_units: effectiveUnits,
      effective_business_units: effectiveUnits,
    } as any,
  })
}

const renderPage = () =>
  render(
    <MemoryRouter initialEntries={['/operations/55']}>
      <Routes>
        <Route path="/operations/:id" element={<OperationDetailPage />} />
      </Routes>
    </MemoryRouter>,
  )

const submitBtn = () => screen.queryByRole('button', { name: 'Enviar a revisión' })
const resubmitBtn = () => screen.queryByRole('button', { name: 'Reenviar a revisión' })

beforeEach(() => {
  get.mockReset(); post.mockReset(); toastError.mockReset(); toastSuccess.mockReset()
  useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false, token: null })
})

describe('GA-FE-05 · R-181 · CTA de envío/reenvío por estado (RED)', () => {
  it('registered + operations:create + unidad ⇒ «Enviar a revisión» visible', async () => {
    setSession(['operations:read', 'operations:create'], ['broiler'])
    get.mockResolvedValue({ data: baseEvent('registered') })
    renderPage()
    await waitFor(() => expect(screen.getByText(/weight_recording/)).toBeTruthy())
    expect(submitBtn()).not.toBeNull()
  })

  it('un clic ⇒ una mutación + GET fresco + estado actualizado y CTA desaparece', async () => {
    setSession(['operations:read', 'operations:create'], ['broiler'])
    get.mockResolvedValueOnce({ data: baseEvent('registered') })
      .mockResolvedValue({ data: baseEvent('pending_review') })
    post.mockResolvedValue({ data: baseEvent('pending_review') })
    renderPage()
    await waitFor(() => expect(submitBtn()).not.toBeNull())
    submitBtn()!.click()
    await waitFor(() => expect(post).toHaveBeenCalledTimes(1))
    expect(String(post.mock.calls[0][0])).toBe('/operations/55/submit')
    await waitFor(() => expect(submitBtn()).toBeNull())
    expect(get.mock.calls.length).toBeGreaterThanOrEqual(2)
  })

  it('returned ⇒ «Reenviar a revisión» visible', async () => {
    setSession(['operations:read', 'operations:create'], ['broiler'])
    get.mockResolvedValue({ data: baseEvent('returned') })
    renderPage()
    await waitFor(() => expect(screen.getByText(/weight_recording/)).toBeTruthy())
    expect(resubmitBtn()).not.toBeNull()
    expect(submitBtn()).toBeNull()
  })

  it('rejected ⇒ «Reenviar a revisión» visible (no terminal, OD-17.a)', async () => {
    setSession(['operations:read', 'operations:create'], ['broiler'])
    get.mockResolvedValue({ data: baseEvent('rejected') })
    renderPage()
    await waitFor(() => expect(screen.getByText(/weight_recording/)).toBeTruthy())
    expect(resubmitBtn()).not.toBeNull()
  })

  it('pending_review ⇒ sin CTA', async () => {
    setSession(['operations:read', 'operations:create'], ['broiler'])
    get.mockResolvedValue({ data: baseEvent('pending_review') })
    renderPage()
    await waitFor(() => expect(screen.getByText(/weight_recording/)).toBeTruthy())
    expect(submitBtn()).toBeNull()
    expect(resubmitBtn()).toBeNull()
  })

  it('approved ⇒ sin CTA (final inmutable)', async () => {
    setSession(['operations:read', 'operations:create'], ['broiler'])
    get.mockResolvedValue({ data: baseEvent('approved') })
    renderPage()
    await waitFor(() => expect(screen.getByText(/weight_recording/)).toBeTruthy())
    expect(submitBtn()).toBeNull()
    expect(resubmitBtn()).toBeNull()
  })

  it('sin operations:create ⇒ sin CTA aunque el estado sea reenviable', async () => {
    setSession(['operations:read'], ['broiler'])
    get.mockResolvedValue({ data: baseEvent('registered') })
    renderPage()
    await waitFor(() => expect(screen.getByText(/weight_recording/)).toBeTruthy())
    expect(submitBtn()).toBeNull()
  })

  it('cero unidades efectivas ⇒ sin CTA aunque haya permiso (fail-closed)', async () => {
    setSession(['operations:read', 'operations:create'], [])
    get.mockResolvedValue({ data: baseEvent('registered') })
    renderPage()
    await waitFor(() => expect(screen.getByText(/weight_recording/)).toBeTruthy())
    expect(submitBtn()).toBeNull()
  })

  it('doble clic ⇒ una sola mutación (loading deshabilita)', async () => {
    setSession(['operations:read', 'operations:create'], ['broiler'])
    get.mockResolvedValueOnce({ data: baseEvent('registered') })
      .mockResolvedValue({ data: baseEvent('pending_review') })
    let resolvePost: (v: any) => void = () => {}
    post.mockImplementation(() => new Promise(r => { resolvePost = r }))
    renderPage()
    await waitFor(() => expect(submitBtn()).not.toBeNull())
    submitBtn()!.click(); submitBtn()!.click()
    expect(post).toHaveBeenCalledTimes(1)
    resolvePost({ data: baseEvent('pending_review') })
    await waitFor(() => expect(submitBtn()).toBeNull())
  })

  it('fallo (403) ⇒ sin éxito falso + error + reconciliación por GET', async () => {
    setSession(['operations:read', 'operations:create'], ['broiler'])
    get.mockResolvedValue({ data: baseEvent('registered') })
    post.mockRejectedValue({ response: { status: 403 } })
    renderPage()
    await waitFor(() => expect(submitBtn()).not.toBeNull())
    const getsBefore = get.mock.calls.length
    submitBtn()!.click()
    await waitFor(() => expect(post).toHaveBeenCalledTimes(1))
    await waitFor(() => expect(toastError).toHaveBeenCalled())
    expect(toastSuccess).not.toHaveBeenCalled()
    await waitFor(() => expect(get.mock.calls.length).toBeGreaterThan(getsBefore))
    expect(submitBtn()).not.toBeNull()
  })
})
