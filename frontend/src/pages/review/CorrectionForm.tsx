import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { Pencil } from 'lucide-react'
import api from '../../services/api'
import { useToast, getErrorMessage } from '../../components/Toast'

export default function CorrectionForm() {
  const { t } = useTranslation()
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [event, setEvent] = useState<any>(null)
  const [correctionTypes, setCorrectionTypes] = useState<any[]>([])
  const toast = useToast()
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  const [fieldName, setFieldName] = useState('observations')
  const [originalValue, setOriginalValue] = useState('')
  const [correctedValue, setCorrectedValue] = useState('')
  const [correctionTypeId, setCorrectionTypeId] = useState<number | undefined>()
  const [reason, setReason] = useState('')

  useEffect(() => {
    const fetch = async () => {
      try {
        const { data: all } = await api.get('/operations?limit=200')
        const ev = (all as any[]).find((e: any) => e.id === Number(id))
        setEvent(ev || null)
        if (ev) {
          setOriginalValue(ev.observations || '')
        }

        const { data: ctypes } = await api.get('/masters/correction-types')
        setCorrectionTypes(Array.isArray(ctypes) ? ctypes : [])
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    fetch()
  }, [id])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!reason || reason.length < 5) return alert(t('review.reasonMinLength'))
    setSubmitting(true)
    try {
      await api.post('/corrections', {
        event_id: Number(id),
        field_name: fieldName,
        original_value: originalValue,
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

  if (loading) return <div className="max-w-2xl mx-auto px-4 py-8 text-center text-slate-500">{t('common.loading')}</div>
  if (!event) return <div className="max-w-2xl mx-auto px-4 py-8 text-center text-slate-500">{t('review.eventNotFound')}</div>

  const fields = [
    { key: 'observations', label: t('common.observations'), current: event.observations || '' },
  ]

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <div className="flex items-center gap-3 mb-6">
        <Link to={`/review/${id}`} className="text-slate-400 hover:text-slate-600">← {t('common.back')}</Link>
        <h1 className="text-xl font-bold text-[#1E3A5F] flex items-center gap-2">
          <Pencil size={20} aria-hidden="true" />
          {t('review.correctEvent', { id })}
        </h1>
      </div>

      <form onSubmit={handleSubmit} className="bg-white dark:bg-slate-800 dark:border-slate-700 rounded-xl shadow-sm border border-slate-200 dark:shadow-none p-6 space-y-5">
        {/* Field selector */}
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-200 mb-1.5">{t('review.fieldToCorrect')}</label>
          <select value={fieldName} onChange={e => { setFieldName(e.target.value); setOriginalValue(event[e.target.value] || '') }}
            className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-[#1E3A5F] focus:border-[#1E3A5F]">
            {fields.map(f => (
              <option key={f.key} value={f.key}>{f.label} ({f.key})</option>
            ))}
          </select>
        </div>

        {/* Side by side: original vs corrected */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="bg-slate-50 dark:bg-slate-800 rounded-lg p-4 border border-slate-200">
            <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">{t('review.originalValue')}</label>
            <input type="text" value={originalValue} onChange={e => setOriginalValue(e.target.value)}
              className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm bg-white" />
            <p className="text-xs text-slate-400 mt-1">{t('review.originalByOperator')}</p>
          </div>
          <div className="bg-amber-50 rounded-lg p-4 border border-amber-200">
            <label className="block text-xs font-semibold text-amber-700 uppercase mb-1">{t('review.correctedValue')}</label>
            <input type="text" value={correctedValue} onChange={e => setCorrectedValue(e.target.value)}
              className="w-full border border-amber-300 rounded-lg px-3 py-2.5 text-sm bg-white focus:ring-2 focus:ring-amber-400" />
            <p className="text-xs text-amber-600 mt-1">{t('review.correctedByYou')}</p>
          </div>
        </div>

        {/* Correction type */}
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-200 mb-1.5">{t('review.correctionType')}</label>
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
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-200 mb-1.5">{t('review.correctionReason')} *</label>
          <textarea value={reason} onChange={e => setReason(e.target.value)}
            rows={3}
            placeholder={t('review.reasonPlaceholder')}
            className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-[#1E3A5F]"
            required />
          <p className="text-xs text-slate-400 mt-1">{t('review.correctionAuditNote')}</p>
        </div>

        {/* Submit */}
        <div className="flex gap-3 pt-2">
          <button type="submit" disabled={submitting}
            className="bg-amber-600 text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-amber-700 transition disabled:opacity-50">
            {submitting ? t('common.saving') : t('review.saveCorrection')}
          </button>
          <Link to={`/review/${id}`}
            className="bg-slate-100 text-slate-700 dark:text-slate-200 px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-slate-200 transition">
            {t('common.cancel')}
          </Link>
        </div>
      </form>
    </div>
  )
}
