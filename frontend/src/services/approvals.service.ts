import api from './api'

export const approvalsService = {
  getPending: (params?: { lot_id?: number; limit?: number; offset?: number }) =>
    api.get<{ events: Record<string, unknown>[]; total: number }>('/approvals/pending', { params }),

  approve: (data: { event_id: number }) =>
    api.post('/approvals/approve', data),

  reject: (data: { event_id: number; observations?: string }) =>
    api.post('/approvals/reject', data),

  batchApprove: (data: { event_ids: number[] }) =>
    api.post('/approvals/batch-approve', data),

  batchReject: (data: { event_ids: number[]; observations?: string }) =>
    api.post('/approvals/batch-reject', data),
}
