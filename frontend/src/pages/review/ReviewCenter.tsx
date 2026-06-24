import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { CheckCircle, Check, Play, Undo2, ZoomIn, Package, Search } from 'lucide-react'
import api from '../../services/api'
import { useToast, getErrorMessage } from '../../components/Toast'
import { EVENT_ICON_MAP } from '../../data/processCatalog'

const EVT_KEYS = Object.keys(EVENT_ICON_MAP)

const getEventLabel = (t: any, key: string) => t(`eventsShort.${key}`, key)

const STATUS_COLORS: Record<string, string> = {
  registered: 'bg-sky-100 text-sky-800', pending_review: 'bg-amber-100 text-amber-800',
  in_review: 'bg-indigo-100 text-indigo-800', returned: 'bg-orange-100 text-orange-800',
  corrected: 'bg-teal-100 text-teal-800', approved: 'bg-emerald-100 text-emerald-800',
  rejected: 'bg-red-100 text-red-800', cancelled: 'bg-slate-100 text-slate-600',
}

export default function ReviewCenter() {
  const { t } = useTranslation()
  const toast = useToast()
  const [events, setEvents] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [_error, _setError] = useState('')
  const [lotId, setLotId] = useState('')
  const [eventType, setEventType] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [farmId, setFarmId] = useState('')
  const [status, setStatus] = useState('')
  const [operatorId, setOperatorId] = useState('')
  const [farms, setFarms] = useState<any[]>([])
  const [users, setUsers] = useState<any[]>([])
  const [page, setPage] = useState(0)
  const limit = 20

  const fetchEvents = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({ limit: String(limit), offset: String(page * limit) })
      if (lotId) params.set('lot_id', lotId)
      if (eventType) params.set('event_type', eventType)
      if (dateFrom) params.set('date_from', dateFrom)
      if (dateTo) params.set('date_to', dateTo)
      if (farmId) params.set('farm_id', farmId)
      if (status) params.set('status', status)
      if (operatorId) params.set('operator_id', operatorId)
      const { data } = await api.get(`/review/pending?${params}`)
      setEvents(data.events || [])
      setTotal(data.total || 0)
    } catch (err: any) {
      const msg = getErrorMessage(err, t('review.errorLoading'))

      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }, [lotId, eventType, dateFrom, dateTo, farmId, status, operatorId, page])

  useEffect(() => { fetchEvents() }, [fetchEvents])
  useEffect(() => {
    api.get('/masters/farms?limit=100').then(r => setFarms(r.data || [])).catch(() => {})
    api.get('/users?limit=100').then(r => setUsers(r.data || [])).catch(() => {})
  }, [])

  const handleAction = async (eventId: number, action: 'start' | 'return' | 'complete') => {
    const observations = action === 'return' ? prompt(t('review.obsPrompt')) : undefined
    if (action === 'return' && !observations) return

    try {
      if (action === 'start') await api.post(`/review/start/${eventId}`)
      else if (action === 'complete') await api.post('/review/complete', { event_id: eventId })
      else if (action === 'return') await api.post('/review/return', { event_id: eventId, observations })
      toast.success(t('review.actionCompleted', { action }))
      fetchEvents()
    } catch (err: any) {
      toast.error(getErrorMessage(err, t('review.errorAction')))
    }
  }

  const handleCreateBatch = async () => {
    const selected = events.filter((e: any) => e._checked)
    if (selected.length === 0) {
      toast.warning(t('common.noSelection'))
      return
    }
    const name = prompt(t('review.batchNamePrompt'))
    if (!name) return
    try {
      await api.post('/review/batches', { batch_name: name, event_ids: selected.map((e: any) => e.id) })
      toast.success(t('review.batchCreated', { name, count: selected.length }))
      fetchEvents()
    } catch (err: any) {
      toast.error(getErrorMessage(err, t('review.errorCreateBatch')))
    }
  }

  const toggleCheck = (id: number) => {
    setEvents(prev => prev.map(e => e.id === id ? { ...e, _checked: !e._checked } : e))
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-[#1E3A5F] flex items-center gap-2"><Search size={24} /> {t('review.center')}</h1>
        <div className="flex gap-2">
          <button onClick={handleCreateBatch} className="bg-[#1E3A5F] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-800 transition flex items-center gap-1.5">
            <Package size={16} /> {t('review.createBatch')}
          </button>
          <Link to="/approvals" className="bg-emerald-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-emerald-700 transition flex items-center gap-1.5">
            <CheckCircle size={16} /> {t('nav.approvals')}
          </Link>
        </div>
      </div>

      {/* Filters — G-10: Added farm, status, operator filters */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4 mb-4 flex flex-wrap gap-3">
        <input type="number" placeholder={t('review.lot') + ' ID'} value={lotId} onChange={e => { setLotId(e.target.value); setPage(0) }}
          className="border border-slate-300 rounded-lg px-3 py-2 text-sm w-28" />
        <select value={farmId} onChange={e => { setFarmId(e.target.value); setPage(0) }}
          className="border border-slate-300 rounded-lg px-3 py-2 text-sm">
          <option value="">{t('review.allFarms')}</option>
          {farms.map((f: any) => <option key={f.id} value={f.id}>{f.name}</option>)}
        </select>
        <select value={eventType} onChange={e => { setEventType(e.target.value); setPage(0) }}
          className="border border-slate-300 rounded-lg px-3 py-2 text-sm">
          <option value="">{t('common.allTypes')}</option>
          {EVT_KEYS.map((k) => (<option key={k} value={k}>{getEventLabel(t, k)}</option>))}
        </select>
        <select value={status} onChange={e => { setStatus(e.target.value); setPage(0) }}
          className="border border-slate-300 rounded-lg px-3 py-2 text-sm">
          <option value="">{t('review.allStatuses')}</option>
          {Object.entries(STATUS_COLORS).map(([k]) => (<option key={k} value={k}>{k}</option>))}
        </select>
        <select value={operatorId} onChange={e => { setOperatorId(e.target.value); setPage(0) }}
          className="border border-slate-300 rounded-lg px-3 py-2 text-sm">
          <option value="">{t('review.allOperators')}</option>
          {users.map((u: any) => <option key={u.id} value={u.id}>{u.username}</option>)}
        </select>
        <input type="date" value={dateFrom} onChange={e => { setDateFrom(e.target.value); setPage(0) }}
          className="border border-slate-300 rounded-lg px-3 py-2 text-sm" />
        <input type="date" value={dateTo} onChange={e => { setDateTo(e.target.value); setPage(0) }}
          className="border border-slate-300 rounded-lg px-3 py-2 text-sm" />
        <span className="text-sm text-slate-500 self-center ml-auto">{total} {t('common.results')}</span>
      </div>

      {/* Mobile Cards */}
      <div className="lg:hidden space-y-3">
        {loading && <p className="text-slate-500 text-center py-8">{t('common.loading')}</p>}
        {!loading && events.length === 0 && <p className="text-slate-500 text-center py-8">{t('common.noResults')}</p>}
        {events.map((event: any) => (
          <div key={event.id} className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
            <div className="flex items-start gap-3">
              <input type="checkbox" checked={!!event._checked} onChange={() => toggleCheck(event.id)}
                className="mt-1 h-4 w-4 rounded border-slate-300" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-semibold text-slate-800">#{event.id}</span>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[event.status] || 'bg-slate-100'}`}>
                    {event.status}
                  </span>
                </div>
                <p className="text-sm text-slate-600">{getEventLabel(t, event.event_type)}</p>
                <p className="text-xs text-slate-400">{t('review.lotPrefix')}{event.lot_id} | {event.event_date}</p>
              </div>
            </div>
            <div className="flex gap-2 mt-3 border-t border-slate-100 pt-3">
              {event.status === 'pending_review' && (
                <button onClick={() => handleAction(event.id, 'start')}
                  className="flex-1 bg-indigo-100 text-indigo-700 px-3 py-1.5 rounded-lg text-xs font-medium hover:bg-indigo-200 transition flex items-center justify-center gap-1">
                  <Play size={14} /> {t('review.start')}
                </button>
              )}
              {event.status === 'in_review' && (
                <>
                  <button onClick={() => handleAction(event.id, 'complete')}
                    className="flex-1 bg-teal-100 text-teal-700 px-3 py-1.5 rounded-lg text-xs font-medium hover:bg-teal-200 transition flex items-center justify-center gap-1">
                    <Check size={14} /> {t('review.complete')}
                  </button>
                  <button onClick={() => handleAction(event.id, 'return')}
                    className="flex-1 bg-orange-100 text-orange-700 px-3 py-1.5 rounded-lg text-xs font-medium hover:bg-orange-200 transition flex items-center justify-center gap-1">
                    <Undo2 size={14} /> {t('review.return')}
                  </button>
                </>
              )}
              <Link to={`/review/${event.id}`}
                className="flex-1 bg-slate-100 text-slate-700 px-3 py-1.5 rounded-lg text-xs font-medium hover:bg-slate-200 transition text-center flex items-center justify-center gap-1">
                <ZoomIn size={14} /> {t('review.detail')}
              </Link>
            </div>
          </div>
        ))}
      </div>

      {/* Desktop Table */}
      <div className="hidden lg:block bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="w-10 px-4 py-3 text-left">
                <input type="checkbox" onChange={e => setEvents(prev => prev.map(ev => ({ ...ev, _checked: e.target.checked })))} />
              </th>
              <th className="px-4 py-3 text-left font-semibold text-slate-600">{t('review.id')}</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-600">{t('common.type')}</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-600">{t('review.lot')}</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-600">{t('common.date')}</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-600">{t('common.status')}</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-600">{t('common.actions')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading && (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-slate-500">{t('common.loading')}</td></tr>
            )}
            {!loading && events.length === 0 && (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-slate-500">{t('common.noResults')}</td></tr>
            )}
            {events.map((event: any) => (
              <tr key={event.id} className="hover:bg-slate-50 transition">
                <td className="px-4 py-3">
                  <input type="checkbox" checked={!!event._checked} onChange={() => toggleCheck(event.id)} className="rounded" />
                </td>
                <td className="px-4 py-3 font-mono text-xs">#{event.id}</td>
                <td className="px-4 py-3">{getEventLabel(t, event.event_type)}</td>
                <td className="px-4 py-3 font-mono text-xs">L-{event.lot_id}</td>
                <td className="px-4 py-3 text-slate-500">{event.event_date}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[event.status] || 'bg-slate-100'}`}>
                    {event.status}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-1.5">
                    {event.status === 'pending_review' && (
                      <button onClick={() => handleAction(event.id, 'start')}
                        className="bg-indigo-100 text-indigo-700 px-2.5 py-1 rounded text-xs font-medium hover:bg-indigo-200 transition flex items-center gap-1">
                        <Play size={12} /> Iniciar
                      </button>
                    )}
                    {event.status === 'in_review' && (
                      <>
                        <button onClick={() => handleAction(event.id, 'complete')}
                          className="bg-teal-100 text-teal-700 px-2.5 py-1 rounded text-xs font-medium hover:bg-teal-200 transition flex items-center gap-1">
                          <Check size={12} /> Completar
                        </button>
                        <button onClick={() => handleAction(event.id, 'return')}
                          className="bg-orange-100 text-orange-700 px-2.5 py-1 rounded text-xs font-medium hover:bg-orange-200 transition flex items-center gap-1">
                          <Undo2 size={12} /> Devolver
                        </button>
                      </>
                    )}
                    <Link to={`/review/${event.id}`}
                      className="bg-slate-100 text-slate-700 px-2.5 py-1 rounded text-xs font-medium hover:bg-slate-200 transition flex items-center gap-1">
                      <ZoomIn size={12} />
                    </Link>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {total > limit && (
        <div className="flex justify-center gap-2 mt-4">
          <button disabled={page === 0} onClick={() => setPage(p => p - 1)}
            className="px-3 py-1.5 rounded-lg text-sm border border-slate-300 disabled:opacity-40">←</button>
          <span className="px-3 py-1.5 text-sm text-slate-600">{page + 1} / {Math.ceil(total / limit)}</span>
          <button disabled={(page + 1) * limit >= total} onClick={() => setPage(p => p + 1)}
            className="px-3 py-1.5 rounded-lg text-sm border border-slate-300 disabled:opacity-40">→</button>
        </div>
      )}
    </div>
  )
}
