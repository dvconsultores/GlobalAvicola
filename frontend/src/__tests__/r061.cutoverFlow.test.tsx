/**
 * GA-REQ-061 · T14 · C8 — RED jsdom del flujo «Cargas Iniciales».
 *
 * AC80 (preview antes de apply), AC81 (sin apply con errores pendientes),
 * AC82 (estado visible en el flujo), AC77 (UNKNOWN visible, jamás 0),
 * AC84/85 (i18n ES/EN por claves).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

const get = vi.fn()
const post = vi.fn()
vi.mock('../services/api', () => ({
  default: {
    get: (...a: any[]) => get(...a),
    post: (...a: any[]) => post(...a),
    put: vi.fn(), patch: vi.fn(), delete: vi.fn(),
  },
}))
vi.mock('react-i18next', async () => {
  const esLoc = (await import('../../public/locales/es/translation.json')).default as any
  const tr = (k: string, f?: any) => {
    const partes = String(k).split('.')
    let nodo: any = esLoc
    for (const p of partes) nodo = nodo?.[p]
    if (typeof nodo === 'string') return nodo
    return typeof f === 'string' ? f : k
  }
  return { useTranslation: () => ({ t: tr, i18n: { language: 'es' } }) }
})
vi.mock('../components/Toast', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() }),
  getErrorMessage: (_e: any, f: string) => f,
}))

import es from '../../public/locales/es/translation.json'
import en from '../../public/locales/en/translation.json'
import CargasInicialesPage from '../pages/cutover/CargasInicialesPage'
import { useAuthStore } from '../stores/auth.store'

const BATCH_DRAFT = {
  id: 1, company_id: 1, business_unit: 'broiler', cutover_datetime: '2026-10-06T00:00:00Z',
  source_type: 'EXCEL', source_filename: null, source_checksum_sha256: null,
  template_version: null, status: 'draft', total_rows: 0, valid_rows: 0, invalid_rows: 0,
}

function setSession(permissions: string[]) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 9, username: 'r061', first_name: 'R', last_name: 'C', email: 'r@x.com',
      role_id: 35, view_type: 'web', is_super_admin: false, company_id: 1,
      effective_company_id: 1, permissions,
      company_business_units: ['broiler'], granted_business_units: [],
      effective_business_units: ['broiler'],
    } as any,
  })
}

const TODOS = ['cutover:read', 'cutover:create', 'cutover:validate', 'cutover:submit', 'cutover:approve', 'cutover:apply']

function renderPage() {
  return render(<MemoryRouter><CargasInicialesPage /></MemoryRouter>)
}

beforeEach(() => {
  get.mockReset(); post.mockReset()
  get.mockResolvedValue({ data: { errors: [] } })
  useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false, token: null })
})

describe('GA-REQ-061 · C8 · Cargas Iniciales (jsdom)', () => {
  it('AC82+AC80: crea el batch, muestra estado y preview con errores de validación', async () => {
    setSession(TODOS)
    post.mockImplementation((url: string) => {
      if (url === '/cutover-batches') return Promise.resolve({ data: BATCH_DRAFT })
      if (String(url).includes('/upload')) {
        return Promise.resolve({
          data: { ...BATCH_DRAFT, status: 'validated', source_filename: 'corte.xlsx', total_rows: 3, valid_rows: 2, invalid_rows: 1 },
        })
      }
      return Promise.resolve({ data: {} })
    })
    get.mockImplementation((url: string) => {
      if (String(url).includes('/validation')) {
        return Promise.resolve({
          data: {
            batch_id: 1, status: 'validated', total_rows: 3, valid_rows: 2, invalid_rows: 1,
            errors: [{ row_number: 4, field: 'farm_code', error_code: 'MASTER_NOT_FOUND', message: 'x', received_value: 'F-999' }],
          },
        })
      }
      if (String(url).includes('/items')) {
        return Promise.resolve({
          data: { items: [
            { id: 11, source_row_number: 2, legacy_lot_reference: 'CUT-1', real_start_date: '2026-08-15', validation_status: 'valid' },
            { id: 12, source_row_number: 3, legacy_lot_reference: 'CUT-2', real_start_date: '2026-09-01', validation_status: 'valid' },
            { id: 13, source_row_number: 4, legacy_lot_reference: 'CUT-3', real_start_date: null, validation_status: 'invalid' },
          ] },
        })
      }
      return Promise.resolve({ data: { errors: [] } })
    })

    renderPage()
    fireEvent.change(screen.getByLabelText('Fecha y hora de corte'), { target: { value: '2026-10-06T08:00' } })
    fireEvent.click(screen.getByText('Crear batch'))

    expect(await screen.findByText('Borrador')).toBeTruthy()
    // Preview antes de aplicar (AC80) + errores estructurados.
    const file = new File(['x'], 'corte.xlsx')
    fireEvent.change(screen.getByLabelText('Subir plantilla Excel'), { target: { files: [file] } })
    expect(await screen.findByText('MASTER_NOT_FOUND')).toBeTruthy()
    expect(await screen.findByText('CUT-1')).toBeTruthy()
    expect(await screen.findByText('F-999')).toBeTruthy()
  })

  it('AC81: «Aplicar» deshabilitado con filas inválidas pendientes (aunque haya permiso)', async () => {
    setSession(TODOS)
    post.mockImplementation((url: string) => {
      if (url === '/cutover-batches') return Promise.resolve({ data: BATCH_DRAFT })
      if (String(url).includes('/upload')) {
        return Promise.resolve({
          data: { ...BATCH_DRAFT, status: 'approved', total_rows: 3, valid_rows: 2, invalid_rows: 1 },
        })
      }
      return Promise.resolve({ data: {} })
    })
    get.mockImplementation((url: string) => {
      if (String(url).includes('/validation')) {
        return Promise.resolve({
          data: { batch_id: 1, status: 'approved', total_rows: 3, valid_rows: 2, invalid_rows: 1,
                  errors: [{ row_number: 4, field: 'farm_code', error_code: 'MASTER_NOT_FOUND', message: 'x', received_value: 'F-999' }] },
        })
      }
      if (String(url).includes('/items')) return Promise.resolve({ data: { items: [] } })
      return Promise.resolve({ data: { errors: [] } })
    })

    renderPage()
    fireEvent.change(screen.getByLabelText('Fecha y hora de corte'), { target: { value: '2026-10-06T08:00' } })
    fireEvent.click(screen.getByText('Crear batch')); await new Promise(r => setTimeout(r, 80)); console.log('POST_CALLS', JSON.stringify(post.mock.calls.map((c)=>c[0])), 'GET_CALLS', JSON.stringify(get.mock.calls.map((c)=>c[0])))
    fireEvent.change(await screen.findByLabelText('Subir plantilla Excel'), { target: { files: [new File(['x'], 'c.xlsx')] } })

    const boton = await screen.findByRole('button', { name: /Aplicar/ })
    await waitFor(() => expect((boton as HTMLButtonElement).disabled).toBe(true))
    expect(screen.getByText('No se aplica con errores pendientes')).toBeTruthy()
  })

  it('AC77: UNKNOWN se muestra tal cual — nunca como 0', async () => {
    setSession(TODOS)
    post.mockImplementation((url: string) => {
      if (url === '/cutover-batches') return Promise.resolve({ data: BATCH_DRAFT })
      if (String(url).includes('/upload')) {
        return Promise.resolve({ data: { ...BATCH_DRAFT, status: 'applied' } })
      }
      return Promise.resolve({ data: {} })
    })
    get.mockImplementation((url: string) => {
      if (String(url).includes('/validation')) {
        return Promise.resolve({ data: { batch_id: 1, status: 'applied', total_rows: 2, valid_rows: 2, invalid_rows: 0, errors: [] } })
      }
      if (String(url).includes('/items')) {
        return Promise.resolve({ data: { items: [
          { id: 11, source_row_number: 2, legacy_lot_reference: 'CUT-1', real_start_date: '2026-08-15', validation_status: 'applied' },
        ] } })
      }
      if (String(url).includes('/reconciliation')) {
        return Promise.resolve({ data: {
          batch_id: 1, company_id: 1, business_unit: 'broiler', cutover_datetime: '2026-10-06T00:00:00Z',
          status: 'applied', source: { type: 'EXCEL', system: 'EXCEL', reference: null, filename: 'corte.xlsx', checksum: 'a'.repeat(64), template_version: 'v1' },
          items: 1, openings: 1, unknown_metrics: 2, applied_by_id: 9, applied_at: '2026-10-06T10:00:00Z',
          lots: [{
            lot_id: 41, legacy_lot_code: 'CUT-1', origin: 'MIGRATED',
            opening: { live: 10000, historical_mortality: null, mortality_status: 'UNKNOWN', feed_status: 'UNKNOWN' },
            post: { mortality: 35, culls: 0, feed_kg: null },
            lifetime: { mortality: null },
            current_live: 9965,
          }],
        } })
      }
      return Promise.resolve({ data: { errors: [] } })
    })

    renderPage()
    fireEvent.change(screen.getByLabelText('Fecha y hora de corte'), { target: { value: '2026-10-06T08:00' } })
    fireEvent.click(screen.getByText('Crear batch')); await new Promise(r => setTimeout(r, 80)); console.log('POST_CALLS', JSON.stringify(post.mock.calls.map((c)=>c[0])), 'GET_CALLS', JSON.stringify(get.mock.calls.map((c)=>c[0])))
    fireEvent.change(await screen.findByLabelText('Subir plantilla Excel'), { target: { files: [new File(['x'], 'c.xlsx')] } })

    // Apertura histórica, lifetime y food: null ⇒ UNKNOWN visible (jamás 0).
    const marcas = await screen.findAllByText('UNKNOWN')
    expect(marcas.length).toBeGreaterThanOrEqual(2)
    expect(await screen.findByText(/9[.,]965/)).toBeTruthy()  // saldo vivo real
  })

  it('AC84/85: claves del namespace cutover presentes en ES y EN (sin hardcodes)', () => {
    const REQUERIDAS = [
      'title', 'newBatch', 'businessUnit', 'cutoverDatetime', 'createBatch', 'created',
      'emptyTitle', 'uploadTemplate', 'uploaded', 'downloadTemplate', 'totalRows', 'validRows', 'invalidRows',
      'unknownMetrics', 'validationErrors', 'row', 'field', 'code', 'receivedValue',
      'submit', 'approve', 'reject', 'rejectReason', 'apply', 'applied', 'applyBlocked',
      'preview', 'sourceRow', 'legacyCode', 'realStartDate', 'reconciliation', 'source',
      'openingLive', 'historicalMortality', 'postMortality', 'lifetimeMortality',
      'currentLive', 'unknown',
    ]
    for (const clave of REQUERIDAS) {
      expect((es as any).cutover[clave], `es.cutover.${clave}`).toBeTruthy()
      expect((en as any).cutover[clave], `en.cutover.${clave}`).toBeTruthy()
    }
    for (const estado of ['draft', 'validating', 'validated', 'pending_approval', 'approved', 'applied', 'rejected']) {
      expect((es as any).cutover.status[estado]).toBeTruthy()
      expect((en as any).cutover.status[estado]).toBeTruthy()
    }
    expect((es as any).nav.cutover).toBeTruthy()
    expect((en as any).nav.cutover).toBeTruthy()
  })
})
