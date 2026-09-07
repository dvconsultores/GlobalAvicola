/**
 * Cliente de la bandeja interna — `OD-07` · `GA-REM-038`.
 *
 * El canal es interno: no hay correo, ni push, ni suscripciones. Estas cuatro llamadas son
 * todo lo que el backend expone, y no hay ninguna de creación: las notificaciones las produce
 * el servidor cuando ocurre el evento del negocio.
 */
import api from './api'

/**
 * Los cinco tipos accionables de `docs/02 §3.14`. Falta el sexto —«lote próximo a cierre»—
 * porque «próximo» no está definido en ninguna fuente y `OD-08` sigue abierta en esa mitad.
 */
export type NotificationType =
  | 'record_rejected'
  | 'sap_send_failed'
  | 'mortality_over_threshold'
  | 'weight_out_of_standard'
  | 'review_pending_24h'

export interface Notification {
  id: number
  company_id: number
  recipient_user_id: number
  notification_type: NotificationType
  /** Datos con los que se compone el texto. El backend no guarda la frase redactada. */
  payload: Record<string, unknown>
  related_entity_type: string | null
  related_entity_id: number | null
  created_at: string
  /** `null` es sin leer. */
  read_at: string | null
}

export async function listNotifications(limit = 20): Promise<Notification[]> {
  const r = await api.get<Notification[]>('/notifications', { params: { limit } })
  return r.data
}

export async function getUnreadCount(): Promise<number> {
  const r = await api.get<{ unread: number }>('/notifications/unread-count')
  return r.data.unread
}

export async function markRead(id: number): Promise<Notification> {
  const r = await api.patch<Notification>(`/notifications/${id}/read`)
  return r.data
}

/**
 * A dónde lleva un aviso, o `null` si no hay pantalla destino.
 *
 * Devolver `null` es deliberado: un enlace roto es peor que ninguno. `sap_payload` no tiene
 * vista propia, de modo que ese aviso se lee y no navega.
 */
export function destino(n: Notification): string | null {
  if (n.related_entity_type === 'operational_event' && n.related_entity_id) {
    return `/operations/${n.related_entity_id}`
  }
  return null
}
