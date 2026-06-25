import { useTranslation } from 'react-i18next'
import { STATUS_STYLES, type StatusKey } from '../../data/statusColors'

export type TimelineEventType =
  | 'create' | 'review' | 'correction' | 'approval' | 'rejection'
  | 'sap_send' | 'sap_error' | 'sap_confirm' | 'return' | 'consolidation' | 'view'

export interface TimelineEvent {
  id: string | number
  date: string
  action: string
  user: string
  description?: string
  type: TimelineEventType
  /** Detalle adicional (valor anterior → nuevo, motivo, etc.) */
  detail?: string
}

interface StatusTimelineProps {
  events: TimelineEvent[]
  className?: string
}

// Mapeo de TimelineEventType a StatusKey para usar colores compartidos
const TYPE_TO_STATUS: Record<TimelineEventType, StatusKey> = {
  create:        'registered',
  review:        'in_review',
  correction:    'corrected',
  approval:      'approved',
  rejection:     'rejected',
  return:        'returned',
  sap_send:      'sent_sap',
  sap_error:     'error_sap',
  sap_confirm:   'confirmed_sap',
  consolidation: 'consolidated',
  view:          'neutral',
}

/**
 * StatusTimeline — Línea de tiempo vertical para mostrar
 * la secuencia de eventos de un registro (trazabilidad/auditoría).
 *
 * Uso: detalle de operación, auditoría, historial de lote.
 */
export default function StatusTimeline({ events, className = '' }: StatusTimelineProps) {
  const { t } = useTranslation()

  if (!events || events.length === 0) return null

  return (
    <div className={`relative ${className}`}>
      {/* Línea vertical conectora */}
      <div className="absolute left-[19px] top-3 bottom-3 w-0.5 bg-slate-200 rounded-full" />

      <div className="space-y-0">
        {events.map((event) => {
          const statusKey = TYPE_TO_STATUS[event.type] || 'neutral'
          const style = STATUS_STYLES[statusKey]
          const Icon = style.icon

          return (
            <div key={event.id} className="relative flex gap-4 pb-6 last:pb-0">
              {/* Círculo indicador con color compartido */}
              <div className={`
                relative z-10 w-10 h-10 rounded-full flex items-center justify-center shrink-0
                ${style.bg} ring-4 ring-white
              `}>
                <Icon size={16} className={style.iconColor} />
              </div>

              {/* Contenido */}
              <div className="flex-1 min-w-0 pt-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-sm font-bold text-slate-800">{event.action}</span>
                  <span className="text-[11px] text-slate-400 font-medium">{event.date}</span>
                </div>

                {event.description && (
                  <p className="text-sm text-slate-600 mt-0.5">{event.description}</p>
                )}

                {event.detail && (
                  <p className="text-xs text-slate-500 mt-1 bg-slate-50 rounded-lg px-3 py-1.5 border border-slate-100">
                    {event.detail}
                  </p>
                )}

                <p className="text-xs text-slate-400 mt-1">
                  {t('common.by', 'por')} {event.user}
                </p>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
