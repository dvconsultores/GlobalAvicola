/**
 * SPEC 006 · Cargas Iniciales v2 — superficie nueva en jsdom.
 *
 * RC-2 (la plantilla sigue a la carga, no al selector), RC-5 (listado y apertura de cargas),
 * RC-6 (CSV admitido), RC-3/AC77 (N/A distinto de UNKNOWN), preview por BU de incubadora y
 * reconciliación de incubadora (huevos), más el guard del estado del botón «Aplicar».
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

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

import CargasInicialesPage, { nombreDescarga } from '../pages/cutover/CargasInicialesPage'
import { Button } from '../components/ui/Button'
import { useAuthStore } from '../stores/auth.store'

const TODOS = ['cutover:read', 'cutover:create', 'cutover:validate', 'cutover:submit', 'cutover:approve', 'cutover:apply']

const BATCH_HATCHERY = {
  id: 7, company_id: 1, business_unit: 'hatchery', cutover_datetime: '2026-10-06T00:00:00Z',
  source_type: 'XLSX', source_filename: 'inc.xlsx', source_checksum_sha256: 'b'.repeat(64),
  template_version: 'v2', status: 'applied', total_rows: 1, valid_rows: 1, invalid_rows: 0,
}

const PREVIEW_HATCHERY = {
  batch_id: 7, business_unit: 'hatchery', status: 'applied', template_version: 'v2', schema_id: 'CUTOVER_HATCHERY_V2',
  columns: ['legacy_lot_code', 'hatchery_code', 'eggs_received', 'eggs_set', 'eggs_transferred', 'chicks_hatched'],
  highlight: ['legacy_lot_code', 'hatchery_code', 'eggs_received', 'eggs_set', 'eggs_transferred', 'chicks_hatched'],
  summary: { lots: 1, valid_rows: 1, invalid_rows: 0, unknown_metrics: 1, not_applicable_metrics: 1, live_birds: 0,
             eggs_received: 10000, eggs_set: 9000, eggs_in_process: 0, chicks_available: 0, hatcheries: ['INC-01'], by_phase: {}, farms: [] },
  rows: [{ row_number: 2, legacy_lot_code: 'INC-1', status: 'applied', errors: 0, unknown_metrics: 1, not_applicable_metrics: 1, derived: {},
           values: { legacy_lot_code: { value: 'INC-1', status: 'KNOWN' }, hatchery_code: { value: 'INC-01', status: 'KNOWN' },
                     eggs_received: { value: 10000, status: 'KNOWN' }, eggs_set: { value: 9000, status: 'KNOWN' },
                     eggs_transferred: { value: null, status: 'UNKNOWN' }, chicks_hatched: { value: null, status: 'NOT_APPLICABLE' } } }],
}

const RECONCILIATION_HATCHERY = {
  batch_id: 7, company_id: 1, business_unit: 'hatchery', cutover_datetime: '2026-10-06T00:00:00Z', status: 'applied',
  source: { type: 'XLSX', system: 'LEGACY', reference: null, filename: 'inc.xlsx', checksum: 'b'.repeat(64), template_version: 'v2' },
  items: 1, openings: 1, unknown_metrics: 1, applied_by_id: 9, applied_at: '2026-10-06T10:00:00Z',
  lots: [{
    lot_id: 77, lot_code: 'INC-1', legacy_lot_code: 'INC-1', origin: 'MIGRATED', business_unit: 'hatchery',
    opening: { live: 0, historical_mortality: null, mortality_status: 'NOT_APPLICABLE', feed_status: 'NOT_APPLICABLE',
               chicks_hatched: null, chicks_hatched_status: 'NOT_APPLICABLE',
               hatchery: { eggs_received: 10000, eggs_received_status: 'KNOWN', eggs_set: 9000, eggs_set_status: 'KNOWN',
                           eggs_transferred: null, eggs_transferred_status: 'UNKNOWN', eggs_in_process: null, chicks_available: 0 } },
    post: { mortality: 0, culls: 0, feed_kg: null, eggs_loaded: 1000, chicks_hatched: 0, chicks_dispatched: 0 },
    lifetime: { mortality: null },
    current_live: 0, current: { live: 0, eggs_available_hatchery: 0, eggs_in_process: null, chicks_available: 0 },
  }],
}

function setSession(permissions: string[], unidades: string[] = ['hatchery', 'broiler']) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 9, username: 'cut2', first_name: 'C', last_name: 'U', email: 'c@x.com', role_id: 35, view_type: 'web',
      is_super_admin: false, company_id: 1, effective_company_id: 1, permissions,
      company_business_units: unidades, granted_business_units: [], effective_business_units: unidades,
    } as any,
  })
}

function mockGetConBatch(batch: any, preview: any, reconciliation: any) {
  get.mockImplementation((url: string, config?: any) => {
    const u = String(url)
    if (u === '/cutover-batches') return Promise.resolve({ data: { items: [batch], total: 1 } })
    if (u === `/cutover-batches/${batch.id}`) return Promise.resolve({ data: batch })
    if (u.includes('/validation')) return Promise.resolve({ data: { batch_id: batch.id, status: batch.status, total_rows: batch.total_rows, valid_rows: batch.valid_rows, invalid_rows: batch.invalid_rows, errors: [] } })
    if (u.includes('/preview')) return Promise.resolve({ data: preview })
    if (u.includes('/reconciliation')) return Promise.resolve({ data: reconciliation })
    if (u.startsWith('/cutover-templates/')) return Promise.resolve({ data: new Blob(['x']), config })
    return Promise.resolve({ data: {} })
  })
}

beforeEach(() => {
  get.mockReset(); post.mockReset()
  get.mockResolvedValue({ data: { items: [], total: 0 } })
  useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false, token: null })
})

describe('SPEC 006 · Cargas Iniciales v2 (jsdom)', () => {
  it('RC-5: lista las cargas de la empresa y abre una existente (persistencia visible)', async () => {
    setSession(TODOS)
    mockGetConBatch(BATCH_HATCHERY, PREVIEW_HATCHERY, RECONCILIATION_HATCHERY)
    render(<MemoryRouter><CargasInicialesPage /></MemoryRouter>)
    const lista = await screen.findByTestId('cutover-batch-list')
    expect(lista.textContent).toContain('#7')
    expect(lista.textContent).toContain('Incubadora')
    fireEvent.click(screen.getByRole('button', { name: 'Abrir' }))
    const cabecera = await screen.findByTestId('cutover-batch-header')
    expect(cabecera.textContent).toContain('#7')
    expect(cabecera.textContent).toContain('Aplicado')
    expect(cabecera.textContent).toContain('v2')
  })

  it('RC-010: descarga temprana de plantilla sin crear carga (CTA visible con unidad+corte)', async () => {
    setSession(TODOS, ['hatchery'])
    get.mockImplementation((url: string, config?: any) => {
      const u = String(url)
      if (u === '/cutover-batches') return Promise.resolve({ data: { items: [], total: 0 } })
      if (u.startsWith('/cutover-templates/')) return Promise.resolve({ data: new Blob(['x']), config })
      return Promise.resolve({ data: {} })
    })
    render(<MemoryRouter><CargasInicialesPage /></MemoryRouter>)
    const btn = screen.getByRole('button', { name: 'Descargar plantilla' }) as HTMLButtonElement
    expect(btn.disabled).toBe(true)
    fireEvent.change(screen.getByLabelText('Fecha y hora de corte'), { target: { value: '2026-10-06T08:00' } })
    expect(btn.disabled).toBe(false)
    fireEvent.click(btn)
    await waitFor(() => expect(get.mock.calls.some(c =>
      String(c[0]) === '/cutover-templates/hatchery' &&
      c[1]?.params?.format === 'xlsx' &&
      c[1]?.params?.batch_id === undefined)).toBe(true))
    // CUTOVER-DATA-01: la descarga temprana envía el corte elegido (solo display en Meta; la autoridad es el batch).
    expect(get.mock.calls.some((c: any) => String(c[0]) === '/cutover-templates/hatchery' && !!c[1]?.params?.cutover_datetime)).toBe(true)
  })

  it('RC-2/RC-6: el selector por defecto es una unidad del usuario, el input acepta CSV y la plantilla sigue a la carga', async () => {
    setSession(TODOS, ['hatchery'])
    const borrador = { ...BATCH_HATCHERY, id: 8, status: 'draft', total_rows: 0, valid_rows: 0, source_filename: null, template_version: null }
    post.mockImplementation((url: string) => url === '/cutover-batches' ? Promise.resolve({ data: borrador }) : Promise.resolve({ data: {} }))
    get.mockImplementation((url: string, config?: any) => {
      const u = String(url)
      if (u === '/cutover-batches') return Promise.resolve({ data: { items: [], total: 0 } })
      if (u.includes('/validation')) return Promise.resolve({ data: { batch_id: 8, status: 'draft', total_rows: 0, valid_rows: 0, invalid_rows: 0, errors: [] } })
      if (u.startsWith('/cutover-templates/')) return Promise.resolve({ data: new Blob(['x']), config })
      return Promise.resolve({ data: {} })
    })
    render(<MemoryRouter><CargasInicialesPage /></MemoryRouter>)
    const selector = screen.getByLabelText('Unidad de negocio') as HTMLSelectElement
    expect(selector.value).toBe('hatchery')
    expect(Array.from(selector.options).map(o => o.value)).toEqual(['hatchery'])
    fireEvent.change(screen.getByLabelText('Fecha y hora de corte'), { target: { value: '2026-10-06T08:00' } })
    fireEvent.click(screen.getByText('Crear carga'))
    const input = await screen.findByTestId('cutover-file-input')
    expect(input.getAttribute('accept')).toBe('.xlsx,.csv')
    // La descarga pide la plantilla de la BU DEL BATCH con su batch_id, en el formato elegido.
    const crear = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:x')
    vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => undefined)
    fireEvent.click(screen.getByRole('button', { name: 'Descargar plantilla CSV' }))
    await waitFor(() => expect(get.mock.calls.some(c => String(c[0]) === '/cutover-templates/hatchery' && c[1]?.params?.format === 'csv' && c[1]?.params?.batch_id === 8)).toBe(true))
    fireEvent.click(screen.getByRole('button', { name: 'Descargar plantilla Excel' }))
    await waitFor(() => expect(get.mock.calls.some(c => String(c[0]) === '/cutover-templates/hatchery' && c[1]?.params?.format === 'xlsx' && c[1]?.params?.batch_id === 8)).toBe(true))
    crear.mockRestore()
  })

  it('AC77 + incubadora: N/A y UNKNOWN distintos en preview y reconciliación de huevos', async () => {
    setSession(TODOS)
    mockGetConBatch(BATCH_HATCHERY, PREVIEW_HATCHERY, RECONCILIATION_HATCHERY)
    render(<MemoryRouter><CargasInicialesPage /></MemoryRouter>)
    fireEvent.click(await screen.findByRole('button', { name: 'Abrir' }))
    const preview = await screen.findByTestId('cutover-preview')
    expect(preview.textContent).toContain('N/A')          // chicks_hatched NOT_APPLICABLE
    expect(preview.textContent).toContain('UNKNOWN')      // eggs_transferred UNKNOWN
    expect(preview.textContent).toContain('Huevos recibidos')
    const rec = await screen.findByTestId('cutover-reconciliation')
    expect(rec.textContent).toContain('Huevo disponible en planta')
    expect(rec.textContent).toMatch(/10[.,]000/)
    expect(rec.textContent).toMatch(/9[.,]000/)
    expect(screen.getByTestId('cutover-applied').textContent).toContain('CUT-GL-02')
    expect(screen.getByRole('button', { name: /Continuar al módulo operativo/ })).toBeTruthy()
  })
})

describe('SPEC 011 · cutover UAT hardening', () => {
  it('CUTOVER-UX-02: nombreDescarga toma el filename del Content-Disposition (versión real), con fallback', () => {
    const r = { headers: { 'content-disposition': 'attachment; filename="cutover_template_hatchery_v3.xlsx"' } }
    expect(nombreDescarga(r, 'fallback.xlsx')).toBe('cutover_template_hatchery_v3.xlsx')
    expect(nombreDescarga({}, 'cutover_template_breeder_v2.xlsx')).toBe('cutover_template_breeder_v2.xlsx')
  })
})

/**
 * GA-CUTOVER-S3-01 · regresión visual de botones «primary».
 *
 * El defecto: `Button` variante `primary` usaba `bg-brand-500 text-white`, pero Tailwind v4 no
 * generaba `bg-brand-*` porque faltaba el token de marca ⇒ el botón quedaba transparente y el
 * texto blanco, invisible. El fix añadió el bloque `@theme` con `--color-brand-50..950` en
 * `index.css`. Estas aserciones fallan si se quita el token o se rompe la variante primary.
 */
describe('GA-CUTOVER-S3-01 · botones primary visibles', () => {
  it('a) la variante primary (por defecto) pinta fondo de marca y texto blanco', () => {
    render(<Button>Aplicar</Button>)
    const btn = screen.getByRole('button', { name: 'Aplicar' })
    // Fondo de marca + texto blanco: si faltara el fondo, el texto blanco sería invisible.
    expect(btn.className).toContain('bg-brand-500')
    expect(btn.className).toContain('text-white')
  })

  it('b) index.css declara @theme con el token --color-brand-500 (cableado Tailwind v4)', () => {
    // process.cwd() en vitest es la carpeta `frontend/`.
    const css = readFileSync(resolve(process.cwd(), 'src', 'index.css'), 'utf8')
    expect(css).toContain('@theme')
    expect(css).toContain('--color-brand-500')
  })
})
