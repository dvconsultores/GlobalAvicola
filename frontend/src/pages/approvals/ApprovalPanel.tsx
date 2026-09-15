import { useState, useEffect, useCallback, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { Check, CheckCircle, X, ArrowLeft, Search, Clock } from 'lucide-react'
import api from '../../services/api'
import { useCan } from '../../auth/actionAuthority'
import { useToast, getErrorMessage } from '../../components/Toast'
import SubNavHeader from '../../components/layout/SubNavHeader'
import { KpiCard, ConfirmDialog, Badge, FilterPanel, FilterGroup } from '../../components/ui'

const getEventLabel = (t: any, key: string) => t(`eventsShort.${key}`, key)

const STATUS_VARIANT: Record<string, string> = {
 corrected: 'corrected', in_review: 'in_review',
 approved: 'approved', rejected: 'rejected',
 reversed: 'reversed',
}

export default function ApprovalPanel() {
 const can = useCan()
 const { t } = useTranslation()
 const toast = useToast()
 const [events, setEvents] = useState<any[]>([])
 const [loading, setLoading] = useState(true)
 const [total, setTotal] = useState(0)
 const [lotId, setLotId] = useState('')
 const [page, setPage] = useState(0)
 const [rejectReason, setRejectReason] = useState('')
 const [showRejectModal, setShowRejectModal] = useState(false)
 const [showApproveModal, setShowApproveModal] = useState(false)
 // `R-220` · A9: guarda de vuelo de la aprobación (una mutación por gesto).
 const approvingRef = useRef(false)
 const [singleApproveId, setSingleApproveId] = useState<number | null>(null)
 const [rejectTarget, setRejectTarget] = useState<'single' | 'batch'>('single')
 const [singleRejectId, setSingleRejectId] = useState<number | null>(null)
 const limit = 20

 const fetchEvents = useCallback(async () => {
 setLoading(true)
 try {
 const params = new URLSearchParams({ limit: String(limit), offset: String(page * limit) })
 if (lotId) params.set('lot_id', lotId)
 const { data } = await api.get(`/approvals/pending?${params}`)
 setEvents(data.events || [])
 setTotal(data.total || 0)
 } catch (err: any) {
 toast.error(getErrorMessage(err, t('review.errorLoadingApprovals')))
 } finally {
 setLoading(false)
 }
 }, [lotId, page, t, toast])

 useEffect(() => { fetchEvents() }, [fetchEvents])

 const handleApprove = async (eventId: number) => {
 // `R-220` · A9 (C#35): un gesto, una mutación — el doble clic no duplica POSTs.
 if (approvingRef.current) return
 approvingRef.current = true
 try {
 await api.post('/approvals/approve', { event_id: eventId })
 toast.success(t('review.eventApproved'))
 setShowApproveModal(false)
 setSingleApproveId(null)
 fetchEvents()
 } catch (err: any) {
 toast.error(getErrorMessage(err, t('review.errorApprove')))
 } finally {
 approvingRef.current = false
 }
 }

 const handleRejectSingle = async () => {
 if (!rejectReason || rejectReason.length < 10) {
 toast.warning(t('review.reasonMinLength'))
 return
 }
 try {
 await api.post('/approvals/reject', { event_id: singleRejectId, observations: rejectReason })
 setShowRejectModal(false)
 setRejectReason('')
 setSingleRejectId(null)
 toast.success(t('review.eventRejected'))
 fetchEvents()
 } catch (err: any) {
 toast.error(getErrorMessage(err, t('review.errorReject')))
 }
 }

 const openApproveSingle = (eventId: number) => {
 setSingleApproveId(eventId)
 setShowApproveModal(true)
 }

 const openRejectSingle = (eventId: number) => {
 setSingleRejectId(eventId)
 setRejectTarget('single')
 setRejectReason('')
 setShowRejectModal(true)
 }

 const handleBatchApprove = async () => {
 const selected = events.filter((e: any) => e._checked)
 if (selected.length === 0) {
 toast.warning(t('common.noSelection'))
 return
 }
 try {
 await api.post('/approvals/batch-approve', { event_ids: selected.map((e: any) => e.id) })
 toast.success(t('review.batchApproved', { count: selected.length }))
 fetchEvents()
 } catch (err: any) {
 toast.error(getErrorMessage(err, t('common.error')))
 }
 }

 const handleBatchReject = async () => {
 if (!rejectReason || rejectReason.length < 10) {
 toast.warning(t('review.reasonMinLength'))
 return
 }
 const selected = events.filter((e: any) => e._checked)
 if (selected.length === 0) {
 toast.warning(t('common.noSelection'))
 return
 }
 try {
 await api.post('/approvals/batch-reject', { event_ids: selected.map((e: any) => e.id), observations: rejectReason })
 setShowRejectModal(false)
 setRejectReason('')
 toast.success(t('review.batchRejected', { count: selected.length }))
 fetchEvents()
 } catch (err: any) {
 toast.error(getErrorMessage(err, t('common.error')))
 }
 }

 const openBatchReject = () => {
 const selected = events.filter((e: any) => e._checked)
 if (selected.length === 0) {
 toast.warning(t('common.noSelection'))
 return
 }
 setRejectTarget('batch')
 setRejectReason('')
 setShowRejectModal(true)
 }

 const toggleCheck = (id: number) => {
 setEvents(prev => prev.map(e => e.id === id ? { ...e, _checked: !e._checked } : e))
 }

 const selectedCount = events.filter((e: any) => e._checked).length
 const pendingCount = events.filter(e => e.status === 'corrected').length

 return (
 <div>
 {/* Header */}
 <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
 <SubNavHeader
 title={t('review.approvalPanel', 'Aprobaciones')}
 hideBack
 actions={
 <Link to="/review"
 className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-600 hover:text-blue-600 bg-slate-100 hover:bg-blue-50 px-4 py-2 rounded-lg transition-colors">
 <ArrowLeft size={16} /> {t('nav.review', 'Revisión')}
 </Link>
 }
 />
 </div>

 {/* `R-220` · A3 (C#25): esta bandeja son PENDIENTES — «Aprobados/Rechazados»
 no son contables aquí (siempre 0) y un cero indistinguible de «no hay nada»
 engaña: se retiran en lugar de fabricar métricas. */}
 <div className="grid grid-cols-2 gap-4 mb-6">
 <KpiCard icon={Clock} label={t('review.pendingApprovals', 'Pendientes')} value={pendingCount} color="amber" />
 <KpiCard icon={Search} label={t('common.results', 'Total')} value={total} color="blue" />
 </div>

 {/* Batch Actions Bar */}
 {/* `R-208`: la barra depende de `approvals:*` — `review:review` no autoriza una aprobación. */}
 {(can({ permission: 'approvals:approve' }) || can({ permission: 'approvals:reject' })) && selectedCount > 0 && (
 <div className="bg-[#1E3A5F] text-white rounded-xl px-5 py-3 mb-4 flex flex-wrap items-center justify-between gap-2 shadow-sm">
 <span className="text-sm font-semibold">{selectedCount} {t('review.selectedEvents', 'seleccionados')}</span>
 <div className="flex gap-2">
 {can({ permission: 'approvals:approve' }) && <button onClick={handleBatchApprove}
 className="bg-emerald-500 hover:bg-emerald-600 text-white px-4 py-2 rounded-lg text-sm font-semibold transition flex items-center gap-1.5 shadow-sm">
 <Check size={16} /> {t('review.approveAll', 'Aprobar todos')}
 </button>}
 {can({ permission: 'approvals:reject' }) && <button onClick={openBatchReject}
 className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg text-sm font-semibold transition flex items-center gap-1.5 shadow-sm">
 <X size={16} /> {t('review.rejectAll', 'Rechazar todos')}
 </button>}
 </div>
 </div>
 )}

 {/* Filter Panel */}
 <FilterPanel totalResults={total}>
 <FilterGroup label={t('review.lot', 'Lote')}>
 <input
 type="text"
 placeholder={t('common.id', 'ID')}
 value={lotId}
 onChange={e => { setLotId(e.target.value); setPage(0) }}
 className="border border-slate-300 rounded-lg px-3 py-2 text-sm w-24 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
 />
 </FilterGroup>
 </FilterPanel>

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
 {!loading && events.length === 0 && (
 <div className="text-center py-12">
 <CheckCircle size={40} className="mx-auto mb-2 text-emerald-300" />
 <p className="text-sm text-slate-500">{t('review.noPendingApprovals', 'Sin aprobaciones pendientes')}</p>
 </div>
 )}
 {events.map((event: any) => (
 <div key={event.id} className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm hover:shadow-md transition-shadow">
 <div className="flex items-start gap-3">
 {can({ permission: 'review:review' }) && <input type="checkbox" checked={!!event._checked} onChange={() => toggleCheck(event.id)}
 className="mt-1 h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500" />}
 <div className="flex-1 min-w-0">
 <div className="flex items-center gap-2 mb-1.5">
 <span className="font-semibold text-slate-800 font-mono text-xs">#{event.id}</span>
 <Badge variant={STATUS_VARIANT[event.status] as any || 'neutral'} size="sm">
 {String(t(`status.${event.status}`, event.status))}
 </Badge>
 </div>
 <p className="text-sm font-medium text-slate-700">{getEventLabel(t, event.event_type)}</p>
 <p className="text-xs text-slate-400 mt-0.5">{String(t('review.lotPrefix', 'Lote'))} #{event.lot_id} · {event.event_date}</p>
 </div>
 </div>
 <div className="flex gap-2 mt-3 border-t border-slate-100 pt-3">
 {can({ permission: 'approvals:approve' }) && <button onClick={() => openApproveSingle(event.id)}
 className="flex-1 bg-emerald-50 text-emerald-700 px-3 py-2 rounded-lg text-xs font-semibold hover:bg-emerald-100 transition flex items-center justify-center gap-1.5">
 <Check size={14} /> {t('review.approve', 'Aprobar')}
 </button>}
 {can({ permission: 'approvals:reject' }) && <button onClick={() => openRejectSingle(event.id)}
 className="flex-1 bg-red-50 text-red-700 px-3 py-2 rounded-lg text-xs font-semibold hover:bg-red-100 transition flex items-center justify-center gap-1.5">
 <X size={14} /> {t('review.reject', 'Rechazar')}
 </button>}
 <Link to={`/review/${event.id}`}
 className="flex-1 bg-slate-50 text-slate-600 px-3 py-2 rounded-lg text-xs font-semibold hover:bg-slate-100 transition text-center flex items-center justify-center gap-1.5">
 <Search size={14} />
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
 {can({ permission: 'review:review' }) && <input type="checkbox"
 onChange={e => setEvents(prev => prev.map(ev => ({ ...ev, _checked: e.target.checked })))}
 className="rounded border-slate-300 text-blue-600 focus:ring-blue-500" />}
 </th>
 <th className="px-4 py-3.5 text-left font-semibold text-slate-600 text-xs uppercase tracking-wider">{t('common.id')}</th>
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
 <CheckCircle size={28} className="mx-auto mb-2 text-emerald-300" />
 <p className="text-sm text-slate-500">{t('review.noPendingApprovals', 'Sin aprobaciones pendientes')}</p>
 </td>
 </tr>
 )}
 {events.map((event: any) => (
 <tr key={event.id} className="hover:bg-blue-50/40 transition-colors">
 <td className="px-4 py-3">
 {can({ permission: 'review:review' }) && <input type="checkbox" checked={!!event._checked} onChange={() => toggleCheck(event.id)}
 className="rounded border-slate-300 text-blue-600 focus:ring-blue-500" />}
 </td>
 <td className="px-4 py-3 font-mono text-xs text-slate-500">#{event.id}</td>
 <td className="px-4 py-3 text-slate-700">{getEventLabel(t, event.event_type)}</td>
 <td className="px-4 py-3">
 <span className="font-mono text-xs font-medium text-slate-600 bg-slate-50 px-2 py-1 rounded">#{event.lot_id}</span>
 </td>
 <td className="px-4 py-3 text-slate-500 text-sm">{event.event_date}</td>
 <td className="px-4 py-3">
 <Badge variant={STATUS_VARIANT[event.status] as any || 'neutral'} size="sm">
 {String(t(`status.${event.status}`, event.status))}
 </Badge>
 </td>
 <td className="px-4 py-3">
 <div className="flex gap-1.5">
 {can({ permission: 'approvals:approve' }) && <button onClick={() => openApproveSingle(event.id)}
 className="bg-emerald-50 text-emerald-700 px-2.5 py-1.5 rounded-lg text-xs font-semibold hover:bg-emerald-100 transition flex items-center gap-1">
 <Check size={12} /> {t('review.approve', 'Aprobar')}
 </button>}
 {can({ permission: 'approvals:reject' }) && <button onClick={() => openRejectSingle(event.id)}
 className="bg-red-50 text-red-700 px-2.5 py-1.5 rounded-lg text-xs font-semibold hover:bg-red-100 transition flex items-center gap-1">
 <X size={12} /> {t('review.reject', 'Rechazar')}
 </button>}
 <Link to={`/review/${event.id}`}
 className="bg-slate-50 text-slate-600 px-2.5 py-1.5 rounded-lg text-xs font-semibold hover:bg-slate-100 transition flex items-center">
 <Search size={12} />
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
 <div className="flex items-center justify-center gap-3 mt-5">
 <button
 disabled={page === 0}
 onClick={() => setPage(p => p - 1)}
 className="px-4 py-2 rounded-lg text-sm font-semibold border border-slate-300 text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
 >
 ← {t('common.back', 'Anterior')}
 </button>
 <span className="text-sm font-medium text-slate-500">
 {page + 1} / {Math.ceil(total / limit)}
 </span>
 <button
 disabled={(page + 1) * limit >= total}
 onClick={() => setPage(p => p + 1)}
 className="px-4 py-2 rounded-lg text-sm font-semibold border border-slate-300 text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
 >
 {t('common.next', 'Siguiente')} →
 </button>
 </div>
 )}

 {/* Approve Dialog */}
 <ConfirmDialog
 open={showApproveModal}
 onClose={() => setShowApproveModal(false)}
 onConfirm={() => handleApprove(singleApproveId!)}
 title={t('review.confirmApprove', '¿Aprobar registro?')}
 message={t('review.confirmApproveMsg', 'El registro será marcado como aprobado y pasará a la etapa de consolidación.')}
 confirmLabel={t('review.approve', 'Aprobar')}
 variant="success"
 showWarning={false}
 />

 {/* Reject Dialog */}
 <ConfirmDialog
 open={showRejectModal}
 onClose={() => setShowRejectModal(false)}
 onConfirm={rejectTarget === 'batch' ? handleBatchReject : handleRejectSingle}
 title={t('review.confirmReject', '¿Rechazar registro?')}
 message={t('review.confirmRejectMsg', 'El registro será devuelto al operador con las observaciones. Esta acción no se puede deshacer.')}
 confirmLabel={t('review.reject', 'Rechazar')}
 variant="danger"
 showWarning
 />
 </div>
 )
}
