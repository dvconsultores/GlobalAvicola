/**
 * R-220 · RED jsdom — Lote B, tercera tanda: B9 (F G-22/R4).
 * El botón de eliminar máquina (`absolute top-2 right-2`) vive en una fila que **no
 * declara `relative`**: se posiciona contra el ancestro posicionado más lejano y
 * queda mal colocado. La fila debe ser su propio contenedor.
 */
import { describe, it, expect, vi, beforeEach, beforeAll } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

// jsdom no trae `matchMedia` (SearchSelect lo consulta para su modo móvil).
beforeAll(() => {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation((q: string) => ({
      matches: false, media: q, onchange: null,
      addListener: vi.fn(), removeListener: vi.fn(),
      addEventListener: vi.fn(), removeEventListener: vi.fn(), dispatchEvent: vi.fn(),
    })),
  })
})

const get = vi.fn()
vi.mock('../services/api', () => ({
  default: { get: (...a: any[]) => get(...a), post: vi.fn(), put: vi.fn(), patch: vi.fn(), delete: vi.fn() },
}))
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (k: string, f?: any) => (typeof f === 'string' ? f : k), i18n: { language: 'es' } }),
}))
vi.mock('../components/Toast', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() }),
  getErrorMessage: (_e: any, f: string) => f,
}))

import OperationFormPage from '../pages/operations/OperationFormPage'
import { useAuthStore } from '../stores/auth.store'

beforeEach(() => {
  get.mockReset()
  get.mockResolvedValue({ data: [], headers: {} })
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 9, username: 'r220k', first_name: 'R', last_name: 'C', email: 'r@x.com',
      role_id: 35, view_type: 'web', is_super_admin: false, company_id: 1,
      effective_company_id: 1, permissions: ['operations:create', 'operations:read'],
      company_business_units: [], granted_business_units: [], effective_business_units: [],
    } as any,
  })
})

describe('R-220 · Lote B tercera tanda (RED)', () => {
  it('AC-R220-B·B9 · el botón eliminar máquina se ancla a su propia fila (relative)', async () => {
    render(
      <MemoryRouter initialEntries={['/operations/new']}>
        <Routes><Route path="/operations/new" element={<OperationFormPage />} /></Routes>
      </MemoryRouter>,
    )
    // paso 1 → etapa; paso 2 → operación (el flujo canónico del formulario)
    const etapas = await screen.findAllByRole('button', { name: /Incubadora.*Recepción de huevo/ })
    fireEvent.click(etapas[0])
    fireEvent.click(await screen.findByRole('button', { name: /^hatchery_inspection$/ }))
    const agregar = await screen.findByRole('button', { name: /Añadir máquina/ })
    fireEvent.click(agregar)
    await waitFor(() => expect(document.querySelector('button.text-red-400')).toBeTruthy())

    const boton = document.querySelector('button.text-red-400') as HTMLElement
    const fila = boton.closest('div.relative')
    expect(fila, 'fila sin contenedor posicionado (el botón escapa)').toBeTruthy()
    // y es la fila real de la máquina (la que lleva el borde separador del bloque)
    expect(fila?.className).toContain('border-b')
  })
})
