/**
 * `R-192` · RED jsdom — el cierre de lote explica por qué no cierra (`LotDetailPage`).
 *
 * `handleCloseLot` sólo hacía `console.error` ante un 400/403/404: el modal se cerraba, el
 * lote seguía activo y el operador no veía nada. La verdad es del backend (`R-169`); la UI
 * debe mostrarla con el patrón ya vigente en la página (`toast.error(getErrorMessage(...))`).
 *
 * RED esperado en HEAD: 01 (no hay toast con el `detail`), 03 (403/404 sin mensaje) y
 * 04 (422 estructurado sin render) rojos; 02 (resumen tras 200) verde como control.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
const get = vi.fn()
const post = vi.fn()
const toastSuccess = vi.fn()
const toastError = vi.fn()

vi.mock('../../../services/api', () => ({
  default: { get: (...a: any[]) => get(...a), post: (...a: any[]) => post(...a) },
}))
const DICCIONARIO: Record<string, string> = {
  'lots.closedSummary': 'Lote Cerrado — Resumen Final',
}
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (k: string, f?: any) => (typeof f === 'string' ? f : (DICCIONARIO[k] ?? k)),
  }),
}))
vi.mock('../../../components/Toast', async (importOriginal) => {
  const real = await importOriginal<typeof import('../../../components/Toast')>()
  return { ...real, useToast: () => ({ success: toastSuccess, error: toastError }) }
})

import LotDetailPage from '../LotDetailPage'
import { useAuthStore } from '../../../stores/auth.store'

const LOTE = { id: 66, lot_code: 'R192-LOTE', bird_type: 'broiler', status: 'active', farm_id: 1, house_id: 1 }

function setSession() {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 99, username: 'probe', first_name: 'P', last_name: 'Q', email: 'p@x.com',
      role_id: 3, view_type: 'web', is_super_admin: false, company_id: 1, effective_company_id: 1,
      permissions: ['lots:read', 'lots:create', 'operations:create'], company_business_units: ['broiler'],
      granted_business_units: ['broiler'], effective_business_units: ['broiler'],
    } as any,
  })
}

beforeEach(() => {
  vi.clearAllMocks()
  get.mockImplementation((url: string) => {
    const u = String(url)
    if (u === '/lots/66') return Promise.resolve({ data: { ...LOTE } })
    if (u === '/lots/66/phases') return Promise.resolve({ data: [] })
    if (u.startsWith('/masters/productive-phases')) return Promise.resolve({ data: [] })
    if (u.includes('/traceability')) {
      return Promise.resolve({ data: {
        egg_batches_sent: [], egg_batches_received: [],
        chick_batches_sent: [], chick_batches_received: [],
      } })
    }
    return Promise.resolve({ data: [] })
  })
  setSession()
})

const montar = () => render(
  <MemoryRouter initialEntries={['/lots/66']}>
    <Routes><Route path="/lots/:id" element={<LotDetailPage />} /></Routes>
  </MemoryRouter>)

const abrirYConfirmarCierre = async () => {
  fireEvent.click(await screen.findByRole('button', { name: /Cerrar Lote/ }))
  const botones = await screen.findAllByRole('button', { name: /Cerrar Lote/ })
  fireEvent.click(botones[botones.length - 1])
}

describe('R-192 · el cierre de lote no falla en silencio', () => {
  it('AC-R192-11 · un 400 R7 se muestra como toast con el detail del backend', async () => {
    post.mockRejectedValueOnce({
      response: { status: 400, data: {
        detail: 'No se puede cerrar el lote: 1 registro(s) sin aprobar (1 reverso pendiente de decisión). Apruébelos o anúlelos antes de cerrar.',
        rule: 'R7',
      } },
    })
    montar()
    await abrirYConfirmarCierre()
    await waitFor(() => expect(toastError).toHaveBeenCalledWith(expect.stringContaining('sin aprobar')))
  })

  it('AC-R192-12 · tras 200 aparece el resumen con los totales netos (control)', async () => {
    post.mockResolvedValueOnce({ data: {
      lot_id: 66, lot_code: 'R192-LOTE', age_days: 40,
      total_mortality: 23, total_feed_kg: 3, total_eggs: 17,
      total_events: 11, approved_events: 9, status: 'closed', end_date: '2026-09-14',
    } })
    montar()
    await abrirYConfirmarCierre()
    expect(await screen.findByText('Lote Cerrado — Resumen Final')).toBeInTheDocument()
    expect(screen.getByText('23')).toBeInTheDocument()
    expect(screen.getByText('17')).toBeInTheDocument()
  })

  it('AC-R192-13 · 403 y 404 se muestran legibles', async () => {
    post.mockRejectedValueOnce({
      response: { status: 403, data: { detail: 'Permission denied: lots:create' } },
    })
    montar()
    await abrirYConfirmarCierre()
    await waitFor(() => expect(toastError).toHaveBeenCalledWith(expect.stringContaining('lots:create')))

    post.mockRejectedValueOnce({
      response: { status: 404, data: { detail: 'Lot no encontrado' } },
    })
    await abrirYConfirmarCierre()
    await waitFor(() => expect(toastError).toHaveBeenCalledWith(expect.stringContaining('Lot no encontrado')))
  })

  it('AC-R192-14 · un 422 con detail estructurado se muestra y no rompe el render', async () => {
    post.mockRejectedValueOnce({
      response: { status: 422, data: { detail: [
        { type: 'missing', loc: ['body', 'lot_id'], msg: 'Field required' },
      ] } },
    })
    montar()
    await abrirYConfirmarCierre()
    await waitFor(() => expect(toastError).toHaveBeenCalledWith(expect.stringContaining('Field required')))
    // La página sigue viva: el botón de cierre continúa disponible.
    expect(screen.getByRole('button', { name: /Cerrar Lote/ })).toBeInTheDocument()
  })
})
