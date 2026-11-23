/**
 * SPEC 019 · Progenitoras V3 preventiva (G2 · D-3 · AC-GP-09) — superficie en jsdom.
 *
 * Lo que se protege aquí:
 *   - El preview de grandparent resalta las cuatro transferencias históricas
 *     (`historical_transfers_in|out_males|females`) y cada cabecera sale con su **etiqueta i18n**
 *     (nunca el nombre técnico de la columna).
 *   - Cada celda se pinta con `Metric`: un `0` KNOWN se ve `0` y un vacío (`null` + UNKNOWN) se ve
 *     `UNKNOWN`, jamás `0`.
 *   - Las claves existen en ES y EN (paridad del namespace `cutover.fields`).
 *   - Breeder no cambia: si su highlight no trae las transferencias, esas columnas no se pintan.
 *
 * Aquí no hay fórmulas: la UI solo pinta lo que entrega la API (el cálculo vive en el backend).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
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

import CargasInicialesPage from '../pages/cutover/CargasInicialesPage'
import { useAuthStore } from '../stores/auth.store'
import es from '../../public/locales/es/translation.json'
import en from '../../public/locales/en/translation.json'

const TODOS = ['cutover:read', 'cutover:create', 'cutover:validate', 'cutover:submit', 'cutover:approve', 'cutover:apply']

/** Las cuatro transferencias históricas del contrato V3 compartido (SPEC 014 · SPEC 019 §1.4). */
const TRANSFERENCIAS = [
  'historical_transfers_in_males',
  'historical_transfers_in_females',
  'historical_transfers_out_males',
  'historical_transfers_out_females',
]

const COLUMNAS_GP_V3 = [
  'legacy_lot_code', 'birds_placed_males', 'birds_placed_females',
  'historical_mortality_males', 'historical_mortality_females',
  'historical_culls_males', 'historical_culls_females',
  ...TRANSFERENCIAS,
  'live_males', 'live_females',
]

/** Celda normalizada del contrato (vacío = UNKNOWN · 0 = KNOWN). */
const celda = (value: number | string | null, status = value === null ? 'UNKNOWN' : 'KNOWN') => ({ value, status })

function batchGrandparent(over: Record<string, any> = {}) {
  return {
    id: 31, company_id: 1, business_unit: 'grandparent', cutover_datetime: '2026-11-22T00:00:00Z',
    source_type: 'XLSX', source_filename: 'abuelas_v3.xlsx', source_checksum_sha256: 'd'.repeat(64),
    template_version: 'v3', status: 'applied', total_rows: 2, valid_rows: 2, invalid_rows: 0,
    ...over,
  }
}

/** Fila A: entrada de machos 200 KNOWN y salida de hembras 0 KNOWN (0 no es UNKNOWN). */
const FILA_A = {
  row_number: 2, legacy_lot_code: 'ABU-A', status: 'applied', errors: 0, unknown_metrics: 2, not_applicable_metrics: 0,
  derived: {},
  values: {
    legacy_lot_code: celda('ABU-A'),
    birds_placed_males: celda(1000), birds_placed_females: celda(4000),
    historical_mortality_males: celda(20), historical_mortality_females: celda(80),
    historical_culls_males: celda(5), historical_culls_females: celda(20),
    historical_transfers_in_males: celda(200),
    historical_transfers_in_females: celda(null),
    historical_transfers_out_males: celda(null),
    historical_transfers_out_females: celda(0),
    live_males: celda(1175), live_females: celda(3900),
  },
}

/** Fila B: lote de cría sin movimientos ⇒ las cuatro transferencias llegan vacías (UNKNOWN). */
const FILA_B = {
  row_number: 3, legacy_lot_code: 'ABU-B', status: 'applied', errors: 0, unknown_metrics: 4, not_applicable_metrics: 0,
  derived: {},
  values: {
    legacy_lot_code: celda('ABU-B'),
    birds_placed_males: celda(500), birds_placed_females: celda(2000),
    historical_mortality_males: celda(0), historical_mortality_females: celda(0),
    historical_culls_males: celda(0), historical_culls_females: celda(0),
    historical_transfers_in_males: celda(null),
    historical_transfers_in_females: celda(null),
    historical_transfers_out_males: celda(null),
    historical_transfers_out_females: celda(null),
    live_males: celda(500), live_females: celda(2000),
  },
}

const PREVIEW_GP_V3 = {
  batch_id: 31, business_unit: 'grandparent', status: 'applied', template_version: 'v3',
  schema_id: 'CUTOVER_GRANDPARENT_V3',
  columns: COLUMNAS_GP_V3, highlight: COLUMNAS_GP_V3,
  summary: {
    lots: 2, valid_rows: 2, invalid_rows: 0, unknown_metrics: 6, not_applicable_metrics: 0, live_birds: 7575,
    live_males: 1675, live_females: 5900, historical_mortality: 100, historical_mortality_status: 'KNOWN',
    accumulated_feed_kg: 12500, hatcheries: [], by_phase: {}, farms: [],
  },
  rows: [FILA_A, FILA_B],
}

/**
 * Reconciliación de grandparent: SPEC 019 · D-3 añade las claves M/H **aditivas** en `lote.opening`
 * (`null` = UNKNOWN); la tabla de reconciliación no cambia, así que se prueban vía el mock real.
 */
function reconciliacionGrandparent(over: Record<string, any> = {}) {
  return {
    batch_id: 31, company_id: 1, business_unit: 'grandparent', cutover_datetime: '2026-11-22T00:00:00Z', status: 'applied',
    source: { type: 'XLSX', system: 'LEGACY', reference: null, filename: 'abuelas_v3.xlsx', checksum: 'd'.repeat(64), template_version: 'v3' },
    items: 2, openings: 2, unknown_metrics: 6, applied_by_id: 9, applied_at: '2026-11-22T10:00:00Z',
    lots: [
      {
        lot_id: 201, lot_code: 'ABU-A', legacy_lot_code: 'ABU-A', origin: 'MIGRATED', business_unit: 'grandparent',
        opening: {
          live: 5075, live_males: 1175, live_females: 3900,
          historical_mortality: 100, mortality_status: 'KNOWN',
          historical_culls: 25, culls_status: 'KNOWN',
          feed_kg: 12500, feed_status: 'KNOWN',
          egg_production: 0, egg_production_status: 'KNOWN',
          historical_transfers_in_males: 200,
          historical_transfers_in_females: null,
          historical_transfers_out_males: null,
          historical_transfers_out_females: 0,
        },
        post: { mortality: 0, culls: 0, feed_kg: 0 },
        lifetime: { mortality: 100 },
        current_live: 5075,
      },
      {
        lot_id: 202, lot_code: 'ABU-B', legacy_lot_code: 'ABU-B', origin: 'MIGRATED', business_unit: 'grandparent',
        opening: {
          live: 2500, live_males: 500, live_females: 2000,
          historical_mortality: 0, mortality_status: 'KNOWN',
          historical_culls: 0, culls_status: 'KNOWN',
          feed_kg: 0, feed_status: 'KNOWN',
          egg_production: 0, egg_production_status: 'KNOWN',
          historical_transfers_in_males: null,
          historical_transfers_in_females: null,
          historical_transfers_out_males: null,
          historical_transfers_out_females: null,
        },
        post: { mortality: 0, culls: 0, feed_kg: 0 },
        lifetime: { mortality: 0 },
        current_live: 2500,
      },
    ],
    ...over,
  }
}

function setSession(permissions: string[], unidades: string[] = ['grandparent']) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 9, username: 'cutgp', first_name: 'C', last_name: 'G', email: 'c@x.com', role_id: 35, view_type: 'web',
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

async function abrirBatch(): Promise<HTMLElement> {
  render(<MemoryRouter><CargasInicialesPage /></MemoryRouter>)
  fireEvent.click(await screen.findByRole('button', { name: 'Abrir' }))
  return screen.findByTestId('cutover-preview')
}

/** Cabeceras y celdas de la tabla del preview (≥ sm), alineadas por índice. */
function tablaPreview(preview: HTMLElement) {
  const tabla = preview.querySelector('table') as HTMLTableElement
  const cabeceras = Array.from(tabla.querySelectorAll('thead th')).map(th => (th.textContent ?? '').trim())
  const filas = Array.from(tabla.querySelectorAll('tbody tr')).map(tr =>
    Array.from(tr.querySelectorAll('td')).map(td => (td.textContent ?? '').trim()))
  return {
    cabeceras,
    filas,
    columna: (nombre: string) => cabeceras.findIndex(c => c === nombre),
    celda: (nFila: number, nombre: string) => filas[nFila]?.[cabeceras.findIndex(c => c === nombre)],
  }
}

beforeEach(() => {
  get.mockReset(); post.mockReset()
  get.mockResolvedValue({ data: { items: [], total: 0 } })
  useAuthStore.setState({ isAuthenticated: false, isLoading: false, token: null, user: null } as any)
})

describe('SPEC 019 · Progenitoras V3 en el preview (AC-GP-09)', () => {
  it('a) grandparent: las 4 transferencias salen con etiqueta propia; 200 y 0 conocidos visibles y UNKNOWN donde está vacío', async () => {
    setSession(TODOS)
    mockGetConBatch(batchGrandparent(), PREVIEW_GP_V3, reconciliacionGrandparent())
    const preview = await abrirBatch()
    const t = tablaPreview(preview)

    // Cabeceras con etiqueta i18n (jamás el nombre técnico de la columna).
    for (const campo of TRANSFERENCIAS) {
      const etiqueta = (es as any).cutover.fields[campo] as string
      expect(etiqueta).toBeTruthy()
      expect(t.columna(etiqueta), `cabecera de ${campo}`).toBeGreaterThan(0)
      expect(preview.textContent).not.toContain(campo)
    }
    expect(t.cabeceras).toContain('Transf. hist. entrada machos')
    expect(t.cabeceras).toContain('Transf. hist. salida hembras')

    // Fila A: entrada de machos 200 y salida de hembras 0 (0 conocido se pinta 0).
    expect(t.celda(0, 'Transf. hist. entrada machos')).toBe('200')
    expect(t.celda(0, 'Transf. hist. salida hembras')).toBe('0')
    expect(t.celda(0, 'Transf. hist. entrada hembras')).toContain('UNKNOWN')

    // Fila B: las cuatro vacías ⇒ UNKNOWN visible y ningún 0 inventado.
    for (const campo of TRANSFERENCIAS) {
      const celdaB = t.celda(1, (es as any).cutover.fields[campo])
      expect(celdaB, `fila B · ${campo}`).toContain('UNKNOWN')
      expect(celdaB, `fila B · ${campo} no inventa 0`).not.toBe('0')
    }

    // Las tarjetas móviles repiten la misma etiqueta y el mismo estado por celda.
    const tarjetas = preview.querySelectorAll('ul.sm\\:hidden > li')
    expect(tarjetas.length).toBe(2)
    expect(tarjetas[0].textContent).toContain('Transf. hist. entrada machos')
    expect(tarjetas[1].textContent).toContain('UNKNOWN')
  })

  it('b) paridad ES/EN: las 4 claves existen con texto propio y distinto del nombre técnico', async () => {
    const camposEs = (es as any).cutover.fields
    const camposEn = (en as any).cutover.fields
    expect(Object.keys(camposEs).sort()).toEqual(Object.keys(camposEn).sort())

    for (const campo of TRANSFERENCIAS) {
      const textoEs = camposEs[campo] as string
      const textoEn = camposEn[campo] as string
      expect(textoEs, `es.cutover.fields.${campo}`).toBeTruthy()
      expect(textoEn, `en.cutover.fields.${campo}`).toBeTruthy()
      expect(textoEs).not.toBe(campo)
      expect(textoEn).not.toBe(campo)
      expect(textoEn).not.toBe(textoEs)
    }

    expect(camposEs.historical_transfers_in_males).toBe('Transf. hist. entrada machos')
    expect(camposEs.historical_transfers_in_females).toBe('Transf. hist. entrada hembras')
    expect(camposEs.historical_transfers_out_males).toBe('Transf. hist. salida machos')
    expect(camposEs.historical_transfers_out_females).toBe('Transf. hist. salida hembras')
    expect(camposEn.historical_transfers_in_males).toBe('Hist. transfers in (males)')
    expect(camposEn.historical_transfers_in_females).toBe('Hist. transfers in (females)')
    expect(camposEn.historical_transfers_out_males).toBe('Hist. transfers out (males)')
    expect(camposEn.historical_transfers_out_females).toBe('Hist. transfers out (females)')
  })

  it('c) breeder: si el highlight no trae transferencias, esas columnas no se pintan (sin cambios)', async () => {
    setSession(TODOS, ['breeder'])
    const batchBreeder = {
      ...batchGrandparent(), id: 32, business_unit: 'breeder', source_filename: 'reproductoras_v3.xlsx',
    }
    const columnasBreeder = [
      'legacy_lot_code', 'birds_placed_males', 'birds_placed_females',
      'historical_mortality_males', 'historical_mortality_females',
      'historical_culls_males', 'historical_culls_females',
    ]
    const previewBreeder = {
      ...PREVIEW_GP_V3,
      batch_id: 32, business_unit: 'breeder', schema_id: 'CUTOVER_BREEDER_V3',
      columns: [...columnasBreeder, ...TRANSFERENCIAS],
      highlight: columnasBreeder,
      rows: [{ ...FILA_A, values: Object.fromEntries(Object.entries(FILA_A.values).filter(([k]) => columnasBreeder.includes(k))) }],
    }
    const recBreeder = reconciliacionGrandparent({
      batch_id: 32, business_unit: 'breeder',
      lots: reconciliacionGrandparent().lots.map(l => ({ ...l, business_unit: 'breeder' })),
    })
    mockGetConBatch(batchBreeder, previewBreeder, recBreeder)
    const preview = await abrirBatch()
    const t = tablaPreview(preview)

    for (const campo of TRANSFERENCIAS) {
      expect(t.cabeceras).not.toContain((es as any).cutover.fields[campo])
      expect(preview.textContent).not.toContain(campo)
    }
    // Las columnas de contrato que sí están en el highlight siguen visibles con su etiqueta.
    expect(t.cabeceras).toContain((es as any).cutover.fields.birds_placed_males)
    expect(t.cabeceras).toContain((es as any).cutover.fields.historical_culls_females)
  })
})
