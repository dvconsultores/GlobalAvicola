import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { Pencil } from 'lucide-react'
import BackNavigation from '../../components/layout/BackNavigation'
import api from '../../services/api'
import ErrorState from '../../components/ui/ErrorState'
import { useCan } from '../../auth/actionAuthority'
import { useToast, getErrorMessage } from '../../components/Toast'
import { describirCampoCorregido } from '../../utils/correctionFields'

/** `015` · AC-S1-C02/C03: campos cuyo valor se puede dejar vacío al corregir. */
const VACIOS_PERMITIDOS = /^(observations|bird_movements\[\d+\]\.(avg_weight|week_number))$/

export default function CorrectionForm() {
 const can = useCan()
 const { t } = useTranslation()
 const { id } = useParams<{ id: string }>()
 const navigate = useNavigate()
 const [event, setEvent] = useState<any>(null)
 const [correctionTypes, setCorrectionTypes] = useState<any[]>([])
 const toast = useToast()
 const [loading, setLoading] = useState(true)
 const [submitting, setSubmitting] = useState(false)
 // `R-212` · AC-04/05.
 const [estado, setEstado] = useState<'ok' | 'prohibido' | 'error'>('ok')
 const [refresco, setRefresco] = useState(0)

 const [fieldName, setFieldName] = useState('')
 const [campos, setCampos] = useState<any[]>([])
 const [correctedValue, setCorrectedValue] = useState('')
 const [correctionTypeId, setCorrectionTypeId] = useState<number | undefined>()
 const [reason, setReason] = useState('')
 // `015` · AC-S1-C04: validación en cliente con mensaje inline (sin `alert`).
 const [error, setError] = useState('')
 // `004` · NAV-01/AC14: cambios sin guardar (formulario de corrección).
 const camposSucios = correctedValue.length > 0 || reason.trim().length > 0

 useEffect(() => {
 const fetch = async () => {
 try {
 // GA-REM-011 C-05: consulta por identificador en lugar de listar 200.
 const { data: ev } = await api.get(`/operations/${id}`)
 setEvent(ev || null)

 // `015` · AC-S1-C01: el formulario ofrece los campos REALES corregibles del evento
 // (columnas + submovimientos); una lista vacía significa «no corregible en este estado».
 const { data: cf } = await api.get(`/corrections/events/${id}/correctable-fields`)
 const lista = Array.isArray(cf) ? cf : []
 setCampos(lista)
 // Por defecto las observaciones si el backend las ofrece; si no, el primer campo.
 const porDefecto = lista.find((f: any) => f.field_name === 'observations') || lista[0]
 setFieldName(porDefecto ? String(porDefecto.field_name) : '')

 const { data: ctypes } = await api.get('/masters/correction-types')
 setCorrectionTypes(Array.isArray(ctypes) ? ctypes : [])
 setEstado('ok')
 } catch (err: any) {
 console.error(err)
 setEstado(err?.response?.status === 403 ? 'prohibido' : 'error')
 } finally {
 setLoading(false)
 }
 }
 fetch()
 }, [id, refresco])

 if (estado !== 'ok') return <div className="py-4 sm:py-6"><ErrorState kind={estado} onRetry={() => setRefresco(n => n + 1)} /></div>

 const campoActual = campos.find((f: any) => String(f.field_name) === fieldName) || null

 /** Devuelve el mensaje de error (clave i18n) o '' si el formulario es válido. */
 const validar = (): string => {
 if (!campoActual) return t('corrections.noFields')
 const tipo = String(campoActual.value_type || 'text')
 if (!correctedValue.trim() && !VACIOS_PERMITIDOS.test(fieldName)) return t('corrections.correctedRequired')
 if ((tipo === 'integer' || tipo === 'decimal') && correctedValue.trim() && Number.isNaN(Number(correctedValue))) {
 return t('corrections.valueNumeric')
 }
 if (reason.trim().length < 5) return t('corrections.reasonMin')
 return ''
 }

 const handleSubmit = async (e: React.FormEvent) => {
 e.preventDefault()
 // `015` · AC-S1-C04: validación en cliente, un único mensaje inline (sin `alert`).
 const problema = validar()
 if (problema) { setError(problema); return }
 setError('')
 setSubmitting(true)
 try {
 await api.post('/corrections', {
 event_id: Number(id),
 field_name: fieldName,
 original_value: campoActual?.current_value ?? '',
 corrected_value: correctedValue,
 correction_type_id: correctionTypeId || null,
 reason,
 })
 toast.success(t('review.correctionSaved'))
 navigate(`/review/${id}`)
 } catch (err: any) {
 toast.error(getErrorMessage(err, t('review.errorSavingCorrection')))
 } finally {
 setSubmitting(false)
 }
 }

 if (loading) return <div className="py-8 text-center text-slate-500">{t('common.loading')}</div>
 if (!event) return <div className="py-8 text-center text-slate-500">{t('review.eventNotFound')}</div>

 // `015` · AC-S1-C03: etiqueta legible del campo (nunca el nombre crudo del backend) y, en
 // submovimientos de aves, el sexo de la fila.
 const etiquetaCampo = (f: any) => {
 const base = describirCampoCorregido(t, String(f.field_name))
 return f.row_label ? `${base} (${t(`corrections.sex.${f.row_label}`, String(f.row_label))})` : base
 }
 // Tipo de control según el backend: fecha, entero, decimal o texto.
 const tipoValor = String(campoActual?.value_type || 'text')
 const propsValor = tipoValor === 'date' ? { type: 'date' as const }
 : tipoValor === 'integer' ? { type: 'number' as const, step: '1' }
 : tipoValor === 'decimal' ? { type: 'number' as const, step: 'any' }
 : { type: 'text' as const }

 return (
 <div className="py-4 sm:py-6">
 <div className="flex items-center gap-3 mb-6">
 <BackNavigation to={`/review/${id}`} dirty={camposSucios} />
 <h1 className="text-xl font-bold text-[#1E3A5F] flex items-center gap-2">
 <Pencil size={20} aria-hidden="true" />
 {t('review.correctEvent', { id })}
 </h1>
 </div>

 {campos.length === 0 ? (
 <p className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 text-sm text-slate-500" data-testid="correction-no-fields">
 {t('corrections.noFields')}
 </p>
 ) : (
 <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 space-y-5">
 {/* Field selector */}
 <div>
 <label className="block text-sm font-medium text-slate-700 mb-1.5">{t('review.fieldToCorrect')}</label>
 <select value={fieldName} onChange={e => { setFieldName(e.target.value); setCorrectedValue(''); setError('') }}
 className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-[#1E3A5F] focus:border-[#1E3A5F]">
 {campos.map((f: any) => (
 <option key={String(f.field_name)} value={String(f.field_name)}>{etiquetaCampo(f)}</option>
 ))}
 </select>
 </div>

 {/* Side by side: original vs corrected */}
 <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
 <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
 <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">{t('review.originalValue')}</label>
 <input type="text" value={campoActual?.current_value ?? ''} readOnly aria-readonly="true" data-testid="correction-original"
 className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm bg-slate-100 text-slate-600" />
 <p className="text-xs text-slate-400 mt-1">{t('review.originalByOperator')}</p>
 </div>
 <div className="bg-amber-50 rounded-lg p-4 border border-amber-200">
 <label className="block text-xs font-semibold text-amber-700 uppercase mb-1">{t('review.correctedValue')}</label>
 <input {...propsValor} value={correctedValue} onChange={e => { setCorrectedValue(e.target.value); setError('') }}
 data-testid="correction-corrected"
 className="w-full border border-amber-300 rounded-lg px-3 py-2.5 text-sm bg-white focus:ring-2 focus:ring-amber-400" />
 <p className="text-xs text-amber-600 mt-1">{t('review.correctedByYou')}</p>
 </div>
 </div>

 {/* Correction type */}
 <div>
 <label className="block text-sm font-medium text-slate-700 mb-1.5">{t('review.correctionType')}</label>
 <select value={correctionTypeId || ''} onChange={e => setCorrectionTypeId(e.target.value ? Number(e.target.value) : undefined)}
 className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm">
 <option value="">-- {t('common.select')} --</option>
 {correctionTypes.map((ct: any) => (
 <option key={ct.id} value={ct.id}>{ct.name}</option>
 ))}
 </select>
 </div>

 {/* Reason */}
 <div>
 <label className="block text-sm font-medium text-slate-700 mb-1.5">{t('review.correctionReason')} *</label>
 <textarea value={reason} onChange={e => { setReason(e.target.value); setError('') }}
 rows={3}
 placeholder={t('review.reasonPlaceholder')}
 aria-invalid={error ? true : undefined}
 className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-[#1E3A5F]" />
 <p className="text-xs text-slate-400 mt-1">{t('review.correctionAuditNote')}</p>
 </div>

 {/* `015` · AC-S1-C04: un único mensaje de validación, inline. */}
 {error && <p role="alert" data-testid="correction-error" className="text-sm text-red-600">{error}</p>}

 {/* Submit */}
 <div className="flex gap-3 pt-2">
 {can({ permission: 'corrections:correct' }) && <button type="submit" disabled={submitting}
 className="bg-amber-600 text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-amber-700 transition disabled:opacity-50">
 {submitting ? t('common.saving') : t('review.saveCorrection')}
 </button>}
 <Link to={`/review/${id}`}
 className="bg-slate-100 text-slate-700 px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-slate-200 transition">
 {t('common.cancel')}
 </Link>
 </div>
 </form>
 )}
 </div>
 )
}
