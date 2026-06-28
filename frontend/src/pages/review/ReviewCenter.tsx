import { useState, useEffect, useCallback, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useSearchParams } from 'react-router-dom'
import {
 CheckCircle, Check, Play, Undo2, ZoomIn, Package, Search,
 Clock, ListChecks,
} from 'lucide-react'
import api from '../../services/api'
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
 { key: 'pending_review', labelKey: 'review.pending', icon: Clock, color: 'text-amber-600' },
 { key: 'in_review', labelKey: 'review.inReview', icon: Search, color: 'text-indigo-600' },
 { key: 'returned', labelKey: 'review.returned', icon: Undo2, color: 'text-orange-600' },
 { key: 'approved', labelKey: 'review.approved', icon: CheckCircle, color: 'text-emerald-600' },
 { key: 'consolidated', labelKey: 'review.consolidated', icon: ListChecks, color: 'text-teal-600' },
] as const

type StatusTab = typeof STATUS_TABS[number]['key']

export default function ReviewCenter() {
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
 const limit = 20

 const setActiveTab = (tab: StatusTab) => {
 setSearchParams({ status: tab })
 setPage(0)
 }

 const statusFilter = useMemo(() => {
 switch (activeTab) {
 case 'pending_review': return 'pending_review'
 case 'in_review': return 'in_review'
 case 'returned': return 'returned'
 case 'approved': return 'approved'
 case 'consolidated': return 'consolidated'
 default: return 'pending_review'
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
 if (operatorId) params.set('operator_id', operatorId)
 const { data } = await api.get(`/review/pending?${params}`)
 setEvents(data.events || [])
 setTotal(data.total || 0)
 } catch (err: any) {
 toast.error(getErrorMessage(err, t('review.errorLoading')))
 } finally {
 setLoading(false)
 }
 }, [lotId, eventType, dateFrom, dateTo, farmId, operatorId, page, statusFilter, t, toast])

 useEffect(() => { fetchEvents() }, [fetchEvents])
 useEffect(() => {
 api.get('/masters/farms?limit=100').then(r => setFarms(r.data || [])).catch(() => {})
 api.get('/users?limit=100').then(r => setUsers(r.data || [])).catch(() => {})
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
 <div>
 {/* Header */}
 <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
 <SubNavHeader
 title={t('review.center')}
 hideBack
 actions={
 <div className="flex gap-2">
 <button onClick={handleCreateBatch}
 className="bg-[#1E3A5F] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-800 transition flex items-center gap-1.5 shadow-sm">
 <Package size={16} /> {t('review.createBatch')}
 </button>
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
 : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 hover:bg-slate-50 hover:border-slate-300'
 }
 `}
 >
 <Icon size={16} className={isActive ? 'text-white' : tab.color} />
 {t(tab.labelKey)}
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
 placeholder="ID"
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

 <FilterGroup label={t('review.operator', 'Operador')}>
 <select
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

 <FilterGroup label={t('common.date', 'Fecha')}>
 <input
 type="date"
 value={dateFrom}
 onChange={e => { setDateFrom(e.target.value); setPage(0) }}
 className="border border-slate-300 rounded-lg px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
 />
 <span className="text-xs text-slate-400 dark:text-slate-500">—</span>
 <input
 type="date"
 value={dateTo}
 onChange={e => { setDateTo(e.target.value); setPage(0) }}
 className="border border-slate-300 rounded-lg px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
 />
 </FilterGroup>
 </FilterPanel>

 {/* Mobile Cards */}
 <div className="lg:hidden space-y-3">
 {loading && (
 <div className="space-y-3">
 {[1,2,3].map(i => (
 <div key={i} className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 p-4 animate-pulse">
 <div className="h-4 bg-slate-100 dark:bg-slate-700 rounded w-1/3 mb-3" />
 <div className="h-3 bg-slate-100 dark:bg-slate-700 rounded w-2/3 mb-2" />
 <div className="h-3 bg-slate-100 dark:bg-slate-700 rounded w-1/2" />
 </div>
 ))}
 </div>
 )}
 {!loading && events.length === 0 && (
 <div className="text-center py-12">
 <Search size={32} className="mx-auto text-slate-300 dark:text-slate-500 mb-3" />
 <p className="text-sm text-slate-500 dark:text-slate-400">{t('common.noResults', 'Sin resultados')}</p>
 </div>
 )}
 {events.map((event: any) => (
 <div key={event.id} className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 p-4 shadow-sm hover:shadow-md transition-shadow">
 <div className="flex items-start gap-3">
 <input
 type="checkbox"
 checked={!!event._checked}
 onChange={() => toggleCheck(event.id)}
 className="mt-1 h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
 />
 <div className="flex-1 min-w-0">
 <div className="flex items-center gap-2 mb-1.5">
 <span className="font-semibold text-slate-800 dark:text-slate-200 font-mono text-xs">#{event.id}</span>
 <Badge variant={STATUS_VARIANT[event.status] as any || 'neutral'} size="sm">
 {String(t(`status.${event.status}`, event.status))}
 </Badge>
 </div>
 <p className="text-sm font-medium text-slate-700 dark:text-slate-200">{getEventLabel(t, event.event_type)}</p>
 <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5">
 {String(t('review.lotPrefix', 'Lote'))} #{event.lot_id} · {event.event_date}
 </p>
 </div>
 </div>
 <div className="flex gap-2 mt-3 border-t border-slate-100 pt-3">
 {event.status === 'pending_review' && (
 <button onClick={() => handleAction(event.id, 'start')}
 className="flex-1 bg-indigo-50 text-indigo-700 px-3 py-2 rounded-lg text-xs font-semibold hover:bg-indigo-100 transition flex items-center justify-center gap-1.5">
 <Play size={14} /> {t('review.start', 'Iniciar')}
 </button>
 )}
 {event.status === 'in_review' && (
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
 className="flex-1 bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-200 px-3 py-2 rounded-lg text-xs font-semibold hover:bg-slate-100 transition text-center flex items-center justify-center gap-1.5">
 <ZoomIn size={14} /> {t('review.detail', 'Detalle')}
 </Link>
 </div>
 </div>
 ))}
 </div>

 {/* Desktop Table */}
 <div className="hidden lg:block bg-white dark:bg-slate-800 rounded-xl border border-slate-200 overflow-hidden shadow-sm">
 <table className="w-full text-sm">
 <thead className="bg-slate-50 dark:bg-slate-800 border-b border-slate-200">
 <tr>
 <th className="w-12 px-4 py-3.5 text-left">
 <input
 type="checkbox"
 onChange={e => setEvents(prev => prev.map(ev => ({ ...ev, _checked: e.target.checked })))}
 className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
 />
 </th>
 <th className="px-4 py-3.5 text-left font-semibold text-slate-600 dark:text-slate-300 text-xs uppercase tracking-wider">{t('review.id', 'ID')}</th>
 <th className="px-4 py-3.5 text-left font-semibold text-slate-600 dark:text-slate-300 text-xs uppercase tracking-wider">{t('common.type', 'Tipo')}</th>
 <th className="px-4 py-3.5 text-left font-semibold text-slate-600 dark:text-slate-300 text-xs uppercase tracking-wider">{t('review.lot', 'Lote')}</th>
 <th className="px-4 py-3.5 text-left font-semibold text-slate-600 dark:text-slate-300 text-xs uppercase tracking-wider">{t('common.date', 'Fecha')}</th>
 <th className="px-4 py-3.5 text-left font-semibold text-slate-600 dark:text-slate-300 text-xs uppercase tracking-wider">{t('common.status', 'Estado')}</th>
 <th className="px-4 py-3.5 text-left font-semibold text-slate-600 dark:text-slate-300 text-xs uppercase tracking-wider">{t('common.actions', 'Acciones')}</th>
 </tr>
 </thead>
 <tbody className="divide-y divide-slate-100">
 {loading && (
 <tr>
 <td colSpan={7} className="px-4 py-12 text-center">
 <div className="flex items-center justify-center gap-2 text-slate-400 dark:text-slate-500">
 <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
 <span className="text-sm">{t('common.loading', 'Cargando...')}</span>
 </div>
 </td>
 </tr>
 )}
 {!loading && events.length === 0 && (
 <tr>
 <td colSpan={7} className="px-4 py-12 text-center">
 <Search size={24} className="mx-auto text-slate-300 dark:text-slate-500 mb-2" />
 <p className="text-sm text-slate-500 dark:text-slate-400">{t('common.noResults', 'Sin resultados')}</p>
 </td>
 </tr>
 )}
 {events.map((event: any) => {
 const EvIcon = EVENT_ICON_MAP[event.event_type]
 return (
 <tr key={event.id} className="hover:bg-blue-50/40 transition-colors">
 <td className="px-4 py-3">
 <input
 type="checkbox"
 checked={!!event._checked}
 onChange={() => toggleCheck(event.id)}
 className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
 />
 </td>
 <td className="px-4 py-3 font-mono text-xs text-slate-500 dark:text-slate-400">#{event.id}</td>
 <td className="px-4 py-3">
 <div className="flex items-center gap-2">
 {EvIcon && <EvIcon size={14} className="text-slate-400 dark:text-slate-500 shrink-0" />}
 <span className="text-slate-700 dark:text-slate-200">{getEventLabel(t, event.event_type)}</span>
 </div>
 </td>
 <td className="px-4 py-3">
 <span className="font-mono text-xs font-medium text-slate-600 dark:text-slate-300 bg-slate-50 dark:bg-slate-800 px-2 py-1 rounded">
 #{event.lot_id}
 </span>
 </td>
 <td className="px-4 py-3 text-slate-500 dark:text-slate-400 text-sm">{event.event_date}</td>
 <td className="px-4 py-3">
 <Badge variant={STATUS_VARIANT[event.status] as any || 'neutral'} size="sm">
 {String(t(`status.${event.status}`, event.status))}
 </Badge>
 </td>
 <td className="px-4 py-3">
 <div className="flex gap-1.5">
 {event.status === 'pending_review' && (
 <button onClick={() => handleAction(event.id, 'start')}
 className="bg-indigo-50 text-indigo-700 px-2.5 py-1.5 rounded-lg text-xs font-semibold hover:bg-indigo-100 transition flex items-center gap-1">
 <Play size={12} /> {t('review.start', 'Iniciar')}
 </button>
 )}
 {event.status === 'in_review' && (
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
 className="bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-300 px-2.5 py-1.5 rounded-lg text-xs font-semibold hover:bg-slate-100 transition flex items-center gap-1">
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
 <span className="px-3 py-1.5 text-sm text-slate-600 dark:text-slate-300">{page + 1} / {Math.ceil(total / limit)}</span>
 <button disabled={(page + 1) * limit >= total} onClick={() => setPage(p => p + 1)}
 className="px-3 py-1.5 rounded-lg text-sm border border-slate-300 disabled:opacity-40">→</button>
 </div>
 )}
 </div>
 )
}
