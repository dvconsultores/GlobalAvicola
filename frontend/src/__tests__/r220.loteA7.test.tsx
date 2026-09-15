/**
 * R-220 · RED jsdom — Lote A, séptima tanda:
 *   A10 (B-18): `LotFormPage` envía `sap_reference` y el contrato lo descarta en el
 *               esquema (patrón P0-14) ⇒ se retira el campo (decisión del SPEC:
 *               «retirar campo o llevarlo al contrato»; sin migración ⇒ retirar).
 *   A11 (B-19): `farm_id` obligatorio en UI contra un esquema `Optional[int]` —
 *               un lote de incubadora no siempre tiene granja ⇒ opcional alineado.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

const get = vi.fn()
const post = vi.fn()
vi.mock('../services/api', () => ({
  default: { get: (...a: any[]) => get(...a), post: (...a: any[]) => post(...a), put: vi.fn(), patch: vi.fn(), delete: vi.fn() },
}))
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (k: string, f?: any) => (typeof f === 'string' ? f : k), i18n: { language: 'es' } }),
}))
vi.mock('../components/Toast', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() }),
  getErrorMessage: (_e: any, f: string) => f,
}))
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<any>()
  return { ...actual, useNavigate: () => vi.fn() }
})

import LotFormPage from '../pages/lots/LotFormPage'
import { useAuthStore } from '../stores/auth.store'

beforeEach(() => {
  get.mockReset(); post.mockReset()
  get.mockImplementation((url: string) => {
    const u = String(url)
    if (u.startsWith('/masters/farms')) return Promise.resolve({ data: [{ id: 1, name: 'Granja A' }] })
    if (u.startsWith('/masters/houses')) return Promise.resolve({ data: [{ id: 2, name: 'Galpón 1', farm_id: 1 }] })
    return Promise.resolve({ data: [] })
  })
  post.mockResolvedValue({ data: { id: 99 } })
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 9, username: 'r220g', first_name: 'R', last_name: 'C', email: 'r@x.com',
      role_id: 35, view_type: 'web', is_super_admin: false, company_id: 1,
      effective_company_id: 1, permissions: ['lots:create', 'lots:read'],
      company_business_units: [], granted_business_units: [], effective_business_units: [],
    } as any,
  })
})

const renderForm = () =>
  render(
    <MemoryRouter initialEntries={['/lots/new']}>
      <Routes><Route path="/lots/new" element={<LotFormPage />} /></Routes>
    </MemoryRouter>,
  )

describe('R-220 · Lote A séptima tanda (RED)', () => {
  it('AC-R220-A·A10 · el formulario no ofrece ni envía `sap_reference` (el contrato lo descarta)', async () => {
    renderForm()
    await waitFor(() => expect(screen.getAllByText('Código').length).toBeGreaterThan(0))
    // el campo prometía integración SAP que jamás llegaba
    expect(screen.queryByText(/Referencia SAP/), 'campo sap_reference aún visible').toBeNull()
  })

  it('AC-R220-A·A11 · `farm_id` deja de ser obligatorio en UI (esquema `Optional`)', async () => {
    renderForm()
    await waitFor(() => expect(screen.getAllByText('Código').length).toBeGreaterThan(0))
    fireEvent.change(screen.getByLabelText(/Código/), { target: { value: 'L-T1' } })
    const selects = document.querySelectorAll('select')
    fireEvent.change(selects[0], { target: { value: 'broiler' } })
    fireEvent.click(screen.getByRole('button', { name: /Crear Lote|common\.save/ }))
    await waitFor(() => {
      const llamadas = post.mock.calls.filter((c) => String(c[0]) === '/lots')
      expect(llamadas.length, 'sin farm_id el formulario debe poder guardar').toBe(1)
      const cuerpo = llamadas[0][1]
      expect('sap_reference' in cuerpo, 'sap_reference descartado en esquema').toBe(false)
      expect(cuerpo.farm_id ?? null).toBeNull()
    })
  })
})
