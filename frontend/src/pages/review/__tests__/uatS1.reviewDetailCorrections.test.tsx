/**
 * `015` · UAT-S1 (AC-S1-C05) — historial de correcciones legible (campo traducido, no el
 * nombre crudo del backend) y botón «Corregir» solo en estados corregibles.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

const get = vi.fn()
const post = vi.fn()
vi.mock('../../../services/api', () => ({
  default: {
    get: (...a: any[]) => get(...a), post: (...a: any[]) => post(...a),
    put: vi.fn(), delete: vi.fn(),
  },
}))

const DICC: Record<string, string> = {
  'corrections.fields.bird_movements.avg_weight': 'Peso promedio',
  'corrections.row': 'fila {{id}}',
}
const t = (k: string, o?: any) => String(DICC[k] ?? (typeof o === 'string' ? o : k))
  .replace(/\{\{(\w+)\}\}/g, (_m, p) => String(o?.[p] ?? ''))
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t, i18n: { language: 'es', resolvedLanguage: 'es' } }),
}))

const toastError = vi.fn()
vi.mock('../../../components/Toast', async (importOriginal) => {
  const actual = await importOriginal<any>()
  return { ...actual, useToast: () => ({ success: vi.fn(), error: toastError, warning: vi.fn(), info: vi.fn() }) }
})

import ReviewDetail from '../ReviewDetail'
import { ToastProvider } from '../../../components/Toast'
import { useAuthStore } from '../../../stores/auth.store'

const CORRECCION = {
  id: 3, event_id: 55, field_name: 'bird_movements[5].avg_weight',
  original_value: '2.0', corrected_value: '2.5', reason: 'pesaje mal digitado',
  created_at: '2026-09-10T09:00:00Z', corrected_by_name: 'María Ruiz',
}

function setSession() {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 5, username: 'uatS1d', first_name: 'U', last_name: 'S', email: 'u@x.com',
      role_id: 35, view_type: 'web', is_super_admin: false, company_id: 1,
      effective_company_id: 1, permissions: ['review:read', 'review:review', 'corrections:correct'],
      company_business_units: [], granted_business_units: [], effective_business_units: [],
    } as any,
  })
}

const montar = (status: string) => {
  get.mockImplementation((url: string) => {
    const u = String(url)
    if (u === '/operations/55') {
      return Promise.resolve({
        data: {
          id: 55, event_type: 'daily_weights', event_date: '2026-09-10', status,
          lot_id: null, farm_id: 1, house_id: 2, version: 1, observations: null,
          bird_movements: [], feed_movements: [], egg_movements: [], sap_document_ref: null,
        },
      })
    }
    if (u === '/corrections/event/55') return Promise.resolve({ data: [CORRECCION] })
    return Promise.resolve({ data: [] })
  })
  return render(
    <MemoryRouter initialEntries={['/review/55']}>
      <Routes>
        <Route path="/review/:id" element={<ToastProvider><ReviewDetail /></ToastProvider>} />
      </Routes>
    </MemoryRouter>,
  )
}

const enlaceCorregir = () => document.querySelector('a[href="/review/55/correct"]')

beforeEach(() => {
  get.mockReset(); post.mockReset(); vi.clearAllMocks()
  setSession()
})

describe('015 · UAT-S1 · historial de correcciones y botón «Corregir»', () => {
  it('AC-S1-C05 · el historial muestra el campo traducido, no el nombre crudo', async () => {
    montar('in_review')
    await waitFor(() => expect(screen.getByText(/Peso promedio/)).toBeTruthy())
    expect(document.body.textContent).not.toContain('bird_movements[')
    expect(document.body.textContent).toContain('2.0')
    expect(document.body.textContent).toContain('2.5')
    expect(document.body.textContent).toContain('pesaje mal digitado')
  })

  it('AC-S1-C05 · con estado `approved` no se ofrece corregir', async () => {
    montar('approved')
    await waitFor(() => expect(screen.getByText(/daily_weights/)).toBeTruthy())
    expect(enlaceCorregir()).toBeNull()
  })

  it('AC-S1-C05 · con estado `in_review` sí se ofrece corregir', async () => {
    montar('in_review')
    await waitFor(() => expect(screen.getByText(/daily_weights/)).toBeTruthy())
    await waitFor(() => expect(enlaceCorregir()).toBeTruthy())
  })
})
