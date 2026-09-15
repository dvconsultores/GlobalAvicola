/**
 * R-220 · Lote C (i18n) — tanda C-β: C3 (mensajes zod de lote en claves), C4 (claves
 * ausentes con fallback ES — 24 relevantes + exportaciones), C6 (formato de fecha-hora
 * de la app + cabeceras de exportación), C8 (texto EN en bundle ES y placeholders),
 * C9 (latentes: flowDesc.bird_transfer, evidence.types.signature/audio, NotificationType).
 *
 * Mayormente datos de i18n: guardas de artefacto (JSON) + guardas de fuente; el
 * formateador se prueba como unidad.
 */
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'
import * as dates from '../utils/dates'

const here = dirname(fileURLToPath(import.meta.url))
const src = (rel: string) => readFileSync(resolve(here, '..', rel), 'utf8')
const locale = (lang: 'es' | 'en') =>
  JSON.parse(readFileSync(resolve(here, '..', '..', 'public', 'locales', lang, 'translation.json'), 'utf8'))

const C4_KEYS = [
  'audit.action', 'audit.module', 'common.forbidden', 'common.loadError', 'common.loadMore',
  'common.previous', 'kpi.birthRate', 'kpi.chicksBorn', 'kpi.hatchRate', 'kpi.hatchery',
  'kpi.hatcheryYield', 'kpi.transferEfficiency', 'kpi.vaccinationEfficiency', 'lots.phaseNotFound',
  'operations.hatcheryParams', 'operations.inspections', 'operations.loaded', 'operations.water',
  'operations.waterConsumed', 'reports.onlyApproved', 'reports.onlyApprovedDetail',
  'reports.selectLot', 'users.deleteUserTitle',
]

const NUEVAS_KEYS = [
  'common.required', 'common.prev', 'common.viewDetail', 'lots.codeMin', 'dashboard.operator',
  'operations.searchTransfer', 'operations.searchPurchaseOrder', 'operations.searchTransferOrder',
  'notifications.types.lot_near_close', 'process.flowDesc.bird_transfer',
  'evidence.types.signature', 'evidence.types.audio',
]

const EQUIPOS = ['bebedero', 'comedero', 'ventilador', 'calefactor', 'nebulizador', 'iluminación', 'cortina', 'extractor', 'otro']
const EXPORT_HEADERS = ['lot_id', 'mortality_rate', 'total_deaths', 'feed_conversion', 'total_feed_kg', 'total_eggs', 'hen_day_pct', 'chicks_born', 'hatchability_pct']

function has(d: any, key: string): boolean {
  let cur = d
  for (const part of key.split('.')) {
    if (!cur || typeof cur !== 'object' || !(part in cur)) return false
    cur = cur[part]
  }
  return true
}

describe('R-220 · Lote C tanda C-β', () => {
  it('C4 · las 23 claves ausentes existen en ambos idiomas', () => {
    for (const lang of ['es', 'en'] as const) {
      const d = locale(lang)
      for (const k of C4_KEYS) expect(has(d, k), `${k} (${lang})`).toBe(true)
    }
  })

  it('C3/C6/C8/C9 · claves nuevas (zod lote, equipos, export, búsquedas, operator, latentes) en ambos idiomas', () => {
    for (const lang of ['es', 'en'] as const) {
      const d = locale(lang)
      for (const k of NUEVAS_KEYS) expect(has(d, k), `${k} (${lang})`).toBe(true)
      for (const eq of EQUIPOS) expect(has(d, `operations.equipment.${eq}`), `operations.equipment.${eq} (${lang})`).toBe(true)
      for (const h of EXPORT_HEADERS) expect(has(d, `reports.exportHeaders.${h}`), `reports.exportHeaders.${h} (${lang})`).toBe(true)
    }
  })

  it('C8 · el bundle ES ya no trae texto inglés en claves críticas', () => {
    const es = locale('es')
    expect(es.reports.sapComparisonLink).toBe('Comparación SAP')
    expect(es.users.mobile).toBe('Móvil')
  })

  it('C3 · los mensajes del esquema de lote son claves i18n', () => {
    const s = src('pages/lots/LotFormPage.tsx')
    expect(s).toContain("'lots.codeMin'")
    expect(s).toContain("'common.required'")
    expect(s.includes("'Mínimo 2 caracteres'"), 'texto ES incrustado en el esquema').toBe(false)
  })

  it('C6 · formato fecha-hora con locale de la app', () => {
    expect(typeof (dates as any).formatFechaHora).toBe('function')
    const out = (dates as any).formatFechaHora('2026-09-11T10:00:00', 'es')
    expect(out).toContain('2026')
    expect(out).not.toContain('T10:00:00')
  })

  it('C6 · export no fija es-VE y los sitios de fecha usan el formateador', () => {
    expect(src('utils/export.ts')).not.toContain("'es-VE'")
    for (const f of ['pages/review/ReviewDetail.tsx', 'pages/audit/AuditPage.tsx', 'pages/sap/SapManagerPage.tsx']) {
      expect(src(f), `${f} debe usar formatFechaHora`).toContain('formatFechaHora')
      expect(src(f), `${f} no debe usar toLocaleString del navegador`).not.toContain('.toLocaleString(')
    }
  })

  it('C6/C8 · equipos, placeholders y «Operador» traducidos en fuente', () => {
    expect(src('pages/operations/OperationFormPage.tsx')).toContain('operations.equipment.${')
    const ofp = src('pages/operations/OperationFormPage.tsx')
    expect(ofp).toContain("'operations.searchTransfer'")
    expect(ofp).toContain("'operations.searchPurchaseOrder'")
    expect(ofp).toContain("'operations.searchTransferOrder'")
    expect(ofp.includes("? 'Buscar transferencia...'"), 'placeholder ES sin t()').toBe(false)
    expect(ofp.includes("? 'Buscar orden de traslado...'"), 'placeholder ES sin t()').toBe(false)
    expect(src('pages/dashboard/DashboardPage.tsx')).toContain("t('dashboard.operator'")
  })

  it('C9 · NotificationType incluye lot_near_close (el backend ya lo emite)', () => {
    expect(src('services/notifications.ts')).toContain("'lot_near_close'")
  })

  it('C6 · las cabeceras de exportación usan claves i18n', () => {
    const s = src('pages/reports/ReportsPage.tsx')
    expect(s).toContain('reports.exportHeaders.')
    expect(s.includes("lot_id: 'Lote ID'"), 'cabeceras ES fijas en la exportación').toBe(false)
  })
})
