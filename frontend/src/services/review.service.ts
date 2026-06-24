import api from './api'

export interface ReviewBatch {
  id: number
  batch_name: string
  status: string
  total_events: number
  approved_count: number
  rejected_count: number
  created_by_id: number
  notes?: string
}

export interface ApprovalAction {
  id: number
  event_id: number
  action_type: string
  user_id: number
  observations?: string
  created_at: string
}

export const reviewService = {
  getPending: (params?: {
    lot_id?: number
    event_type?: string
    date_from?: string
    date_to?: string
    farm_id?: number
    status?: string
    operator_id?: number
    limit?: number
    offset?: number
  }) =>
    api.get<{ events: ApprovalAction[]; total: number }>('/review/pending', { params }),

  createBatch: (data: { batch_name: string; event_ids: number[] }) =>
    api.post<ReviewBatch>('/review/batches', data),

  listBatches: (params?: { limit?: number }) =>
    api.get<ReviewBatch[]>('/review/batches', { params }),

  startReview: (eventId: number) =>
    api.post(`/review/start/${eventId}`),

  returnEvent: (data: { event_id: number; observations?: string }) =>
    api.post('/review/return', data),

  completeReview: (data: { event_id: number }) =>
    api.post('/review/complete', data),
}
