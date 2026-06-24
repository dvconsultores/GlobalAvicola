import { type LucideIcon } from 'lucide-react'
import {
  FileText, Search, RotateCcw, CheckCircle, XCircle, Send,
  Clock, RefreshCw, Ban, Package, AlertTriangle, Eye,
} from 'lucide-react'
import { useTranslation } from 'react-i18next'

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

const EVENT_STYLES: Record<TimelineEventType, { bg: string; icon: LucideIcon; color: string; dot: string }> = {
  create:        { bg: 'bg-blue-100', icon: FileText,    color: 'text-blue-600',   dot: 'bg-blue-500' },
  review:        { bg: 'bg-indigo-100', icon: Search,    color: 'text-indigo-600', dot: 'bg-indigo-500' },
  correction:    { bg: 'bg-purple-100', icon: RotateCcw, color: 'text-purple-600', dot: 'bg-purple-500' },
  approval:      { bg: 'bg-emerald-100', icon: CheckCircle, color: 'text-emerald-600', dot: 'bg-emerald-500' },
  rejection:     { bg: 'bg-red-100', icon: XCircle,     color: 'text-red-600',    dot: 'bg-red-500' },
  return:        { bg: 'bg-orange-100', icon: RotateCcw, color: 'text-orange-600', dot: 'bg-orange-500' },
  sap_send:      { bg: 'bg-blue-100', icon: Send,       color: 'text-blue-600',   dot: 'bg-blue-500' },
  sap_error:     { bg: 'bg-red-100', icon: AlertTriangle, color: 'text-red-600',  dot: 'bg-red-500' },
  sap_confirm:   { bg: 'bg-emerald-100', icon: CheckCircle, color: 'text-emerald-600', dot: 'bg-emerald-500' },
  consolidation: { bg: 'bg-teal-100', icon: Package,    color: 'text-teal-600',   dot: 'bg-teal-500' },
  view:          { bg: 'bg-slate-100', icon: Eye,       color: 'text-slate-600',  dot: 'bg-slate-400' },
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
        {events.map((event, index) => {
          const style = EVENT_STYLES[event.type] || EVENT_STYLES.view
          const Icon = style.icon

          return (
            <div key={event.id} className="relative flex gap-4 pb-6 last:pb-0">
              {/* Círculo indicador */}
              <div className={`
                relative z-10 w-10 h-10 rounded-full flex items-center justify-center shrink-0
                ${style.bg} ring-4 ring-white
              `}>
                <Icon size={16} className={style.color} />
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
