import api from './api'

export interface SapReference {
  id: number
  company_id: number
  ref_type: string
  sap_code: string
  description: string
  quantity?: number
  unit?: string
  extra_data?: Record<string, unknown>
}

export interface SapSyncJob {
  id: number
  company_id: number
  direction: 'import' | 'export'
  status: string
  total_records: number
  success_count: number
  error_count: number
}

export interface SapPayload {
  id: number
  company_id: number
  sync_job_id?: number
  idempotency_key: string
  status: string
  retry_count: number
}

/** SPEC 005 · estado del inbound SAP HANA Cloud (solo lectura). Nunca trae secretos. */
export interface SapInboundReadiness {
  phase: 'READ_ONLY_INBOUND'
  status: string
  configured: boolean
  connected: boolean
  simulated: boolean
  missing: string[]
  outbound_enabled: boolean
  write_operations_allowed: false
}

export interface SapInboundJob {
  id: number
  sync_request_id: string
  object_type: string
  status: 'in_progress' | 'completed' | 'partial' | 'failed' | 'skipped'
  rows_read: number
  rows_raw: number
  rows_promoted: number
  rows_pending_mapping: number
  error_code?: string | null
  error_message?: string | null
  completed_at?: string | null
}

export interface SapConnectionCheck {
  inbound_hana: SapInboundReadiness
  outbound: { enabled: boolean; delivers_to_sap: boolean; mode: string; adapter: string }
  connected: boolean
  adapter: string
  delivers_to_sap: boolean
  mode: string
}

export const sapInboundService = {
  readiness: () => api.get<SapInboundReadiness>('/sap/inbound/readiness'),
  objects: () => api.get<{ objects: Record<string, unknown>[] }>('/sap/inbound/objects'),
  sync: (data: { object_types?: string[]; date_from?: string; date_to?: string } = {}) =>
    api.post<{ sync_request_id: string | null; jobs: SapInboundJob[] }>('/sap/inbound/sync', data),
  syncObject: (objectType: string, data: { date_from?: string; date_to?: string } = {}) =>
    api.post<{ sync_request_id: string | null; jobs: SapInboundJob[] }>(`/sap/inbound/sync/${objectType}`, data),
  jobs: (params?: { limit?: number; offset?: number; object_type?: string }) =>
    api.get<{ jobs: SapInboundJob[]; total: number }>('/sap/inbound/jobs', { params }),
  records: (params?: { limit?: number; offset?: number; object_type?: string; mapping_status?: string; promotion_status?: string }) =>
    api.get<{ records: Record<string, unknown>[]; total: number }>('/sap/inbound/records', { params }),
  errors: (params?: { limit?: number; offset?: number }) =>
    api.get<{ records: Record<string, unknown>[]; jobs: SapInboundJob[] }>('/sap/inbound/errors', { params }),
}

export const sapService = {
  // `/sap/references/import` espera `{ references: [...] }` (esquema `SapReferenceImportRequest`).
  importReferences: (data: { references: { ref_type: string; sap_code: string; description?: string; quantity?: number; extra_data?: Record<string, unknown> }[] }) =>
    api.post<SapReference[]>('/sap/references/import', data),

  listReferences: (params?: { ref_type?: string; limit?: number }) =>
    api.get<{ references: SapReference[] }>('/sap/references', { params }),

  consolidate: () =>
    api.post('/sap/consolidate'),

  listConsolidated: () =>
    api.get('/sap/consolidated'),

  exportToSap: () =>
    api.post<{ sync_job_id: number }>('/sap/export'),

  retry: () =>
    api.post('/sap/retry'),

  listSyncJobs: (params?: { limit?: number }) =>
    api.get<{ jobs: SapSyncJob[] }>('/sap/sync/jobs', { params }),

  listPayloads: (params?: { limit?: number }) =>
    api.get<{ payloads: SapPayload[] }>('/sap/payloads', { params }),

  listErrors: () =>
    api.get('/sap/errors'),

  checkConnection: () =>
    api.get<SapConnectionCheck>('/sap/connection-check'),
}
