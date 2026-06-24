import api from './api'

export interface CorrectionLog {
  id: number
  event_id: number
  field_name: string
  original_value: unknown
  corrected_value: unknown
  corrected_by_id: number
  correction_type_id?: number
  reason?: string
  created_at: string
}

export const correctionsService = {
  create: (data: {
    event_id: number
    field_name: string
    original_value: unknown
    corrected_value: unknown
    correction_type_id?: number
    reason?: string
  }) =>
    api.post<CorrectionLog>('/corrections', data),

  getByEvent: (eventId: number) =>
    api.get<CorrectionLog[]>(`/corrections/event/${eventId}`),

  list: (params?: { lot_id?: number }) =>
    api.get<CorrectionLog[]>('/corrections', { params }),
}
