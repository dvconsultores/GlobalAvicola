import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useTranslation } from 'react-i18next'
import { useNavigate, useSearchParams } from 'react-router-dom'
import api from '../../services/api'
import { useToast } from '../../components/Toast'

// ============================================================
// All 24 event types with their required movement sub-forms
// ============================================================
const EVENT_DEFS: Record<string, {
  icon: string
  birdMovements?: boolean
  eggMovements?: boolean
  feedMovements?: boolean
  hatcheryParams?: boolean
  inspectionDetails?: boolean
}> = {
  bird_reception: { icon: '🐔', birdMovements: true },
  bird_distribution: { icon: '📦', birdMovements: true },
  bird_transfer: { icon: '🚛', birdMovements: true },
  bird_exit: { icon: '📤', birdMovements: true },
  feed_registration: { icon: '🌾', feedMovements: true },
  weight_recording: { icon: '⚖️', birdMovements: true },
  mortality_recording: { icon: '💀', birdMovements: true },
  cull_recording: { icon: '🗑️', birdMovements: true },
  vaccination: { icon: '💉', birdMovements: true },
  medication: { icon: '💊', birdMovements: true },
  farm_inspection: { icon: '🏭', inspectionDetails: true },
  transport_inspection: { icon: '🚛', inspectionDetails: true },
  hatchery_inspection: { icon: '🔥', inspectionDetails: true },
  egg_collection: { icon: '🥚', eggMovements: true },
  egg_classification: { icon: '📋', eggMovements: true },
  egg_dispatch: { icon: '📤', eggMovements: true },
  egg_reception_hatchery: { icon: '📥', eggMovements: true },
  incubation_load: { icon: '🔥', hatcheryParams: true },
  ovoscopy: { icon: '🔦', eggMovements: true },
  transfer_to_hatcher: { icon: '🔄', hatcheryParams: true },
  birth_registration: { icon: '🐤', birdMovements: true },
  chick_dispatch: { icon: '📤', birdMovements: true },
  lot_closure: { icon: '🔒' },
  grandparent_import: { icon: '✈️', birdMovements: true },
}

// ============================================================
// Zod Schema
// ============================================================
const operationSchema = z.object({
  lot_id: z.number({ message: 'operations.selectLot' }).min(1),
  event_type: z.string().min(1),
  event_date: z.string().min(1),
  observations: z.string().optional(),
  bird_movements: z.array(z.object({
    sex: z.string().optional(),
    quantity: z.number().min(0),
    avg_weight: z.number().optional(),
    week_number: z.number().optional(),
    breed_id: z.number().optional(),
    source_house_id: z.number().optional(),
    target_house_id: z.number().optional(),
  })).optional(),
  egg_movements: z.array(z.object({
    egg_type: z.string(),
    quantity: z.number().min(0),
    avg_weight: z.number().optional(),
  })).optional(),
  feed_movements: z.array(z.object({
    feed_type_id: z.number().optional(),
    quantity_kg: z.number().min(0.1),
    sacks_count: z.number().optional(),
    week_number: z.number().optional(),
    sap_order_id: z.string().optional(),
  })).optional(),
  hatchery_params: z.array(z.object({
    incubator_id: z.number().optional(),
    temperature: z.number().optional(),
    humidity: z.number().optional(),
    quantity_loaded: z.number().optional(),
  })).optional(),
  inspection_details: z.array(z.object({
    parameter: z.string(),
    value: z.string().optional(),
    status: z.string().optional(),
  })).optional(),
})

type OperationFormData = z.infer<typeof operationSchema>

// ============================================================
// Component
// ============================================================
export default function OperationFormPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const prefillLotId = searchParams.get('lot_id')
  const prefillType = searchParams.get('type')
  const [lots, setLots] = useState<any[]>([])
  const [feedTypes, setFeedTypes] = useState<any[]>([])
  const [sapOrders, setSapOrders] = useState<any[]>([])
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<{ ok: boolean; message: string } | null>(null)
  const toast = useToast()

  const { register, handleSubmit, watch, formState: { errors } } = useForm<OperationFormData>({
    resolver: zodResolver(operationSchema),
    defaultValues: {
      event_date: new Date().toISOString().split('T')[0],
      lot_id: prefillLotId ? Number(prefillLotId) : undefined,
      event_type: prefillType || '',
      bird_movements: [], egg_movements: [], feed_movements: [], hatchery_params: [], inspection_details: [],
    },
  })

  const eventType = watch('event_type')
  const def = eventType ? EVENT_DEFS[eventType] : null

  useEffect(() => {
    api.get('/lots?limit=100').then(r => setLots(r.data)).catch(() => toast.error(t('operations.errorLoadingLots')))
    api.get('/masters/feed-types?limit=100').then(r => setFeedTypes(r.data || [])).catch(() => {})
    api.get('/sap/references?ref_type=transfer_order&limit=50').then(r => setSapOrders(r.data?.references || [])).catch(() => {})
  }, [])

  const onSubmit = async (data: OperationFormData) => {
    setSubmitting(true)
    setResult(null)
    try {
      const payload: any = { ...data }
      if (!def?.birdMovements) payload.bird_movements = []
      if (!def?.eggMovements) payload.egg_movements = []
      if (!def?.feedMovements) payload.feed_movements = []
      if (!def?.hatcheryParams) payload.hatchery_params = []
      if (!def?.inspectionDetails) payload.inspection_details = []
      await api.post('/operations', payload)
      setResult({ ok: true, message: '✅ ' + t('operations.saveSuccess') })
      setTimeout(() => navigate('/operations'), 1500)
    } catch (err: any) {
      setResult({ ok: false, message: err.response?.data?.detail || t('operations.saveError') })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="p-6 max-w-lg mx-auto">
      <h1 className="text-xl font-bold text-slate-800 mb-1">{t('nav.operations')}</h1>
      <p className="text-sm text-slate-500 mb-6">{t('operations.subtitle')}</p>

      {result && (
        <div className={`px-4 py-3 rounded-lg text-sm font-medium mb-4 ${result.ok ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
          {result.message}
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* Lot selector */}
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-1">{t('operations.lot')}</label>
          <select {...register('lot_id', { valueAsNumber: true })} className="w-full h-11 px-3 border border-slate-300 rounded-lg text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none">
            <option value="">{t('operations.selectLot')}</option>
            {lots.map((l: any) => <option key={l.id} value={l.id}>{l.lot_code} ({l.status === 'active' ? '✅' : '🔒'})</option>)}
          </select>
          {errors.lot_id && <p className="text-red-500 text-xs mt-1">{t(errors.lot_id.message)}</p>}
        </div>

        {/* Event type selector */}
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-1">{t('operations.recordType')}</label>
          <select {...register('event_type')} className="w-full h-11 px-3 border border-slate-300 rounded-lg text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none">
            <option value="">{t('operations.selectType')}</option>
            {Object.entries(EVENT_DEFS).map(([key, val]) => (
              <option key={key} value={key}>{val.icon} {t(`events.${key}`, key)}</option>
            ))}
          </select>
        </div>

        {/* Date */}
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-1">{t('operations.date')}</label>
          <input type="date" {...register('event_date')} className="w-full h-11 px-3 border border-slate-300 rounded-lg text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none" />
        </div>

        {/* Bird Movements */}
        {def?.birdMovements && (
          <div className="border border-slate-200 rounded-lg p-3">
            <p className="text-sm font-semibold text-slate-700 mb-2">🐔 {t('operations.birdMovements')}</p>
            {[0].map((_, i) => (
              <div key={i} className="grid grid-cols-2 gap-2">
                <select {...register(`bird_movements.${i}.sex`)} className="h-10 px-2 border border-slate-200 rounded text-sm">
                  <option value="">{t('operations.sex')}</option><option value="male">{t('operations.male')}</option><option value="female">{t('operations.female')}</option><option value="mixed">{t('operations.mixed')}</option>
                </select>
                <input type="number" {...register(`bird_movements.${i}.quantity`, { valueAsNumber: true })} placeholder={t('operations.quantity')} className="h-10 px-2 border border-slate-200 rounded text-sm" />
                <input type="number" step="0.1" {...register(`bird_movements.${i}.avg_weight`, { valueAsNumber: true })} placeholder={t('operations.avgWeight')} className="h-10 px-2 border border-slate-200 rounded text-sm" />
                <input type="number" {...register(`bird_movements.${i}.week_number`, { valueAsNumber: true })} placeholder={t('operations.weekNumber')} className="h-10 px-2 border border-slate-200 rounded text-sm" />
              </div>
            ))}
          </div>
        )}

        {/* Feed Movements — G-08: Enhanced with feed_type, sacks, week, SAP order */}
        {def?.feedMovements && (
          <div className="border border-slate-200 rounded-lg p-3 space-y-2">
            <p className="text-sm font-semibold text-slate-700">🌾 {t('operations.feed')}</p>
            <div className="grid grid-cols-2 gap-2">
              <select {...register('feed_movements.0.feed_type_id', { valueAsNumber: true })} className="h-10 px-2 border border-slate-200 rounded text-sm">
                <option value="">{t('operations.feedType')}</option>
                {feedTypes.map((ft: any) => <option key={ft.id} value={ft.id}>{ft.name}</option>)}
              </select>
              <input type="number" {...register('feed_movements.0.week_number', { valueAsNumber: true })} placeholder={t('operations.weekNumber')} className="h-10 px-2 border border-slate-200 rounded text-sm" />
            </div>
            <div className="grid grid-cols-3 gap-2">
              <input type="number" step="0.1" {...register('feed_movements.0.quantity_kg', { valueAsNumber: true })} placeholder={t('operations.quantityKg')} className="h-10 px-2 border border-slate-200 rounded text-sm" />
              <input type="number" {...register('feed_movements.0.sacks_count', { valueAsNumber: true })} placeholder={t('operations.sacks')} className="h-10 px-2 border border-slate-200 rounded text-sm" />
              <select {...register('feed_movements.0.sap_order_id')} className="h-10 px-2 border border-slate-200 rounded text-sm">
                <option value="">{t('operations.sapOrder')}</option>
                {sapOrders.map((s: any) => <option key={s.id} value={s.sap_code}>{s.sap_code}</option>)}
              </select>
            </div>
          </div>
        )}

        {/* Egg Movements */}
        {def?.eggMovements && (
          <div className="border border-slate-200 rounded-lg p-3">
            <p className="text-sm font-semibold text-slate-700 mb-2">🥚 {t('operations.eggs')}</p>
            {[0].map((_, i) => (
              <div key={i} className="grid grid-cols-2 gap-2">
                <select {...register(`egg_movements.${i}.egg_type`)} className="h-10 px-2 border border-slate-200 rounded text-sm">
                  <option value="">{t('operations.eggType')}</option><option value="fertile">{t('operations.fertile')}</option><option value="dirty">{t('operations.dirty')}</option><option value="broken">{t('operations.broken')}</option><option value="infertile">{t('operations.infertile')}</option><option value="discarded">{t('operations.discarded')}</option>
                </select>
                <input type="number" {...register(`egg_movements.${i}.quantity`, { valueAsNumber: true })} placeholder={t('operations.quantity')} className="h-10 px-2 border border-slate-200 rounded text-sm" />
              </div>
            ))}
          </div>
        )}

        {/* Hatchery Params */}
        {def?.hatcheryParams && (
          <div className="border border-slate-200 rounded-lg p-3">
            <p className="text-sm font-semibold text-slate-700 mb-2">🔥 {t('operations.incubationParams')}</p>
            <div className="grid grid-cols-2 gap-2">
              <input type="number" step="0.1" {...register('hatchery_params.0.temperature', { valueAsNumber: true })} placeholder={t('operations.temp')} className="h-10 px-2 border border-slate-200 rounded text-sm" />
              <input type="number" step="0.1" {...register('hatchery_params.0.humidity', { valueAsNumber: true })} placeholder={t('operations.humidity')} className="h-10 px-2 border border-slate-200 rounded text-sm" />
              <input type="number" {...register('hatchery_params.0.quantity_loaded', { valueAsNumber: true })} placeholder={t('operations.quantityLoaded')} className="h-10 px-2 border border-slate-200 rounded text-sm" />
            </div>
          </div>
        )}

        {/* Inspection Details */}
        {def?.inspectionDetails && (
          <div className="border border-slate-200 rounded-lg p-3">
            <p className="text-sm font-semibold text-slate-700 mb-2">🔍 {t('operations.inspection')}</p>
            {[t('operations.temperature'), t('operations.humidity'), t('operations.camaCondition'), t('operations.equipmentStatus')].map((param, i) => (
              <input key={i} {...register(`inspection_details.${i}.parameter`)} defaultValue={param} type="hidden" />
            ))}
            <div className="space-y-2">
              {[t('operations.temperature'), t('operations.humidity'), t('operations.camaCondition'), t('operations.equipmentStatus')].map((param, i) => (
                <div key={i} className="flex gap-2">
                  <span className="text-xs text-slate-500 w-32 pt-2">{param}</span>
                  <select {...register(`inspection_details.${i}.status`)} className="h-10 flex-1 px-2 border border-slate-200 rounded text-sm">
                    <option value="">--</option><option value="good">✅ {t('operations.good')}</option><option value="regular">⚠️ {t('operations.regular')}</option><option value="bad">❌ {t('operations.bad')}</option>
                  </select>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Observations */}
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-1">{t('operations.observations')}</label>
          <textarea {...register('observations')} rows={2} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none" />
        </div>

        <button type="submit" disabled={submitting || !eventType} className="w-full h-12 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition disabled:opacity-50">
          {submitting ? t('common.loading') : t('common.save')}
        </button>
      </form>
    </div>
  )
}
