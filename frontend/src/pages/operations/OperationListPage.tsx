import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import api from '../../services/api'
import { PROCESS_STAGES, flowForStage, type StageKey } from '../../data/processCatalog'

const getEventLabel = (t: any, key: string) => t(`eventsShort.${key}`, key)

const STATUS_COLORS: Record<string, string> = {
  registered: 'bg-blue-100 text-blue-800', pending_review: 'bg-yellow-100 text-yellow-800',
  approved: 'bg-green-100 text-green-800', rejected: 'bg-red-100 text-red-800',
  cancelled: 'bg-slate-100 text-slate-600',
}

export default function OperationListPage() {
  const { t } = useTranslation()
  const [events, setEvents] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [lotId, setLotId] = useState('')
  const [eventType, setEventType] = useState('')

  const fetchEvents = useCallback(async () => {
    setLoading(true)
    try {
      const params: any = { limit: 100 }
      if (lotId) params.lot_id = lotId
      // For stage-based filter: fetch all and filter client-side
      // (backend doesn't support multi event_type yet)
      if (eventType && !eventType.startsWith('__stage__')) {
        params.event_type = eventType
      }
      const r = await api.get('/operations', { params })
      let result = r.data ?? []
      // Client-side filter by stage
      if (eventType && eventType.startsWith('__stage__')) {
        const stageKey = eventType.replace('__stage__', '') as StageKey
        const flowEvents = new Set(flowForStage(stageKey).map(s => s.event))
        result = result.filter((ev: any) => flowEvents.has(ev.event_type))
      }
      setEvents(result)
    } catch { setEvents([]) }
    finally { setLoading(false) }
  }, [lotId, eventType])

  useEffect(() => { fetchEvents() }, [fetchEvents])

  return (
    <div className="p-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">{t('nav.operations')}</h1>
          <p className="text-sm text-slate-500">{events.length} {t('common.results')}</p>
        </div>
        <Link to="/processes" className="inline-flex items-center h-10 px-4 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition">
          + {t('common.create')}
        </Link>
      </div>

      {/* Filters — stage-based instead of old 24-event flat dropdown */}
      <div className="flex gap-3 mb-4 flex-wrap">
        <input type="number" placeholder={t('review.lot') + ' ID'} value={lotId} onChange={e => setLotId(e.target.value)} className="h-10 px-3 border border-slate-300 rounded-lg text-sm w-28" />
        <select value={eventType} onChange={e => setEventType(e.target.value)} className="h-10 px-3 border border-slate-300 rounded-lg text-sm max-w-[200px]">
          <option value="">{t('common.allTypes')}</option>
          <optgroup label={t('process.hub.title', 'Etapas de producción')}>
            {PROCESS_STAGES.map(s => (
              <option key={s.key} value={`__stage__${s.key}`}>
                {t(s.labelKey, s.fallback)}
              </option>
            ))}
          </optgroup>
        </select>
      </div>

      {/* Event list (mobile cards) */}
      {loading ? <p className="text-slate-500 text-sm py-8 text-center">{t('common.loading')}</p>
        : events.length === 0 ? <p className="text-slate-400 text-sm py-8 text-center">{t('common.noResults')}</p>
        : <div className="space-y-3">
          {events.map((ev: any) => (
            <div key={ev.id} className="bg-white rounded-xl shadow-sm border border-slate-200 p-4 flex items-center justify-between">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-lg">📋</span>
                  <span className="text-sm font-medium text-slate-700">{getEventLabel(t, ev.event_type)}</span>
                  <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[ev.status] || 'bg-slate-100 text-slate-600'}`}>{ev.status}</span>
                </div>
                <p className="text-xs text-slate-500">{t('review.lot')} #{ev.lot_id} — {ev.event_date}</p>
              </div>
              <Link to={`/operations/${ev.id}`} className="text-blue-600 text-sm hover:underline ml-3">{t('common.edit')}</Link>
            </div>
          ))}
        </div>
      }
    </div>
  )
}
