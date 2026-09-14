import api from './api'

/** `R-207` · superficie de reverso. Contrato existente:
 * `POST /reversals {event_id, reason}` ⇒ `ReversalRead` (contrapartida en `reversal_event_id`). */
export interface ReversalRead {
  id: number
  original_event_id: number
  reversal_event_id: number | null
  status?: string
  reason?: string
  created_at?: string
}

export const reversalsService = {
  solicitar: (eventId: number, reason: string) =>
    api.post<ReversalRead>('/reversals', { event_id: eventId, reason }),

  porEvento: (eventId: number) =>
    api.get<ReversalRead[]>(`/reversals/event/${eventId}`),
}
