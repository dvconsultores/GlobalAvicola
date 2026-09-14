/**
 * R-198 · RED jsdom — evidencias del detalle: contrato del servidor, gate por estado y
 * visibilidad táctil.
 *
 * Diseño: `specs/R-198/R-198_AC_MATRIX.md` (AC-01/02/03/07).
 *
 * Rojo en HEAD:
 *   02 · tras subir no relee del servidor (confía en la respuesta local del POST) — un
 *        fallo de contrato no se reconcilia y la “F5” depende del backend roto.
 *   03 · en estado no editable los controles de evidencia siguen ofreciéndose.
 *   07 · las acciones de la evidencia viven tras `opacity-0 group-hover` (invisibles en
 *        táctil, R3 del informe F).
 * Control verde: 01 · la lista se construye del detalle cuando el contrato lo trae.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

const get = vi.fn()
const post = vi.fn()
const del = vi.fn()
vi.mock('../../../services/api', () => ({
  default: {
    get: (...a: any[]) => get(...a),
    post: (...a: any[]) => post(...a),
    put: vi.fn(), patch: vi.fn(),
    delete: (...a: any[]) => del(...a),
  },
}))
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (k: string, f?: any) => (typeof f === 'string' ? f : k) }),
}))
vi.mock('../../../components/Toast', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() }),
  getErrorMessage: (_e: any, f: string) => f,
}))
vi.mock('../../../../src/components/operations/WeightEvaluation', () => ({ default: () => null }))

import OperationDetailPage from '../OperationDetailPage'
import { useAuthStore } from '../../../stores/auth.store'

const EVIDENCIA_LOCAL = {
  id: 501, event_id: 55, file_name: 'local.png', file_size: 120,
  mime_type: 'image/png', evidence_type: 'photo', description: null,
  uploaded_by_id: 9, created_at: '2026-09-14T10:00:00Z',
}
const EVIDENCIA_FRESCA = { ...EVIDENCIA_LOCAL, file_name: 'fresca.png' }

function baseEvent(status: string, evidences: any[] = []) {
  return {
    id: 55, lot_id: 1, event_type: 'weight_recording', event_date: '2026-09-11',
    status, company_id: 1, registered_by_id: 1, version: 1, observations: null,
    bird_movements: [], feed_movements: [], egg_movements: [], evidences,
  }
}

function setSession(permissions: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 9, username: 'r198-c', first_name: 'R', last_name: 'C', email: 'c@x.com',
      role_id: 1, view_type: 'web', is_super_admin: false, company_id: 1, effective_company_id: 1,
      permissions, company_business_units: ['broiler'], granted_business_units: ['broiler'],
      effective_business_units: ['broiler'],
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

beforeEach(() => {
  get.mockReset(); post.mockReset(); del.mockReset()
  useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false, token: null })
})

describe('R-198 · evidencias del detalle (RED)', () => {
  it('01 · control: la lista se construye del detalle del servidor', async () => {
    setSession(['operations:read'])
    get.mockResolvedValue({ data: baseEvent('registered', [EVIDENCIA_LOCAL]) })
    renderPage()
    await waitFor(() => expect(screen.getByText('local.png')).toBeTruthy())
  })

  it('02 · tras subir, relee la verdad del servidor (no la respuesta local)', async () => {
    setSession(['operations:read', 'operations:create'])
    get.mockResolvedValueOnce({ data: baseEvent('registered', []) })
      .mockResolvedValue({ data: baseEvent('registered', [EVIDENCIA_FRESCA]) })
    post.mockResolvedValue({ data: EVIDENCIA_LOCAL })
    renderPage()
    await waitFor(() => expect(screen.getByText('evidence.noFiles')).toBeTruthy())

    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    expect(input, 'control de subida').toBeTruthy()
    const archivo = new File(['x'], 'nueva.png', { type: 'image/png' })
    fireEvent.change(input, { target: { files: [archivo] } })

    await waitFor(() => expect(post).toHaveBeenCalledTimes(1))
    await waitFor(() => expect(get.mock.calls.length).toBeGreaterThanOrEqual(2))
    await waitFor(() => expect(screen.getByText('fresca.png')).toBeTruthy())
    expect(screen.queryByText('local.png')).toBeNull()
  })

  it('03 · estado no editable ⇒ sin controles de evidencia', async () => {
    setSession(['operations:read', 'operations:create', 'operations:delete'])
    get.mockResolvedValue({ data: baseEvent('approved', [EVIDENCIA_LOCAL]) })
    renderPage()
    await waitFor(() => expect(screen.getByText('local.png')).toBeTruthy())

    expect(document.querySelector('input[type="file"]')).toBeNull()
    expect(screen.queryByTitle('common.delete')).toBeNull()
  })

  it('07 · acciones de evidencia visibles en táctil (sin opacity-0)', async () => {
    setSession(['operations:read', 'operations:delete'])
    get.mockResolvedValue({ data: baseEvent('registered', [EVIDENCIA_LOCAL]) })
    renderPage()
    await waitFor(() => expect(screen.getByText('local.png')).toBeTruthy())

    const ocultos = document.querySelectorAll('[class*="opacity-0"]')
    expect(ocultos.length, `elementos con opacity-0: ${ocultos.length}`).toBe(0)
  })
})
