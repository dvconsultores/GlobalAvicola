import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { ClipboardList } from 'lucide-react'
import api from '../../services/api'
import ErrorState from '../../components/ui/ErrorState'
import { PROCESS_STAGES, flowForStage, type StageKey } from '../../data/processCatalog'

const getEventLabel = (t: any, key: string) => t(`eventsShort.${key}`, key)

const STATUS_COLORS: Record<string, string> = {
 registered: 'bg-blue-100 text-blue-800', pending_review: 'bg-yellow-100 text-yellow-800',
 approved: 'bg-green-100 text-green-800', rejected: 'bg-red-100 text-red-800',
 cancelled: 'bg-slate-100 text-slate-600',
 reversed: 'bg-rose-100 text-rose-800',
}

export default function OperationListPage() {
 const { t } = useTranslation()
 const [brutos, setBrutos] = useState<any[]>([])
 const [total, setTotal] = useState(0)
 const [cargandoMas, setCargandoMas] = useState(false)
 const [loading, setLoading] = useState(true)
 // `R-212` · AC-04: denegación ≠ vacío.
 const [estado, setEstado] = useState<'ok' | 'prohibido' | 'error'>('ok')
 const [lotId, setLotId] = useState(() => {
 // `004` · AC10: filtros preservados al volver (mismo mecanismo sessionStorage del repo).
 try { return sessionStorage.getItem('ga.filters.operations.lotId') ?? '' } catch { return '' }
 })
 const [eventType, setEventType] = useState(() => {
 try { return sessionStorage.getItem('ga.filters.operations.eventType') ?? '' } catch { return '' }
 })

 const fetchEvents = useCallback(async () => {
 setLoading(true)
 try {
 const params: any = { limit: 100, skip: 0 }
 if (lotId) params.lot_id = lotId
 // For stage-based filter: fetch all and filter client-side
 // (backend doesn't support multi event_type yet)
 if (eventType && !eventType.startsWith('__stage__')) {
 params.event_type = eventType
 }
 const r = await api.get('/operations', { params })
 setBrutos(r.data ?? [])
 setTotal(Number(r.headers?.['x-total-count'] ?? (r.data ?? []).length))
 setEstado('ok')
 } catch (err: any) {
 setEstado(err?.response?.status === 403 ? 'prohibido' : 'error')
 }
 finally { setLoading(false) }
 }, [lotId, eventType])

 // `R-220` · A8 (C#33): página siguiente acumulada (skip por lo ya cargado).
 const cargarMas = async () => {
 setCargandoMas(true)
 try {
 const params: any = { limit: 100, skip: brutos.length }
 if (lotId) params.lot_id = lotId
 if (eventType && !eventType.startsWith('__stage__')) params.event_type = eventType
 const r = await api.get('/operations', { params })
 setBrutos(prev => [...prev, ...(r.data ?? [])])
 setTotal(Number(r.headers?.['x-total-count'] ?? total))
 } catch (err: any) {
 setEstado(err?.response?.status === 403 ? 'prohibido' : 'error')
 } finally { setCargandoMas(false) }
 }

 // El filtro por etapa es de cliente; la paginación no (`R-220` · A8).
 const events = (eventType && eventType.startsWith('__stage__'))
 ? brutos.filter((ev: any) => flowForStage(eventType.replace('__stage__', '') as StageKey).map(s => s.event).includes(ev.event_type))
 : brutos

 useEffect(() => { fetchEvents() }, [fetchEvents])

 // `004` · AC10: persistir filtros para el retorno lista→detalle→lista.
 useEffect(() => {
 try {
 if (lotId) sessionStorage.setItem('ga.filters.operations.lotId', lotId)
 else sessionStorage.removeItem('ga.filters.operations.lotId')
 if (eventType) sessionStorage.setItem('ga.filters.operations.eventType', eventType)
 else sessionStorage.removeItem('ga.filters.operations.eventType')
 } catch { /* storage no disponible */ }
 }, [lotId, eventType])

 if (estado !== 'ok') {
 return (
 <div className="py-4 sm:py-6">
 <ErrorState kind={estado} onRetry={fetchEvents} />
 </div>
 )
 }

 return (
 <div className="py-4 sm:py-6">
 <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
 <div>
 <h1 className="text-2xl font-bold text-slate-800">{t('nav.operations')}</h1>
 <p className="text-sm text-slate-500">{events.length} {t('common.results')}</p>
 </div>
 <Link to="/menu/poultry" className="inline-flex items-center h-10 px-4 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition">
 + {t('common.create')}
 </Link>
 </div>

 {/* Filters — stage-based instead of old 24-event flat dropdown */}
 <div className="flex gap-3 mb-4 flex-wrap">
 <input type="number" placeholder={t('review.lot') + ' ID'} value={lotId} onChange={e => setLotId(e.target.value)} className="h-10 px-3 border border-slate-300 rounded-lg text-sm w-28" />
 <select value={eventType} onChange={e => setEventType(e.target.value)} className="h-10 px-3 border border-slate-300 rounded-lg text-sm max-w-[200px]">
 <option value="">{t('common.allTypes')}</option>
 <optgroup label={t('operations.stagesGroup', 'Etapas de producción')}>
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
 <ClipboardList size={20} className="text-slate-400" aria-hidden="true" />
 <span className="text-sm font-medium text-slate-700">{getEventLabel(t, ev.event_type)}</span>
 <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[ev.status] || 'bg-slate-100 text-slate-600'}`}>{t(`status.${ev.status}`)}</span>
 </div>
 <p className="text-xs text-slate-500">{ev.lot_id ? `${t('review.lot')} #${ev.lot_id}` : t('operations.lotAutoPending', 'Se creará al aprobar')} — {ev.event_date}</p>
 </div>
 <Link to={`/operations/${ev.id}`} className="text-blue-600 text-sm hover:underline ml-3">{t('common.viewDetail', 'Ver detalle')}</Link>
 </div>
 ))}
 </div>
 }
 {/* `R-220` · A8: paginación real con `X-Total-Count`. */}
 {!loading && brutos.length < total && (
 <div className="flex justify-center py-4">
 <button
 type="button"
 onClick={cargarMas}
 disabled={cargandoMas}
 className="px-4 py-2 rounded-lg text-sm font-semibold border border-slate-300 text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
 >
 {cargandoMas ? t('common.loading') : t('common.loadMore', 'Cargar más')}
 </button>
 </div>
 )}
 </div>
 )
}
