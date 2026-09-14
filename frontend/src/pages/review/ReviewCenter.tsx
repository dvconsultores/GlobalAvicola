import { useState, useEffect, useCallback, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useSearchParams } from 'react-router-dom'
import {
 CheckCircle, Check, Play, Undo2, ZoomIn, Package, Search,
 Clock, ListChecks, Pencil, XCircle,
} from 'lucide-react'
import api from '../../services/api'
import { useCan } from '../../auth/actionAuthority'
import { useToast, getErrorMessage } from '../../components/Toast'
import { EVENT_ICON_MAP } from '../../data/processCatalog'
import { Badge, FilterPanel, FilterGroup } from '../../components/ui'
import SubNavHeader from '../../components/layout/SubNavHeader'

const EVT_KEYS = Object.keys(EVENT_ICON_MAP)

const getEventLabel = (t: any, key: string) => t(`eventsShort.${key}`, key)

// Mapa de estados a variantes de Badge
const STATUS_VARIANT: Record<string, string> = {
 registered: 'registered',
 pending_review: 'pending',
 in_review: 'in_review',
 returned: 'returned',
 corrected: 'corrected',
 approved: 'approved',
 rejected: 'rejected',
 cancelled: 'cancelled',
 consolidated: 'consolidated',
}

// Tabs de estado
const STATUS_TABS = [
 { key: 'pending_review', labelKey: 'review.pending', fallback: 'Pendientes', icon: Clock, color: 'text-amber-600' },
 { key: 'in_review', labelKey: 'review.inReview', fallback: 'En revisión', icon: Search, color: 'text-indigo-600' },
 { key: 'returned', labelKey: 'review.returned', fallback: 'Devueltos', icon: Undo2, color: 'text-orange-600' },
 // `R-197` C-03: las siete pestañas de bandeja.
 { key: 'corrected', labelKey: 'review.corrected', fallback: 'Corregidos', icon: Pencil, color: 'text-amber-700' },
 { key: 'approved', labelKey: 'review.approved', fallback: 'Aprobados', icon: CheckCircle, color: 'text-emerald-600' },
 { key: 'rejected', labelKey: 'review.rejected', fallback: 'Rechazados', icon: XCircle, color: 'text-red-600' },
 { key: 'consolidated', labelKey: 'review.consolidated', fallback: 'Consolidados', icon: ListChecks, color: 'text-teal-600' },
] as const

type StatusTab = typeof STATUS_TABS[number]['key']

export default function ReviewCenter() {
 const can = useCan()
 const { t } = useTranslation()
 const toast = useToast()
 const [searchParams, setSearchParams] = useSearchParams()

 // Estado activo desde URL (default: pending_review)
 const activeTab = (searchParams.get('status') as StatusTab) || 'pending_review'

 const [events, setEvents] = useState<any[]>([])
 const [loading, setLoading] = useState(true)
 const [total, setTotal] = useState(0)
 const [lotId, setLotId] = useState('')
 const [eventType, setEventType] = useState('')
 const [dateFrom, setDateFrom] = useState('')
 const [dateTo, setDateTo] = useState('')
 const [farmId, setFarmId] = useState('')
 const [operatorId, setOperatorId] = useState('')
 const [farms, setFarms] = useState<any[]>([])
 const [users, setUsers] = useState<any[]>([])
 const [page, setPage] = useState(0)
 const [estado, setEstado] = useState<'ok' | 'prohibido' | 'error'>('ok')
 const [returnTarget, setReturnTarget] = useState<number | null>(null)
 const [returnObs, setReturnObs] = useState('')
 const [returnError, setReturnError] = useState('')
 const limit = 20

 const setActiveTab = (tab: StatusTab) => {
 setSearchParams({ status: tab })
 setPage(0)
 }

 const statusFilter = useMemo(() => {
 switch (activeTab) {
 // C-04: el «Pendientes» del supervisor conserva lo registrado aún no enviado.
 case 'pending_review': return 'registered,pending_review'
 case 'in_review': return 'in_review'
 case 'returned': return 'returned'
 case 'corrected': return 'corrected'
 case 'approved': return 'approved'
 case 'rejected': return 'rejected'
 case 'consolidated': return 'consolidated'
 default: return 'registered,pending_review'
 }
 }, [activeTab])

 const fetchEvents = useCallback(async () => {
 setLoading(true)
 try {
 const params = new URLSearchParams({
 limit: String(limit),
 offset: String(page * limit),
 status: statusFilter,
 })
 if (lotId) params.set('lot_id', lotId)
 if (eventType) params.set('event_type', eventType)
 if (dateFrom) params.set('date_from', dateFrom)
 if (dateTo) params.set('date_to', dateTo)
 if (farmId) params.set('farm_id', farmId)
 if (operatorId && can({ permission: 'users:read' })) params.set('registered_by_id', operatorId)
 const { data } = await api.get(`/review/pending?${params}`)
 setEvents(data.events || [])
 setTotal(data.total || 0)
 setEstado('ok')
 } catch (err: any) {
 // `R-197` AC19: 403 es falta de permiso — jamás «sin resultados».
 if (err?.response?.status === 403) {
 setEstado('prohibido')
 } else {
 setEstado('error')
 toast.error(getErrorMessage(err, t('review.errorLoading')))
 }
 } finally {
 setLoading(false)
 }
 }, [lotId, eventType, dateFrom, dateTo, farmId, operatorId, page, statusFilter, t, toast, can])

 useEffect(() => { fetchEvents() }, [fetchEvents])
 useEffect(() => {
 api.get('/masters/farms?limit=100').then(r => setFarms(r.data || [])).catch(() => {})
 // `R-197` AC18/C-05: administración de acceso ≠ acceso operativo. Sin
 // `users:read` no se pide `/users` y el filtro de operador no se muestra.
 if (can({ permission: 'users:read' })) {
 api.get('/users?limit=100').then(r => setUsers(r.data || [])).catch(() => {})
 }
 }, [])

 const clearFilters = () => {
 setLotId('')
 setEventType('')
 setDateFrom('')
 setDateTo('')
 setFarmId('')
 setOperatorId('')
 setPage(0)
 }

 const handleAction = async (eventId: number, action: 'start' | 'return' | 'complete') => {
 // `R-197` AC07/AC20: la devolución usa modal propio (sin `prompt` nativo)
 // y exige observación ≥ 10 en cliente (el servidor ya la exige).
 if (action === 'return') {
 setReturnTarget(eventId)
 setReturnObs('')
 setReturnError('')
 return
 }

 try {
 if (action === 'start') await api.post(`/review/start/${eventId}`)
 else if (action === 'complete') await api.post('/review/complete', { event_id: eventId })
 toast.success(t('review.actionCompleted', { action }))
 fetchEvents()
 } catch (err: any) {
 toast.error(getErrorMessage(err, t('review.errorAction')))
 }
 }

 const confirmarDevolucion = async () => {
 if (returnTarget === null) return
 if (returnObs.trim().length < 10) {
 setReturnError(t('review.observationsMin', 'La observación debe tener al menos 10 caracteres'))
 return
 }
 try {
 await api.post('/review/return', { event_id: returnTarget, observations: returnObs })
 setReturnTarget(null)
 toast.success(t('review.actionCompleted', { action: 'return' }))
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
 <div>
 {/* Header */}
 <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
 <SubNavHeader
 title={t('review.center')}
 hideBack
 actions={
 <div className="flex gap-2">
 {can({ permission: 'review:review' }) && <button onClick={handleCreateBatch}
 className="bg-[#1E3A5F] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-800 transition flex items-center gap-1.5 shadow-sm">
 <Package size={16} /> {t('review.createBatch')}
 </button>}
 <Link to="/approvals"
 className="bg-emerald-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-emerald-700 transition flex items-center gap-1.5 shadow-sm">
 <CheckCircle size={16} /> {t('nav.approvals')}
 </Link>
 </div>
 }
 />
 </div>

 {/* Status Tabs */}
 <div className="flex gap-1 mb-5 overflow-x-auto pb-1 scrollbar-hide">
 {STATUS_TABS.map((tab) => {
 const isActive = activeTab === tab.key
 const Icon = tab.icon
 return (
 <button
 key={tab.key}
 onClick={() => setActiveTab(tab.key)}
 className={`
 inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all whitespace-nowrap shrink-0
 ${isActive
 ? 'bg-[#1E3A5F] text-white shadow-md'
 : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50 hover:border-slate-300'
 }
 `}
 >
 <Icon size={16} className={isActive ? 'text-white' : tab.color} />
 {t(tab.labelKey, tab.fallback)}
 </button>
 )
 })}
 </div>

 {/* Filter Panel */}
 <FilterPanel
 onClear={clearFilters}
 totalResults={total}
 >
 <FilterGroup label={t('review.lot', 'Lote')}>
 <input
 type="text"
 placeholder={t('common.id', 'ID')}
 value={lotId}
 onChange={e => { setLotId(e.target.value); setPage(0) }}
 className="border border-slate-300 rounded-lg px-3 py-2 text-sm w-24 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
 />
 </FilterGroup>

 <FilterGroup label={t('review.farm', 'Granja')}>
 <select
 value={farmId}
 onChange={e => { setFarmId(e.target.value); setPage(0) }}
 className="border border-slate-300 rounded-lg px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
 >
 <option value="">{t('review.allFarms', 'Todas')}</option>
 {farms.map((f: any) => (
 <option key={f.id} value={f.id}>{f.name}</option>
 ))}
 </select>
 </FilterGroup>

 <FilterGroup label={t('common.type', 'Tipo')}>
 <select
 value={eventType}
 onChange={e => { setEventType(e.target.value); setPage(0) }}
 className="border border-slate-300 rounded-lg px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
 >
 <option value="">{t('common.allTypes', 'Todos')}</option>
 {EVT_KEYS.map((k) => (
 <option key={k} value={k}>{getEventLabel(t, k)}</option>
 ))}
 </select>
 </FilterGroup>

 {can({ permission: 'users:read' }) && (
 <FilterGroup label={t('review.operator', 'Operador')}>
 <select
 data-filtro="operador"
 value={operatorId}
 onChange={e => { setOperatorId(e.target.value); setPage(0) }}
 className="border border-slate-300 rounded-lg px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
 >
 <option value="">{t('review.allOperators', 'Todos')}</option>
 {users.map((u: any) => (
 <option key={u.id} value={u.id}>{u.username}</option>
 ))}
 </select>
 </FilterGroup>
 )}

 <FilterGroup label={t('common.date', 'Fecha')}>
 <input
 type="date"
 value={dateFrom}
 onChange={e => { setDateFrom(e.target.value); setPage(0) }}
 className="border border-slate-300 rounded-lg px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
 />
 <span className="text-xs text-slate-400">—</span>
 <input
 type="date"
 value={dateTo}
 onChange={e => { setDateTo(e.target.value); setPage(0) }}
 className="border border-slate-300 rounded-lg px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
 />
 </FilterGroup>
 </FilterPanel>

 {/* `R-197` AC07/AC20: devolución con modal propio (sin diálogos nativos). */}
 {returnTarget !== null && (
 <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setReturnTarget(null)}>
 <div className="bg-white rounded-2xl shadow-xl p-6 max-w-md w-full mx-4" onClick={(e) => e.stopPropagation()}>
 <h2 className="text-lg font-bold text-[#1E3A5F] mb-1">{t('review.returnToOperator', 'Devolver al operador')}</h2>
 <p className="text-xs text-slate-500 mb-3">{t('review.observationsHint', 'Motivo (mínimo 10 caracteres).')}</p>
 <textarea
 aria-label={t('review.observationsLabel', 'Observaciones')}
 value={returnObs}
 onChange={(e) => setReturnObs(e.target.value)}
 rows={3}
 className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
 />
 {returnError && <p className="text-xs text-red-600 mt-1">{returnError}</p>}
 <div className="flex gap-3 mt-4">
 <button onClick={() => setReturnTarget(null)} className="flex-1 bg-slate-100 text-slate-700 px-4 py-2.5 rounded-lg text-sm font-medium hover:bg-slate-200 transition">{t('common.cancel', 'Cancelar')}</button>
 <button onClick={confirmarDevolucion} className="flex-1 bg-orange-600 text-white px-4 py-2.5 rounded-lg text-sm font-medium hover:bg-orange-700 transition">{t('common.confirm', 'Confirmar')}</button>
 </div>
 </div>
 </div>
 )}

 {/* Mobile Cards */}
 <div className="lg:hidden space-y-3">
 {loading && (
 <div className="space-y-3">
 {[1,2,3].map(i => (
 <div key={i} className="bg-white rounded-xl border border-slate-200 p-4 animate-pulse">
 <div className="h-4 bg-slate-100 rounded w-1/3 mb-3" />
 <div className="h-3 bg-slate-100 rounded w-2/3 mb-2" />
 <div className="h-3 bg-slate-100 rounded w-1/2" />
 </div>
 ))}
 </div>
 )}
 {!loading && estado === 'prohibido' && (
 <div role="alert" className="bg-amber-50 border border-amber-200 rounded-xl p-6 text-center">
 <p className="text-sm font-medium text-amber-800">{t('review.noPermissionQueue')}</p>
 </div>
 )}
 {!loading && estado === 'ok' && events.length === 0 && (
 <div className="text-center py-12">
 <Search size={32} className="mx-auto text-slate-300 mb-3" />
 <p className="text-sm text-slate-500">{t('common.noResults', 'Sin resultados')}</p>
 </div>
 )}
 {events.map((event: any) => (
 <div key={event.id} className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm hover:shadow-md transition-shadow">
 <div className="flex items-start gap-3">
 {can({ permission: 'review:review' }) && <input
 type="checkbox"
 checked={!!event._checked}
 onChange={() => toggleCheck(event.id)}
 className="mt-1 h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
 />}
 <div className="flex-1 min-w-0">
 <div className="flex items-center gap-2 mb-1.5">
 <span className="font-semibold text-slate-800 font-mono text-xs">#{event.id}</span>
 <Badge variant={STATUS_VARIANT[event.status] as any || 'neutral'} size="sm">
 {String(t(`status.${event.status}`, event.status))}
 </Badge>
 </div>
 <p className="text-sm font-medium text-slate-700">{getEventLabel(t, event.event_type)}</p>
 <p className="text-xs text-slate-400 mt-0.5">
 {String(t('review.lotPrefix', 'Lote'))} #{event.lot_id} · {event.event_date}
 </p>
 </div>
 </div>
 <div className="flex gap-2 mt-3 border-t border-slate-100 pt-3">
 {can({ permission: 'review:review' }) && event.status === 'pending_review' && (
 <button onClick={() => handleAction(event.id, 'start')}
 className="flex-1 bg-indigo-50 text-indigo-700 px-3 py-2 rounded-lg text-xs font-semibold hover:bg-indigo-100 transition flex items-center justify-center gap-1.5">
 <Play size={14} /> {t('review.start', 'Iniciar')}
 </button>
 )}
 {can({ permission: 'review:review' }) && event.status === 'in_review' && (
 <>
 <button onClick={() => handleAction(event.id, 'complete')}
 className="flex-1 bg-teal-50 text-teal-700 px-3 py-2 rounded-lg text-xs font-semibold hover:bg-teal-100 transition flex items-center justify-center gap-1.5">
 <Check size={14} /> {t('review.complete', 'Completar')}
 </button>
 <button onClick={() => handleAction(event.id, 'return')}
 className="flex-1 bg-orange-50 text-orange-700 px-3 py-2 rounded-lg text-xs font-semibold hover:bg-orange-100 transition flex items-center justify-center gap-1.5">
 <Undo2 size={14} /> {t('review.return', 'Devolver')}
 </button>
 </>
 )}
 <Link to={`/review/${event.id}`}
 className="flex-1 bg-slate-50 text-slate-700 px-3 py-2 rounded-lg text-xs font-semibold hover:bg-slate-100 transition text-center flex items-center justify-center gap-1.5">
 <ZoomIn size={14} /> {t('review.detail', 'Detalle')}
 </Link>
 </div>
 </div>
 ))}
 </div>

 {/* Desktop Table */}
 <div className="hidden lg:block bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
 <table className="w-full text-sm">
 <thead className="bg-slate-50 border-b border-slate-200">
 <tr>
 <th className="w-12 px-4 py-3.5 text-left">
 {can({ permission: 'review:review' }) && <input
 type="checkbox"
 onChange={e => setEvents(prev => prev.map(ev => ({ ...ev, _checked: e.target.checked })))}
 className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
 />}
 </th>
 <th className="px-4 py-3.5 text-left font-semibold text-slate-600 text-xs uppercase tracking-wider">{t('review.id', 'ID')}</th>
 <th className="px-4 py-3.5 text-left font-semibold text-slate-600 text-xs uppercase tracking-wider">{t('common.type', 'Tipo')}</th>
 <th className="px-4 py-3.5 text-left font-semibold text-slate-600 text-xs uppercase tracking-wider">{t('review.lot', 'Lote')}</th>
 <th className="px-4 py-3.5 text-left font-semibold text-slate-600 text-xs uppercase tracking-wider">{t('common.date', 'Fecha')}</th>
 <th className="px-4 py-3.5 text-left font-semibold text-slate-600 text-xs uppercase tracking-wider">{t('common.status', 'Estado')}</th>
 <th className="px-4 py-3.5 text-left font-semibold text-slate-600 text-xs uppercase tracking-wider">{t('common.actions', 'Acciones')}</th>
 </tr>
 </thead>
 <tbody className="divide-y divide-slate-100">
 {loading && (
 <tr>
 <td colSpan={7} className="px-4 py-12 text-center">
 <div className="flex items-center justify-center gap-2 text-slate-400">
 <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
 <span className="text-sm">{t('common.loading', 'Cargando...')}</span>
 </div>
 </td>
 </tr>
 )}
 {!loading && events.length === 0 && (
 <tr>
 <td colSpan={7} className="px-4 py-12 text-center">
 <Search size={24} className="mx-auto text-slate-300 mb-2" />
 <p className="text-sm text-slate-500">{t('common.noResults', 'Sin resultados')}</p>
 </td>
 </tr>
 )}
 {events.map((event: any) => {
 const EvIcon = EVENT_ICON_MAP[event.event_type]
 return (
 <tr key={event.id} className="hover:bg-blue-50/40 transition-colors">
 <td className="px-4 py-3">
 {can({ permission: 'review:review' }) && <input
 type="checkbox"
 checked={!!event._checked}
 onChange={() => toggleCheck(event.id)}
 className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
 />}
 </td>
 <td className="px-4 py-3 font-mono text-xs text-slate-500">#{event.id}</td>
 <td className="px-4 py-3">
 <div className="flex items-center gap-2">
 {EvIcon && <EvIcon size={14} className="text-slate-400 shrink-0" />}
 <span className="text-slate-700">{getEventLabel(t, event.event_type)}</span>
 </div>
 </td>
 <td className="px-4 py-3">
 <span className="font-mono text-xs font-medium text-slate-600 bg-slate-50 px-2 py-1 rounded">
 #{event.lot_id}
 </span>
 </td>
 <td className="px-4 py-3 text-slate-500 text-sm">{event.event_date}</td>
 <td className="px-4 py-3">
 <Badge variant={STATUS_VARIANT[event.status] as any || 'neutral'} size="sm">
 {String(t(`status.${event.status}`, event.status))}
 </Badge>
 </td>
 <td className="px-4 py-3">
 <div className="flex gap-1.5">
 {can({ permission: 'review:review' }) && event.status === 'pending_review' && (
 <button onClick={() => handleAction(event.id, 'start')}
 className="bg-indigo-50 text-indigo-700 px-2.5 py-1.5 rounded-lg text-xs font-semibold hover:bg-indigo-100 transition flex items-center gap-1">
 <Play size={12} /> {t('review.start', 'Iniciar')}
 </button>
 )}
 {can({ permission: 'review:review' }) && event.status === 'in_review' && (
 <>
 <button onClick={() => handleAction(event.id, 'complete')}
 className="bg-teal-50 text-teal-700 px-2.5 py-1.5 rounded-lg text-xs font-semibold hover:bg-teal-100 transition flex items-center gap-1">
 <Check size={12} /> {t('review.complete', 'Completar')}
 </button>
 <button onClick={() => handleAction(event.id, 'return')}
 className="bg-orange-50 text-orange-700 px-2.5 py-1.5 rounded-lg text-xs font-semibold hover:bg-orange-100 transition flex items-center gap-1">
 <Undo2 size={12} /> {t('review.return', 'Devolver')}
 </button>
 </>
 )}
 <Link to={`/review/${event.id}`}
 className="bg-slate-50 text-slate-600 px-2.5 py-1.5 rounded-lg text-xs font-semibold hover:bg-slate-100 transition flex items-center gap-1">
 <ZoomIn size={12} />
 </Link>
 </div>
 </td>
 </tr>
 )
 })}
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
