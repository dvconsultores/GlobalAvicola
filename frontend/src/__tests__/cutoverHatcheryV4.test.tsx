/**
 * SPEC 018 · Incubadora v4 (D-3, D-5, D-9, D-10 · AC-V4-13) — superficie en jsdom.
 *
 * Lo que se protege aquí:
 *   - «Total no incubables» es **derivado** (etiquetado, no editable) y solo existe si los tres
 *     componentes son KNOWN; con un UNKNOWN se pinta UNKNOWN, nunca una suma parcial.
 *   - El desglose (extra grande / sucio / roto) se ve compacto en la misma celda, con su estado,
 *     sin fabricar cifras; `0` conocido se pinta `0`.
 *   - «Huevos fértiles a fosa» es una métrica **separada** (fosa 0 conocida ⇒ 0, no vacío ni
 *     UNKNOWN) y nunca se suma a los no incubables ni a los descartados V3.
 *   - «Huevos en proceso» se pinta tal como lo entrega la API: SPEC 018 §7 · D-12
 *     (`set − transferred − fosa` solo si los tres son KNOWN) es regla de servidor; la UI no
 *     calcula nada y un `null` es UNKNOWN, jamás 0 ni una cifra inventada.
 *   - «Huevos descartados (histórico V3)» SOLO aparece si el batch trae descartados KNOWN; en V4
 *     (`NOT_APPLICABLE`) esa columna no se muestra y el preview no la usa como dato de entrada.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, within } from '@testing-library/react'
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
import { useAuthStore } from '../stores/auth.store'
import es from '../../public/locales/es/translation.json'
import en from '../../public/locales/en/translation.json'

const TODOS = ['cutover:read', 'cutover:create', 'cutover:validate', 'cutover:submit', 'cutover:approve', 'cutover:apply']

const CAMPOS_NO_INCUBABLES = ['eggs_non_incubable_oversized', 'eggs_non_incubable_dirty', 'eggs_non_incubable_broken']

const COLUMNAS_V4 = [
  'legacy_lot_code', 'hatchery_code', 'eggs_received', 'eggs_set',
  'eggs_non_incubable_oversized', 'eggs_non_incubable_dirty', 'eggs_non_incubable_broken',
  'eggs_transferred', 'fertile_eggs_to_pit', 'chicks_hatched',
]

function batchV4(over: Record<string, any> = {}) {
  return {
    id: 21, company_id: 1, business_unit: 'hatchery', cutover_datetime: '2026-11-20T00:00:00Z',
    source_type: 'XLSX', source_filename: 'inc_v4.xlsx', source_checksum_sha256: 'c'.repeat(64),
    template_version: 'v4', status: 'applied', total_rows: 1, valid_rows: 1, invalid_rows: 0,
    ...over,
  }
}

/** Celda normalizada del contrato V4 (vacío = UNKNOWN · 0 = KNOWN). */
const celda = (value: number | string | null, status = value === null ? 'UNKNOWN' : 'KNOWN') => ({ value, status })

const PREVIEW_V4 = {
  batch_id: 21, business_unit: 'hatchery', status: 'applied', template_version: 'v4', schema_id: 'CUTOVER_HATCHERY_V4',
  columns: COLUMNAS_V4, highlight: COLUMNAS_V4,
  summary: {
    lots: 1, valid_rows: 1, invalid_rows: 0, unknown_metrics: 1, not_applicable_metrics: 0, live_birds: 0,
    eggs_received: 10000, eggs_set: 9000, eggs_in_process: 0, chicks_available: 0, hatcheries: ['INC-01'],
    by_phase: {}, farms: [],
  },
  rows: [{
    row_number: 2, legacy_lot_code: 'INC-1', status: 'applied', errors: 0, unknown_metrics: 1, not_applicable_metrics: 0,
    // SPEC 018 · D-3: derivados por fila, calculados por el backend (nunca por la UI).
    derived: { eggs_non_incubable_total: 1000, eggs_in_process: null },
    values: {
      legacy_lot_code: celda('INC-1'), hatchery_code: celda('INC-01'),
      eggs_received: celda(10000), eggs_set: celda(9000),
      eggs_non_incubable_oversized: celda(500), eggs_non_incubable_dirty: celda(300),
      eggs_non_incubable_broken: celda(200),
      eggs_transferred: celda(null), fertile_eggs_to_pit: celda(25), chicks_hatched: celda(null),
    },
  }],
}

/** Apertura de incubadora V4 (lo que devuelve la reconciliación del batch aplicado). */
function hatcheryV4(over: Record<string, any> = {}) {
  return {
    eggs_received: 10000, eggs_received_status: 'KNOWN',
    eggs_set: 9000, eggs_set_status: 'KNOWN',
    eggs_transferred: null, eggs_transferred_status: 'UNKNOWN',
    eggs_non_incubable_oversized: 500, eggs_non_incubable_oversized_status: 'KNOWN',
    eggs_non_incubable_dirty: 300, eggs_non_incubable_dirty_status: 'KNOWN',
    eggs_non_incubable_broken: 200, eggs_non_incubable_broken_status: 'KNOWN',
    eggs_non_incubable_total: 1000, eggs_non_incubable_total_status: 'KNOWN',
    fertile_eggs_to_pit: 25, fertile_eggs_to_pit_status: 'KNOWN',
    // SPEC 018 · D-2: en V4 la columna histórica llega NULL + NOT_APPLICABLE (no se muestra).
    eggs_discarded: null, eggs_discarded_status: 'NOT_APPLICABLE',
    // SPEC 018 §7 · D-12: `null` aquí significa «falta un KNOWN» (transferidos), nunca «fosa > 0».
    eggs_in_process: null,
    chicks_available: 0, chicks_available_status: 'KNOWN',
    ...over,
  }
}

function reconciliacion(lotId: number, hatchery: Record<string, any>, over: Record<string, any> = {}) {
  return {
    batch_id: 21, company_id: 1, business_unit: 'hatchery', cutover_datetime: '2026-11-20T00:00:00Z', status: 'applied',
    source: { type: 'XLSX', system: 'LEGACY', reference: null, filename: 'inc_v4.xlsx', checksum: 'c'.repeat(64), template_version: 'v4' },
    items: 1, openings: 1, unknown_metrics: 1, applied_by_id: 9, applied_at: '2026-11-20T10:00:00Z',
    lots: [{
      lot_id: lotId, lot_code: 'INC-1', legacy_lot_code: 'INC-1', origin: 'MIGRATED', business_unit: 'hatchery',
      opening: {
        live: 0, historical_mortality: null, mortality_status: 'NOT_APPLICABLE', feed_status: 'NOT_APPLICABLE',
        chicks_hatched: null, chicks_hatched_status: 'NOT_APPLICABLE', hatchery,
      },
      post: { mortality: 0, culls: 0, feed_kg: null, eggs_loaded: 0, chicks_hatched: 0, chicks_dispatched: 0 },
      lifetime: { mortality: null },
      current_live: 0,
      current: { live: 0, eggs_available_hatchery: 0, eggs_in_process: null, chicks_available: 0 },
      ...over,
    }],
  }
}

function setSession(permissions: string[], unidades: string[] = ['hatchery']) {
  useAuthStore.setState({
    isAuthenticated: true, isLoading: false, token: null,
    user: {
      id: 9, username: 'cut4', first_name: 'C', last_name: 'U', email: 'c@x.com', role_id: 35, view_type: 'web',
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
  return screen.findByTestId('cutover-reconciliation')
}

beforeEach(() => {
  get.mockReset(); post.mockReset()
  get.mockResolvedValue({ data: { items: [], total: 0 } })
  useAuthStore.setState({ isAuthenticated: false, isLoading: false, token: null, user: null } as any)
})

describe('SPEC 018 · incubadora v4 en la UI (AC-V4-13)', () => {
  it('a) V4 500/300/200 + fosa 25: cifras, total derivado 1.000 y sin columna de descartados históricos', async () => {
    setSession(TODOS)
    mockGetConBatch(batchV4(), PREVIEW_V4, reconciliacion(101, hatcheryV4()))
    const rec = await abrirBatch()

    // Cabecera: total derivado (etiquetado) y fosa presentes.
    const thTotal = within(rec).getByTestId('cutover-th-non-incubable-total')
    expect(thTotal.textContent).toContain('Total no incubables')
    expect(thTotal.textContent).toContain('derivado')
    expect(within(rec).getByRole('columnheader', { name: /Huevos fértiles a fosa/ })).toBeTruthy()

    // Total derivado = 1.000 (nunca editable) con desglose visible.
    const total = within(rec).getByTestId('cutover-non-incubable-total-101')
    expect(total.textContent).toMatch(/1[.,]000/)
    expect(total.textContent).toContain('500')
    expect(total.textContent).toContain('300')
    expect(total.textContent).toContain('200')
    expect(within(total).getByTestId('cutover-non-incubable-eggs_non_incubable_oversized').textContent)
      .toContain('No incubable extra grande')

    // Fosa 25 conocida.
    expect(within(rec).getByTestId('cutover-fertile-pit-101').textContent).toBe('25')

    // V4: sin columna histórica de descartados en ninguna parte de la pantalla.
    expect(within(rec).queryByTestId('cutover-th-eggs-discarded')).toBeNull()
    expect(screen.queryByText(/Huevos descartados/)).toBeNull()

    // Preview: cada campo nuevo con su etiqueta i18n y su estado; el total derivado va aparte.
    const preview = screen.getByTestId('cutover-preview')
    for (const campo of CAMPOS_NO_INCUBABLES) {
      expect((es as any).cutover.fields[campo]).toBeTruthy()
      expect(preview.textContent).toContain((es as any).cutover.fields[campo])
    }
    expect(preview.textContent).toContain((es as any).cutover.fields.fertile_eggs_to_pit)
    const totalPreview = screen.getByTestId('cutover-preview-total-2')
    expect(totalPreview.textContent).toMatch(/1[.,]000/)
    expect(preview.textContent).toContain('Total no incubables')
    expect(preview.textContent).toContain('derivado')
  })

  it('b) V4 con un componente UNKNOWN: el total es UNKNOWN (no la suma parcial) y el conocido sigue visible', async () => {
    setSession(TODOS)
    const hatchery = hatcheryV4({
      eggs_non_incubable_oversized: 500, eggs_non_incubable_oversized_status: 'KNOWN',
      eggs_non_incubable_dirty: null, eggs_non_incubable_dirty_status: 'UNKNOWN',
      eggs_non_incubable_broken: 50, eggs_non_incubable_broken_status: 'KNOWN',
      eggs_non_incubable_total: null, eggs_non_incubable_total_status: 'UNKNOWN',
    })
    mockGetConBatch(batchV4(), PREVIEW_V4, reconciliacion(102, hatchery))
    const rec = await abrirBatch()

    const total = within(rec).getByTestId('cutover-non-incubable-total-102')
    expect(total.textContent).toContain('UNKNOWN')
    expect(total.textContent).not.toMatch(/55[.,]?0/)     // ni 550 (suma parcial) ni 550 en ninguna forma
    expect(total.textContent).not.toMatch(/\b1000\b/)
    // El componente conocido sigue visible con su cifra; el desconocido se marca UNKNOWN.
    expect(within(total).getByTestId('cutover-non-incubable-eggs_non_incubable_oversized').textContent).toContain('500')
    expect(within(total).getByTestId('cutover-non-incubable-eggs_non_incubable_broken').textContent).toContain('50')
    expect(within(total).getByTestId('cutover-non-incubable-eggs_non_incubable_dirty').textContent).toContain('UNKNOWN')
  })

  it('c) fosa 0 conocida se pinta 0 (ni vacío ni UNKNOWN)', async () => {
    setSession(TODOS)
    mockGetConBatch(batchV4(), PREVIEW_V4, reconciliacion(103, hatcheryV4({ fertile_eggs_to_pit: 0, fertile_eggs_to_pit_status: 'KNOWN' })))
    const rec = await abrirBatch()

    const fosa = within(rec).getByTestId('cutover-fertile-pit-103')
    expect(fosa.textContent?.trim()).toBe('0')
    expect(fosa.textContent).not.toContain('UNKNOWN')
  })

  it('d) V3 histórica (descartados 100 KNOWN, desglose UNKNOWN): columna histórica con 100 y total UNKNOWN sin repartir', async () => {
    setSession(TODOS)
    const batchV3 = batchV4({ template_version: 'v3', source_filename: 'inc_v3.xlsx' })
    const previewV3 = {
      ...PREVIEW_V4, template_version: 'v3', schema_id: 'CUTOVER_HATCHERY_V3',
      // V3 no deriva el total no incubable (no existe el desglose).
      rows: PREVIEW_V4.rows.map(fila => ({ ...fila, derived: {} })),
    }
    const hatcheryV3 = hatcheryV4({
      eggs_non_incubable_oversized: null, eggs_non_incubable_oversized_status: 'UNKNOWN',
      eggs_non_incubable_dirty: null, eggs_non_incubable_dirty_status: 'UNKNOWN',
      eggs_non_incubable_broken: null, eggs_non_incubable_broken_status: 'UNKNOWN',
      eggs_non_incubable_total: null, eggs_non_incubable_total_status: 'UNKNOWN',
      fertile_eggs_to_pit: null, fertile_eggs_to_pit_status: 'UNKNOWN',
      eggs_discarded: 100, eggs_discarded_status: 'KNOWN',
    })
    mockGetConBatch(batchV3, previewV3, reconciliacion(104, hatcheryV3))
    const rec = await abrirBatch()

    // La columna histórica aparece y trae el valor original (V3 intacta).
    expect(within(rec).getByTestId('cutover-th-eggs-discarded').textContent).toContain('Huevos descartados (histórico V3)')
    expect(within(rec).getByTestId('cutover-eggs-discarded-104').textContent).toBe('100')

    // El total no incubable no se inventa: UNKNOWN y ningún reparto numérico en la celda.
    const total = within(rec).getByTestId('cutover-non-incubable-total-104')
    expect(total.textContent).toContain('UNKNOWN')
    expect(total.textContent).not.toMatch(/\d/)
  })

  it('e) la plantilla/descarga vigente de incubadora ya no se anuncia como v3', () => {
    // El nombre real lo fija el servidor (Content-Disposition) y hoy es v4.
    const res = { headers: { 'content-disposition': 'attachment; filename="cutover_template_hatchery_v4.xlsx"' } }
    expect(nombreDescarga(res, 'fallback.xlsx')).toBe('cutover_template_hatchery_v4.xlsx')
    // Sin textos fijos que anuncien la plantilla v3 en la pantalla de cargas iniciales.
    const src = readFileSync(resolve(process.cwd(), 'src', 'pages', 'cutover', 'CargasInicialesPage.tsx'), 'utf8')
    expect(src).not.toMatch(/cutover_template_hatchery_v3/)
    expect(src).not.toMatch(/CUTOVER_HATCHERY_V3/)
  })

  it('i18n: las etiquetas nuevas están en ES y EN (paridad del namespace de campos)', () => {
    const clavesEs = Object.keys((es as any).cutover.fields).sort()
    const clavesEn = Object.keys((en as any).cutover.fields).sort()
    expect(clavesEs).toEqual(clavesEn)
    for (const campo of [...CAMPOS_NO_INCUBABLES, 'fertile_eggs_to_pit', 'eggs_discarded']) {
      expect((es as any).cutover.fields[campo], `es.cutover.fields.${campo}`).toBeTruthy()
      expect((en as any).cutover.fields[campo], `en.cutover.fields.${campo}`).toBeTruthy()
      expect((en as any).cutover.fields[campo]).not.toBe((es as any).cutover.fields[campo])
    }
    for (const clave of ['eggsNonIncubableTotal', 'fertileEggsToPit', 'eggsDiscardedHistorical', 'derivedLabel']) {
      expect((es as any).cutover[clave], `es.cutover.${clave}`).toBeTruthy()
      expect((en as any).cutover[clave], `en.cutover.${clave}`).toBeTruthy()
    }
    expect((es as any).cutover.fields.eggs_discarded).toBe('Huevos descartados (histórico V3)')
    expect((en as any).cutover.fields.eggs_discarded).toBe('Discarded eggs (V3 historical)')
  })
})

/**
 * SPEC 018 §7 · AMENDMENT OD-HATCH-V4-01 = RATIFIED (2026-11-21): la fosa es POST-CARGA.
 *
 * `eggs_in_process` V4 = `set − transferred − fosa` **solo si los tres son KNOWN** (D-12), y la fosa
 * sigue siendo una métrica separada: no se suma a los no incubables ni a los descartados V3. Todo el
 * cálculo vive en el backend; aquí se protege que la pantalla pinte exactamente lo que recibe.
 */
describe('SPEC 018 §7 · fosa post-carga en la UI (OD-HATCH-V4-01 ratificado)', () => {
  it('a) reconciliación 9.000/8.000/100 con en proceso 900: fosa aparte y 900 en «Huevos en proceso»', async () => {
    setSession(TODOS)
    const hatchery = hatcheryV4({
      eggs_transferred: 8000, eggs_transferred_status: 'KNOWN',
      fertile_eggs_to_pit: 100, fertile_eggs_to_pit_status: 'KNOWN',
      eggs_in_process: 900,   // 9.000 − 8.000 − 100, calculado por el servidor
    })
    const lote = reconciliacion(105, hatchery, {
      current: { live: 0, eggs_available_hatchery: 0, eggs_in_process: 900, chicks_available: 0 },
    })
    mockGetConBatch(batchV4(), PREVIEW_V4, lote)
    const rec = await abrirBatch()

    // «Huevos en proceso» = 900 (D-12), tal cual lo entrega la API.
    const enProceso = within(rec).getByTestId('cutover-eggs-in-process-105')
    expect(enProceso.textContent).toMatch(/9\s?00/)
    expect(enProceso.textContent).not.toContain('UNKNOWN')

    // La fosa va en SU celda: 100, métrica separada del total no incubable.
    const fosa = within(rec).getByTestId('cutover-fertile-pit-105')
    expect(fosa.textContent?.trim()).toBe('100')

    // El total no incubable sigue siendo el derivado de los tres componentes (1.000) y NO incluye la fosa.
    const total = within(rec).getByTestId('cutover-non-incubable-total-105')
    expect(total.textContent).toMatch(/1[.,]000/)
    expect(total.textContent).not.toContain('100')
    expect(within(total).getByTestId('cutover-non-incubable-eggs_non_incubable_oversized').textContent).toContain('500')
    expect(within(total).getByTestId('cutover-non-incubable-eggs_non_incubable_dirty').textContent).toContain('300')
    expect(within(total).getByTestId('cutover-non-incubable-eggs_non_incubable_broken').textContent).toContain('200')

    // V4: ni columna de descartados históricos ni la fosa contada como descarte.
    expect(within(rec).queryByTestId('cutover-th-eggs-discarded')).toBeNull()
    expect(within(rec).queryByTestId('cutover-eggs-discarded-105')).toBeNull()
    expect(rec.textContent).not.toMatch(/Huevos descartados/)
  })

  it('b) fosa UNKNOWN con en proceso null: «Huevos en proceso» es UNKNOWN (nunca 0 ni 1.000)', async () => {
    setSession(TODOS)
    const hatchery = hatcheryV4({
      eggs_transferred: 0, eggs_transferred_status: 'KNOWN',
      fertile_eggs_to_pit: null, fertile_eggs_to_pit_status: 'UNKNOWN',
      eggs_in_process: null,  // D-12: falta un KNOWN ⇒ UNKNOWN, jamás un cero supuesto
    })
    mockGetConBatch(batchV4(), PREVIEW_V4, reconciliacion(106, hatchery))
    const rec = await abrirBatch()

    const enProceso = within(rec).getByTestId('cutover-eggs-in-process-106')
    expect(enProceso.textContent).toContain('UNKNOWN')
    expect(enProceso.textContent).not.toMatch(/\d/)

    // La fosa se declara UNKNOWN, no 0.
    const fosa = within(rec).getByTestId('cutover-fertile-pit-106')
    expect(fosa.textContent).toContain('UNKNOWN')
    expect(fosa.textContent).not.toMatch(/\d/)
  })

  it('c) fosa 0 conocida: la celda muestra 0 y en proceso = cargados − transferidos', async () => {
    setSession(TODOS)
    const hatchery = hatcheryV4({
      eggs_transferred: 0, eggs_transferred_status: 'KNOWN',
      fertile_eggs_to_pit: 0, fertile_eggs_to_pit_status: 'KNOWN',
      eggs_in_process: 9000,  // 9.000 − 0 − 0: el cero conocido sí participa en la resta
    })
    const lote = reconciliacion(107, hatchery, {
      current: { live: 0, eggs_available_hatchery: 0, eggs_in_process: 9000, chicks_available: 0 },
    })
    mockGetConBatch(batchV4(), PREVIEW_V4, lote)
    const rec = await abrirBatch()

    const fosa = within(rec).getByTestId('cutover-fertile-pit-107')
    expect(fosa.textContent?.trim()).toBe('0')
    expect(fosa.textContent).not.toContain('UNKNOWN')
    const enProceso = within(rec).getByTestId('cutover-eggs-in-process-107')
    expect(enProceso.textContent).toMatch(/9[.,]000/)
    expect(enProceso.textContent).not.toContain('UNKNOWN')
  })
})

/**
 * SPEC 018 §8 · RESIDUAL O-15 — el chip del resumen ya no convierte UNKNOWN en 0 (D-18/D-19/D-20).
 *
 * El backend publica `<clave>`, `<clave>_status` y `<clave>_unknown_rows`; la UI pinta UNKNOWN
 * cuando el estado lo dice (o el valor es `null`), un número conocido tal cual y `0` conocido como
 * `0`. La fila del preview muestra su propio derivado (`derived.eggs_in_process`).
 */
function previewO15(summary: Record<string, any>, rows: any[] = PREVIEW_V4.rows) {
  return { ...PREVIEW_V4, summary: { ...PREVIEW_V4.summary, ...summary }, rows }
}

describe('SPEC 018 §8 · O-15: agregado del preview con UNKNOWN', () => {
  it('chip de huevos en proceso UNKNOWN no pinta una suma parcial', async () => {
    setSession(TODOS)
    mockGetConBatch(batchV4(), previewO15({
      eggs_in_process: null, eggs_in_process_status: 'UNKNOWN', eggs_in_process_unknown_rows: 1,
    }), reconciliacion(111, hatcheryV4()))
    await abrirBatch()

    const chip = screen.getByTestId('cutover-chip-eggs-in-process')
    expect(chip.textContent).toContain('UNKNOWN')
    expect(chip.textContent).not.toContain('900')
  })

  it('chip de huevos en proceso numérico con estado KNOWN pinta el total', async () => {
    setSession(TODOS)
    mockGetConBatch(batchV4(), previewO15({
      eggs_in_process: 1700, eggs_in_process_status: 'KNOWN', eggs_in_process_unknown_rows: 0,
    }), reconciliacion(112, hatcheryV4()))
    await abrirBatch()

    const chip = screen.getByTestId('cutover-chip-eggs-in-process')
    expect(chip.textContent).toMatch(/1[.,]700/)
    expect(chip.textContent).not.toContain('UNKNOWN')
  })

  it('chip de huevos en proceso con cero conocido pinta 0', async () => {
    setSession(TODOS)
    mockGetConBatch(batchV4(), previewO15({
      eggs_in_process: 0, eggs_in_process_status: 'KNOWN', eggs_in_process_unknown_rows: 0,
    }), reconciliacion(113, hatcheryV4()))
    await abrirBatch()

    expect(screen.getByTestId('cutover-chip-eggs-in-process').textContent?.trim()).toMatch(/:\s*0$/)
    expect(screen.getByTestId('cutover-chip-eggs-in-process').textContent).not.toContain('UNKNOWN')
  })

  it('preview por fila: A = 900 y B = UNKNOWN en «Huevos en proceso (derivado)»', async () => {
    setSession(TODOS)
    const filaA = { ...PREVIEW_V4.rows[0], row_number: 2, legacy_lot_code: 'INC-A',
                    derived: { eggs_non_incubable_total: 1000, eggs_in_process: 900 } }
    const filaB = { ...PREVIEW_V4.rows[0], row_number: 3, legacy_lot_code: 'INC-B',
                    derived: { eggs_non_incubable_total: 1000, eggs_in_process: null } }
    mockGetConBatch(batchV4(), previewO15({}, [filaA, filaB]), reconciliacion(114, hatcheryV4()))
    await abrirBatch()

    const th = screen.getByTestId('cutover-th-preview-in-process')
    expect(th.textContent).toContain('Huevos en proceso')
    expect(th.textContent).toContain('derivado')

    const celdaA = screen.getByTestId('cutover-preview-in-process-2')
    expect(celdaA.textContent).toMatch(/9\s?00/)
    expect(celdaA.textContent).not.toContain('UNKNOWN')

    const celdaB = screen.getByTestId('cutover-preview-in-process-3')
    expect(celdaB.textContent).toContain('UNKNOWN')
    expect(celdaB.textContent).not.toMatch(/\d/)
  })

  it('chip de pollitos disponibles: UNKNOWN con null y numérico con KNOWN', async () => {
    setSession(TODOS)
    mockGetConBatch(batchV4(), previewO15({
      chicks_available: null, chicks_available_status: 'UNKNOWN', chicks_available_unknown_rows: 1,
    }), reconciliacion(115, hatcheryV4()))
    await abrirBatch()

    const chip = screen.getByTestId('cutover-chip-chicks-available')
    expect(chip.textContent).toContain('UNKNOWN')
    expect(chip.textContent).not.toMatch(/\d/)
  })

  it('chip de pollitos disponibles con 0 conocido pinta 0 (no UNKNOWN)', async () => {
    setSession(TODOS)
    mockGetConBatch(batchV4(), previewO15({
      chicks_available: 0, chicks_available_status: 'KNOWN', chicks_available_unknown_rows: 0,
    }), reconciliacion(116, hatcheryV4()))
    await abrirBatch()

    const chip = screen.getByTestId('cutover-chip-chicks-available')
    expect(chip.textContent?.trim()).toMatch(/:\s*0$/)
    expect(chip.textContent).not.toContain('UNKNOWN')
  })

  it('respuesta antigua sin *_status: el chip sigue pintando el número', async () => {
    setSession(TODOS)
    const { eggs_in_process_status: _a, chicks_available_status: _b, ...sinEstados } = previewO15({}).summary
    mockGetConBatch(batchV4(), { ...PREVIEW_V4, summary: { ...sinEstados, eggs_in_process: 1700, chicks_available: 25 } },
                    reconciliacion(117, hatcheryV4()))
    await abrirBatch()

    expect(screen.getByTestId('cutover-chip-eggs-in-process').textContent).toMatch(/1[.,]700/)
    expect(screen.getByTestId('cutover-chip-chicks-available').textContent).toMatch(/\b25\b/)
  })
})
