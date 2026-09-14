import { useState, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { useParams, Link } from 'react-router-dom'
import { ClipboardList, Bird, Wheat, Egg, RefreshCw, Pencil, FileText } from 'lucide-react'
import api from '../../services/api'
import { useCan } from '../../auth/actionAuthority'
import { useToast, getErrorMessage } from '../../components/Toast'

const getEventLabel = (t: any, key: string) => t(`eventsShort.${key}`, key)

const STATUS_COLORS: Record<string, string> = {
 registered: 'bg-sky-100 text-sky-800', pending_review: 'bg-amber-100 text-amber-800',
 in_review: 'bg-indigo-100 text-indigo-800', returned: 'bg-orange-100 text-orange-800',
 corrected: 'bg-teal-100 text-teal-800', approved: 'bg-emerald-100 text-emerald-800',
 rejected: 'bg-red-100 text-red-800', cancelled: 'bg-slate-100 text-slate-600',
 reversed: 'bg-rose-100 text-rose-800',
}

export default function ReviewDetail() {
 const can = useCan()
 const { t } = useTranslation()
 const { id } = useParams<{ id: string }>()
 const toast = useToast()
 const enVuelo = useRef(false)
 const [event, setEvent] = useState<any>(null)
 const [corrections, setCorrections] = useState<any[]>([])
 const [actions, setActions] = useState<any[]>([])
 const [loading, setLoading] = useState(true)
 const [obs, setObs] = useState('')
 const [obsError, setObsError] = useState('')
 const [loteCreado, setLoteCreado] = useState<{ id: number; code: string | null } | null>(null)

 useEffect(() => {
 const fetch = async () => {
 try {
 // Get event from operations endpoint
 // GA-REM-011 C-04: consulta por identificador en lugar de listar 200.
 const { data: ev } = await api.get(`/operations/${id}`)
 setEvent(ev || null)

 // Get corrections for this event
 try {
 const { data: corr } = await api.get(`/corrections/event/${id}`)
 setCorrections(Array.isArray(corr) ? corr : [])
 } catch { /* no corrections yet */ }

 // `R-197` AC13: historial real por evento (individuales + de lote).
 try {
 const { data: acts } = await api.get(`/review/events/${id}/actions`)
 setActions(Array.isArray(acts) ? acts : [])
 } catch { /* no actions */ }
 } catch (err) {
 console.error(err)
 } finally {
 setLoading(false)
 }
 }
 fetch()
 }, [id])

 const recargar = async () => {
 try {
 const { data: ev } = await api.get(`/operations/${id}`)
 setEvent(ev || null)
 } catch { /* mantiene el detalle actual */ }
 }

 const handleAction = async (action: string) => {
 // `R-197` AC17: una sola mutación por gesto (guard de vuelo).
 if (enVuelo.current) return
 enVuelo.current = true
 try {
 if (action === 'start') await api.post(`/review/start/${id}`)
 else if (action === 'complete') await api.post('/review/complete', { event_id: Number(id) })
 else if (action === 'return') {
 if (obs.trim().length < 10) { setObsError(t('review.observationsMin', 'La observación debe tener al menos 10 caracteres')); return }
 setObsError('')
 await api.post('/review/return', { event_id: Number(id), observations: obs })
 }
 else if (action === 'approve') {
 const { data } = await api.post('/approvals/approve', { event_id: Number(id) })
 // `R-197` AC14: si la aprobación creó el lote, se ofrece el enlace.
 if (data?.lot_id) setLoteCreado({ id: data.lot_id, code: data.lot_code || null })
 }
 else if (action === 'reject') {
 if (!obs.trim()) { setObsError(t('review.obsRequired')); return }
 setObsError('')
 await api.post('/approvals/reject', { event_id: Number(id), observations: obs })
 }
 // `R-197` AC15: permanecer en el detalle y refrescarlo (sin navegar fuera).
 await recargar()
 } catch (err: any) {
 toast.error(getErrorMessage(err, t('review.errorAction')))
 } finally {
 enVuelo.current = false
 }
 }

 if (loading) return <div className="py-8 text-center text-slate-500">{t('common.loading')}</div>
 if (!event) return <div className="py-8 text-center text-slate-500">{t('review.eventNotFound')}</div>

 return (
 <div className="py-4 sm:py-6">
 {/* Header */}
 <div className="flex items-center gap-3 mb-6">
 <Link to="/review" className="text-slate-400 hover">← {t('common.back')}</Link>
 <h1 className="text-xl font-bold text-[#1E3A5F]">
 {t('review.detailTitle', { id: event.id })}
 </h1>
 <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[event.status] || 'bg-slate-100'}`}>
 {t(`status.${event.status}`)}
 </span>
 </div>

 {/* `R-207` · AC-02: enlace a la contrapartida cuando el detalle trae el campo. */}
 {event.reversal_event_id && (
 <div className="mb-5 bg-rose-50 border border-rose-200 rounded-xl px-4 py-3 text-sm text-rose-800">
 {t('reversals.counterpart', 'Contrapartida')}{' '}
 <Link to={`/operations/${event.reversal_event_id}`} className="font-mono underline">#{event.reversal_event_id}</Link>
 </div>
 )}

 {loteCreado && (
 <div className="mb-5 bg-emerald-50 border border-emerald-200 rounded-xl px-4 py-3 text-sm text-emerald-800">
 {t('review.lotCreated', 'La aprobación creó el lote')}{' '}
 <Link to={`/lots/${loteCreado.id}`} className="font-mono underline">
 #{loteCreado.id}{loteCreado.code ? ` · ${loteCreado.code}` : ''}
 </Link>
 </div>
 )}

 <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
 {/* Original Data */}
 <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
 <h2 className="font-semibold text-slate-700 mb-4">
 <ClipboardList size={18} className="inline-block mr-1.5 -mt-0.5" aria-hidden="true" />
 {t('review.originalData')}
 </h2>
 <dl className="space-y-2 text-sm">
 <div className="flex justify-between"><dt className="text-slate-500">{t('common.type')}</dt><dd>{getEventLabel(t, event.event_type)}</dd></div>
 <div className="flex justify-between"><dt className="text-slate-500">{t('common.date')}</dt><dd>{event.event_date}</dd></div>
 <div className="flex justify-between"><dt className="text-slate-500">{t('review.lot')}</dt><dd className="font-mono">#{event.lot_id}</dd></div>
 <div className="flex justify-between"><dt className="text-slate-500">{t('review.farm')}</dt><dd>{event.farm_id || '-'}</dd></div>
 <div className="flex justify-between"><dt className="text-slate-500">{t('review.house')}</dt><dd>{event.house_id || '-'}</dd></div>
 <div className="flex justify-between"><dt className="text-slate-500">{t('common.observations')}</dt><dd className="max-w-[200px] truncate">{event.observations || '-'}</dd></div>
 <div className="flex justify-between"><dt className="text-slate-500">{t('common.version')}</dt><dd>v{event.version}</dd></div>
 </dl>

 {/* Sub-movements */}
 {event.bird_movements?.length > 0 && (
 <div className="mt-4 pt-4 border-t border-slate-100">
 <h3 className="text-xs font-semibold text-slate-500 uppercase mb-2">
 <Bird size={14} className="inline-block mr-1 -mt-0.5" aria-hidden="true" />
 {t('review.birdMovements')}
 </h3>
 {event.bird_movements.map((bm: any, i: number) => (
 <div key={i} className="text-xs text-slate-600 flex gap-3">
 <span>{bm.sex || t('review.mixto')}</span>
 <span>{bm.quantity} {t('review.aves')}</span>
 <span>{bm.avg_weight ? `${bm.avg_weight}g` : ''}</span>
 </div>
 ))}
 </div>
 )}
 <Wheat size={14} className="inline-block mr-1 -mt-0.5" aria-hidden="true" />
 {t('review.feedMovements')}
 
 {event.feed_movements?.length > 0 && (
 <div className="mt-4 pt-4 border-t border-slate-100">
 <h3 className="text-xs font-semibold text-slate-500 uppercase mb-2">
 <Wheat size={14} className="inline-block mr-1 -mt-0.5" aria-hidden="true" />
 {t('review.feedMovements')}
 </h3>
 {event.feed_movements.map((fm: any, i: number) => (
 <div key={i} className="text-xs text-slate-600">{fm.quantity_kg} kg</div>
 ))}
 </div>
 )}
 {event.egg_movements?.length > 0 && (
 <div className="mt-4 pt-4 border-t border-slate-100">
 <h3 className="text-xs font-semibold text-slate-500 uppercase mb-2">
 <Egg size={14} className="inline-block mr-1 -mt-0.5" aria-hidden="true" />
 {t('review.eggMovements')}
 </h3>
 {event.egg_movements.map((em: any, i: number) => (
 <div key={i} className="text-xs text-slate-600">{em.quantity} {t('review.huevos')} ({em.egg_type})</div>
 ))}
 </div>
 )}
 </div>

 {/* SAP Reference & Corrections */}
 <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
 <h2 className="font-semibold text-slate-700 mb-4">
 <RefreshCw size={18} className="inline-block mr-1.5 -mt-0.5" aria-hidden="true" />
 {t('review.sapReference')}
 </h2>
 {event.sap_document_ref ? (
 <dl className="space-y-2 text-sm">
 <div className="flex justify-between"><dt className="text-slate-500">{t('sap.references')}</dt><dd className="font-mono">{event.sap_document_ref}</dd></div>
 </dl>
 ) : (
 <p className="text-sm text-slate-400 italic">{t('review.noSapRef')}</p>
 )}

 {/* Corrections history */}
 {corrections.length > 0 && (
 <div className="mt-4 pt-4 border-t border-slate-100">
 <h3 className="text-xs font-semibold text-slate-500 uppercase mb-2 flex items-center gap-1">
 <Pencil size={14} aria-hidden="true" />
 {t('review.correctionsHistory')}
 </h3>
 {corrections.map((c: any) => (
 <div key={c.id} className="text-xs text-slate-600 mb-2 p-2 bg-amber-50 rounded-lg">
 <p><strong>{c.field_name}:</strong> "{c.original_value}" → "{c.corrected_value}"</p>
 <p className="text-slate-400 mt-0.5">{c.reason} — {new Date(c.created_at).toLocaleString()}</p>
 </div>
 ))}
 </div>
 )}

 {/* Approval actions */}
 {actions.length > 0 && (
 <div className="mt-4 pt-4 border-t border-slate-100">
 <h3 className="text-xs font-semibold text-slate-500 uppercase mb-2 flex items-center gap-1">
 <FileText size={14} aria-hidden="true" />
 {t('review.actionsHistory')}
 </h3>
 {actions.map((a: any) => (
 <div key={a.id} className="text-xs text-slate-600 mb-1">
 <span className="font-medium">{a.action_type}</span>
 {a.observations && <span className="text-slate-400"> — {a.observations}</span>}
 <span className="text-slate-400 ml-2">{new Date(a.created_at).toLocaleString()}</span>
 </div>
 ))}
 </div>
 )}
 </div>
 </div>

 {/* Actions */}
 <div className="mt-6 bg-white rounded-xl shadow-sm border border-slate-200 p-5">
 <h2 className="font-semibold text-slate-700 mb-3">{t('common.actions')}</h2>
 <div className="flex flex-wrap gap-3">
 {can({ permission: 'review:review' }) && event.status === 'pending_review' && (
 <button onClick={() => handleAction('start')}
 className="bg-indigo-600 text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-indigo-700 transition">
 ▶ {t('review.startReview')}
 </button>
 )}
 {can({ permission: 'review:review' }) && event.status === 'in_review' && (
 <>
 <button onClick={() => handleAction('complete')}
 className="bg-teal-600 text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-teal-700 transition">
 ✓ {t('review.completeReview')}
 </button>
 <div className="flex gap-2 items-center">
 <input type="text" placeholder={t('review.observationsPlaceholder')} value={obs} onChange={e => setObs(e.target.value)}
 className="border border-slate-300 rounded-lg px-3 py-2 text-sm w-48" />
 <button onClick={() => handleAction('return')}
 className="bg-orange-600 text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-orange-700 transition">
 ↩ {t('review.returnToOperator')}
 </button>
 </div>
 {can({ permission: 'corrections:correct' }) && <Link to={`/review/${id}/correct`}
 className="bg-amber-600 text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-amber-700 transition">
 <Pencil size={14} className="inline-block mr-1" aria-hidden="true" />
 {t('review.correct')}
 </Link>}
 </>
 )}
 {(event.status === 'corrected' || event.status === 'in_review') && (
 <>
 {can({ permission: 'approvals:approve' }) && <button onClick={() => handleAction('approve')}
 className="bg-emerald-600 text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-emerald-700 transition">
 ✓ {t('review.approve')}
 </button>}
 <div className="flex gap-2 items-center">
 <input type="text" placeholder={t('review.rejectionReason')} value={obs} onChange={e => setObs(e.target.value)}
 className="border border-slate-300 rounded-lg px-3 py-2 text-sm w-48" />
 {can({ permission: 'approvals:reject' }) && <button onClick={() => handleAction('reject')}
 className="bg-red-600 text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-red-700 transition">
 ✗ {t('review.reject')}
 </button>}
 </div>
 </>
 )}
 {can({ permission: 'corrections:correct' }) && <Link to={`/review/${id}/correct`}
 className="bg-amber-100 text-amber-700 px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-amber-200 transition inline-flex items-center gap-1">
 <Pencil size={14} aria-hidden="true" />
 {t('review.correct')}
 </Link>}
 </div> {obsError && <p role="alert" className="text-xs text-red-600 mt-2">{obsError}</p>} </div>
 </div>
 )
}
