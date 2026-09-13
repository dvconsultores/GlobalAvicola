/**
 * `R-191` · RED jsdom — transición de fase por UI (`LotDetailPage`).
 *
 * La acción «Iniciar Producción» enviaba `{phase_code:'production', …}` al contrato que
 * exige `{lot_id, phase_id}` (422 en producción) y sin toast: el botón seguía visible y
 * la fase activa no se reflejaba. Estos casos fijan el contrato nuevo: `lot_id` + `phase_id`
 * resuelto por **código** (`PROD`) contra `masters/productive-phases`, error legible con
 * toast y badge/persistencia tras el 201.
 *
 * RED esperado en HEAD: 01/02/03 rojos (el POST viaja con `phase_code`; sin toast; badge
 * ausente); 04 control de i18n rojo (claves nuevas).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
const get = vi.fn()
const post = vi.fn()
const toastSuccess = vi.fn()
const toastError = vi.fn()

vi.mock('../../../services/api', () => ({
  default: { get: (...a: any[]) => get(...a), post: (...a: any[]) => post(...a) },
}))
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (k: string, f?: any) => (typeof f === 'string' ? f : k) }),
}))
vi.mock('../../../components/Toast', async (importOriginal) => {
  const real = await importOriginal<typeof import('../../../components/Toast')>()
  return { ...real, useToast: () => ({ success: toastSuccess, error: toastError }) }
})

import LotDetailPage from '../LotDetailPage'
import { useAuthStore } from '../../../stores/auth.store'

const LOTE = { id: 66, lot_code: 'L-GP-2026-12', bird_type: 'grandparent', status: 'active', farm_id: 1, house_id: null }
const FASES_HEAD = [{ id: 10, lot_id: 66, phase_id: 1, start_date: '2026-09-01', end_date: null, is_active: true, start_population_male: 0, start_population_female: 0 }]
const FASES_NUEVAS = [
  { ...FASES_HEAD[0], is_active: false, end_date: '2026-09-14' },
  { id: 11, lot_id: 66, phase_id: 2, start_date: '2026-09-14', end_date: null, is_active: true, start_population_male: 35, start_population_female: 60, phase: { id: 2, code: 'PROD', name: 'Producción' } },
]
const FASES_MAESTRAS = [{ id: 1, code: 'CRIA', name: 'Cría', order: 1 }, { id: 2, code: 'PROD', name: 'Producción', order: 2 }]

let fasesActuales = FASES_HEAD

function setSession() {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 99, username: 'probe', first_name: 'P', last_name: 'Q', email: 'p@x.com',
      role_id: 3, view_type: 'web', is_super_admin: false, company_id: 1, effective_company_id: 1,
      permissions: ['lots:read', 'lots:create', 'operations:create'], company_business_units: ['grandparent'],
      granted_business_units: ['grandparent'], effective_business_units: ['grandparent'],
    } as any,
  })
}

beforeEach(() => {
  vi.clearAllMocks()
  fasesActuales = FASES_HEAD
  get.mockImplementation((url: string) => {
    const u = String(url)
    if (u === '/lots/66/phases') return Promise.resolve({ data: fasesActuales })
    if (u === '/lots/66') return Promise.resolve({ data: LOTE })
    if (u.startsWith('/masters/productive-phases')) return Promise.resolve({ data: FASES_MAESTRAS })
    return Promise.resolve({ data: [] })
  })
  post.mockResolvedValue({ data: { id: 11 } })
  setSession()
})

const montar = () => render(
  <MemoryRouter initialEntries={['/lots/66']}>
    <Routes><Route path="/lots/:id" element={<LotDetailPage />} /></Routes>
  </MemoryRouter>)

const abrirYConfirmar = async () => {
  fireEvent.click(await screen.findByRole('button', { name: /Iniciar Producción/ }))
  fireEvent.click(await screen.findByRole('button', { name: /Confirmar/ }))
}

describe('R-191 · transición de fase por UI', () => {
  it('AC-R191-03 · el POST lleva lot_id y phase_id (resuelto por código PROD) y nunca phase_code', async () => {
    montar()
    await abrirYConfirmar()
    await waitFor(() => expect(post).toHaveBeenCalled())
    const llamada = post.mock.calls.find((c) => String(c[0]).includes('/phases'))
    expect(llamada, 'POST /lots/66/phases').toBeTruthy()
    const cuerpo = llamada![1]
    expect(cuerpo.lot_id).toBe(66)
    expect(cuerpo.phase_id).toBe(2)
    expect(cuerpo.phase_code).toBeUndefined()
  })

  it('AC-R191-02 · 422 del servidor ⇒ toast.error con mensaje legible', async () => {
    post.mockRejectedValueOnce({
      response: { status: 422, data: { detail: [
        { type: 'missing', loc: ['body', 'lot_id'], msg: 'Field required' },
        { type: 'missing', loc: ['body', 'phase_id'], msg: 'Field required' },
      ] } },
    })
    montar()
    await abrirYConfirmar()
    await waitFor(() => expect(toastError).toHaveBeenCalledWith(expect.stringContaining('lot_id')))
  })

  it('AC-R191-01 · tras 201 la fase activa se muestra y el botón desaparece', async () => {
    montar()
    post.mockImplementationOnce(() => {
      fasesActuales = FASES_NUEVAS
      return Promise.resolve({ data: FASES_NUEVAS[1] })
    })
    await abrirYConfirmar()
    await waitFor(() => expect(toastSuccess).toHaveBeenCalled())
    expect(await screen.findByText('Producción')).toBeTruthy()
    await waitFor(() => {
      expect(screen.queryByRole('button', { name: /Iniciar Producción/ })).toBeNull()
    })
  })
})

describe('R-191 · i18n de transición', () => {
  it('AC-R191-10 · claves lots.transitionSuccess y lots.phaseAlreadyActive en ES/EN', () => {
    for (const idioma of ['es', 'en']) {
      const ruta = resolve(__dirname, `../../../../public/locales/${idioma}/translation.json`)
      const dict = JSON.parse(readFileSync(ruta, 'utf8'))
      expect(dict.lots?.transitionSuccess, `${idioma}.lots.transitionSuccess`).toBeTruthy()
      expect(dict.lots?.phaseAlreadyActive, `${idioma}.lots.phaseAlreadyActive`).toBeTruthy()
    }
  })
})

