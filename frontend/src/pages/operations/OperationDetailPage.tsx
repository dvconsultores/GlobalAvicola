import { useState, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Activity, Paperclip, Upload, Trash2, FileText, Image, Download, X, RotateCcw } from 'lucide-react'
import api from '../../services/api'
import { operationsService } from '../../services/operations.service'
import { reversalsService } from '../../services/reversals.service'
import { useCan } from '../../auth/actionAuthority'
import WeightEvaluation from '../../components/operations/WeightEvaluation'
import { useToast, getErrorMessage } from '../../components/Toast'

const STATUS_COLORS: Record<string, string> = {
 draft: 'bg-slate-100 text-slate-600', registered: 'bg-blue-100 text-blue-800',
 pending_review: 'bg-amber-100 text-amber-800', in_review: 'bg-indigo-100 text-indigo-800',
 returned: 'bg-orange-100 text-orange-800', corrected: 'bg-teal-100 text-teal-800',
 approved: 'bg-emerald-100 text-emerald-800', rejected: 'bg-red-100 text-red-800',
 consolidated: 'bg-purple-100 text-purple-800', sent_to_sap: 'bg-cyan-100 text-cyan-800',
 sap_confirmed: 'bg-green-100 text-green-800',
 // `R-207`: estado propio del reverso (nunca el gris de fallback).
 reversed: 'bg-rose-100 text-rose-800',
}

const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'application/pdf']
const MAX_SIZE_MB = 10

/** `GA-FE-05` · `R-181` · `OD-17.a/b` · `docs/12 §2`: estados que el backend acepta en
 * `POST /operations/{id}/submit` (`REENVIABLES`). El CTA refleja exactamente ese conjunto:
 * registrado ⇒ enviar; devuelto/rechazado ⇒ reenviar; el resto no ofrece acción. */
const SUBMITTABLE_STATUSES = ['registered', 'returned', 'rejected']

function formatBytes(bytes: number) {
 if (bytes < 1024) return `${bytes} B`
 if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
 return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

interface Evidence {
 id: number
 file_name: string
 file_size: number | null
 mime_type: string | null
 evidence_type: string
 description: string | null
 uploaded_by_id: number
 created_at: string
}

export default function OperationDetailPage() {
 const can = useCan()
 const { t } = useTranslation()
 const { id } = useParams<{ id: string }>()
 const [event, setEvent] = useState<any>(null)
 const [loading, setLoading] = useState(true)
 const [error, setError] = useState('')
 const [evidences, setEvidences] = useState<Evidence[]>([])
 const [uploading, setUploading] = useState(false)
 const [description, setDescription] = useState('')
 const [evidenceType, setEvidenceType] = useState('') // `GA-REM-042` · `R-152`: clase del adjunto del plan de importación
 const [deletingId, setDeletingId] = useState<number | null>(null)
 const [submitting, setSubmitting] = useState(false)
 const submittingRef = useRef(false)
 const [previewUrl, setPreviewUrl] = useState<string | null>(null)
 // `R-207` · AC-01/02/04: superficie de reverso (gate `reversals:create`).
 const [showReversal, setShowReversal] = useState(false)
 const [reversalReason, setReversalReason] = useState('')
 const [reversalError, setReversalError] = useState('')
 const [contrapartidaId, setContrapartidaId] = useState<number | null>(null)
 const reversalRef = useRef(false)
 const fileRef = useRef<HTMLInputElement>(null)
 const toast = useToast()
 // `R-198` · `AC-03` (`C-02`): estados en los que el backend acepta adjuntar/borrar; la UI
 // es espejo del servidor (que es quien decide).
 const EVIDENCE_EDITABLE_STATUSES = ['draft', 'registered', 'pending_review', 'in_review', 'returned', 'rejected', 'corrected']

 const loadEvent = () => {
 api.get(`/operations/${id}`).then(({ data }) => {
 setEvent(data)
 setEvidences(data.evidences || [])
 }).catch((e: any) => {
 const msg = getErrorMessage(e, t('operations.errorLoadingEvent'))
 setError(msg)
 toast.error(msg)
 }).finally(() => setLoading(false))
 }

 useEffect(() => { loadEvent() }, [id]) // eslint-disable-line react-hooks/exhaustive-deps

 const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
 const file = e.target.files?.[0]
 if (!file) return
 if (!ALLOWED_TYPES.includes(file.type)) {
 toast.error(t('evidence.invalidType'))
 return
 }
 if (file.size > MAX_SIZE_MB * 1024 * 1024) {
 toast.error(t('evidence.tooLarge', { max: MAX_SIZE_MB }))
 return
 }
 setUploading(true)
 try {
 const fd = new FormData()
 fd.append('file', file)
 fd.append('description', description)
 if (evidenceType) fd.append('evidence_type', evidenceType)
 await api.post(`/operations/${id}/evidences`, fd, {
 headers: { 'Content-Type': 'multipart/form-data' },
 })
 setDescription('')
 if (fileRef.current) fileRef.current.value = ''
 // `R-198` · `AC-01/02` (`C-01=A`): relee la verdad del servidor tras mutar — la
 // respuesta local no es fuente; el contrato del detalle es el que manda.
 await loadEvent()
 toast.success(t('evidence.uploadSuccess'))
 } catch (err: any) {
 toast.error(getErrorMessage(err, t('evidence.uploadError')))
 } finally { setUploading(false) }
 }

 const handleDelete = async (evidenceId: number) => {
 setDeletingId(evidenceId)
 try {
 await api.delete(`/operations/${id}/evidences/${evidenceId}`)
 // `R-198` · `AC-02`: relee del servidor tras borrar.
 await loadEvent()
 toast.success(t('evidence.deleteSuccess'))
 } catch (err: any) {
 toast.error(getErrorMessage(err, t('evidence.deleteError')))
 } finally { setDeletingId(null) }
 }

 // `GA-FE-05` · `R-181`: acto explícito de envío/reenvío a revisión.
 // Autoridad: permiso de la ACCIÓN (`operations:create`, contrato real del endpoint) ∧ unidad
 // disponible (GA-FE-04). Estado: solo los aceptados por el backend (`REENVIABLES`).
 // Tras éxito **y** tras fallo se relee la verdad del backend (nada optimista).
 const canSubmit = !!event && SUBMITTABLE_STATUSES.includes(event.status)
 && can({ permission: 'operations:create', requiresUnits: true })
 // `R-207` · AC-01: reverso solo desde un aprobado y con el permiso de la acción.
 const canReverse = !!event && event.status === 'approved'
 && can({ permission: 'reversals:create' })
 const isResubmit = !!event && (event.status === 'returned' || event.status === 'rejected')
 const submitLabel = isResubmit
 ? String(t('operations.resubmitToReview', 'Reenviar a revisión'))
 : String(t('operations.submitToReview', 'Enviar a revisión'))

 const handleSubmitToReview = async () => {
 if (!event || submittingRef.current) return
 submittingRef.current = true
 setSubmitting(true)
 try {
 await operationsService.submit(event.id)
 toast.success(t(
 isResubmit ? 'operations.resubmittedToReview' : 'operations.submittedToReview',
 isResubmit ? 'Reenviado a revisión' : 'Enviado a revisión',
 ))
 } catch (err: any) {
 toast.error(getErrorMessage(err, t('operations.submitError', 'No se pudo enviar a revisión')))
 } finally {
 submittingRef.current = false
 setSubmitting(false)
 loadEvent()
 }
 }

 // `R-207` · AC-R207-02/04: motivo ≥5 validado en cliente (el servidor es autoridad);
 // la contrapartida se enlaza desde la respuesta 201 (verdad del contrato de reverso).
 const confirmarReverso = async () => {
 if (!event || reversalRef.current) return
 if (reversalReason.trim().length < 5) {
 setReversalError(t('reversals.reasonTooShort', 'El motivo debe tener al menos 5 caracteres'))
 return
 }
 reversalRef.current = true
 try {
 const { data } = await reversalsService.solicitar(event.id, reversalReason.trim())
 if (data?.reversal_event_id) setContrapartidaId(data.reversal_event_id)
 setShowReversal(false)
 toast.success(t('reversals.requested', 'Reverso solicitado'))
 await loadEvent()
 } catch (err: any) {
 toast.error(getErrorMessage(err, t('reversals.requestError', 'No se pudo solicitar el reverso')))
 } finally {
 reversalRef.current = false
 }
 }

 const handleDownload = async (ev: Evidence) => {
 try {
 const response = await api.get(`/operations/${id}/evidences/${ev.id}/download`, { responseType: 'blob' })
 const url = URL.createObjectURL(response.data)
 const a = document.createElement('a')
 a.href = url; a.download = ev.file_name; a.click()
 URL.revokeObjectURL(url)
 } catch (err: any) {
 toast.error(getErrorMessage(err, t('evidence.downloadError')))
 }
 }

 const handlePreview = async (ev: Evidence) => {
 if (!ev.mime_type?.startsWith('image/')) { handleDownload(ev); return }
 try {
 const response = await api.get(`/operations/${id}/evidences/${ev.id}/download`, { responseType: 'blob' })
 setPreviewUrl(URL.createObjectURL(response.data))
 } catch { handleDownload(ev) }
 }

 if (loading) return <div className="p-6 text-slate-500">{t('common.loading')}</div>
 if (error) return <div className="p-6 text-red-600 bg-red-50 rounded-lg">{error}</div>
 if (!event) return <div className="p-6 text-slate-500">{t('operations.eventNotFound')}</div>

 return (
 <div className="py-4 sm:py-6 space-y-4">
 <Link to="/operations" className="text-slate-400 hover flex items-center gap-1 text-sm">
 <ArrowLeft size={16} /> {t('operations.backToOperations')}
 </Link>

 {/* Event Card */}
 <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
 <div className="flex items-center justify-between mb-4">
 <h1 className="text-xl font-bold text-[#1E3A5F]">{t('operations.eventDetail', { id: event.id })}</h1>
 <span className={`px-3 py-1 rounded-full text-sm font-medium ${STATUS_COLORS[event.status] || 'bg-slate-100'}`}>{String(t(`status.${event.status}`, event.status))}</span>
 </div>
 {/* `R-207` · AC-R207-02: enlace original ↔ contrapartida (respuesta 201 o campo del detalle). */}
 {(contrapartidaId || event.reversal_event_id) && (
 <div className="mb-4 bg-rose-50 border border-rose-200 rounded-lg px-4 py-3 text-sm text-rose-800">
 {t('reversals.counterpart', 'Contrapartida')}{' '}
 <Link to={`/operations/${contrapartidaId ?? event.reversal_event_id}`} className="font-mono underline">
 #{contrapartidaId ?? event.reversal_event_id}
 </Link>
 </div>
 )}
 {/* `GA-FE-05` · `R-181`: acción primaria state-aware (desktop y móvil comparten vista). */}
 {canSubmit && (
 <div className="flex flex-wrap justify-end mb-4">
 <button
 type="button"
 onClick={handleSubmitToReview}
 disabled={submitting}
 className="bg-[#1E3A5F] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-800 transition disabled:opacity-50 disabled:cursor-not-allowed"
 >
 {submitting ? t('common.saving') : submitLabel}
 </button>
 </div>
 )}
 {/* `R-207` · AC-01: acción «Solicitar reverso» (gate espejo `reversals:create`). */}
 {canReverse && (
 <div className="flex flex-wrap justify-end mb-4">
 <button
 type="button"
 onClick={() => { setShowReversal(true); setReversalReason(''); setReversalError('') }}
 className="bg-rose-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-rose-700 transition inline-flex items-center gap-1"
 >
 <RotateCcw size={14} aria-hidden="true" /> {t('reversals.request', 'Solicitar reverso')}
 </button>
 </div>
 )}
 <dl className="grid grid-cols-2 gap-4 text-sm">
 <div><dt className="text-slate-500">{t('common.type')}</dt><dd className="font-medium">{event.event_type}</dd></div>
 <div><dt className="text-slate-500">{t('common.date')}</dt><dd>{event.event_date}</dd></div>
 <div>
 <dt className="text-slate-500">{t('lots.lot')}</dt>
 <dd className="font-mono">
 {event.lot_id ? (
 <Link to={`/lots/${event.lot_id}`} className="text-[#5a9bba] hover:underline">#{event.lot_id}</Link>
 ) : event.event_type === 'grandparent_import' ? (
 <span className="text-slate-500">{t('operations.lotAutoPending', 'Se creará al aprobar')}</span>
 ) : (
 '—'
 )}
 </dd>
 </div>
 <div><dt className="text-slate-500">{t('common.version')}</dt><dd>v{event.version}</dd></div>
 <div className="col-span-2"><dt className="text-slate-500">{t('common.observations')}</dt><dd>{event.observations || '—'}</dd></div>
 {event.sap_document_ref && <div className="col-span-2"><dt className="text-slate-500">{t('operations.sapRef')}</dt><dd className="font-mono">{event.sap_document_ref}</dd></div>}
 </dl>

 {event.bird_movements?.length > 0 && (
 <div className="mt-4 pt-4 border-t">
 <h3 className="font-semibold text-sm text-slate-600 mb-2 flex items-center gap-1">
 <Activity size={14} /> {t('review.birdMovements')}
 </h3>
 {event.bird_movements.map((bm: any, i: number) => (
 <div key={i} className="text-xs text-slate-600">{bm.quantity} {t('review.aves')} {bm.sex || ''} {bm.avg_weight ? `· ${bm.avg_weight}g` : ''}</div>
 ))}
 </div>
 )}
 {/*
 `spec.md §4.5` pide avisar por desviación de peso, y `OD-06` fijó contra qué. La
 conclusión la calcula el backend; aquí solo se muestra (`AC-FE11`, `AC-FE14`).
 */}
 {/* `GA-REM-037-B` · B02: la recepción de reproductoras también muestra la evaluación del backend */}
 {(event.event_type === 'weight_recording' || event.event_type === 'bird_reception') && <WeightEvaluation eventId={event.id} />}
 {event.feed_movements?.length > 0 && (
 <div className="mt-4 pt-4 border-t">
 <h3 className="font-semibold text-sm text-slate-600 mb-2">{t('operations.feed')}</h3>
 {event.feed_movements.map((fm: any, i: number) => <div key={i} className="text-xs text-slate-600">{fm.quantity_kg} kg</div>)}
 </div>
 )}
 {event.egg_movements?.length > 0 && (
 <div className="mt-4 pt-4 border-t">
 <h3 className="font-semibold text-sm text-slate-600 mb-2">{t('operations.eggs')}</h3>
 {event.egg_movements.map((em: any, i: number) => <div key={i} className="text-xs text-slate-600">{em.quantity} · {em.egg_type}</div>)}
 </div>
 )}
 {/* `GA-REM-042` · `R-152`: el plan de importación de abuelas (`docs/02 §3.4.1`) */}
 {event.event_type === 'grandparent_import' && event.extra_data?.import_plan && (
 <div className="mt-4 pt-4 border-t">
 <h3 className="font-semibold text-sm text-slate-600 mb-2">{t('operations.importPlanTitle', 'Plan de importación')}</h3>
 <dl className="grid grid-cols-2 gap-2 text-xs text-slate-600">
 {([
 ['origin_country', 'importOriginCountry'], ['purchased_total', 'importPurchasedTotal'], ['shipped_total', 'importShippedTotal'],
 ['received_total', 'importReceivedTotal'], ['transit_mortality', 'importTransitMortality'], ['departure_date', 'importDepartureDate'],
 ['arrival_date', 'importArrivalDate'], ['reception_condition', 'importReceptionCondition'], ['quarantine_days', 'importQuarantineDays'],
 ['quarantine_end_date', 'importQuarantineEndDate'], ['initial_health_inspection', 'importInitialHealthInspection'],
 ] as [string, string][]).map(([campo, clave]) => (
 <div key={campo}><dt className="text-slate-500">{t(`operations.${clave}`)}</dt><dd>{String(event.extra_data.import_plan[campo] ?? '—')}</dd></div>
 ))}
 </dl>
 </div>
 )}
 </div>

 {/* Evidence Section */}
 <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
 <div className="flex items-center gap-2 mb-4">
 <Paperclip size={18} className="text-[#5a9bba]" />
 <h2 className="text-base font-bold text-slate-800">{t('evidence.title')}</h2>
 <span className="ml-auto text-xs text-slate-400">{t('evidence.allowedTypes')}</span>
 </div>

 {/* Existing evidences */}
 {evidences.length > 0 ? (
 <ul className="space-y-2 mb-4">
 {evidences.map((ev) => {
 const isImage = ev.mime_type?.startsWith('image/')
 return (
 <li key={ev.id} className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg border border-slate-200 group">
 <div className="shrink-0 text-slate-400">
 {isImage ? <Image size={20} className="text-blue-500" /> : <FileText size={20} className="text-red-500" />}
 </div>
 <div className="flex-1 min-w-0">
 <p className="text-sm font-medium text-slate-700 truncate">{ev.file_name}</p>
 <p className="text-xs text-slate-400">
 {ev.file_size ? formatBytes(ev.file_size) : ''}
 {ev.evidence_type && ev.evidence_type !== 'document' && ev.evidence_type !== 'photo' ? ` · ${t(`evidence.types.${ev.evidence_type}`, ev.evidence_type)}` : ''}
{ev.description ? ` · ${ev.description}` : ''}
 </p>
 </div>
 <div className="flex items-center gap-1">
 <button
 type="button"
 onClick={() => handlePreview(ev)}
 title={t('evidence.download')}
 className="p-1.5 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-md"
 >
 <Download size={14} />
 </button>
 {can({ permission: 'operations:delete' }) && event && EVIDENCE_EDITABLE_STATUSES.includes(event.status) && <button
 type="button"
 onClick={() => handleDelete(ev.id)}
 disabled={deletingId === ev.id}
 title={t('common.delete')}
 className="p-1.5 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-md disabled:opacity-40"
 >
 <Trash2 size={14} />
 </button>}
 </div>
 </li>
 )
 })}
 </ul>
 ) : (
 <p className="text-sm text-slate-400 mb-4 italic">{t('evidence.noFiles')}</p>
 )}

 {/* Upload area */}
 {event.event_type === 'grandparent_import' && (
 <div className="mb-3">
 <label className="block text-xs font-semibold text-slate-600 mb-1">{t('evidence.typeLabel', 'Clase de adjunto')}</label>
 <select value={evidenceType} onChange={(e) => setEvidenceType(e.target.value)} className="w-full h-10 px-2 border border-slate-200 rounded-lg text-sm bg-white">
 <option value="">{t('evidence.typeAuto', 'Según el archivo (foto o documento)')}</option>
 {['sanitary_document', 'import_permit', 'customs_document', 'vaccination_certificate', 'origin_certificate'].map((clase) => (
 <option key={clase} value={clase}>{t(`evidence.types.${clase}`, clase)}</option>
 ))}
 </select>
 </div>
 )}
 {can({ permission: 'operations:create' }) && event && EVIDENCE_EDITABLE_STATUSES.includes(event.status) && (
 <div className="border-2 border-dashed border-slate-200 rounded-lg p-4 space-y-3">
 <input
 ref={fileRef}
 type="text"
 placeholder={t('evidence.descriptionPlaceholder')}
 value={description}
 onChange={e => setDescription(e.target.value)}
 className="w-full h-9 px-3 border border-slate-300 rounded-lg text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
 />
 <label className={`flex items-center gap-2 cursor-pointer w-full justify-center px-4 py-2.5 rounded-lg text-sm font-medium transition-colors
 ${uploading ? 'bg-slate-100 text-slate-400 cursor-not-allowed' : 'bg-[#5a9bba] text-white hover:bg-[#155bb5]'}`}>
 <Upload size={16} />
 {uploading ? t('evidence.uploading') : t('evidence.uploadButton')}
 <input
 type="file"
 className="hidden"
 accept=".jpg,.jpeg,.png,.gif,.webp,.pdf"
 disabled={uploading}
 onChange={handleFileChange}
 />
 </label>
 <p className="text-xs text-center text-slate-400">{t('evidence.maxSize', { max: MAX_SIZE_MB })}</p>
 </div>
 )}
 </div>

 {/* Image Preview Modal */}
 {previewUrl && (
 <div
 className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4"
 onClick={() => { URL.revokeObjectURL(previewUrl); setPreviewUrl(null) }}
 >
 <button
 className="absolute top-4 right-4 text-white bg-black/50 rounded-full p-2 hover:bg-black/80"
 onClick={() => { URL.revokeObjectURL(previewUrl); setPreviewUrl(null) }}
 >
 <X size={20} />
 </button>
 <img
 src={previewUrl}
 alt="preview"
 className="max-w-full max-h-[90vh] rounded-lg shadow-xl object-contain"
 onClick={e => e.stopPropagation()}
 />
 </div>
 )}

 {/* `R-207` · modal de solicitud de reverso (sin diálogos nativos). */}
 {showReversal && (
 <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" onClick={() => setShowReversal(false)}>
 <div className="bg-white rounded-2xl shadow-xl p-6 max-w-md w-full mx-4" onClick={(e) => e.stopPropagation()}>
 <h2 className="text-lg font-bold text-[#1E3A5F] mb-1">{t('reversals.request', 'Solicitar reverso')}</h2>
 <p className="text-xs text-slate-500 mb-3">{t('reversals.confirm', 'Se creará una contrapartida que deberá aprobarse para neutralizar el registro.')}</p>
 <textarea
 aria-label={t('reversals.reason', 'Motivo (mín. 5 caracteres)')}
 value={reversalReason}
 onChange={(e) => setReversalReason(e.target.value)}
 rows={3}
 className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
 />
 {reversalError && <p role="alert" className="text-xs text-red-600 mt-1">{reversalError}</p>}
 <div className="flex gap-3 mt-4">
 <button onClick={() => setShowReversal(false)} className="flex-1 bg-slate-100 text-slate-700 px-4 py-2.5 rounded-lg text-sm font-medium hover:bg-slate-200 transition">{t('common.cancel', 'Cancelar')}</button>
 <button onClick={confirmarReverso} className="flex-1 bg-rose-600 text-white px-4 py-2.5 rounded-lg text-sm font-medium hover:bg-rose-700 transition">{t('common.confirm', 'Confirmar')}</button>
 </div>
 </div>
 </div>
 )}
 </div>
 )
}

