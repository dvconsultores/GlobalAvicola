import api from './api'

export interface OperationEvent {
  id: number
  lot_id: number
  event_type: string
  event_date: string
  status: string
  company_id: number
  farm_id?: number
  house_id?: number
  observations?: string
  registered_by_id: number
  bird_movements?: Record<string, unknown>[]
  egg_movements?: Record<string, unknown>[]
  feed_movements?: Record<string, unknown>[]
  hatchery_params?: Record<string, unknown>[]
  inspection_details?: Record<string, unknown>[]
}

export const operationsService = {
  list: (params?: {
    lot_id?: number
    farm_id?: number
    event_type?: string
    status?: string
    date_from?: string
    date_to?: string
    limit?: number
    registered_by_me?: boolean
  }) =>
    api.get<OperationEvent[]>('/operations', { params }),

  get: (id: number) =>
    api.get<OperationEvent>(`/operations/${id}`),

  create: (data: Record<string, unknown>) =>
    api.post<OperationEvent>('/operations', data),

  update: (id: number, data: Record<string, unknown>) =>
    api.put<OperationEvent>(`/operations/${id}`, data),

  submit: (id: number) =>
    api.post(`/operations/${id}/submit`),

  cancel: (id: number) =>
    api.post(`/operations/${id}/cancel`),

  getEventTypes: () =>
    api.get<string[]>('/operations/event-types'),
}
