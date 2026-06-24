import api from './api'

export interface AuditLog {
  id: number
  company_id: number
  user_id: number
  action: string
  entity_type: string
  entity_id: number
  module: string
  previous_values?: Record<string, unknown>
  new_values?: Record<string, unknown>
  change_reason?: string
  created_at: string
}

export const auditService = {
  list: (params?: {
    user_id?: number
    lot_id?: number
    farm_id?: number
    action?: string
    module?: string
    date_from?: string
    date_to?: string
    limit?: number
  }) =>
    api.get<AuditLog[]>('/audit', { params }),

  get: (logId: number) =>
    api.get<AuditLog>(`/audit/${logId}`),

  getTimeline: (entityType: string, entityId: number) =>
    api.get<AuditLog[]>(`/audit/timeline/${entityType}/${entityId}`),
}
