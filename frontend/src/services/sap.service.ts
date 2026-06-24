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

export const sapService = {
  importReferences: (data: { ref_type: string; entries: Record<string, unknown>[] }) =>
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
    api.get<{ connected: boolean; adapter: string }>('/sap/connection-check'),
}
