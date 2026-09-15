/**
 * GA-REQ-061 · T14 · C8 — cliente del cutover (Cargas Iniciales).
 * Espejo exacto de las rutas del backend; los textos viven en i18n (AC84/85).
 */
import api from './api'

export type BusinessUnitCode = 'grandparent' | 'breeder' | 'hatchery' | 'broiler'

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

export interface CutoverReconciliationLot {
  lot_id: number
  legacy_lot_code?: string | null
  origin?: string | null
  opening: {
    live: number
    /** `null` = UNKNOWN: jamás se presenta como 0 (AC77). */
    historical_mortality: number | null
    mortality_status: string
    feed_status: string
  }
  post: { mortality: number; culls: number; feed_kg: number | null }
  lifetime: { mortality: number | null }
  current_live: number
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

export const cutoverService = {
  create: (data: { business_unit: BusinessUnitCode; cutover_datetime: string }) =>
    api.post<CutoverBatch>('/cutover-batches', data),

  upload: (batchId: number, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post<CutoverBatch>(`/cutover-batches/${batchId}/upload`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  /** Plantilla Excel v1 de la BU (AC45: la versión viaja en la hoja Meta). */
  template: (businessUnit: BusinessUnitCode) =>
    api.get(`/cutover-templates/${businessUnit}`, { responseType: 'blob' }),

  submit: (batchId: number) => api.post<CutoverBatch>(`/cutover-batches/${batchId}/submit`),
  approve: (batchId: number) => api.post<CutoverBatch>(`/cutover-batches/${batchId}/approve`),
  reject: (batchId: number, reason: string) =>
    api.post<CutoverBatch>(`/cutover-batches/${batchId}/reject`, { reason }),
  apply: (batchId: number) => api.post<CutoverBatch>(`/cutover-batches/${batchId}/apply`),

  validation: (batchId: number) =>
    api.get<CutoverValidation>(`/cutover-batches/${batchId}/validation`),
  items: (batchId: number) =>
    api.get<{ items: CutoverItem[] }>(`/cutover-batches/${batchId}/items`),
  reconciliation: (batchId: number) =>
    api.get<CutoverReconciliation>(`/cutover-batches/${batchId}/reconciliation`),

  corrections: (openingId: number) =>
    api.get<{ items: OpeningCorrection[] }>(`/opening-balances/${openingId}/corrections`),
  correctOpening: (openingId: number, data: { field: string; new_value: number; reason: string }) =>
    api.post<OpeningCorrection>(`/opening-balances/${openingId}/corrections`, data),
}

export default cutoverService
