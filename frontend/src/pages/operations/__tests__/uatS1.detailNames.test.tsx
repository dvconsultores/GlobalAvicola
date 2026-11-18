/**
 * F3 · AC-S1-I01 — los detalles muestran NOMBRES (`lot_code`/`farm_name`/`house_name`)
 * y no ids crudos («Lote #138»).
 *
 * Contrato backend ya implementado:
 *  - `GET /operations/{id}` ⇒ `lot_code`, `farm_name`, `house_name`.
 *  - `GET /lots/{id}` ⇒ `farm_name`, `house_name`.
 * Fallback: si el nombre no viene, se conserva el id (`#138`, `7`, `3`).
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
  useTranslation: () => ({ t: (k: string, f?: any) => (typeof f === 'string' ? f : k), i18n: { language: 'es' } }),
}))
const toastError = vi.fn()
vi.mock('../../../components/Toast', async (importOriginal) => {
  const actual = await importOriginal<any>()
  return { ...actual, useToast: () => ({ success: vi.fn(), error: toastError, warning: vi.fn(), info: vi.fn() }) }
})
vi.mock('../../../../src/components/operations/WeightEvaluation', () => ({ default: () => null }))

import OperationDetailPage from '../OperationDetailPage'
import ReviewDetail from '../../review/ReviewDetail'
import { ToastProvider } from '../../../components/Toast'
import { useAuthStore } from '../../../stores/auth.store'

function setSession(permissions: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 9, username: 'f3names', first_name: 'F', last_name: '3', email: 'f3@x.com',
      role_id: 35, view_type: 'web', is_super_admin: false, company_id: 1,
      effective_company_id: 1, permissions,
      company_business_units: ['broiler'], granted_business_units: ['broiler'],
      effective_business_units: ['broiler'],
    } as any,
  })
}

function evento(extra: Record<string, any> = {}) {
  return {
    id: 700, lot_id: 138, event_type: 'mortality_recording', event_date: '2026-09-11',
    status: 'approved', company_id: 1, registered_by_id: 1, version: 1, observations: null,
    bird_movements: [], feed_movements: [], egg_movements: [], evidences: [],
    ...extra,
  }
}

beforeEach(() => {
  get.mockReset(); post.mockReset()
  useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false, token: null })
})

describe('F3 · detalles con nombres', () => {
  it('AC-S1-I01 · OperationDetailPage muestra lot_code, granja y galpón (no `#138`)', async () => {
    setSession(['operations:read'])
    get.mockResolvedValue({
      data: evento({ lot_code: 'L-A-138', farm_name: 'Granja Norte', house_name: 'Galpón 3' }),
    })
    render(
      <MemoryRouter initialEntries={['/operations/700']}>
        <Routes><Route path="/operations/:id" element={<OperationDetailPage />} /></Routes>
      </MemoryRouter>,
    )
    await screen.findByText(/operations\.eventDetail/)

    const enlace = document.querySelector('a[href="/lots/138"]')
    expect(enlace, 'enlace al lote ausente').toBeTruthy()
    expect(enlace?.textContent, 'debe mostrarse el código del lote').toBe('L-A-138')
    expect(screen.queryByText('#138'), 'no debe mostrarse el id crudo').toBeNull()
    expect(screen.getByText('Granja Norte')).toBeTruthy()
    expect(screen.getByText('Galpón 3')).toBeTruthy()
  })

  it('AC-S1-I01 · OperationDetailPage sin nombres ⇒ conserva el fallback con id', async () => {
    setSession(['operations:read'])
    get.mockResolvedValue({ data: evento({ farm_id: 7, house_id: 3 }) })
    render(
      <MemoryRouter initialEntries={['/operations/700']}>
        <Routes><Route path="/operations/:id" element={<OperationDetailPage />} /></Routes>
      </MemoryRouter>,
    )
    await screen.findByText(/operations\.eventDetail/)
    expect(screen.getByText('#138')).toBeTruthy()
    expect(screen.queryByText('Granja Norte')).toBeNull()
  })

  it('AC-S1-I01 · ReviewDetail muestra lot_code, granja y galpón (no «Lote #138»)', async () => {
    setSession(['review:read'])
    get.mockImplementation((url: string) => {
      const u = String(url)
      if (u === '/operations/700') {
        return Promise.resolve({
          data: evento({ lot_code: 'L-A-138', farm_name: 'Granja Norte', house_name: 'Galpón 3' }),
        })
      }
      return Promise.resolve({ data: [] })
    })
    render(
      <MemoryRouter initialEntries={['/review/700']}>
        <Routes>
          <Route path="/review/:id" element={<ToastProvider><ReviewDetail /></ToastProvider>} />
        </Routes>
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getByText('L-A-138')).toBeTruthy())
    expect(screen.queryByText('#138'), 'no debe mostrarse «#138»').toBeNull()
    expect(screen.getByText('Granja Norte')).toBeTruthy()
    expect(screen.getByText('Galpón 3')).toBeTruthy()
  })
})
