import { useState, useEffect, useMemo } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useTranslation } from 'react-i18next'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { ChevronLeft, Bird, Wheat, Egg, Flame, Search, CheckCircle, Lock } from 'lucide-react'
import api from '../../services/api'
import { useToast } from '../../components/Toast'
import { EVENT_ICONS } from '../../components/Icon'
import {
  PROCESS_STAGES, EVENT_ICON_MAP, categoriesForStage,
  type StageKey,
} from '../../data/processCatalog'
import FormSection from '../../components/ui/FormSection'

// Map a process stage to the lot bird_type(s) it draws lots from
const STAGE_BIRD_TYPES: Record<StageKey, string[]> = {
  grandparent_rearing: ['grandparent'],
  grandparent_production: ['grandparent'],
  breeder_rearing: ['breeder'],
  breeder_production: ['breeder'],
  hatchery: ['hatchery'],
  broiler: ['broiler'],
}

// ============================================================
// All 24 event types with their required movement sub-forms
// ============================================================
const EVENT_DEFS: Record<string, {
  birdMovements?: boolean
  eggMovements?: boolean
  feedMovements?: boolean
  hatcheryParams?: boolean
  inspectionDetails?: boolean
}> = {
  bird_reception:          { birdMovements: true },
  bird_distribution:       { birdMovements: true },
  bird_transfer:           { birdMovements: true },
  bird_exit:               { birdMovements: true },
  feed_registration:       { feedMovements: true },
  weight_recording:        { birdMovements: true },
  mortality_recording:     { birdMovements: true },
  cull_recording:          { birdMovements: true },
  vaccination:             { birdMovements: true },
  medication:              { birdMovements: true },
  farm_inspection:         { inspectionDetails: true },
  transport_inspection:    { inspectionDetails: true },
  hatchery_inspection:     { inspectionDetails: true },
  egg_collection:          { eggMovements: true },
  egg_classification:      { eggMovements: true },
  egg_dispatch:            { eggMovements: true },
  egg_reception_hatchery:  { eggMovements: true },
  incubation_load:         { hatcheryParams: true },
  ovoscopy:                { eggMovements: true },
  transfer_to_hatcher:     { hatcheryParams: true },
  birth_registration:      { birdMovements: true },
  chick_dispatch:          { birdMovements: true },
  lot_closure:             {},
  grandparent_import:      { birdMovements: true },
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

  const { register, handleSubmit, watch, setValue, formState: { errors } } = useForm<OperationFormData>({
    resolver: zodResolver(operationSchema),
    defaultValues: {
      event_date: new Date().toISOString().split('T')[0],
      lot_id: prefillLotId ? Number(prefillLotId) : undefined,
      event_type: prefillType || '',
      bird_movements: [], egg_movements: [], feed_movements: [], hatchery_params: [], inspection_details: [],
    },
  })

  const eventType = watch('event_type')
  const lotId = watch('lot_id')
  const def = eventType ? EVENT_DEFS[eventType] : null

  // ----- Wizard state -----
  // Step 1 = choose process/stage · Step 2 = choose lot + operation · Step 3 = fill data
  const [stage, setStage] = useState<StageKey | null>(null)
  const [step, setStep] = useState<1 | 2 | 3>(prefillType ? 3 : 1)

  // Lots filtered by the chosen stage's bird type(s)
  const stageLots = useMemo(() => {
    if (!stage) return lots
    const allowed = STAGE_BIRD_TYPES[stage]
    return lots.filter((l: any) => allowed.includes(l.bird_type))
  }, [lots, stage])

  const goToStep2 = (s: StageKey) => {
    setStage(s)
    // Reset selections that may not apply to the new stage
    setValue('event_type', '')
    setStep(2)
  }

  const chooseOperation = (evt: string) => {
    setValue('event_type', evt)
    setStep(3)
  }


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
      setResult({ ok: true, message: t('operations.saveSuccess') })
      setTimeout(() => navigate('/operations'), 1500)
    } catch (err: any) {
      setResult({ ok: false, message: err.response?.data?.detail || t('operations.saveError') })
    } finally {
      setSubmitting(false)
    }
  }

  const selectedStageMeta = PROCESS_STAGES.find(s => s.key === stage)
  const SelectedEventIcon = eventType ? (EVENT_ICON_MAP[eventType] ?? EVENT_ICONS[eventType]) : null
  const SelectedStageIcon = selectedStageMeta?.Icon

  return (
    <div className="p-4 sm:p-6 max-w-2xl mx-auto">
      {/* Stepper */}
      <nav className="flex items-center gap-1.5 text-xs font-semibold mb-5 select-none">
        <button type="button" onClick={() => setStep(1)} className={step >= 1 ? 'text-[#2563EB]' : 'text-slate-400'}>
          {t('process.step1', '1 · Proceso')}
        </button>
        <span className="text-slate-300">/</span>
        <button type="button" disabled={!stage} onClick={() => stage && setStep(2)} className={`${step >= 2 ? 'text-[#2563EB]' : 'text-slate-400'} disabled:cursor-not-allowed`}>
          {t('process.step2', '2 · Lote y Operación')}
        </button>
        <span className="text-slate-300">/</span>
        <button type="button" disabled={!eventType} onClick={() => eventType && setStep(3)} className={`${step >= 3 ? 'text-[#2563EB]' : 'text-slate-400'} disabled:cursor-not-allowed`}>
          {t('process.step3', '3 · Datos')}
        </button>
      </nav>

      {/* ===================== STEP 1 — PROCESS ===================== */}
      {step === 1 && (
        <div>
          <h1 className="text-xl font-bold text-slate-800">{t('process.title', 'Registrar Operación')}</h1>
          <p className="text-sm text-slate-500 mt-1 mb-5">{t('process.subtitle', '¿Qué proceso vas a registrar?')}</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {PROCESS_STAGES.map(s => {
              const Icon = s.Icon
              return (
                <button
                  key={s.key}
                  type="button"
                  onClick={() => goToStep2(s.key)}
                  className={`flex items-center gap-4 p-4 min-h-[5rem] rounded-xl border border-slate-200 bg-white text-left shadow-sm transition-colors ${s.accent}`}
                >
                  <div className={`shrink-0 w-12 h-12 rounded-lg flex items-center justify-center ${s.iconBg}`}>
                    <Icon size={26} className={s.iconColor} />
                  </div>
                  <div className="min-w-0">
                    <p className="font-semibold text-slate-800 leading-tight">{t(s.labelKey, s.fallback)}</p>
                    <p className="text-xs text-slate-500 leading-snug mt-1">{t(s.descKey, s.descFallback)}</p>
                  </div>
                </button>
              )
            })}
          </div>
        </div>
      )}

      {/* ============== STEP 2 — LOT + OPERATION SELECTION ============== */}
      {step === 2 && stage && selectedStageMeta && (
        <div>
          <button type="button" onClick={() => setStep(1)} className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-[#2563EB] mb-3">
            <ChevronLeft size={16} /> {t('common.back', 'Atrás')}
          </button>
          <div className="flex items-center gap-3 mb-5">
            <div className={`shrink-0 w-10 h-10 rounded-lg flex items-center justify-center ${selectedStageMeta.iconBg}`}>
              {SelectedStageIcon && <SelectedStageIcon size={22} className={selectedStageMeta.iconColor} />}
            </div>
            <h1 className="text-lg font-bold text-slate-800">{t(selectedStageMeta.labelKey, selectedStageMeta.fallback)}</h1>
          </div>

          {/* Lot selector */}
          <label className="block text-sm font-semibold text-slate-700 mb-1">{t('operations.lot')}</label>
          <select {...register('lot_id', { valueAsNumber: true })} className="w-full h-11 px-3 border border-slate-300 rounded-lg text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none">
            <option value="">{t('operations.selectLot')}</option>
            {stageLots.map((l: any) => <option key={l.id} value={l.id}>{l.lot_code} ({l.status === 'active'
              ? <><CheckCircle size={12} className="inline-block text-green-600" aria-hidden="true" /> </>
              : <><Lock size={12} className="inline-block text-amber-600" aria-hidden="true" /> </>})</option>)}
          </select>
          {stageLots.length === 0 && (
            <p className="text-xs text-amber-600 mt-2">{t('process.noLots', 'No hay lotes activos para este proceso.')}</p>
          )}

          {/* Operation cards grouped by category */}
          <p className="text-sm font-semibold text-slate-700 mt-6 mb-1">{t('process.chooseOperation', 'Elige la operación')}</p>
          {!lotId && <p className="text-xs text-slate-400 mb-3">{t('process.selectLotFirst', 'Selecciona un lote para habilitar las operaciones.')}</p>}
          <div className={`space-y-5 ${!lotId ? 'opacity-50 pointer-events-none' : ''} mt-3`}>
            {categoriesForStage(stage).map(({ category, events }) => {
              const CatIcon = category.Icon
              return (
                <div key={category.key}>
                  <div className="flex items-center gap-2 mb-2">
                    <CatIcon size={16} className={category.color} />
                    <span className="text-xs font-bold uppercase tracking-wide text-slate-500">{t(category.labelKey, category.fallback)}</span>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                    {events.map(evt => {
                      const EvIcon = EVENT_ICON_MAP[evt] ?? EVENT_ICONS[evt]
                      return (
                        <button
                          key={evt}
                          type="button"
                          disabled={!lotId}
                          onClick={() => chooseOperation(evt)}
                          className="flex flex-col items-center gap-1.5 p-3 min-h-[4.5rem] rounded-lg border border-slate-200 bg-white hover:border-[#2563EB] hover:bg-blue-50 transition-colors text-center group"
                        >
                          {EvIcon && <EvIcon size={22} className="text-[#2563EB] group-hover:scale-110 transition-transform" />}
                          <span className="text-xs text-slate-600 leading-tight">{t(`eventsShort.${evt}`, evt)}</span>
                        </button>
                      )
                    })}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* ===================== STEP 3 — DATA FORM ===================== */}
      {step === 3 && (
      <div>
        <button type="button" onClick={() => setStep(stage ? 2 : 1)} className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-[#2563EB] mb-3">
          <ChevronLeft size={16} /> {t('common.back', 'Atrás')}
        </button>
        {eventType && (
          <div className="flex items-center gap-3 mb-4 p-3 rounded-lg bg-blue-50 border border-blue-100">
            {SelectedEventIcon && <SelectedEventIcon size={22} className="text-[#2563EB]" />}
            <div>
              <p className="text-sm font-bold text-slate-800">{t(`events.${eventType}`, eventType)}</p>
              {selectedStageMeta && <p className="text-xs text-slate-500">{t(selectedStageMeta.labelKey, selectedStageMeta.fallback)}</p>}
            </div>
          </div>
        )}

        {result && (
          <div className={`px-4 py-3 rounded-lg text-sm font-medium mb-4 ${result.ok ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
            {result.message}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Lot selector — self-contained so the form works from the process flow */}
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1">{t('operations.lot')}</label>
            <select {...register('lot_id', { valueAsNumber: true })} className="w-full h-11 px-3 border border-slate-300 rounded-lg text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none">
              <option value="">{t('operations.selectLot')}</option>
              {lots.map((l: any) => <option key={l.id} value={l.id}>{l.lot_code}{l.status && l.status !== 'active' ? ` · ${String(l.status)}` : ''}</option>)}
            </select>
            {errors.lot_id && <p className="text-red-500 text-xs mt-1">{t(errors.lot_id.message ?? '')}</p>}
          </div>

          {/* Date */}

        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-1">{t('operations.date')}</label>
          <input type="date" {...register('event_date')} className="w-full h-11 px-3 border border-slate-300 rounded-lg text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none" />
        </div>

        {/* Bird Movements */}
        {def?.birdMovements && (
          <FormSection
            title={t('operations.birdMovements', 'Movimiento de Aves')}
            description={t('operations.birdMovementsDesc', 'Registra cantidades, peso y semana')}
            icon={Bird}
            iconColor="text-blue-600"
            collapsible
          >
            {[0].map((_, i) => (
              <div key={i} className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-500 mb-1">{t('operations.sex', 'Sexo')}</label>
                  <select {...register(`bird_movements.${i}.sex`)} className="w-full h-11 px-3 border border-slate-300 rounded-lg text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none">
                    <option value="">{t('operations.selectSex', 'Seleccionar...')}</option>
                    <option value="male">{t('operations.male', 'Macho')}</option>
                    <option value="female">{t('operations.female', 'Hembra')}</option>
                    <option value="mixed">{t('operations.mixed', 'Mixto')}</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-500 mb-1">{t('operations.quantity', 'Cantidad')}</label>
                  <input type="number" {...register(`bird_movements.${i}.quantity`, { valueAsNumber: true })}
                    placeholder="0"
                    className="w-full h-11 px-3 border border-slate-300 rounded-lg text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-500 mb-1">{t('operations.avgWeight', 'Peso Promedio (kg)')}</label>
                  <input type="number" step="0.1" {...register(`bird_movements.${i}.avg_weight`, { valueAsNumber: true })}
                    placeholder="0.0"
                    className="w-full h-11 px-3 border border-slate-300 rounded-lg text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-500 mb-1">{t('operations.weekNumber', 'Semana')}</label>
                  <input type="number" {...register(`bird_movements.${i}.week_number`, { valueAsNumber: true })}
                    placeholder="1"
                    className="w-full h-11 px-3 border border-slate-300 rounded-lg text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none" />
                </div>
              </div>
            ))}
          </FormSection>
        )}

        {/* Feed Registration */}
        {def?.feedMovements && (
          <FormSection
            title={t('operations.feed', 'Registro de Alimento')}
            description={t('operations.feedDesc', 'Tipo de alimento, cantidad y orden SAP')}
            icon={Wheat}
            iconColor="text-amber-600"
            collapsible
          >
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-500 mb-1">{t('operations.feedType', 'Tipo de Alimento')}</label>
                <select {...register('feed_movements.0.feed_type_id', { valueAsNumber: true })}
                  className="w-full h-11 px-3 border border-slate-300 rounded-lg text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none">
                  <option value="">{t('operations.selectType', 'Seleccionar...')}</option>
                  {feedTypes.map((ft: any) => <option key={ft.id} value={ft.id}>{ft.name}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-500 mb-1">{t('operations.weekNumber', 'Semana')}</label>
                <input type="number" {...register('feed_movements.0.week_number', { valueAsNumber: true })}
                  placeholder="1"
                  className="w-full h-11 px-3 border border-slate-300 rounded-lg text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none" />
              </div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-500 mb-1">{t('operations.quantityKg', 'Cantidad (kg)')}</label>
                <input type="number" step="0.1" {...register('feed_movements.0.quantity_kg', { valueAsNumber: true })}
                  placeholder="0.0"
                  className="w-full h-11 px-3 border border-slate-300 rounded-lg text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none" />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-500 mb-1">{t('operations.sacks', 'Sacos')}</label>
                <input type="number" {...register('feed_movements.0.sacks_count', { valueAsNumber: true })}
                  placeholder="0"
                  className="w-full h-11 px-3 border border-slate-300 rounded-lg text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none" />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-500 mb-1">{t('operations.sapOrder', 'Orden SAP')}</label>
                <select {...register('feed_movements.0.sap_order_id')}
                  className="w-full h-11 px-3 border border-slate-300 rounded-lg text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none">
                  <option value="">{t('operations.noOrder', 'Sin orden')}</option>
                  {sapOrders.map((s: any) => <option key={s.id} value={s.sap_code}>{s.sap_code}</option>)}
                </select>
              </div>
            </div>
          </FormSection>
        )}

        {/* Egg Movements */}
        {def?.eggMovements && (
          <FormSection
            title={t('operations.eggs', 'Registro de Huevos')}
            description={t('operations.eggsDesc', 'Tipo y cantidad de huevos')}
            icon={Egg}
            iconColor="text-indigo-600"
            collapsible
          >
            {[0].map((_, i) => (
              <div key={i} className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-500 mb-1">{t('operations.eggType', 'Tipo de Huevo')}</label>
                  <select {...register(`egg_movements.${i}.egg_type`)}
                    className="w-full h-11 px-3 border border-slate-300 rounded-lg text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none">
                    <option value="">{t('operations.selectType', 'Seleccionar...')}</option>
                    <option value="fertile">{t('operations.fertile', 'Fértil')}</option>
                    <option value="dirty">{t('operations.dirty', 'Sucio')}</option>
                    <option value="broken">{t('operations.broken', 'Roto')}</option>
                    <option value="infertile">{t('operations.infertile', 'Infértil')}</option>
                    <option value="discarded">{t('operations.discarded', 'Descartado')}</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-500 mb-1">{t('operations.quantity', 'Cantidad')}</label>
                  <input type="number" {...register(`egg_movements.${i}.quantity`, { valueAsNumber: true })}
                    placeholder="0"
                    className="w-full h-11 px-3 border border-slate-300 rounded-lg text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none" />
                </div>
              </div>
            ))}
          </FormSection>
        )}

        {/* Hatchery Params */}
        {def?.hatcheryParams && (
          <FormSection
            title={t('operations.incubationParams', 'Parámetros de Incubación')}
            description={t('operations.incubationDesc', 'Temperatura, humedad y carga')}
            icon={Flame}
            iconColor="text-orange-600"
            collapsible
          >
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-500 mb-1">{t('operations.temp', 'Temperatura (°C)')}</label>
                <input type="number" step="0.1" {...register('hatchery_params.0.temperature', { valueAsNumber: true })}
                  placeholder="37.5"
                  className="w-full h-11 px-3 border border-slate-300 rounded-lg text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none" />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-500 mb-1">{t('operations.humidity', 'Humedad (%)')}</label>
                <input type="number" step="0.1" {...register('hatchery_params.0.humidity', { valueAsNumber: true })}
                  placeholder="55"
                  className="w-full h-11 px-3 border border-slate-300 rounded-lg text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none" />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-500 mb-1">{t('operations.quantityLoaded', 'Cantidad Cargada')}</label>
                <input type="number" {...register('hatchery_params.0.quantity_loaded', { valueAsNumber: true })}
                  placeholder="0"
                  className="w-full h-11 px-3 border border-slate-300 rounded-lg text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none" />
              </div>
            </div>
          </FormSection>
        )}

        {/* Inspection Details */}
        {def?.inspectionDetails && (
          <FormSection
            title={t('operations.inspection', 'Detalles de Inspección')}
            description={t('operations.inspectionDesc', 'Estado de parámetros de la granja')}
            icon={Search}
            iconColor="text-cyan-600"
            collapsible
          >
            {[t('operations.temperature', 'Temperatura'), t('operations.humidity', 'Humedad'), t('operations.camaCondition', 'Condición de Cama'), t('operations.equipmentStatus', 'Estado de Equipos')].map((param, i) => (
              <input key={i} {...register(`inspection_details.${i}.parameter`)} defaultValue={param} type="hidden" />
            ))}
            <div className="space-y-3">
              {[t('operations.temperature', 'Temperatura'), t('operations.humidity', 'Humedad'), t('operations.camaCondition', 'Condición de Cama'), t('operations.equipmentStatus', 'Estado de Equipos')].map((param, i) => (
                <div key={i} className="flex items-center gap-3">
                  <span className="text-sm text-slate-600 w-32 shrink-0">{param}</span>
                  <select {...register(`inspection_details.${i}.status`)}
                    className="flex-1 h-11 px-3 border border-slate-300 rounded-lg text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none">
                    <option value="">{t('operations.selectState', 'Seleccionar...')}</option>
                    <option value="good">✅ {t('operations.good', 'Bueno')}</option>
                    <option value="regular">⚠️ {t('operations.regular', 'Regular')}</option>
                    <option value="bad">❌ {t('operations.bad', 'Malo')}</option>
                  </select>
                </div>
              ))}
            </div>
          </FormSection>
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
      )}
    </div>
  )
}
