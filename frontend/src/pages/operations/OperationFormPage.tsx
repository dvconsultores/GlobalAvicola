import { useState, useEffect, useMemo } from 'react'
import { useForm, useFieldArray } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useTranslation } from 'react-i18next'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { ChevronLeft, Plus, Trash2 } from 'lucide-react'
import api from '../../services/api'
import { useToast } from '../../components/Toast'
import { EVENT_ICONS } from '../../components/Icon'
import {
 PROCESS_STAGES, EVENT_ICON_MAP, categoriesForStage,
 type StageKey,
} from '../../data/processCatalog'

// ============================================================
// Technical ranges — Ross/Cobb guidelines
// ============================================================
// Thermal zones — Ross/Cobb dynamic curves by bird type + week
import { getThermalZone, DEFAULT_THERMAL_ZONE } from '../../data/thermalCurves'
// Incubator (setter) and Hatcher fixed ranges
const INCUBATOR_TEMP_RANGE: [number, number] = [37.5, 38.0]
const HATCHER_TEMP_RANGE: [number, number] = [37.0, 37.5]
const INCUBATOR_HUM_RANGE: [number, number] = [55, 62]
const HATCHER_HUM_RANGE: [number, number] = [65, 75]

function getTempRange(birdType: string, ageWeeks: number): [number, number] {
 const zone = getThermalZone(birdType, 'rearing', ageWeeks)
 if (zone) return [zone.tempMin, zone.tempMax]
 return [DEFAULT_THERMAL_ZONE.tempMin, DEFAULT_THERMAL_ZONE.tempMax]
}

function getHumidityRange(ageWeeks: number): [number, number] {
 const zone = getThermalZone('broiler', 'rearing', ageWeeks)
 if (zone) return [zone.humidMin, zone.humidMax]
 return [DEFAULT_THERMAL_ZONE.humidMin, DEFAULT_THERMAL_ZONE.humidMax]
}

type RangeStatus = 'ok' | 'warn' | 'error' | 'none'
function getRangeStatus(value: number | undefined, min: number, max: number): RangeStatus {
 if (value == null || isNaN(value)) return 'none'
 if (value >= min && value <= max) return 'ok'
 const margin = (max - min) * 0.5
 if (value >= min - margin && value <= max + margin) return 'warn'
 return 'error'
}

function RangeIndicator({ value, min, max, unit, weekLabel }: {
 value: number | undefined; min: number; max: number; unit: string; weekLabel?: string
}) {
 const s = getRangeStatus(value, min, max)
 if (s === 'none') return null
 const cfg: Record<RangeStatus, { bg: string; text: string; icon: string }> = {
 ok: { bg: 'bg-emerald-50 dark:bg-emerald-950 border-emerald-200 dark:border-emerald-800', text: 'text-emerald-700 dark:text-emerald-300', icon: '✅' },
 warn: { bg: 'bg-amber-50 dark:bg-amber-950 border-amber-200 dark:border-amber-800', text: 'text-amber-700 dark:text-amber-300', icon: '⚠️' },
 error: { bg: 'bg-red-50 dark:bg-red-950 border-red-200 dark:border-red-800', text: 'text-red-700 dark:text-red-300', icon: '❌' },
 none: { bg: '', text: '', icon: '' },
 }
 const { bg, text, icon } = cfg[s]
 return (
 <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs border ${bg} ${text} mt-1`}>
 {icon} {min}–{max}{unit}{weekLabel ? ` (${weekLabel})` : ''}
 </span>
 )
}

// ============================================================
// Zod Schema — covers all 24 operation types
// ============================================================
const operationSchema = z.object({
 lot_id: z.number({ message: 'operations.selectLot' }).min(1),
 event_type: z.string().min(1),
 event_date: z.string().min(1),
 observations: z.string().optional(),
 // Operation-specific catalog FKs
 supplier_id: z.number().optional(),
 cause_id: z.number().optional(),
 cull_cause_id: z.number().optional(),
 vaccine_id: z.number().optional(),
 vaccination_route: z.string().optional(),
 vaccine_lot_number: z.string().optional(),
 medication_id: z.number().optional(),
 dosage_per_bird: z.number().optional(),
 treatment_days: z.number().optional(),
 destination_farm_id: z.number().optional(),
 destination_plant_id: z.number().optional(),
 transport_id: z.number().optional(),
 sample_size: z.number().optional(),
 extra_data: z.record(z.string(), z.any()).optional(),
 // Sub-models
 bird_movements: z.array(z.object({
 sex: z.string().optional(),
 quantity: z.number().min(0).optional(),
 avg_weight: z.number().optional(),
 week_number: z.number().optional(),
 breed_id: z.number().optional(),
 source_house_id: z.number().optional(),
 target_house_id: z.number().optional(),
 })).optional(),
 egg_movements: z.array(z.object({
 egg_type: z.string(),
 quantity: z.number().min(0).optional(),
 avg_weight: z.number().optional(),
 })).optional(),
 feed_movements: z.array(z.object({
 feed_type_id: z.number().optional(),
 quantity_kg: z.number().min(0).optional(),
 sacks_count: z.number().optional(),
 week_number: z.number().optional(),
 sap_order_id: z.string().optional(),
 })).optional(),
 hatchery_params: z.array(z.object({
 machine_type: z.enum(['incubator', 'hatcher']).optional(), // UI-only, stripped on submit
 incubator_id: z.number().optional(),
 hatcher_id: z.number().optional(),
 temperature: z.number().optional(),
 humidity: z.number().optional(),
 co2: z.number().optional(),
 turning: z.boolean().optional(),
 quantity_loaded: z.number().optional(),
 quantity_transferred: z.number().optional(),
 })).optional(),
 inspection_details: z.array(z.object({
 house_id: z.number().optional(),
 parameter: z.string(),
 value: z.string().optional(),
 status: z.string().optional(),
 })).optional(),
 // UI-only: per-house inspection rows → converted to inspection_details on submit
 house_inspections: z.array(z.object({
 house_id: z.number().optional(),
 temperature: z.number().optional(),
 humidity: z.number().optional(),
 litter_condition: z.string().optional(),
 litter_notes: z.string().optional(),
 equipment_notes: z.string().optional(),
 })).optional(),
 egg_storage_records: z.array(z.object({
 eggs_received: z.number().optional(),
 storage_temp_c: z.number().optional(),
 storage_humidity_pct: z.number().optional(),
 transport_temp_c: z.number().optional(),
 transport_duration_min: z.number().optional(),
 notes: z.string().optional(),
 })).optional(),
})

type OperationFormData = z.infer<typeof operationSchema>

// Shared CSS helpers (module-level to avoid recreating on each render)
const ic = 'w-full h-11 px-3 border border-slate-300 rounded-lg text-base text-slate-900 dark:text-slate-100 bg-white dark:bg-slate-800 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none'
const lc = 'block text-sm font-semibold text-slate-700 dark:text-slate-200 mb-1.5'

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
 const [lotsLoadError, setLotsLoadError] = useState(false)
 const [sapOrders, setSapOrders] = useState<any[]>([])
 const [submitting, setSubmitting] = useState(false)
 const [result, setResult] = useState<{ ok: boolean; message: string } | null>(null)

 // Catalogs
 const [vaccines, setVaccines] = useState<any[]>([])
 const [medications, setMedications] = useState<any[]>([])
 const [mortalityCauses, setMortalityCauses] = useState<any[]>([])
 const [cullCauses, setCullCauses] = useState<any[]>([])
 const [transports, setTransports] = useState<any[]>([])
 const [farms, setFarms] = useState<any[]>([])
 const [processingPlants, setProcessingPlants] = useState<any[]>([])
 const [suppliers, setSuppliers] = useState<any[]>([])
 const [breeds, setBreeds] = useState<any[]>([])
 const [houses, setHouses] = useState<any[]>([])
 const [feedTypes, setFeedTypes] = useState<any[]>([])
 const [incubators, setIncubators] = useState<any[]>([])
 const [hatchers, setHatchers] = useState<any[]>([])

 const toast = useToast()

 const { register, handleSubmit, watch, setValue, control, formState: { errors } } = useForm<OperationFormData>({
 resolver: zodResolver(operationSchema),
 defaultValues: {
 event_date: new Date().toISOString().split('T')[0],
 lot_id: prefillLotId ? Number(prefillLotId) : undefined,
 event_type: prefillType || '',
 bird_movements: [{ sex: 'male', quantity: 0 }, { sex: 'female', quantity: 0 }],
 egg_movements: [],
 feed_movements: [{ quantity_kg: 0 }],
 hatchery_params: [{}],
 inspection_details: [],
 house_inspections: [],
 egg_storage_records: [{}],
 },
 })

 const eventType = watch('event_type')
 const lotId = watch('lot_id')

 // Houses filtered to the farm of the selected lot (for farm_inspection per-house rows)
 const farmHouses = useMemo(() => {
 const lot = lots.find((l: any) => l.id === lotId)
 if (!lot?.farm_id) return houses
 return houses.filter((h: any) => h.farm_id === lot.farm_id)
 }, [lots, lotId, houses])

 // Age of selected lot in weeks (for technical range indicators)
 const { lotAgeWeeks, lotBirdType } = useMemo(() => {
 const lot = lots.find((l: any) => l.id === lotId)
 if (!lot?.start_date) return { lotAgeWeeks: 0, lotBirdType: 'default' }
 const startMs = new Date(lot.start_date).getTime()
 const weeks = Math.max(0, Math.floor((Date.now() - startMs) / (7 * 24 * 60 * 60 * 1000)))
 return { lotAgeWeeks: weeks, lotBirdType: lot.bird_type ?? 'default' }
 }, [lots, lotId])

 const { fields: birdFields, append: appendBird, remove: removeBird } =
 useFieldArray({ control, name: 'bird_movements' })
 const { fields: incubatorFields, append: appendIncubator, remove: removeIncubator } =
 useFieldArray({ control, name: 'hatchery_params' })
 const { fields: houseInspFields, append: appendHouseInsp, remove: removeHouseInsp } =
 useFieldArray({ control, name: 'house_inspections' })

 const [stage, setStage] = useState<StageKey | null>(null)
 const [step, setStep] = useState<1 | 2 | 3>(prefillType ? 3 : 1)

 const goToStep2 = (s: StageKey) => { setStage(s); setValue('event_type', ''); setStep(2) }
 const chooseOperation = (evt: string) => { setValue('event_type', evt); setStep(3) }

 // Auto-init: add one empty house row when farm_inspection is selected
 useEffect(() => {
 if (eventType === 'farm_inspection' && houseInspFields.length === 0) {
 appendHouseInsp({ litter_condition: '' })
 }
 }, [eventType]) // eslint-disable-line react-hooks/exhaustive-deps

 // Auto-init: add one empty machine row when hatchery_inspection is selected
 useEffect(() => {
 if (eventType === 'hatchery_inspection' && incubatorFields.length === 0) {
 appendIncubator({ machine_type: 'incubator' } as any)
 }
 }, [eventType]) // eslint-disable-line react-hooks/exhaustive-deps

 useEffect(() => {
 api.get('/lots?limit=100')
 .then(r => {
 setLots(Array.isArray(r.data) ? r.data : [])
 setLotsLoadError(false)
 })
 .catch(() => {
 setLots([])
 setLotsLoadError(true)
 })
 api.get('/sap/references?ref_type=transfer_order&limit=50').then(r => setSapOrders(r.data?.references || [])).catch(() => {})
 Promise.allSettled([
 api.get('/masters/vaccines?limit=100'),
 api.get('/masters/medications?limit=100'),
 api.get('/masters/mortality-causes?limit=100'),
 api.get('/masters/cull-causes?limit=100'),
 api.get('/masters/transports?limit=100'),
 api.get('/masters/farms?limit=100'),
 api.get('/masters/processing-plants?limit=100'),
 api.get('/masters/suppliers?limit=100'),
 api.get('/masters/breeds?limit=100'),
 api.get('/masters/houses?limit=100'),
 api.get('/masters/feed-types?limit=100'),
 api.get('/masters/incubators?limit=100'),
 api.get('/masters/hatchers?limit=100'),
 ]).then(results => {
 const get = (r: PromiseSettledResult<any>) => r.status === 'fulfilled' ? (r.value.data || []) : []
 setVaccines(get(results[0])); setMedications(get(results[1]))
 setMortalityCauses(get(results[2])); setCullCauses(get(results[3]))
 setTransports(get(results[4])); setFarms(get(results[5]))
 setProcessingPlants(get(results[6])); setSuppliers(get(results[7]))
 setBreeds(get(results[8])); setHouses(get(results[9]))
 setFeedTypes(get(results[10])); setIncubators(get(results[11]))
 setHatchers(get(results[12]))
 })
 }, []) // eslint-disable-line react-hooks/exhaustive-deps

 const onSubmit = async (data: OperationFormData) => {
 setSubmitting(true); setResult(null)
 try {
 // Convert per-house inspection rows into inspection_details records with house_id
 const houseDetails: any[] = []
 for (const h of data.house_inspections || []) {
 if (h.temperature != null && !isNaN(Number(h.temperature)))
 houseDetails.push({ house_id: h.house_id, parameter: 'temperature', value: String(h.temperature) })
 if (h.humidity != null && !isNaN(Number(h.humidity)))
 houseDetails.push({ house_id: h.house_id, parameter: 'humidity', value: String(h.humidity) })
 if (h.litter_condition)
 houseDetails.push({ house_id: h.house_id, parameter: 'litter_condition', status: h.litter_condition })
 if (h.litter_notes)
 houseDetails.push({ house_id: h.house_id, parameter: 'litter_notes', value: h.litter_notes })
 if (h.equipment_notes)
 houseDetails.push({ house_id: h.house_id, parameter: 'equipment_notes', value: h.equipment_notes })
 }

 const payload: any = {
 ...data,
 bird_movements: (data.bird_movements || []).filter(m => (m.quantity ?? 0) > 0),
 egg_movements: (data.egg_movements || []).filter(m => (m.quantity ?? 0) > 0),
 feed_movements: data.feed_movements || [],
 hatchery_params: (data.hatchery_params || []).map(({ machine_type: _mt, ...hp }: any) => hp), // strip UI-only machine_type
 inspection_details: [...(data.inspection_details || []), ...houseDetails],
 egg_storage_records: data.egg_storage_records || [],
 house_inspections: undefined, // strip UI-only field
 }
 await api.post('/operations', payload)
 setResult({ ok: true, message: t('operations.saveSuccess') })
 toast.success(t('operations.saveSuccess'))
 setTimeout(() => navigate('/operations'), 1500)
 } catch (err: any) {
 const message = err.response?.data?.detail || t('operations.saveError')
 setResult({ ok: false, message })
 toast.error(message)
 } finally { setSubmitting(false) }
 }

 // ── M+F rows helper ──────────────────────────────────────────────
 const renderMFRows = (showWeight = true) => (
 <div>
 <div className={`grid ${showWeight ? 'grid-cols-3' : 'grid-cols-2'} px-1 py-2 border-b border-slate-200`}>
 <span className="text-sm font-semibold text-slate-500 dark:text-slate-400">{t('operations.sex', 'Sexo')}</span>
 <span className="text-sm font-semibold text-slate-500 dark:text-slate-400">{t('operations.quantity', 'Cantidad')}</span>
 {showWeight && <span className="text-sm font-semibold text-slate-500 dark:text-slate-400">{t('operations.avgWeight', 'Peso prom. (kg)')}</span>}
 </div>
 {[
 { idx: 0, defaultSex: 'male', label: t('operations.males', 'Machos'), color: 'text-blue-700 dark:text-blue-300' },
 { idx: 1, defaultSex: 'female', label: t('operations.females', 'Hembras'), color: 'text-pink-700' },
 ].map(({ idx, defaultSex, label, color }) => (
 <div key={idx} className={`grid ${showWeight ? 'grid-cols-3' : 'grid-cols-2'} px-1 py-2.5 gap-2 items-center border-b border-slate-100 last:border-0`}>
 <div className="flex items-center gap-1.5">
 <input type="hidden" {...register(`bird_movements.${idx}.sex`)} defaultValue={defaultSex} />
 <span className={`text-sm font-semibold ${color}`}>{label}</span>
 </div>
 <input type="number" min="0" {...register(`bird_movements.${idx}.quantity`, { valueAsNumber: true })}
 className={ic} placeholder="0" />
 {showWeight && (
 <input type="number" step="0.001" {...register(`bird_movements.${idx}.avg_weight`, { valueAsNumber: true })}
 className={ic} placeholder="0.000" />
 )}
 </div>
 ))}
 </div>
 )

 // ── Select helper ─────────────────────────────────────────────────
 const sel = (field: any, items: any[], placeholder: string, renderLabel = (x: any) => x.name) => (
 <select {...field} className={ic}>
 <option value="">{placeholder}</option>
 {items.map((x: any) => <option key={x.id} value={x.id}>{renderLabel(x)}</option>)}
 </select>
 )

 // ── Operation-specific fields switch ─────────────────────────────
 const renderOperationFields = () => {
 switch (eventType) {

 case 'mortality_recording': return (
 <div className="space-y-4">
 <div className="flex flex-col gap-3 lg:grid lg:grid-cols-2">
 <div>
 <label className={lc}>{t('operations.mortalityCause', 'Causa de mortalidad')}</label>
 {sel(register('cause_id', { valueAsNumber: true }), mortalityCauses, t('operations.selectCause', 'Seleccionar causa...'))}
 </div>
 <div>
 <label className={lc}>{t('operations.weekNumber', 'Semana')}</label>
 <input type="number" min="1" {...register('bird_movements.0.week_number', { valueAsNumber: true })} className={ic} placeholder="1" />
 </div>
 </div>
 {renderMFRows(false)}
 </div>
 )

 case 'cull_recording': return (
 <div className="space-y-4">
 <div className="flex flex-col gap-3 lg:grid lg:grid-cols-2">
 <div>
 <label className={lc}>{t('operations.cullCause', 'Causa de descarte')}</label>
 {sel(register('cull_cause_id', { valueAsNumber: true }), cullCauses, t('operations.selectCause', 'Seleccionar causa...'))}
 </div>
 <div>
 <label className={lc}>{t('operations.weekNumber', 'Semana')}</label>
 <input type="number" min="1" {...register('bird_movements.0.week_number', { valueAsNumber: true })} className={ic} placeholder="1" />
 </div>
 </div>
 {renderMFRows(false)}
 </div>
 )

 case 'vaccination': return (
 <div className="space-y-4">
 <div className="flex flex-col gap-3 lg:grid lg:grid-cols-2">
 <div>
 <label className={lc}>{t('operations.vaccine', 'Vacuna')}</label>
 {sel(register('vaccine_id', { valueAsNumber: true }), vaccines, t('operations.selectVaccine', 'Seleccionar vacuna...'))}
 </div>
 <div>
 <label className={lc}>{t('operations.vaccinationRoute', 'Vía de administración')}</label>
 <select {...register('vaccination_route')} className={ic}>
 <option value="">{t('operations.selectType', 'Seleccionar...')}</option>
 <option value="spray">{t('operations.spray', 'Aspersión (spray)')}</option>
 <option value="water">{t('operations.waterRoute', 'Agua de bebida')}</option>
 <option value="injection">{t('operations.injection', 'Inyectable')}</option>
 <option value="eye">{t('operations.eye', 'Ocular')}</option>
 <option value="gel">{t('operations.gel', 'Gel')}</option>
 </select>
 </div>
 <div>
 <label className={lc}>{t('operations.vaccineLot', 'Lote de vacuna')}</label>
 <input {...register('vaccine_lot_number')} className={ic} placeholder="LOT-2024-001" />
 </div>
 <div>
 <label className={lc}>{t('operations.dosePerBird', 'Dosis por ave')}</label>
 <input type="number" step="0.01" {...register('dosage_per_bird', { valueAsNumber: true })} className={ic} placeholder="0.00" />
 </div>
 </div>
 {renderMFRows(false)}
 </div>
 )

 case 'medication': return (
 <div className="space-y-4">
 <div className="flex flex-col gap-3 lg:grid lg:grid-cols-2">
 <div>
 <label className={lc}>{t('operations.medication', 'Medicamento')}</label>
 {sel(register('medication_id', { valueAsNumber: true }), medications, t('operations.selectMedication', 'Seleccionar medicamento...'))}
 </div>
 <div>
 <label className={lc}>{t('operations.dosePerBird', 'Dosis por ave (mL/mg)')}</label>
 <input type="number" step="0.001" {...register('dosage_per_bird', { valueAsNumber: true })} className={ic} placeholder="0.000" />
 </div>
 <div>
 <label className={lc}>{t('operations.treatmentDays', 'Días de tratamiento')}</label>
 <input type="number" min="1" {...register('treatment_days', { valueAsNumber: true })} className={ic} placeholder="5" />
 </div>
 </div>
 {renderMFRows(false)}
 </div>
 )

 case 'weight_recording': return (
 <div className="space-y-4">
 <div className="flex flex-col gap-3">
 <div>
 <label className={lc}>{t('operations.weekNumber', 'Semana')}</label>
 <input type="number" min="1" {...register('bird_movements.0.week_number', { valueAsNumber: true })} className={ic} placeholder="1" />
 </div>
 <div>
 <label className={lc}>{t('operations.sampleSize', 'Aves pesadas')}</label>
 <input type="number" min="1" {...register('sample_size', { valueAsNumber: true })} className={ic} placeholder="50" />
 </div>
 </div>
 {renderMFRows(true)}
 </div>
 )

 case 'bird_reception': return (
 <div className="space-y-4">
 <div className="flex flex-col gap-3 lg:grid lg:grid-cols-2">
 <div>
 <label className={lc}>{t('operations.supplier', 'Proveedor')}</label>
 {sel(register('supplier_id', { valueAsNumber: true }), suppliers, t('operations.selectSupplier', 'Seleccionar proveedor...'))}
 </div>
 <div>
 <label className={lc}>{t('operations.breed', 'Línea / Raza')}</label>
 {sel(register('bird_movements.0.breed_id', { valueAsNumber: true }), breeds, t('operations.selectBreed', 'Seleccionar línea...'))}
 </div>
 <div>
 <label className={lc}>{t('operations.targetHouse', 'Galpón destino')}</label>
 {sel(register('bird_movements.0.target_house_id', { valueAsNumber: true }), houses, t('operations.selectHouse', 'Seleccionar galpón...'))}
 </div>
 <div>
 <label className={lc}>{t('operations.weekNumber', 'Semana de vida')}</label>
 <input type="number" min="0" {...register('bird_movements.0.week_number', { valueAsNumber: true })} className={ic} placeholder="0" />
 </div>
 <div>
 <label className={lc}>{t('operations.sapOrderRef', 'Ref. OC SAP')}</label>
 <input {...register('extra_data.sap_order_ref' as any)} className={ic} placeholder="OC-SAP-001" />
 </div>
 </div>
 {renderMFRows(true)}
 </div>
 )

 case 'bird_distribution': return (
 <div className="space-y-3">
 <p className="text-xs text-slate-500 dark:text-slate-400">{t('operations.addHouseRows', 'Añade una fila por galpón destino')}</p>
 {birdFields.map((field, i) => (
 <div key={field.id} className="grid grid-cols-[1fr_90px_90px_auto] gap-2 items-end">
 <div>
 <label className={lc}>{t('operations.targetHouse', 'Galpón')}</label>
 {sel(register(`bird_movements.${i}.target_house_id`, { valueAsNumber: true }), houses, '---')}
 </div>
 <div>
 <label className={lc}>{t('operations.sex', 'Sexo')}</label>
 <select {...register(`bird_movements.${i}.sex`)} className={ic}>
 <option value="male">M</option>
 <option value="female">H</option>
 <option value="mixed">Mix</option>
 </select>
 </div>
 <div>
 <label className={lc}>{t('operations.quantity', 'Qty')}</label>
 <input type="number" min="0" {...register(`bird_movements.${i}.quantity`, { valueAsNumber: true })} className={ic} placeholder="0" />
 </div>
 <button type="button" onClick={() => removeBird(i)}
 className="h-11 w-10 flex items-center justify-center text-red-400 hover:text-red-600 border border-red-200 dark:border-red-800 rounded-lg mt-4">
 <Trash2 size={13} />
 </button>
 </div>
 ))}
 <button type="button" onClick={() => appendBird({ sex: 'mixed', quantity: 0 })}
 className="flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-800 font-medium">
 <Plus size={14} /> {t('operations.addRow', 'Añadir galpón')}
 </button>
 </div>
 )

 case 'bird_transfer': return (
 <div className="space-y-4">
 <div className="flex flex-col gap-3 lg:grid lg:grid-cols-2">
 <div>
 <label className={lc}>{t('operations.sourceHouse', 'Galpón origen')}</label>
 {sel(register('bird_movements.0.source_house_id', { valueAsNumber: true }), houses, t('operations.selectHouse', 'Seleccionar galpón...'))}
 </div>
 <div>
 <label className={lc}>{t('operations.targetHouse', 'Galpón destino')}</label>
 {sel(register('bird_movements.0.target_house_id', { valueAsNumber: true }), houses, t('operations.selectHouse', 'Seleccionar galpón...'))}
 </div>
 </div>
 {renderMFRows(true)}
 </div>
 )

 case 'bird_exit': return (
 <div className="space-y-4">
 <div className="flex flex-col gap-3 lg:grid lg:grid-cols-2">
 <div>
 <label className={lc}>{t('operations.destinationFarm', 'Granja destino')}</label>
 {sel(register('destination_farm_id', { valueAsNumber: true }), farms, t('operations.selectType', 'Seleccionar...'))}
 </div>
 <div>
 <label className={lc}>{t('operations.destinationPlant', 'Planta procesadora')}</label>
 {sel(register('destination_plant_id', { valueAsNumber: true }), processingPlants, t('operations.selectType', 'Seleccionar...'))}
 </div>
 <div>
 <label className={lc}>{t('operations.transport', 'Transporte')}</label>
 {sel(register('transport_id', { valueAsNumber: true }), transports, t('operations.selectTransport', 'Seleccionar transporte...'), (x: any) => `${x.plate} — ${x.name}`)}
 </div>
 <div>
 <label className={lc}>{t('operations.sapOrderRef', 'Ref. OC SAP')}</label>
 <input {...register('extra_data.sap_order_ref' as any)} className={ic} placeholder="OC-SAP-001" />
 </div>
 </div>
 {renderMFRows(true)}
 </div>
 )

 case 'feed_registration': return (
 <div className="space-y-4">
 <div className="flex flex-col gap-3 lg:grid lg:grid-cols-2">
 <div>
 <label className={lc}>{t('operations.feedPhase', 'Fase de alimento')}</label>
 <select {...register('extra_data.feed_phase' as any)} className={ic}>
 <option value="">{t('operations.selectType', 'Seleccionar...')}</option>
 <option value="pre_starter">{t('operations.feedPreStarter', 'Pre-iniciador')}</option>
 <option value="starter">{t('operations.feedStarter', 'Iniciador')}</option>
 <option value="grower">{t('operations.feedGrower', 'Crecimiento')}</option>
 <option value="finisher">{t('operations.feedFinisher', 'Finalizador')}</option>
 </select>
 </div>
 <div>
 <label className={lc}>{t('operations.feedType', 'Tipo de Alimento')}</label>
 {sel(register('feed_movements.0.feed_type_id', { valueAsNumber: true }), feedTypes, t('operations.selectType', 'Seleccionar...'))}
 </div>
 <div>
 <label className={lc}>{t('operations.weekNumber', 'Semana')}</label>
 <input type="number" min="1" {...register('feed_movements.0.week_number', { valueAsNumber: true })} className={ic} placeholder="1" />
 </div>
 </div>
 <div className="flex flex-col gap-3 lg:grid lg:grid-cols-3">
 <div>
 <label className={lc}>{t('operations.quantityKg', 'Cantidad (kg)')}</label>
 <input type="number" step="0.1" min="0" {...register('feed_movements.0.quantity_kg', { valueAsNumber: true })} className={ic} placeholder="0.0" />
 </div>
 <div>
 <label className={lc}>{t('operations.sacks', 'Sacos / bultos')}</label>
 <input type="number" min="0" {...register('feed_movements.0.sacks_count', { valueAsNumber: true })} className={ic} placeholder="0" />
 </div>
 <div>
 <label className={lc}>{t('operations.sapOrder', 'Orden SAP')}</label>
 <select {...register('feed_movements.0.sap_order_id')} className={ic}>
 <option value="">{t('operations.noOrder', 'Sin orden')}</option>
 {sapOrders.map((s: any) => <option key={s.id} value={s.sap_code}>{s.sap_code}</option>)}
 </select>
 </div>
 </div>
 </div>
 )

 case 'egg_collection':
 case 'egg_classification':
 case 'egg_reception_classification':
 case 'egg_dispatch': {
 const eggTypes = [
 { key: 'fertile', label: t('operations.fertile', 'Fértiles') },
 { key: 'dirty', label: t('operations.dirty', 'Sucios') },
 { key: 'broken', label: t('operations.broken', 'Rotos') },
 { key: 'infertile', label: t('operations.infertile', 'Infértiles') },
 { key: 'discarded', label: t('operations.discarded', 'Descartados') },
 ]
 return (
 <div className="space-y-4">
 {eventType === 'egg_dispatch' && (
 <div className="flex flex-col gap-3 lg:grid lg:grid-cols-2">
 <div>
 <label className={lc}>{t('operations.destinationIncubator', 'Incubadora destino')}</label>
 {sel(register('hatchery_params.0.incubator_id', { valueAsNumber: true }), incubators, t('operations.selectType', 'Seleccionar...'))} </div>
 <div>
 <label className={lc}>{t('operations.transport', 'Transporte')}</label>
 {sel(register('transport_id', { valueAsNumber: true }), transports, t('operations.selectTransport', 'Seleccionar transporte...'), (x: any) => `${x.plate} — ${x.name}`)}
 </div>
 </div>
 )}
 <div>
 <div className="grid grid-cols-2 px-1 py-2 border-b border-slate-200">
 <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">{t('operations.eggType', 'Tipo de huevo')}</span>
 <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">{t('operations.quantity', 'Cantidad')}</span>
 </div>
 {eggTypes.map(({ key, label }, i) => (
 <div key={key} className="grid grid-cols-2 px-1 py-2.5 gap-2 items-center border-b border-slate-100 last:border-0">
 <div>
 <input type="hidden" {...register(`egg_movements.${i}.egg_type`)} defaultValue={key} />
 <span className="text-sm text-slate-700 dark:text-slate-200">{label}</span>
 </div>
 <input type="number" min="0" {...register(`egg_movements.${i}.quantity`, { valueAsNumber: true })} className={ic} placeholder="0" />
 </div>
 ))}
 </div>
 {eventType === 'egg_collection' && (
 <div className="flex flex-col gap-3">
 <label className="text-sm font-medium text-slate-600 dark:text-slate-300">{t('operations.avgWeight', 'Peso prom. huevo (g)')}</label>
 <input type="number" step="0.1" min="0" {...register('egg_movements.0.avg_weight', { valueAsNumber: true })} className={ic} placeholder="60.0" />
 </div>
 )}
 </div>
 )
 }

 case 'egg_reception_hatchery': return (
 <div className="space-y-4">
 <div className="flex flex-col gap-3 lg:grid lg:grid-cols-2">
 <div>
 <label className={lc}>{t('operations.sourceOriginFarm', 'Granja de origen')}</label>
 {sel(register('extra_data.source_farm_id' as any), farms, t('operations.selectType', 'Seleccionar...'))} </div>
 <div>
 <label className={lc}>{t('operations.transport', 'Transporte')}</label>
 {sel(register('transport_id', { valueAsNumber: true }), transports, t('operations.selectTransport', 'Seleccionar...'), (x: any) => `${x.plate} — ${x.name}`)}
 </div>
 <div>
 <label className={lc}>{t('operations.dispatchOrder', 'No. de orden de despacho')}</label>
 <input {...register('extra_data.dispatch_order' as any)} className={ic} placeholder="D-2024-001" />
 </div>
 <div>
 <label className={lc}>{t('operations.quantity', 'Huevos recibidos')}</label>
 <input type="number" min="0" {...register('egg_storage_records.0.eggs_received', { valueAsNumber: true })} className={ic} placeholder="0" />
 </div>
 <div>
 <label className={lc}>{t('operations.tempTransport', 'Temp. transporte (°C)')}</label>
 <input type="number" step="0.1" {...register('egg_storage_records.0.transport_temp_c', { valueAsNumber: true })} className={ic} placeholder="15.0" />
 </div>
 <div>
 <label className={lc}>{t('operations.durationTransport', 'Duración transporte (min)')}</label>
 <input type="number" min="0" {...register('egg_storage_records.0.transport_duration_min', { valueAsNumber: true })} className={ic} placeholder="60" />
 </div>
 <div>
 <label className={lc}>{t('operations.storageTemp', 'Temp. almacén (°C)')}</label>
 <input type="number" step="0.1" {...register('egg_storage_records.0.storage_temp_c', { valueAsNumber: true })} className={ic} placeholder="15.0" />
 </div>
 <div>
 <label className={lc}>{t('operations.storageHumidity', 'Humedad almacén (%)')}</label>
 <input type="number" step="0.1" {...register('egg_storage_records.0.storage_humidity_pct', { valueAsNumber: true })} className={ic} placeholder="75" />
 </div>
 </div>
 </div>
 )

 case 'farm_inspection': {
 return (
 <div className="space-y-4">
 <p className="text-xs text-slate-500 dark:text-slate-400">{t('operations.inspectionPerHouse', 'Registra T°, H° y estado de cama por cada galpón inspeccionado')}</p>
 {houseInspFields.map((field, i) => (
 <div key={field.id} className="space-y-3 pb-4 mb-3 border-b border-slate-200 last:border-0">
 <div className="flex items-center justify-between mb-1">
 <span className="text-sm font-semibold text-slate-600 dark:text-slate-300">{t('operations.house', 'Galpón')} {i + 1}</span>
 {i > 0 && (
 <button type="button" onClick={() => removeHouseInsp(i)}
 className="text-red-400 hover:text-red-600 p-1"><Trash2 size={16} /></button>
 )}
 </div>
 {/* House selector */}
 <div>
 <label className={lc}>{t('operations.selectHouse', 'Galpón')}</label>
 <select {...register(`house_inspections.${i}.house_id`, { valueAsNumber: true })} className={ic}>
 <option value="">{t('operations.selectHouse', 'Seleccionar galpón...')}</option>
 {(farmHouses.length > 0 ? farmHouses : houses).map((h: any) => (
 <option key={h.id} value={h.id}>{h.name}{h.capacity ? ` (cap. ${h.capacity})` : ''}</option>
 ))}
 </select>
 </div>
 {/* T° and H° row */}
 <div className="flex flex-col gap-3">
 <div>
 <label className={lc}>{t('operations.tempC', 'Temperatura (°C)')}</label>
 <input type="number" step="0.1" min="0" max="60"
 {...register(`house_inspections.${i}.temperature`, { valueAsNumber: true })}
 className={ic} placeholder="28.0" />
 {(() => {
 const v = watch(`house_inspections.${i}.temperature` as any)
 const [tMin, tMax] = getTempRange(lotBirdType, lotAgeWeeks)
 return <RangeIndicator value={v} min={tMin} max={tMax} unit="°C" weekLabel={`sem.${lotAgeWeeks}`} />
 })()}
 </div>
 <div>
 <label className={lc}>{t('operations.humidityPct', 'Humedad (%)')}</label>
 <input type="number" step="0.1" min="0" max="100"
 {...register(`house_inspections.${i}.humidity`, { valueAsNumber: true })}
 className={ic} placeholder="65" />
 {(() => {
 const v = watch(`house_inspections.${i}.humidity` as any)
 const [hMin, hMax] = getHumidityRange(lotAgeWeeks)
 return <RangeIndicator value={v} min={hMin} max={hMax} unit="%" />
 })()}
 </div>
 </div>
 {/* Litter condition */}
 <div>
 <label className={lc}>{t('operations.litterCondition', 'Condición de cama')}</label>
 <select {...register(`house_inspections.${i}.litter_condition`)} className={ic}>
 <option value="">{t('operations.selectState', 'Seleccionar...')}</option>
 <option value="seca">{t('operations.litterDry', 'Seca')}</option>
 <option value="húmeda">{t('operations.litterWet', 'Húmeda')}</option>
 <option value="amoniacal">{t('operations.litterAmmoniacal', 'Amoniacal')}</option>
 <option value="compactada">{t('operations.litterCompacted', 'Compactada')}</option>
 </select>
 </div>
 {/* Litter notes */}
 <div>
 <label className={lc}>{t('operations.litterNotes', 'Observaciones de cama')}</label>
 <input type="text" {...register(`house_inspections.${i}.litter_notes`)}
 className={ic} placeholder={t('operations.litterNotesPlaceholder', 'Profundidad, renovación, etc.')} />
 </div>
 {/* Equipment notes */}
 <div>
 <label className={lc}>{t('operations.equipmentNotes', 'Estado de equipos (bebederos, comederos, ventiladores)')}</label>
 <input type="text" {...register(`house_inspections.${i}.equipment_notes`)}
 className={ic} placeholder={t('operations.equipmentNotesPlaceholder', 'Observaciones de equipos')} />
 </div>
 </div>
 ))}
 <button type="button"
 onClick={() => appendHouseInsp({ litter_condition: '' })}
 className="flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-800 font-medium">
 <Plus size={14} /> {t('operations.addHouse', 'Añadir galpón')}
 </button>
 </div>
 )
 }

 case 'transport_inspection': {
 const params = [
 { key: 'cage_condition', label: t('operations.cageCondition', 'Estado de jaulas'), numeric: false },
 { key: 'density', label: t('operations.densityBirdsM2', 'Densidad (aves/m²)'), numeric: true },
 { key: 'temperature', label: t('operations.temperature', 'Temperatura (°C)'), numeric: true },
 { key: 'ventilation', label: t('operations.ventilation', 'Ventilación'), numeric: false },
 { key: 'hygiene', label: t('operations.hygiene', 'Higiene del vehículo'), numeric: false },
 { key: 'duration_min', label: t('operations.durationMin', 'Duración viaje (min)'), numeric: true },
 ]
 return (
 <div className="space-y-4">
 <div>
 <label className={lc}>{t('operations.transport', 'Vehículo / Transporte')}</label>
 {sel(register('transport_id', { valueAsNumber: true }), transports, t('operations.selectTransport', 'Seleccionar...'), (x: any) => `${x.plate} — ${x.name}`)}
 </div>
 {params.map((param, i) => (
 <div key={param.key} className="flex items-center gap-3">
 <input type="hidden" {...register(`inspection_details.${i}.parameter`)} defaultValue={param.key} />
 <span className="text-sm text-slate-600 dark:text-slate-300 w-44 shrink-0">{param.label}</span>
 {param.numeric ? (
 <input type="number" step="0.1" {...register(`inspection_details.${i}.value`)}
 className="flex-1 h-11 px-3 border border-slate-300 rounded-lg text-sm focus:border-blue-500 outline-none" placeholder="--" />
 ) : (
 <select {...register(`inspection_details.${i}.status`)}
 className="flex-1 h-11 px-3 border border-slate-300 rounded-lg text-sm focus:border-blue-500 outline-none">
 <option value="">{t('operations.selectState', 'Seleccionar...')}</option>
 <option value="good">✅ {t('operations.good', 'Bueno')}</option>
 <option value="regular">⚠️ {t('operations.regular', 'Regular')}</option>
 <option value="bad">❌ {t('operations.bad', 'Malo')}</option>
 </select>
 )}
 </div>
 ))}
 </div>
 )
 }

 case 'hatchery_inspection': return (
 <div className="space-y-4">
 <p className="text-xs text-slate-500 dark:text-slate-400">{t('operations.addMachineRows', 'Registra los parámetros de cada máquina (incubadora o nacedora)')}</p>
 {incubatorFields.map((field, i) => {
 const machineType = watch(`hatchery_params.${i}.machine_type` as any)
 return (
 <div key={field.id} className="space-y-3 pb-4 mb-3 border-b border-slate-200 last:border-0">
 <p className="text-sm font-semibold text-slate-600 dark:text-slate-300">{t('operations.machine', 'Máquina')} {i + 1}</p>
 <div className="flex flex-col gap-3 lg:grid lg:grid-cols-3">
 <div>
 <label className={lc}>{t('operations.machineType', 'Tipo de máquina')}</label>
 <select {...register(`hatchery_params.${i}.machine_type` as any)} className={ic}>
 <option value="incubator">{t('operations.incubatorMachine', 'Incubadora')}</option>
 <option value="hatcher">{t('operations.hatcherMachine', 'Nacedora')}</option>
 </select>
 </div>
 <div>
 <label className={lc}>{machineType === 'hatcher' ? t('operations.hatcher', 'Nacedora') : t('operations.incubator', 'Incubadora')}</label>
 {machineType === 'hatcher'
 ? sel(register(`hatchery_params.${i}.hatcher_id`, { valueAsNumber: true }), hatchers, '---')
 : sel(register(`hatchery_params.${i}.incubator_id`, { valueAsNumber: true }), incubators, '---')
 }
 </div>
 <div>
 <label className={lc}>{t('operations.temp', 'T° (°C)')}</label>
 <input type="number" step="0.1" {...register(`hatchery_params.${i}.temperature`, { valueAsNumber: true })} className={ic} placeholder="37.5" />
 {(() => {
 const v = watch(`hatchery_params.${i}.temperature` as any)
 const [tMin, tMax] = machineType === 'hatcher' ? HATCHER_TEMP_RANGE : INCUBATOR_TEMP_RANGE
 return <RangeIndicator value={v} min={tMin} max={tMax} unit="°C" />
 })()}
 </div>
 <div>
 <label className={lc}>{t('operations.humidity', 'H° (%)')}</label>
 <input type="number" step="0.1" min="0" max="100" {...register(`hatchery_params.${i}.humidity`, { valueAsNumber: true })} className={ic} placeholder="56" />
 {(() => {
 const v = watch(`hatchery_params.${i}.humidity` as any)
 const [hMin, hMax] = machineType === 'hatcher' ? HATCHER_HUM_RANGE : INCUBATOR_HUM_RANGE
 return <RangeIndicator value={v} min={hMin} max={hMax} unit="%" />
 })()}
 </div>
 <div>
 <label className={lc}>{t('operations.co2', 'CO₂ (%)')}</label>
 <input type="number" step="0.01" min="0" {...register(`hatchery_params.${i}.co2`, { valueAsNumber: true })} className={ic} placeholder="0.50" />
 {(() => {
 const v = watch(`hatchery_params.${i}.co2` as any)
 return <RangeIndicator value={v} min={0} max={0.5} unit="%" />
 })()}
 </div>
 </div>
 {i > 0 && (
 <button type="button" onClick={() => removeIncubator(i)}
 className="absolute top-2 right-2 text-red-400 hover:text-red-600 p-1">
 <Trash2 size={14} />
 </button>
 )}
 </div>
 )
 })}
 <button type="button" onClick={() => appendIncubator({ machine_type: 'incubator' } as any)}
 className="flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-800 font-medium">
 <Plus size={14} /> {t('operations.addMachine', 'Añadir máquina')}
 </button>
 </div>
 )

 case 'incubation_load': return (
 <div className="space-y-4">
 <div className="flex flex-col gap-3 lg:grid lg:grid-cols-2">
 <div>
 <label className={lc}>{t('operations.incubator', 'Incubadora')}</label>
 {sel(register('hatchery_params.0.incubator_id', { valueAsNumber: true }), incubators, t('operations.selectType', 'Seleccionar...'))}
 </div>
 <div>
 <label className={lc}>{t('operations.quantityLoaded', 'Cantidad cargada')}</label>
 <input type="number" min="0" {...register('hatchery_params.0.quantity_loaded', { valueAsNumber: true })} className={ic} placeholder="0" />
 </div>
 <div>
 <label className={lc}>{t('operations.temp', 'Temperatura (°C)')}</label>
 <input type="number" step="0.1" {...register('hatchery_params.0.temperature', { valueAsNumber: true })} className={ic} placeholder="37.5" />
 </div>
 <div>
 <label className={lc}>{t('operations.humidity', 'Humedad (%)')}</label>
 <input type="number" step="0.1" {...register('hatchery_params.0.humidity', { valueAsNumber: true })} className={ic} placeholder="55" />
 </div>
 <div>
 <label className={lc}>{t('operations.co2', 'CO₂ (%)')}</label>
 <input type="number" step="0.01" {...register('hatchery_params.0.co2', { valueAsNumber: true })} className={ic} placeholder="0.5" />
 </div>
 <div className="flex items-center gap-2 pt-5">
 <input type="checkbox" id="turning" {...register('hatchery_params.0.turning')}
 className="h-4 w-4 rounded border-slate-300 text-blue-600" />
 <label htmlFor="turning" className="text-sm text-slate-700 dark:text-slate-200">{t('operations.turning', 'Volteo activo')}</label>
 </div>
 </div>
 </div>
 )

 case 'ovoscopy': {
 const types = [
 { key: 'fertile', label: t('operations.fertile', 'Fértiles') },
 { key: 'infertile', label: t('operations.infertile', 'Infértiles') },
 { key: 'dead_early', label: t('operations.deadEarly', 'Muertos tempranos') },
 { key: 'dead_late', label: t('operations.deadLate', 'Muertos tardíos') },
 { key: 'contaminated', label: t('operations.contaminated', 'Contaminados') },
 ]
 return (
 <div className="space-y-4">
 <div>
 <label className={lc}>{t('operations.candlingDay', 'Día de ovoscopía')}</label>
 <input type="number" min="1" {...register('bird_movements.0.week_number', { valueAsNumber: true })} className={ic} placeholder="10" />
 <input type="hidden" {...register('bird_movements.0.sex')} defaultValue="mixed" />
 <input type="hidden" {...register('bird_movements.0.quantity')} defaultValue="0" />
 </div>
 <div>
 {types.map(({ key, label }, i) => (
 <div key={key} className="grid grid-cols-2 px-1 py-2.5 gap-2 items-center border-b border-slate-100 last:border-0">
 <div>
 <input type="hidden" {...register(`egg_movements.${i}.egg_type`)} defaultValue={key} />
 <span className="text-sm text-slate-700 dark:text-slate-200">{label}</span>
 </div>
 <input type="number" min="0" {...register(`egg_movements.${i}.quantity`, { valueAsNumber: true })} className={ic} placeholder="0" />
 </div>
 ))}
 </div>
 </div>
 )
 }

 case 'transfer_to_hatcher': return (
 <div className="space-y-4">
 <div className="flex flex-col gap-3 lg:grid lg:grid-cols-2">
 <div>
 <label className={lc}>{t('operations.hatcher', 'Nacedora')}</label>
 {sel(register('hatchery_params.0.hatcher_id', { valueAsNumber: true }), hatchers, t('operations.selectType', 'Seleccionar...'))}
 </div>
 <div>
 <label className={lc}>{t('operations.incubationDay', 'Día de incubación')}</label>
 <input type="number" min="1" max="21" {...register('extra_data.incubation_day' as any)} className={ic} placeholder="18" />
 </div>
 <div>
 <label className={lc}>{t('operations.qtyTransferred', 'Cantidad transferida')}</label>
 <input type="number" min="0" {...register('hatchery_params.0.quantity_transferred', { valueAsNumber: true })} className={ic} placeholder="0" />
 </div>
 <div>
 <label className={lc}>{t('operations.temp', 'Temperatura (°C)')}</label>
 <input type="number" step="0.1" {...register('hatchery_params.0.temperature', { valueAsNumber: true })} className={ic} placeholder="37.0" />
 </div>
 <div>
 <label className={lc}>{t('operations.humidity', 'Humedad (%)')}</label>
 <input type="number" step="0.1" {...register('hatchery_params.0.humidity', { valueAsNumber: true })} className={ic} placeholder="68" />
 </div>
 </div>
 </div>
 )

 case 'birth_registration': {
 const rows = [
 { sex: 'mixed', label: t('operations.totalHatched', 'Total nacidos'), idx: 0 },
 { sex: 'male', label: t('operations.males', 'Machos viables'), idx: 1 },
 { sex: 'female',label: t('operations.females', 'Hembras viables'), idx: 2 },
 { sex: 'mixed', label: t('operations.weak', 'Débiles'), idx: 3 },
 ]
 return (
 <div>
 {rows.map(({ sex, label, idx }) => (
 <div key={idx} className="grid grid-cols-2 px-1 py-2.5 gap-2 items-center border-b border-slate-100 last:border-0">
 <div>
 <input type="hidden" {...register(`bird_movements.${idx}.sex`)} defaultValue={sex} />
 <span className="text-sm text-slate-700 dark:text-slate-200">{label}</span>
 </div>
 <input type="number" min="0" {...register(`bird_movements.${idx}.quantity`, { valueAsNumber: true })} className={ic} placeholder="0" />
 </div>
 ))}
 </div>
 )
 }

 case 'chick_dispatch': return (
 <div className="space-y-4">
 <div className="flex flex-col gap-3 lg:grid lg:grid-cols-2">
 <div>
 <label className={lc}>{t('operations.destinationFarm', 'Granja destino')}</label>
 {sel(register('destination_farm_id', { valueAsNumber: true }), farms, t('operations.selectType', 'Seleccionar...'))}
 </div>
 <div>
 <label className={lc}>{t('operations.transport', 'Transporte')}</label>
 {sel(register('transport_id', { valueAsNumber: true }), transports, t('operations.selectTransport', 'Seleccionar transporte...'), (x: any) => `${x.plate} — ${x.name}`)}
 </div>
 <div>
 <label className={lc}>{t('operations.sanitaryCert', 'Certificado sanitario')}</label>
 <input {...register('extra_data.sanitary_cert' as any)} className={ic} placeholder="No. de certificado" />
 </div>
 </div>
 {renderMFRows(false)}
 </div>
 )

 case 'lot_closure': return (
 <div className="space-y-4">
 <div className="flex flex-col gap-3 lg:grid lg:grid-cols-2">
 <div>
 <label className={lc}>{t('operations.finalPopulation', 'Población final')}</label>
 <input type="number" min="0" {...register('bird_movements.0.quantity', { valueAsNumber: true })} className={ic} placeholder="0" />
 <input type="hidden" {...register('bird_movements.0.sex')} defaultValue="mixed" />
 </div>
 <div>
 <label className={lc}>{t('operations.avgWeight', 'Peso final prom. (kg)')}</label>
 <input type="number" step="0.001" {...register('bird_movements.0.avg_weight', { valueAsNumber: true })} className={ic} placeholder="0.000" />
 </div>
 <div>
 <label className={lc}>{t('operations.fcr', 'FCR (Conversión alimenticia)')}</label>
 <input type="number" step="0.001" {...register('extra_data.fcr' as any)} className={ic} placeholder="2.000" />
 </div>
 <div>
 <label className={lc}>{t('operations.totalMortality', 'Mortalidad total (%)')}</label>
 <input type="number" step="0.01" {...register('extra_data.mortality_pct' as any)} className={ic} placeholder="0.00" />
 </div>
 </div>
 </div>
 )

 case 'grandparent_import': return (
 <div className="space-y-4">
 <div className="flex flex-col gap-3 lg:grid lg:grid-cols-2">
 <div>
 <label className={lc}>{t('operations.importCountry', 'País de origen')}</label>
 <input {...register('extra_data.origin_country' as any)} className={ic} placeholder="Ej. Francia" />
 </div>
 <div>
 <label className={lc}>{t('operations.sanitaryCert', 'Certificado sanitario')}</label>
 <input {...register('extra_data.sanitary_cert' as any)} className={ic} placeholder="No. de certificado" />
 </div>
 <div>
 <label className={lc}>{t('operations.quarantineDays', 'Días de cuarentena')}</label>
 <input type="number" min="0" {...register('extra_data.quarantine_days' as any)} className={ic} placeholder="21" />
 </div>
 <div>
 <label className={lc}>{t('operations.importDoc', 'Documento de importación')}</label>
 <input {...register('extra_data.import_doc' as any)} className={ic} placeholder="No. de guía" />
 </div>
 </div>
 {renderMFRows(true)}
 </div>
 )

 default: return (
 <div className="py-6 text-sm text-slate-900 dark:text-slate-100 text-center italic">
 {t('operations.noSpecificFields', 'Registra tus observaciones en el campo de abajo.')}
 </div>
 )
 }
 }

 const selectedStageMeta = PROCESS_STAGES.find(s => s.key === stage)
 const SelectedEventIcon = eventType ? (EVENT_ICON_MAP[eventType] ?? EVENT_ICONS[eventType]) : null
 const SelectedStageIcon = selectedStageMeta?.Icon

 return (
 <div className="py-4 sm:p-6 max-w-2xl mx-auto text-slate-900 dark:text-slate-100">
 {/* Stepper */}
 <nav className="flex items-center gap-1.5 text-sm font-semibold mb-5 select-none">
 <button type="button" onClick={() => setStep(1)} className={step >= 1 ? 'text-[#2563EB]' : 'text-slate-900 dark:text-slate-100'}>
 {t('process.step1', '1 · Proceso')}
 </button>
 <span className="text-slate-900 dark:text-slate-100">/</span>
 <button type="button" disabled={!stage} onClick={() => stage && setStep(2)}
 className={`${step >= 2 ? 'text-[#2563EB]' : 'text-slate-900 dark:text-slate-100'} disabled:cursor-not-allowed`}>
 {t('process.step2', '2 · Operación')}
 </button>
 <span className="text-slate-900 dark:text-slate-100">/</span>
 <button type="button" disabled={!eventType} onClick={() => eventType && setStep(3)}
 className={`${step >= 3 ? 'text-[#2563EB]' : 'text-slate-900 dark:text-slate-100'} disabled:cursor-not-allowed`}>
 {t('process.step3', '3 · Datos')}
 </button>
 </nav>

 {/* ===================== STEP 1 — PROCESS ===================== */}
 {step === 1 && (
 <div>
 <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">{t('process.title', 'Registrar Operación')}</h1>
 <p className="text-sm text-slate-900 dark:text-slate-100 mt-1 mb-5">{t('process.subtitle', '¿Qué proceso vas a registrar?')}</p>
 <div className="flex flex-col gap-3 lg:grid lg:grid-cols-2">
 {PROCESS_STAGES.map(s => {
 const Icon = s.Icon
 return (
 <button key={s.key} type="button" onClick={() => goToStep2(s.key)}
 className={`flex items-center gap-3 p-4 min-h-[5rem] rounded-xl border border-slate-200 bg-white dark:bg-slate-800 text-left active:bg-slate-50 transition-colors ${s.accent}`}>
 <div className={`shrink-0 w-12 h-12 rounded-lg flex items-center justify-center ${s.iconBg}`}>
 <Icon size={26} className={s.iconColor} />
 </div>
 <div className="min-w-0">
 <p className="font-semibold text-slate-900 dark:text-slate-100 leading-tight">{t(s.labelKey, s.fallback)}</p>
 <p className="text-sm text-slate-500 dark:text-slate-400 leading-snug mt-1">{t(s.descKey, s.descFallback)}</p>
 </div>
 </button>
 )
 })}
 </div>
 </div>
 )}

 {/* ============== STEP 2 — OPERATION ============== */}
 {step === 2 && stage && selectedStageMeta && (
 <div>
 <button type="button" onClick={() => setStep(1)}
 className="inline-flex items-center gap-1 text-sm text-slate-900 dark:text-slate-100 hover:text-[#2563EB] mb-3">
 <ChevronLeft size={16} /> {t('common.back', 'Atrás')}
 </button>
 <div className="flex items-center gap-3 mb-5">
 <div className={`shrink-0 w-10 h-10 rounded-lg flex items-center justify-center ${selectedStageMeta.iconBg}`}>
 {SelectedStageIcon && <SelectedStageIcon size={22} className={selectedStageMeta.iconColor} />}
 </div>
 <h1 className="text-lg font-bold text-slate-900 dark:text-slate-100">{t(selectedStageMeta.labelKey, selectedStageMeta.fallback)}</h1>
 </div>

 <p className="text-sm font-semibold text-slate-700 dark:text-slate-200 mt-1 mb-1">{t('process.chooseOperation', 'Elige la operación')}</p>
 <div className="space-y-5 mt-3">
 {categoriesForStage(stage).map(({ category, events }) => {
 const CatIcon = category.Icon
 return (
 <div key={category.key}>
 <div className="flex items-center gap-2 mb-2">
 <CatIcon size={16} className={category.color} />
 <span className="text-sm font-bold uppercase tracking-wide text-slate-600 dark:text-slate-300">
 {t(category.labelKey, category.fallback)}
 </span>
 </div>
 <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
 {events.map(evt => {
 const EvIcon = EVENT_ICON_MAP[evt] ?? EVENT_ICONS[evt]
 return (
 <button key={evt} type="button" onClick={() => chooseOperation(evt)}
 className="flex flex-col items-center gap-1.5 p-3 min-h-[4.5rem] rounded-lg border border-slate-200 bg-white dark:bg-slate-800 hover:border-[#2563EB] hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors text-center group">
 {EvIcon && <EvIcon size={22} className="text-[#2563EB] group-hover:scale-110 transition-transform" />}
 <span className="text-sm text-slate-700 dark:text-slate-200 leading-tight">{t(`eventsShort.${evt}`, evt)}</span>
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
 <button
 type="button"
 onClick={() => {
 if (prefillType && !stage) {
 const target = sessionStorage.getItem('operationBackTarget')
 if (target && (target.startsWith('/poultry') || target.startsWith('/menu/poultry'))) {
 navigate(target)
 return
 }
 navigate('/menu/poultry')
 return
 }
 setStep(stage ? 2 : 1)
 }}
 className="inline-flex items-center gap-1 text-sm text-slate-900 dark:text-slate-100 hover:text-[#2563EB] mb-3"
 >
 <ChevronLeft size={16} /> {t('common.back', 'Atrás')}
 </button>

 {eventType && (
 <div className="flex items-center gap-3 mb-4 p-3 rounded-lg bg-blue-50 dark:bg-blue-950 border border-blue-100 dark:border-blue-800">
 {SelectedEventIcon && <SelectedEventIcon size={22} className="text-[#2563EB]" />}
 <div>
 <p className="text-sm font-bold text-slate-900 dark:text-slate-100">{t(`events.${eventType}`, eventType)}</p>
 {selectedStageMeta && (
 <p className="text-xs text-slate-900 dark:text-slate-100">{t(selectedStageMeta.labelKey, selectedStageMeta.fallback)}</p>
 )}
 </div>
 </div>
 )}

 {result && (
 <div className={`px-4 py-3 rounded-lg text-sm font-medium mb-4 ${result.ok ? 'bg-green-50 dark:bg-green-950 text-green-700' : 'bg-red-50 dark:bg-red-950 text-red-700 dark:text-red-300'}`}>
 {result.message}
 </div>
 )}

 <form id="operation-form" onSubmit={handleSubmit(onSubmit)} className="space-y-5">
 <div>
 <label className="block text-sm font-semibold text-slate-700 dark:text-slate-200 mb-1">{t('operations.lot')}</label>
 <select {...register('lot_id', { valueAsNumber: true })}
 className="w-full h-11 px-3 border border-slate-300 rounded-lg text-sm text-slate-900 dark:text-slate-100 bg-white dark:bg-slate-800 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none">
 <option value="">{t('operations.selectLot')}</option>
 {lots.map((l: any) => (
 <option key={l.id} value={l.id}>{l.lot_code}{l.status && l.status !== 'active' ? ` · ${String(l.status)}` : ''}</option>
 ))}
 </select>
 {lotsLoadError && <p className="text-xs text-red-600 dark:text-red-400 mt-1">{t('operations.errorLoadingLots', 'Error al cargar lotes')}</p>}
 {errors.lot_id && <p className="text-red-500 text-xs mt-1">{t(errors.lot_id.message ?? '')}</p>}
 </div>

 <div>
 <label className="block text-sm font-semibold text-slate-700 dark:text-slate-200 mb-1">{t('operations.date')}</label>
 <input type="date" {...register('event_date')}
 className="w-full h-11 px-3 border border-slate-300 rounded-lg text-sm text-slate-900 dark:text-slate-100 bg-white dark:bg-slate-800 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none" />
 </div>

 {/* Operation-specific fields */}
 <div>
 {renderOperationFields()}
 </div>

 <div>
 <label className="block text-sm font-semibold text-slate-700 dark:text-slate-200 mb-1">{t('operations.observations')}</label>
 <textarea {...register('observations')} rows={2}
 className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm text-slate-900 dark:text-slate-100 bg-white dark:bg-slate-800 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none" />
 </div>

 <button type="submit" disabled={submitting || !eventType}
 className="w-full h-12 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition disabled:opacity-50">
 {submitting ? t('common.loading') : t('common.save')}
 </button>
 </form>
 </div>
 )}
 </div>
 )
}
