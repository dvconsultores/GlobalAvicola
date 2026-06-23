import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import api from '../../services/api'

const EVENT_LABELS: Record<string, string> = {
  bird_reception: 'Recepción de Aves', bird_distribution: 'Distribución', bird_transfer: 'Transferencia',
  bird_exit: 'Salida de Aves', feed_registration: 'Alimento', weight_recording: 'Pesaje',
  mortality_recording: 'Mortalidad', cull_recording: 'Descarte', vaccination: 'Vacunación',
  medication: 'Medicación', farm_inspection: 'Inspección Granja', transport_inspection: 'Inspección Transporte',
  hatchery_inspection: 'Inspección Incubadora', egg_collection: 'Recolección Huevos', egg_classification: 'Clasificación',
  egg_dispatch: 'Despacho Huevos', egg_reception_hatchery: 'Recepción Huevos Incub.',
  incubation_load: 'Carga Incubación', ovoscopy: 'Ovoscopia', transfer_to_hatcher: 'Transferencia a Nacedora',
  birth_registration: 'Nacimiento', chick_dispatch: 'Despacho Pollitos', lot_closure: 'Cierre de Lote',
  grandparent_import: 'Importación',
}

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
      const params: any = { limit: 50 }
      if (lotId) params.lot_id = lotId
      if (eventType) params.event_type = eventType
      const r = await api.get('/operations', { params })
      setEvents(r.data)
    } catch { setEvents([]) }
    finally { setLoading(false) }
  }, [lotId, eventType])

  useEffect(() => { fetchEvents() }, [fetchEvents])

  return (
    <div className="p-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">{t('nav.operations')}</h1>
          <p className="text-sm text-slate-500">{events.length} registros</p>
        </div>
        <Link to="/operations/new" className="inline-flex items-center h-10 px-4 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition">
          + {t('common.create')}
        </Link>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-4">
        <input type="number" placeholder="Lote ID" value={lotId} onChange={e => setLotId(e.target.value)} className="h-10 px-3 border border-slate-300 rounded-lg text-sm w-28" />
        <select value={eventType} onChange={e => setEventType(e.target.value)} className="h-10 px-3 border border-slate-300 rounded-lg text-sm">
          <option value="">Todos los tipos</option>
          {Object.entries(EVENT_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
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
                  <span className="text-lg">{EVENT_LABELS[ev.event_type]?.split(' ')[0] || '📋'}</span>
                  <span className="text-sm font-medium text-slate-700">{EVENT_LABELS[ev.event_type]?.split(' ').slice(1).join(' ') || ev.event_type}</span>
                  <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[ev.status] || 'bg-slate-100 text-slate-600'}`}>{ev.status}</span>
                </div>
                <p className="text-xs text-slate-500">Lote #{ev.lot_id} — {ev.event_date}</p>
              </div>
              <Link to={`/operations/${ev.id}`} className="text-blue-600 text-sm hover:underline ml-3">{t('common.edit')}</Link>
            </div>
          ))}
        </div>
      }
    </div>
  )
}
