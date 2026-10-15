/**
 * GA-REQ-061 · T14 · C8 — flujo «Cargas Iniciales» en jsdom (adaptado a SPEC 006 · cutover v2).
 *
 * AC80 (preview antes de apply), AC81 (sin apply con errores pendientes), AC82 (estado visible
 * en el flujo), AC77 (UNKNOWN visible, jamás 0), AC84/85 (i18n ES/EN por claves). Las etiquetas
 * son las del contrato v2 («Crear carga», «Subir archivo (XLSX o CSV)»); el preview viene del
 * endpoint por BU.
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
  source_type: 'XLSX', source_filename: null, source_checksum_sha256: null,
  template_version: null, status: 'draft', total_rows: 0, valid_rows: 0, invalid_rows: 0,
}

const PREVIEW = {
  batch_id: 1, business_unit: 'broiler', status: 'validating', template_version: 'v2', schema_id: 'CUTOVER_BROILER_V2',
  columns: ['legacy_lot_code', 'farm_code', 'live_birds', 'historical_mortality'],
  highlight: ['legacy_lot_code', 'farm_code', 'live_birds', 'historical_mortality'],
  summary: { lots: 3, valid_rows: 2, invalid_rows: 1, unknown_metrics: 1, not_applicable_metrics: 0, live_birds: 15000,
             historical_mortality: 300, historical_mortality_status: 'UNKNOWN', historical_mortality_unknown_rows: 1,
             accumulated_feed_kg: 0, by_phase: { ENGORDE: 2 }, farms: ['GR-01'], hatcheries: [] },
  rows: [
    { row_number: 2, legacy_lot_code: 'CUT-1', status: 'valid', errors: 0, unknown_metrics: 0, not_applicable_metrics: 0, derived: {},
      values: { legacy_lot_code: { value: 'CUT-1', status: 'KNOWN' }, farm_code: { value: 'GR-01', status: 'KNOWN' },
                live_birds: { value: 10000, status: 'KNOWN' }, historical_mortality: { value: 300, status: 'KNOWN' } } },
    { row_number: 3, legacy_lot_code: 'CUT-2', status: 'valid', errors: 0, unknown_metrics: 1, not_applicable_metrics: 0, derived: {},
      values: { legacy_lot_code: { value: 'CUT-2', status: 'KNOWN' }, farm_code: { value: 'GR-01', status: 'KNOWN' },
                live_birds: { value: 5000, status: 'KNOWN' }, historical_mortality: { value: null, status: 'UNKNOWN' } } },
    { row_number: 4, legacy_lot_code: 'CUT-3', status: 'invalid', errors: 1, unknown_metrics: 0, not_applicable_metrics: 0, derived: {},
      values: { legacy_lot_code: { value: 'CUT-3', status: 'KNOWN' }, farm_code: { value: 'F-999', status: 'KNOWN' },
                live_birds: { value: 1, status: 'KNOWN' }, historical_mortality: { value: 0, status: 'KNOWN' } } },
  ],
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

function mockGet(estado: string, extra: Record<string, any> = {}) {
  get.mockImplementation((url: string) => {
    const u = String(url)
    if (u === '/cutover-batches') return Promise.resolve({ data: { items: extra.items ?? [], total: 0 } })
    if (u.includes('/validation')) {
      return Promise.resolve({ data: extra.validation ?? {
        batch_id: 1, status: estado, total_rows: 3, valid_rows: 2, invalid_rows: 1,
        errors: [{ row_number: 4, field: 'farm_code', error_code: 'MASTER_NOT_FOUND', message: 'Granja no existe', received_value: 'F-999' }],
      } })
    }
    if (u.includes('/preview')) return Promise.resolve({ data: extra.preview ?? { ...PREVIEW, status: estado } })
    if (u.includes('/reconciliation')) return Promise.resolve({ data: extra.reconciliation })
    return Promise.resolve({ data: { errors: [] } })
  })
}

beforeEach(() => {
  get.mockReset(); post.mockReset()
  get.mockResolvedValue({ data: { items: [], total: 0 } })
  useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false, token: null })
})

describe('GA-REQ-061 · C8 · Cargas Iniciales (jsdom)', () => {
  it('AC82+AC80: crea la carga, muestra estado y preview por BU con errores de validación', async () => {
    setSession(TODOS)
    post.mockImplementation((url: string) => {
      if (url === '/cutover-batches') return Promise.resolve({ data: BATCH_DRAFT })
      if (String(url).includes('/upload')) {
        return Promise.resolve({
          data: { ...BATCH_DRAFT, status: 'validating', source_filename: 'corte.xlsx', template_version: 'v2', total_rows: 3, valid_rows: 2, invalid_rows: 1 },
        })
      }
      return Promise.resolve({ data: {} })
    })
    mockGet('validating')

    renderPage()
    fireEvent.change(screen.getByLabelText('Fecha y hora de corte'), { target: { value: '2026-10-06T08:00' } })
    fireEvent.click(screen.getByText('Crear carga'))

    expect(await screen.findByText('Borrador')).toBeTruthy()
    const file = new File(['x'], 'corte.xlsx')
    fireEvent.change(screen.getByLabelText('Subir archivo (XLSX o CSV)'), { target: { files: [file] } })
    // Errores con mensaje visible (RC-7) y preview por BU antes de aplicar (AC80).
    expect(await screen.findByText('MASTER_NOT_FOUND')).toBeTruthy()
    expect(screen.getByText('Granja no existe')).toBeTruthy()
    expect(screen.getAllByText('F-999').length).toBeGreaterThanOrEqual(1)  // tabla de errores (+ preview)
    expect(await screen.findByText('CUT-1')).toBeTruthy()
    expect(screen.getByText('Descargar errores (CSV)')).toBeTruthy()
  })

  it('AC81: «Aplicar» deshabilitado con filas inválidas pendientes (aunque haya permiso)', async () => {
    setSession(TODOS)
    post.mockImplementation((url: string) => {
      if (url === '/cutover-batches') return Promise.resolve({ data: BATCH_DRAFT })
      if (String(url).includes('/upload')) {
        return Promise.resolve({ data: { ...BATCH_DRAFT, status: 'approved', total_rows: 3, valid_rows: 2, invalid_rows: 1 } })
      }
      return Promise.resolve({ data: {} })
    })
    mockGet('approved')

    renderPage()
    fireEvent.change(screen.getByLabelText('Fecha y hora de corte'), { target: { value: '2026-10-06T08:00' } })
    fireEvent.click(screen.getByText('Crear carga'))
    fireEvent.change(await screen.findByLabelText('Subir archivo (XLSX o CSV)'), { target: { files: [new File(['x'], 'c.xlsx')] } })

    // Tras la carga el batch queda APPROVED con una fila inválida: el aviso aparece y el botón sigue deshabilitado.
    expect(await screen.findByText('No se aplica con errores pendientes')).toBeTruthy()
    const boton = await screen.findByRole('button', { name: /^Aplicar$/ })
    await waitFor(() => expect((boton as HTMLButtonElement).disabled).toBe(true))
  })

  it('AC77: UNKNOWN y N/A se muestran tal cual — nunca como 0', async () => {
    setSession(TODOS)
    post.mockImplementation((url: string) => {
      if (url === '/cutover-batches') return Promise.resolve({ data: BATCH_DRAFT })
      if (String(url).includes('/upload')) return Promise.resolve({ data: { ...BATCH_DRAFT, status: 'applied', total_rows: 1, valid_rows: 1 } })
      return Promise.resolve({ data: {} })
    })
    mockGet('applied', {
      validation: { batch_id: 1, status: 'applied', total_rows: 1, valid_rows: 1, invalid_rows: 0, errors: [] },
      preview: { ...PREVIEW, status: 'applied', rows: [PREVIEW.rows[1]] },
      reconciliation: {
        batch_id: 1, company_id: 1, business_unit: 'broiler', cutover_datetime: '2026-10-06T00:00:00Z',
        status: 'applied', source: { type: 'XLSX', system: 'LEGACY', reference: null, filename: 'corte.xlsx', checksum: 'a'.repeat(64), template_version: 'v2' },
        items: 1, openings: 1, unknown_metrics: 2, applied_by_id: 9, applied_at: '2026-10-06T10:00:00Z',
        lots: [{
          lot_id: 41, lot_code: 'CUT-1', legacy_lot_code: 'CUT-1', origin: 'MIGRATED', business_unit: 'broiler',
          opening: { live: 10000, historical_mortality: null, mortality_status: 'UNKNOWN', historical_culls: null, culls_status: 'UNKNOWN',
                     feed_kg: null, feed_status: 'UNKNOWN', egg_production: null, egg_production_status: 'NOT_APPLICABLE' },
          post: { mortality: 35, culls: 0, feed_kg: null, feed_kg_registered: 0 },
          lifetime: { mortality: null },
          current_live: 9965, current: { live: 9965 },
        }],
      },
    })

    renderPage()
    fireEvent.change(screen.getByLabelText('Fecha y hora de corte'), { target: { value: '2026-10-06T08:00' } })
    fireEvent.click(screen.getByText('Crear carga'))
    fireEvent.change(await screen.findByLabelText('Subir archivo (XLSX o CSV)'), { target: { files: [new File(['x'], 'c.xlsx')] } })

    const marcas = await screen.findAllByText('UNKNOWN')
    expect(marcas.length).toBeGreaterThanOrEqual(2)
    expect(await screen.findByText(/9[.,]965/)).toBeTruthy()  // saldo vivo real, nunca 9.465
    expect(screen.queryByText(/9[.,]465/)).toBeNull()
    expect(screen.getByText('Ver lote')).toBeTruthy()
    expect(screen.getByText('Registrar primer evento')).toBeTruthy()
  })

  it('AC84/85: claves del namespace cutover presentes en ES y EN (sin hardcodes)', () => {
    const REQUERIDAS = [
      'title', 'newBatch', 'businessUnit', 'cutoverDatetime', 'createBatch', 'created',
      'emptyTitle', 'uploadTemplate', 'uploaded', 'downloadTemplate', 'downloadTemplateCsv', 'downloadErrors',
      'totalRows', 'validRows', 'invalidRows', 'unknownMetrics', 'validationErrors', 'row', 'field', 'code', 'message',
      'receivedValue', 'submit', 'approve', 'reject', 'rejectReason', 'apply', 'applied', 'applyBlocked',
      'preview', 'sourceRow', 'legacyCode', 'realStartDate', 'reconciliation', 'source',
      'openingLive', 'historicalMortality', 'postMortality', 'lifetimeMortality',
      'currentLive', 'unknown', 'notApplicable', 'list', 'listEmpty', 'open', 'viewLot', 'firstEvent', 'continueOps',
    ]
    for (const clave of REQUERIDAS) {
      expect((es as any).cutover[clave], `es.cutover.${clave}`).toBeTruthy()
      expect((en as any).cutover[clave], `en.cutover.${clave}`).toBeTruthy()
    }
    for (const estado of ['draft', 'validating', 'validated', 'pending_approval', 'approved', 'applied', 'rejected']) {
      expect((es as any).cutover.status[estado]).toBeTruthy()
      expect((en as any).cutover.status[estado]).toBeTruthy()
    }
    for (const paso of ['unit', 'template', 'upload', 'validation', 'preview', 'approval', 'apply', 'reconcile']) {
      expect((es as any).cutover.steps[paso]).toBeTruthy()
      expect((en as any).cutover.steps[paso]).toBeTruthy()
    }
    expect(Object.keys((es as any).cutover.fields).sort()).toEqual(Object.keys((en as any).cutover.fields).sort())
    expect((es as any).nav.cutover).toBeTruthy()
    expect((en as any).nav.cutover).toBeTruthy()
  })
})
