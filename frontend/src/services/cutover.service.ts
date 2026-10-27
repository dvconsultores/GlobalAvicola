/**
 * GA-REQ-061 · T14 · C8 + SPEC 006 — cliente del cutover (Cargas Iniciales v2).
 * Espejo exacto de las rutas del backend; los textos viven en i18n (AC84/85).
 *
 * SPEC 006: plantilla por BU en XLSX o CSV (la BU la fija el batch), listado y detalle de
 * batches, preview funcional por BU, informe de errores descargable y reconciliación por
 * métrica con `value + status` (UNKNOWN / N/A nunca se pintan como 0).
 */
import api from './api'

export type BusinessUnitCode = 'grandparent' | 'breeder' | 'hatchery' | 'broiler'
export type TemplateFormat = 'xlsx' | 'csv'
export type MetricStatus = 'KNOWN' | 'UNKNOWN' | 'NOT_APPLICABLE'

export interface CutoverBatch {
  id: number
  company_id: number
  business_unit: BusinessUnitCode
  cutover_datetime: string
  source_type: string
  source_filename?: string | null
  source_checksum_sha256?: string | null
  template_version?: string | null
  status: string
  total_rows: number
  valid_rows: number
  invalid_rows: number
  source_system?: string | null
  source_reference?: string | null
  created_at?: string | null
  applied_at?: string | null
  rejection_reason?: string | null
}

export interface CutoverBatchList {
  items: CutoverBatch[]
  total: number
}

export interface CutoverValidationError {
  row_number: number
  column?: string | null
  field?: string | null
  error_code: string
  message: string
  received_value?: string | null
}

export interface CutoverValidation {
  batch_id: number
  status: string
  total_rows: number
  valid_rows: number
  invalid_rows: number
  errors: CutoverValidationError[]
}

export interface CutoverItem {
  id: number
  source_row_number: number
  legacy_lot_reference?: string | null
  lot_id?: number | null
  real_start_date?: string | null
  validation_status: string
  validation_errors?: unknown[] | null
}

/** Celda normalizada del contrato v2: valor + estado (vacío = UNKNOWN · 0 = KNOWN · N/A = NOT_APPLICABLE). */
export interface MetricCell {
  value: number | string | null
  status: MetricStatus
}

export interface CutoverPreviewRow {
  row_number: number
  legacy_lot_code?: string | null
  lot_id?: number | null
  status: string
  errors: number
  values: Record<string, MetricCell | undefined>
  derived: Record<string, unknown>
  unknown_metrics: number
  not_applicable_metrics: number
}

export interface CutoverPreview {
  batch_id: number
  business_unit: BusinessUnitCode
  status: string
  template_version?: string | null
  schema_id: string
  columns: string[]
  highlight: string[]
  summary: Record<string, any>
  rows: CutoverPreviewRow[]
}

export interface CutoverReconciliationLot {
  lot_id: number
  lot_code?: string | null
  legacy_lot_code?: string | null
  origin?: string | null
  business_unit?: string | null
  opening: {
    live: number
    live_males?: number
    live_females?: number
    live_mixed?: number
    /** `null` = UNKNOWN: jamás se presenta como 0 (AC77). */
    historical_mortality: number | null
    mortality_status: string
    historical_culls?: number | null
    culls_status?: string
    feed_kg?: number | null
    feed_status: string
    egg_production?: number | null
    egg_production_status?: string
    chicks_hatched?: number | null
    chicks_hatched_status?: string
    hatchery?: Record<string, any> | null
    [k: string]: any
  }
  post: { mortality: number; culls: number; feed_kg: number | null; [k: string]: any }
  lifetime: { mortality: number | null; [k: string]: any }
  current_live: number
  current?: Record<string, number | null>
}

export interface CutoverReconciliation {
  batch_id: number
  company_id: number
  business_unit: BusinessUnitCode
  cutover_datetime: string
  status: string
  source: {
    type: string
    system?: string | null
    reference?: string | null
    filename?: string | null
    checksum?: string | null
    template_version?: string | null
  }
  items: number
  openings: number
  unknown_metrics: number
  applied_by_id?: number | null
  applied_at?: string | null
  lots: CutoverReconciliationLot[]
}

export interface OpeningCorrection {
  id: number
  opening_id: number
  field: string
  old_value?: string | null
  new_value?: string | null
  delta?: string | null
  reason: string
  requested_by_id: number
  approved_by_id?: number | null
  created_at: string
  applied_at?: string | null
}

export const BUSINESS_UNITS: BusinessUnitCode[] = ['grandparent', 'breeder', 'hatchery', 'broiler']

export const cutoverService = {
  create: (data: { business_unit: BusinessUnitCode; cutover_datetime: string }) =>
    api.post<CutoverBatch>('/cutover-batches', data),

  list: (params?: { status?: string; business_unit?: BusinessUnitCode; limit?: number; offset?: number }) =>
    api.get<CutoverBatchList>('/cutover-batches', { params }),
  get: (batchId: number) => api.get<CutoverBatch>(`/cutover-batches/${batchId}`),

  upload: (batchId: number, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post<CutoverBatch>(`/cutover-batches/${batchId}/upload`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  /** Plantilla v2 de la BU. Con `batchId` la BU la fija el batch (y `Meta.cutover_datetime` viaja rellena). */
  template: (businessUnit: BusinessUnitCode, opts: { format?: TemplateFormat; batchId?: number; cutoverDatetime?: string } = {}) =>
    api.get(`/cutover-templates/${businessUnit}`, {
      responseType: 'blob',
      params: {
        format: opts.format ?? 'xlsx',
        ...(opts.batchId ? { batch_id: opts.batchId } : {}),
        ...(opts.cutoverDatetime ? { cutover_datetime: opts.cutoverDatetime } : {}),
      },
    }),

  submit: (batchId: number) => api.post<CutoverBatch>(`/cutover-batches/${batchId}/submit`),
  approve: (batchId: number) => api.post<CutoverBatch>(`/cutover-batches/${batchId}/approve`),
  reject: (batchId: number, reason: string) =>
    api.post<CutoverBatch>(`/cutover-batches/${batchId}/reject`, { reason }),
  apply: (batchId: number) => api.post<CutoverBatch>(`/cutover-batches/${batchId}/apply`),

  validation: (batchId: number) =>
    api.get<CutoverValidation>(`/cutover-batches/${batchId}/validation`),
  errorsReport: (batchId: number, format: TemplateFormat) =>
    api.get(`/cutover-batches/${batchId}/errors`, { responseType: 'blob', params: { format } }),
  preview: (batchId: number) => api.get<CutoverPreview>(`/cutover-batches/${batchId}/preview`),
  items: (batchId: number) =>
    api.get<{ items: CutoverItem[] }>(`/cutover-batches/${batchId}/items`),
  reconciliation: (batchId: number) =>
    api.get<CutoverReconciliation>(`/cutover-batches/${batchId}/reconciliation`),

  corrections: (openingId: number) =>
    api.get<{ items: OpeningCorrection[] }>(`/opening-balances/${openingId}/corrections`),
  correctOpening: (openingId: number, data: { field: string; new_value: number; reason: string }) =>
    api.post<OpeningCorrection>(`/opening-balances/${openingId}/corrections`, data),
}

/** Descarga un blob con el nombre indicado (sin dejar el object URL colgando). */
export function descargarBlob(contenido: Blob, nombre: string): void {
  const url = URL.createObjectURL(contenido)
  const enlace = document.createElement('a')
  enlace.href = url
  enlace.download = nombre
  enlace.click()
  URL.revokeObjectURL(url)
}

export default cutoverService
