/**
 * export.ts — Cliente de exportación Excel/PDF
 * Excel: SheetJS (xlsx) — no requiere backend
 * PDF:   jsPDF + jspdf-autotable — no requiere backend
 * Compatible con Chrome, Edge, Firefox, Safari, Opera, iOS Safari, Android Chrome
 */

import { formatFechaHora } from './dates'

// ─── Excel ────────────────────────────────────────────────────────────────────

export async function exportToExcel(
  rows: Record<string, unknown>[],
  headers: Record<string, string>,
  filename: string,
): Promise<void> {
  const { utils, writeFile } = await import('xlsx')

  // Build header row with friendly labels then data rows
  const wsData = [
    Object.values(headers),
    ...rows.map(row => Object.keys(headers).map(k => row[k] ?? '')),
  ]

  const ws = utils.aoa_to_sheet(wsData)
  const wb = utils.book_new()
  utils.book_append_sheet(wb, ws, 'Datos')
  writeFile(wb, `${filename}.xlsx`)
}

// ─── PDF ──────────────────────────────────────────────────────────────────────

export async function exportToPDF(
  rows: Record<string, unknown>[],
  headers: Record<string, string>,
  title: string,
  filename: string,
  /** `R-220` · C6: locale de la app — el export no fija idioma por su cuenta. */
  locale?: string,
): Promise<void> {
  const { default: jsPDF } = await import('jspdf')
  const { default: autoTable } = await import('jspdf-autotable')

  const doc = new jsPDF({ orientation: 'landscape', unit: 'pt', format: 'a4' })

  // Title
  doc.setFontSize(14)
  doc.setTextColor(30, 58, 95)  // #1E3A5F
  doc.text(title, 40, 40)

  // Date
  doc.setFontSize(9)
  doc.setTextColor(100, 116, 139)  // slate-500
  doc.text(formatFechaHora(new Date(), locale), 40, 56)

  const cols = Object.values(headers)
  const bodyRows = rows.map(row => Object.keys(headers).map(k => String(row[k] ?? '')))

  autoTable(doc, {
    startY: 70,
    head: [cols],
    body: bodyRows,
    styles: { fontSize: 8, cellPadding: 4 },
    headStyles: { fillColor: [30, 58, 95], textColor: 255, fontStyle: 'bold' },
    alternateRowStyles: { fillColor: [248, 250, 252] },
    margin: { left: 40, right: 40 },
  })

  doc.save(`${filename}.pdf`)
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

/** Convert a lot report API response to flat rows suitable for export */
export function lotReportToRows(report: any): Record<string, unknown>[] {
  if (!report) return []
  const lot = report.lot ?? {}
  const ob  = report.opening_balance ?? {}
  const es  = report.event_summary ?? {}

  const summary: Record<string, unknown> = {
    lot_code:    lot.lot_code ?? '',
    bird_type:   lot.bird_type ?? '',
    status:      lot.status ?? '',
    start_date:  lot.start_date ?? '',
    end_date:    lot.end_date ?? '',
    total_birds: ob.total_birds ?? '',
    males:       ob.total_males ?? '',
    females:     ob.total_females ?? '',
    total_events: es.total_events ?? '',
  }
  return [summary]
}

/** Convert a KPI response to flat rows suitable for export */
export function kpisToRows(kpis: any, lotId: number): Record<string, unknown>[] {
  if (!kpis) return []
  return [
    {
      lot_id:                   lotId,
      mortality_rate:           kpis.mortality?.mortality_rate_pct ?? '',
      total_deaths:             kpis.mortality?.total_deaths ?? '',
      feed_conversion:          kpis.feed_conversion?.feed_conversion_ratio ?? '',
      total_feed_kg:            kpis.feed_conversion?.total_feed_kg ?? '',
      total_eggs:               kpis.egg_production?.total_eggs ?? '',
      hen_day_pct:              kpis.egg_production?.hen_day_production_pct ?? '',
      chicks_born:              kpis.hatchery_yield?.total_chicks_born ?? '',
      hatchability_pct:         kpis.hatchery_yield?.hatchability_pct ?? '',
    },
  ]
}
