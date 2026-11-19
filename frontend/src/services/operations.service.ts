import api from './api'

export interface OperationEvent {
  id: number
  lot_id?: number
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

/** `SPEC 016` · `O-3`: destino posible de un pendiente — `code` canónico + `name_key` i18n.
 *  Nunca viaja el id interno de la habilitación (decisión de seguridad `GA-REM-040`). */
export interface ClassificationCandidate {
  code: string
  name_key?: string | null
}

/** `SPEC 016` · `O-3`: cuerpo de `POST /operations/{id}/classify`. */
export interface ClassifyEventPayload {
  business_unit_code: string
  reason: string
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

  /** `SPEC 016` · `O-3`: cadenas a las que se puede clasificar ESTE pendiente (403/404 del
   *  backend se propagan: no se ofrecen destinos sobre un registro que luego se rechazaría). */
  getClassificationCandidates: (eventId: number) =>
    api.get<ClassificationCandidate[]>(`/operations/${eventId}/classification-candidates`),

  /** `SPEC 016` · `O-3`: fija la cadena productiva del pendiente. La unidad se envía por su
   *  CÓDIGO; el backend la resuelve contra la empresa del evento. */
  classifyEvent: (eventId: number, data: ClassifyEventPayload) =>
    api.post<OperationEvent>(`/operations/${eventId}/classify`, data),
}
