import { useState, useEffect, useMemo } from 'react'
import { useForm, useFieldArray } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useTranslation } from 'react-i18next'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { ChevronLeft, Plus, Trash2 } from 'lucide-react'
import api from '../../services/api'
import { useToast, getErrorMessage } from '../../components/Toast'
import { serializarAlmacenamientoDeHuevos, serializarMovimientosDeAves, serializarMovimientosDeAlimento, serializarParamsDeIncubadora, identificadorDeOrdenSap, resolverUbicacionDelEvento, resolverStageDelAsistente, limpiarVacios, anclarCampoEnPrimeraFila, validarReglasDeNacimiento } from './operationPayload'
import SearchSelect from '../../components/ui/SearchSelect'
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

const LOT_OPTIONAL_INSPECTION_EVENTS = new Set([
 'farm_inspection',
 'hatchery_inspection',
])

// `R-153` · `OD-25 (B)`: la importación de abuelas también puede registrarse sin lote — el
// lote (`L-GP-{año}-{nn}`) nace al aprobarla, como consecuencia de `P-07`. La vía con lote
// previo (legado `R-152`) sigue disponible eligiéndolo en el selector.
const LOT_OPTIONAL_EVENTS = new Set<string>([
 ...LOT_OPTIONAL_INSPECTION_EVENTS,
 'grandparent_import',
])

// `R-190`: tipos que requieren ubicación derivada del evento (la recepción ya F-01e).
const EVENTOS_UBICACION_EVENTO = new Set([
  'bird_distribution', 'bird_transfer', 'bird_exit', 'farm_inspection',
  'transport_inspection', 'egg_collection', 'egg_dispatch',
])

// `R-190` · C-05: tipos con selector «Galpón del evento» (fuente sin fila propia).
const EVENTOS_CON_SELECTOR_GALPON = new Set([
  'bird_exit', 'egg_collection', 'egg_dispatch', 'transport_inspection',
])

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
 ok: { bg: 'bg-emerald-50 border-emerald-200', text: 'text-emerald-700', icon: '✅' },
 warn: { bg: 'bg-amber-50 border-amber-200', text: 'text-amber-700', icon: '⚠️' },
 error: { bg: 'bg-red-50 border-red-200', text: 'text-red-700', icon: '❌' },
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
const operacionBase = z.object({
 lot_id: z.number({ message: 'operations.selectLot' }).min(1).optional(),
 farm_id: z.number().optional(),
 house_id: z.number().optional(),
 event_type: z.string().min(1),
 event_date: z.string().min(1),
 observations: z.string().optional(),
 // Operation-specific catalog FKs
 // `R-189 (F-01)`: el campo tipado que la importación valida (`BR-22`) y la UI escribe
 // (`GA-TD-014`); sin declararlo aquí, zod lo descartaba y nunca viajaba al API.
 sap_document_ref: z.string().optional(),
 supplier_id: z.number().optional(),
 cause_id: z.number().optional(),
 cull_cause_id: z.number().optional(),
 vaccine_id: z.number().optional(),
 vaccination_route: z.string().optional(),
 vaccine_lot_number: z.string().optional(),
 medication_id: z.number().optional(),
 dosage_per_bird: z.number().min(0, { message: 'operations.dosageInvalid' }).optional(),
 treatment_days: z.number().optional(),
 destination_farm_id: z.number().optional(),
 destination_plant_id: z.number().optional(),
 transport_id: z.number().optional(),
 sample_size: z.number().optional(),
 water_liters: z.number().positive().optional(), // `GA-REM-021-A` · B05 (L, RR-11)
 received_total: z.number().int().min(1).optional(), // `GA-REM-021-B` · B01 (aves)
 dead_on_arrival: z.number().int().min(0).optional(),
 rejected_on_arrival: z.number().int().min(0).optional(),
 chicks_healthy: z.number().int().min(0).optional(), // `GA-REM-021-C` · B13
 chicks_weak: z.number().int().min(0).optional(),
 extra_data: z.record(z.string(), z.any()).optional(),
 // Sub-models
 bird_movements: z.array(z.object({
 sex: z.string().optional(),
 quantity: z.number().min(0).optional(),
 avg_weight: z.number().optional(),
 sample_size: z.number().optional(),
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
 equipment_count: z.number().optional(),
 equipment_items: z.array(z.object({
 equipment_type: z.string(),
 observation: z.string().optional(),
 })).optional(),
 })).optional(),
 egg_storage_records: z.array(z.object({
 eggs_received: z.number().optional(),
 storage_temp_c: z.number().optional(),
 storage_humidity_pct: z.number().optional(),
 transport_temp_c: z.number().optional(),
 transport_duration_min: z.number().optional(),
 notes: z.string().optional(),
 })).optional(),
}).superRefine((data, ctx) => {
 if (!data.event_type) return
 if (!LOT_OPTIONAL_EVENTS.has(data.event_type) && (!data.lot_id || data.lot_id < 1)) {
 ctx.addIssue({
 code: z.ZodIssueCode.custom,
 path: ['lot_id'],
 message: 'operations.selectLot',
 })
 }
})

/** `R-189 (F-01)`: un campo numérico vacío llega como `NaN` (`valueAsNumber`) y zod invalida **en silencio**
 * (el submit no viaja). Se normaliza a `undefined` ANTES de validar: el «vacío» es ausencia, no un número.
 * No se inventan valores y la cantidad 0 declarada se conserva. */
function limpiarNumerosNoFinitos(valor: unknown): unknown {
 if (typeof valor === 'number') return Number.isFinite(valor) ? valor : undefined
 if (Array.isArray(valor)) return valor.map(limpiarNumerosNoFinitos)
 if (valor && typeof valor === 'object' && Object.getPrototypeOf(valor) === Object.prototype) {
 const limpio: Record<string, unknown> = {}
 for (const [clave, v] of Object.entries(valor as Record<string, unknown>)) {
 limpio[clave] = limpiarNumerosNoFinitos(v)
 }
 return limpio
 }
 return valor
}

// El preprocesado normaliza el ENTRANTE (NaN ⇒ ausencia) sin cambiar la forma del formulario:
// el cast conserva el tipado que el resolver ya usaba para `operacionBase`.
// `R-206`: la cadena vacía de un opcional es ausencia — se compone con la limpieza de
// `NaN` para que el contrato canónico no lleve `''` (fecha de cuarentena, numéricos como
// cadena, `sap_document_ref`/`vaccination_route` sin elegir).
const operationSchema = z.preprocess((v) => limpiarVacios(limpiarNumerosNoFinitos(v)), operacionBase) as unknown as typeof operacionBase

type OperationFormData = z.infer<typeof operationSchema>

// Shared CSS helpers (module-level to avoid recreating on each render)
const ic = 'w-full h-11 px-3 border border-slate-300 rounded-lg text-base text-slate-900 bg-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none'
const lc = 'block text-sm font-semibold text-slate-700 mb-1.5'

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
 const [sapPurchaseOrders, setSapPurchaseOrders] = useState<any[]>([])
 const [submitting, setSubmitting] = useState(false)
 const [result, setResult] = useState<{ ok: boolean; message: string } | null>(null)

 // Multi-company: farm/hatchery filter for lot narrowing
 const [selectedFarmId, setSelectedFarmId] = useState<number | null>(null)
 const [selectedHatcheryId, setSelectedHatcheryId] = useState<number | null>(null)

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
 const [hatcheries, setHatcheries] = useState<any[]>([])

 const toast = useToast()

 const { register, handleSubmit, watch, setValue, control, formState: { errors } } = useForm<OperationFormData>({
 resolver: zodResolver(operationSchema),
 defaultValues: {
 event_date: new Date().toISOString().split('T')[0],
 lot_id: prefillLotId ? Number(prefillLotId) : undefined,
 event_type: prefillType || '',
 bird_movements: [{ sex: 'male' }, { sex: 'female' }],
 egg_movements: [],
 feed_movements: [{}],
 hatchery_params: [{}],
 inspection_details: [],
 house_inspections: [],
 egg_storage_records: [{}],
 },
 })

 const eventType = watch('event_type')
 const lotId = watch('lot_id')
 // `R-190`: el lote seleccionado a nivel de componente — la derivación del JSX y de la guarda lo consulta.
 const selectedLot = useMemo(() => lots.find((l: any) => l.id === lotId) ?? null, [lots, lotId])

 // Hatchery event types (for determining whether to show Farm or Hatchery selector)
 const HATCHERY_EVENTS = new Set([
 'egg_reception_classification', 'egg_reception_hatchery', 'incubation_load',
 'ovoscopy', 'transfer_to_hatcher', 'birth_registration', 'chick_dispatch',
 'hatchery_inspection',
 ])
 const isHatcheryStage = eventType ? HATCHERY_EVENTS.has(eventType) : false
 const isLotOptionalInspection = eventType ? LOT_OPTIONAL_INSPECTION_EVENTS.has(eventType) : false

 // Lots filtered by selected farm
 const filteredLots = useMemo(() => {
 if (!isHatcheryStage && selectedFarmId) {
 return lots.filter((l: any) => l.farm_id === selectedFarmId)
 }
 return lots
 }, [lots, selectedFarmId, isHatcheryStage])

 // Houses filtered to the farm of the selected lot (for farm_inspection per-house rows)
 const farmHouses = useMemo(() => {
 if (selectedFarmId) {
 return houses.filter((h: any) => h.farm_id === selectedFarmId)
 }
 const lot = lots.find((l: any) => l.id === lotId)
 if (!lot?.farm_id) return houses
 return houses.filter((h: any) => h.farm_id === lot.farm_id)
 }, [selectedFarmId, lots, lotId, houses])

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
  // `R-190`: «Galpón del evento» (selector) y el error de ubicación en cliente.
  const [eventHouseId, setEventHouseId] = useState<number | null>(null)
  const [ubicacionError, setUbicacionError] = useState<string | null>(null)
 // `R-205`: la etapa también se deriva del contexto — `?stage=` o el lote — no sólo del paso 1.
 const stageDerivada = useMemo(() => resolverStageDelAsistente({
 search: searchParams.toString() ? `?${searchParams.toString()}` : '',
 lote: selectedLot ? { bird_type: selectedLot.bird_type, fase: selectedLot.fase } : null,
 eventType,
 }) as StageKey | null, [selectedLot, eventType, searchParams])
 const stageFinal = stage ?? stageDerivada

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
 if (isLotOptionalInspection && lotId) {
 setValue('lot_id', undefined as any)
 }
 }, [isLotOptionalInspection, lotId, setValue])

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
 api.get('/sap/references?ref_type=purchase_order&limit=50').then(r => setSapPurchaseOrders(r.data?.references || [])).catch(() => {})
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
 api.get('/masters/hatcheries?limit=100'),
 ]).then(results => {
 const get = (r: PromiseSettledResult<any>) => r.status === 'fulfilled' ? (r.value.data || []) : []
 setVaccines(get(results[0])); setMedications(get(results[1]))
 setMortalityCauses(get(results[2])); setCullCauses(get(results[3]))
 setTransports(get(results[4])); setFarms(get(results[5]))
 setProcessingPlants(get(results[6])); setSuppliers(get(results[7]))
 setBreeds(get(results[8])); setHouses(get(results[9]))
 setFeedTypes(get(results[10])); setIncubators(get(results[11]))
 setHatchers(get(results[12])); setHatcheries(get(results[13]))
 })
 }, []) // eslint-disable-line react-hooks/exhaustive-deps

 const onSubmit = async (data: OperationFormData) => {
 setSubmitting(true); setResult(null)
 try {
 const selectedLot = data.lot_id ? lots.find((l: any) => l.id === data.lot_id) : null
 const firstInspectedHouseId = data.house_inspections?.find((h: any) => h?.house_id)?.house_id
        // `R-190`: una sola fuente de verdad para la ubicación del evento (helper puro con test propio).
        // La recepción conserva su regla F-01e dentro del helper (galpón del lote ?? fila de distribución);
        // los demás tipos derivan según C-01/C-05/C-07 — sin fuente, ausencia (no se inventa).
        const filasUbicacion = data.event_type === 'farm_inspection'
          ? (data.house_inspections || []).map((h: any) => ({ target_house_id: h?.house_id }))
          : (data.bird_movements || [])
        const ubicacion = resolverUbicacionDelEvento({
          eventType: data.event_type,
          lote: selectedLot,
          filas: filasUbicacion,
          houseSeleccionado: eventHouseId,
          granjaSeleccionada: selectedFarmId,
          galpones: houses,
        })
        const derivedFarmId = ubicacion.farm_id ?? selectedFarmId ?? selectedLot?.farm_id ?? undefined
        const derivedHouseId = ubicacion.house_id ?? undefined
        // `R-190` · C-03: la ubicación obligatoria se exige en cliente — sin petición y con mensaje
        // claro cuando falta (la recepción F-01e conserva su ausencia-no-inventada).
        if (EVENTOS_UBICACION_EVENTO.has(data.event_type)) {
          if (data.event_type === 'farm_inspection') {
            if (!derivedFarmId) {
              setUbicacionError('operations.farmRequired')
              setSubmitting(false)
              return
            }
          } else if (!derivedHouseId) {
            setUbicacionError('operations.eventHouseRequired')
            setSubmitting(false)
            return
          }
        }
        // `R-205`: el cuadre de reproductoras (BR-20 · `B01` · RR-12) se exige en cliente — sin
        // petición y con mensaje claro cuando falta. La regla del servidor no cambia (control BR-20).
        if (data.event_type === 'bird_reception' && selectedLot?.bird_type === 'breeder') {
          const d: any = data
          const completos = [d.received_total, d.dead_on_arrival, d.rejected_on_arrival]
            .every((v) => v !== undefined && v !== null && Number.isFinite(Number(v)))
          if (!completos) {
            setUbicacionError('operations.cuadreRequired')
            setSubmitting(false)
            return
          }
        }
        // `R-220` · A16 (B-35 · BR-21): reglas de nacimiento advertidas EN CLIENTE — el 400
        // ya no es la primera fuente de verdad: `mixed` excluyente y sanos/débiles obligatorios.
        if (data.event_type === 'birth_registration') {
          const faltaDeNacimiento = validarReglasDeNacimiento(data as any)
          if (faltaDeNacimiento) {
            setUbicacionError(faltaDeNacimiento)
            setSubmitting(false)
            return
          }
        }
        setUbicacionError(null)
        void firstInspectedHouseId
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
 // Equipment items → individual inspection_details per equipment type
 if (h.equipment_items) {
 for (const item of h.equipment_items) {
 if (item.equipment_type) {
 houseDetails.push({
 house_id: h.house_id,
 parameter: `equipment_${item.equipment_type}`,
 value: item.observation || '',
 })
 }
 }
 }
 }

 // `R-169` (`GA-REM-035-A`): sin tolerancia ±10 % en el cliente; la verdad de cantidades es BR-18 (backend).
 // Lo que el operador escribe en observaciones es lo que se persiste.
 const observations = data.observations || ''

 // `R-189 (F-01)` · el serializador limpia `NaN`/filas vacías y el almacenamiento sin contenido
 // (el `[{}]` por omisión del formulario ya no viaja: el contrato canónico es `[]`).
 const normalizedBirdMovements = serializarMovimientosDeAves((data.bird_movements || []).map((m) => {
 if (data.event_type === 'bird_reception' && (m.week_number == null || Number.isNaN(m.week_number))) {
 return { ...m, week_number: 0 }
 }
 return m
 }))
 // `R-220` · A17 (B-38): la «Semana» se captura una vez (fila 0 de la UI); se ancla a la
 // primera fila superviviente para que no muera con el descarte de filas sin cantidad.
 const semanaDelEvento = (data.bird_movements?.[0] as any)?.week_number
 const movimientosAves = anclarCampoEnPrimeraFila(
 normalizedBirdMovements.filter((m) => (m.quantity ?? 0) > 0),
 'week_number',
 semanaDelEvento,
 )

 // `R-194`: la cadena de incubadora — recepción de huevos y despacho de pollitos son
 // `location_events`: llevan la granja/galpón reales (los del lote incubadora); los demás
 // eventos de la etapa incubadora conservan su mapeo anterior.
 const eventosUbicacionIncubadora = ['egg_reception_hatchery', 'chick_dispatch']
 let movimientosHuevo = anclarCampoEnPrimeraFila(
 (data.egg_movements || []).filter(m => (m.quantity ?? 0) > 0),
 // `R-220` · A17 (B-39): el «Peso prom.» declarado en la fila fértil viaja anclado a la
 // primera fila superviviente (mismo criterio que B-38).
 'avg_weight',
 (data.egg_movements?.[0] as any)?.avg_weight,
 )
 let almacenamiento = serializarAlmacenamientoDeHuevos(data.egg_storage_records)
 if (data.event_type === 'egg_reception_hatchery') {
 // El saldo de incubadora (BR-03) lee `egg_movements[fertile]`: la recepción escribe la
 // fila fértil con lo declarado como recibido (C-04) y `arrival_date` capturada (default `event_date`).
 const recibidos = Number((data.egg_storage_records?.[0] as any)?.eggs_received ?? 0)
 if (recibidos > 0 && !movimientosHuevo.some((m: any) => m?.egg_type === 'fertile')) {
 movimientosHuevo = [...movimientosHuevo, { egg_type: 'fertile', quantity: recibidos }]
 }
 almacenamiento = (almacenamiento.length > 0 ? almacenamiento : [{}]).map((r: any) => ({
 ...r,
 arrival_date: r?.arrival_date ?? data.event_date,
 }))
 }
 let paramsIncubadora = serializarParamsDeIncubadora(
 (data.hatchery_params || []).map(({ machine_type: _mt, ...hp }: any) => hp), // strip UI-only machine_type
 )
 if (selectedHatcheryId) {
 // `R-194` · B-22: la incubadora elegida viaja en la fila (`hatchery_id`); la tenencia la
 // verifica el servidor contra el catálogo de la empresa.
 if (paramsIncubadora.length === 0) paramsIncubadora = [{}]
 paramsIncubadora = [{ ...paramsIncubadora[0], hatchery_id: selectedHatcheryId },
 ...paramsIncubadora.slice(1)]
 }
 const payload: any = {
 ...data,
 farm_id: data.farm_id ?? ((isHatcheryStage && !eventosUbicacionIncubadora.includes(data.event_type)) ? undefined : derivedFarmId),
 house_id: data.house_id ?? derivedHouseId,
 observations,
 bird_movements: movimientosAves,
 egg_movements: movimientosHuevo,
 // `R-189 (F-01d)`: alimento e incubadora también se serializan — el `[{}]` de arranque nunca viaja.
 feed_movements: serializarMovimientosDeAlimento(data.feed_movements),
 hatchery_params: paramsIncubadora,
 inspection_details: [...(data.inspection_details || []), ...houseDetails],
 egg_storage_records: almacenamiento,
 house_inspections: undefined, // strip UI-only field
 }
 await api.post('/operations', payload)
 setResult({ ok: true, message: t('operations.saveSuccess') })
 toast.success(t('operations.saveSuccess'))
 setTimeout(() => navigate('/operations'), 1500)
 } catch (err: any) {
 // `R-189 (F-01)`: mensaje siempre renderizable (lista de validación de FastAPI incluida).
 const message = getErrorMessage(err, t('operations.saveError'))
 setResult({ ok: false, message })
 toast.error(message)
 } finally { setSubmitting(false) }
 }

 // ── M+F rows helper ──────────────────────────────────────────────
 const renderMFRows = (showWeight = true) => (
 <div>
 <div className={`grid ${showWeight ? 'grid-cols-1 sm:grid-cols-3' : 'grid-cols-1 sm:grid-cols-2'} px-1 py-2 border-b border-slate-200`}>
 <span className="text-sm font-semibold text-slate-500">{t('operations.sex', 'Sexo')}</span>
 <span className="text-sm font-semibold text-slate-500">{t('operations.quantity', 'Cantidad')}</span>
 {showWeight && <span className="text-sm font-semibold text-slate-500">{t('operations.avgWeight', 'Peso prom. (g)')}</span>}
 </div>
 {[
 { idx: 0, defaultSex: 'male', label: t('operations.males', 'Machos'), color: 'text-blue-700' },
 { idx: 1, defaultSex: 'female', label: t('operations.females', 'Hembras'), color: 'text-pink-700' },
 ].map(({ idx, defaultSex, label, color }) => (
 <div key={idx} className={`grid ${showWeight ? 'grid-cols-1 sm:grid-cols-3' : 'grid-cols-1 sm:grid-cols-2'} px-1 py-2.5 gap-2 items-center border-b border-slate-100 last:border-0`}>
 <div className="flex items-center gap-1.5">
 <input type="hidden" {...register(`bird_movements.${idx}.sex`)} defaultValue={defaultSex} />
 <span className={`text-sm font-semibold ${color}`}>{label}</span>
 </div>
 <input type="number" inputMode="decimal" min="0" {...register(`bird_movements.${idx}.quantity`, { valueAsNumber: true })}
 className={ic} />
 {showWeight && (
 <input type="number" inputMode="decimal" step="1" {...register(`bird_movements.${idx}.avg_weight`, { valueAsNumber: true })}
 className={ic} />
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
 <SearchSelect
 value={watch('cause_id' as any) ?? ''}
 onChange={(v) => setValue('cause_id' as any, v ? Number(v) : undefined)}
 items={mortalityCauses}
 placeholder={t('operations.selectCause', 'Seleccionar causa...')}

 renderLabel={(x: any) => x.name}
 />
 </div>
 <div>
 <label className={lc}>{t('operations.weekNumber', 'Semana')}</label>
 <input type="number" inputMode="decimal" min="1" {...register('bird_movements.0.week_number', { valueAsNumber: true })} className={ic} placeholder="1" />
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
 <SearchSelect
 value={watch('cull_cause_id' as any) ?? ''}
 onChange={(v) => setValue('cull_cause_id' as any, v ? Number(v) : undefined)}
 items={cullCauses}
 placeholder={t('operations.selectCause', 'Seleccionar causa...')}

 renderLabel={(x: any) => x.name}
 />
 </div>
 <div>
 <label className={lc}>{t('operations.weekNumber', 'Semana')}</label>
 <input type="number" inputMode="decimal" min="1" {...register('bird_movements.0.week_number', { valueAsNumber: true })} className={ic} placeholder="1" />
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
 <SearchSelect
 value={watch('vaccine_id' as any) ?? ''}
 onChange={(v) => setValue('vaccine_id' as any, v ? Number(v) : undefined)}
 items={vaccines}
 placeholder={t('operations.selectVaccine', 'Seleccionar vacuna...')}

 renderLabel={(x: any) => x.name}
 />
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
 <input type="number" inputMode="decimal" step="0.01" {...register('dosage_per_bird', { valueAsNumber: true })} className={ic} />
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
 <SearchSelect
 value={watch('medication_id' as any) ?? ''}
 onChange={(v) => setValue('medication_id' as any, v ? Number(v) : undefined)}
 items={medications}
 placeholder={t('operations.selectMedication', 'Seleccionar medicamento...')}

 renderLabel={(x: any) => x.name}
 />
 </div>
 <div>
 <label className={lc}>{t('operations.dosePerBird', 'Dosis por ave (mL/mg)')}</label>
 <input type="number" inputMode="decimal" step="0.001" {...register('dosage_per_bird', { valueAsNumber: true })} className={ic} />
 </div>
 <div>
 <label className={lc}>{t('operations.treatmentDays', 'Días de tratamiento')}</label>
 <input type="number" inputMode="decimal" min="1" {...register('treatment_days', { valueAsNumber: true })} className={ic} placeholder="5" />
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
 <input type="number" inputMode="decimal" min="1" {...register('bird_movements.0.week_number', { valueAsNumber: true })} className={ic} placeholder="1" />
 </div>
 <div>
 <label className={lc}>{t('operations.sampleSize', 'Aves pesadas')}</label>
 <input type="number" inputMode="decimal" min="1" {...register('sample_size', { valueAsNumber: true })} className={ic} placeholder="50" />
 </div>
 </div>
 {renderMFRows(true)}
 </div>
 )

 case 'bird_reception': {
 const sapOrderRef = watch('sap_document_ref' as any) ?? watch('extra_data.sap_order_ref' as any)
 const sapOrder = sapPurchaseOrders.find((o: any) =>
 identificadorDeOrdenSap(o) === sapOrderRef
 )
 const declaredQty = sapOrder?.quantity || (watch('extra_data.declared_quantity' as any) || 0)
 const declaredAvgM = sapOrder?.extra_data?.avg_weight_male || (watch('extra_data.declared_avg_weight_m' as any) || 0)
 const declaredAvgF = sapOrder?.extra_data?.avg_weight_female || (watch('extra_data.declared_avg_weight_f' as any) || 0)
 const dispatchDate = sapOrder?.extra_data?.dispatch_date || watch('extra_data.dispatch_date' as any) || ''
 const vendorName = sapOrder?.extra_data?.vendor_name || watch('extra_data.vendor_name' as any) || ''

 // Total alojado (Σ filas), solo informativo; la regla del cuadre (BR-20) y de la OC (BR-18) viven en el backend.
 const totalReceived = birdFields.reduce((sum, _, i) => {
 const qty = watch(`bird_movements.${i}.quantity` as any) || 0
 return sum + Number(qty)
 }, 0)

 return (
 <div className="space-y-4">
 {/* SAP Order info card */}
 {sapOrder && (
 <div className="bg-blue-50 border border-blue-100 rounded-lg p-3 text-sm space-y-1">
 <p className="font-semibold text-blue-800">{t('operations.sapOrderInfo', 'Información de la orden SAP')}</p>
 <p><strong>{t('operations.purchaseOrderAbbrev')}:</strong> {sapOrder.sap_code || sapOrder.ref_id} {vendorName ? `— ${vendorName}` : ''}</p>
 {sapOrder.description && <p className="text-slate-600">{sapOrder.description}</p>}
 <div className="grid grid-cols-1 sm:grid-cols-2 gap-1 mt-1">
 {declaredQty > 0 && <p><strong>{t('operations.declaredQty', 'Cantidad declarada')}:</strong> {declaredQty} aves</p>}
 {dispatchDate && <p><strong>{t('operations.dispatchDate', 'Fecha despacho')}:</strong> {dispatchDate}</p>}
 {declaredAvgM > 0 && <p><strong>{t('operations.declaredAvgWeightM', 'Peso prom. machos')}:</strong> {declaredAvgM}g</p>}
 {declaredAvgF > 0 && <p><strong>{t('operations.declaredAvgWeightF', 'Peso prom. hembras')}:</strong> {declaredAvgF}g</p>}
 </div>
 </div>
 )}

 {/* `GA-REM-021-B` · B01: cuadre de la recepción de reproductoras (Rec. §6). Solo aritmética informativa; la regla (BR-20) la aplica el backend. */}
 {/* `R-205`: visible por etapa derivada **o** por el lote (bird_type=breeder en recepción, C-02). */}
 {(stageFinal === 'breeder_rearing' || (eventType === 'bird_reception' && selectedLot?.bird_type === 'breeder')) && (() => {
 const dead = Number(watch('dead_on_arrival' as any) || 0)
 const rejected = Number(watch('rejected_on_arrival' as any) || 0)
 const received = Number(watch('received_total' as any) || 0)
 return (
 <div className="bg-slate-50 rounded-lg p-3 space-y-2">
 <p className="text-sm font-semibold text-slate-700">{t('operations.receptionReconciliation', 'Cuadre de la recepción')}</p>
 <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
 <div>
 <label className="text-xs font-medium text-slate-500">{t('operations.receivedTotal', 'Cantidad recibida (aves)')}</label>
 <input type="number" inputMode="decimal" min="1" step="1" {...register('received_total' as any, { valueAsNumber: true })} className={ic} />
 </div>
 <div>
 <label className="text-xs font-medium text-slate-500">{t('operations.deadOnArrival', 'Mortalidad al arribo')}</label>
 <input type="number" inputMode="decimal" min="0" step="1" {...register('dead_on_arrival' as any, { valueAsNumber: true })} className={ic} />
 </div>
 <div>
 <label className="text-xs font-medium text-slate-500">{t('operations.rejectedOnArrival', 'Rechazo')}</label>
 <input type="number" inputMode="decimal" min="0" step="1" {...register('rejected_on_arrival' as any, { valueAsNumber: true })} className={ic} />
 </div>
 </div>
 <div>
 {/* `R-168` (`GA-REM-021-C §C.2`): «Muestra tomada» (Rec. §6) es un dato de la recepción, en el campo de evento */}
 <label className="text-xs font-medium text-slate-500">{t('operations.sampleTaken', 'Muestra tomada (aves pesadas)')}</label>
 <input type="number" inputMode="decimal" min="1" step="1" {...register('sample_size', { valueAsNumber: true })} className={ic} />
 </div>
 <p className="text-xs text-slate-500">
 {t('operations.reconciliationHint', { placed: totalReceived, dead, rejected, sum: totalReceived + dead + rejected, received })}
 </p>
 </div>
 )
 })()}

 {/* Supplier & Breed — stacked on mobile, side-by-side on desktop */}
 <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
 <div>
 <label className={lc}>{t('operations.supplier', 'Proveedor')}</label>
 <SearchSelect
 value={watch('supplier_id' as any) ?? ''}
 onChange={(v) => setValue('supplier_id' as any, v ? Number(v) : undefined)}
 items={suppliers}
 placeholder={t('operations.selectSupplier', 'Seleccionar proveedor...')}

 renderLabel={(s: any) => s.name}
 />
 </div>
 <div>
 <label className={lc}>{t('operations.breed', 'Línea / Raza')}</label>
 <SearchSelect
 value={watch('bird_movements.0.breed_id' as any) ?? ''}
 onChange={(v) => setValue('bird_movements.0.breed_id' as any, v ? Number(v) : undefined)}
 items={breeds}
 placeholder={t('operations.selectBreed', 'Seleccionar línea...')}

 renderLabel={(b: any) => b.name}
 />
 </div>
 </div>

 {/* Per-house distribution */}
 <div className="bg-slate-50 rounded-lg p-3 space-y-3">
 <p className="text-sm font-semibold text-slate-700">{t('operations.houseDistribution', 'Distribución por galpón')}</p>
 {birdFields.map((field, i) => (
 <div key={field.id} className="space-y-2 pb-3 mb-2 border-b border-slate-200 last:border-0">
 <div className="flex items-center justify-between">
 <span className="text-xs font-semibold text-slate-500">{t('operations.house', 'Galpón')} {i + 1}</span>
 {i > 0 && (
 <button type="button" onClick={() => removeBird(i)}
 className="text-red-400 hover:text-red-600 p-0.5"><Trash2 size={14} /></button>
 )}
 </div>
 <div>
 <label className="text-xs font-medium text-slate-500">{t('operations.targetHouse', 'Galpón')}</label>
 <SearchSelect
 value={watch(`bird_movements.${i}.target_house_id` as any) ?? ''}
 onChange={(v) => setValue(`bird_movements.${i}.target_house_id` as any, v ? Number(v) : undefined)}
 items={farmHouses.length > 0 ? farmHouses : houses}
 placeholder={t('operations.selectHouse', 'Seleccionar galpón...')}

 renderLabel={(h: any) => `${h.name}${h.capacity ? ` (cap. ${h.capacity})` : ''}`}
 />
 </div>
 <div className="grid grid-cols-1 gap-2">
 <div>
 <label className="text-xs font-medium text-slate-500">{t('operations.sex', 'Sexo')}</label>
 <select {...register(`bird_movements.${i}.sex`)} className={ic}>
 <option value="male">{t('operations.male', 'Macho')}</option>
 <option value="female">{t('operations.female', 'Hembra')}</option>
 <option value="mixed">{t('operations.mixed', 'Mixto')}</option>
 </select>
 </div>
 <div>
 <label className="text-xs font-medium text-slate-500">{t('operations.quantity', 'Cantidad')}</label>
 <input type="number" inputMode="decimal" min="0" {...register(`bird_movements.${i}.quantity`, { valueAsNumber: true })} className={ic} />
 </div>
 <div>
 <label className="text-xs font-medium text-slate-500">{t('operations.avgWeightG', 'Peso prom. (g)')}</label>
 <input type="number" inputMode="decimal" step="0.1" min="0" {...register(`bird_movements.${i}.avg_weight`, { valueAsNumber: true })} className={ic} />
 </div>
 </div>
 </div>
 ))}
 <button type="button" onClick={() => appendBird({ sex: 'female' })}
 className="flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-800 font-medium">
 <Plus size={14} /> {t('operations.addHouse', 'Añadir galpón')}
 </button>
 </div>


 </div>
 )}

 case 'bird_distribution': return (
 <div className="space-y-3">
 <p className="text-xs text-slate-500">{t('operations.distributionHint', 'Confirma la distribución de la recepción o registra movimiento de aves entre galpones')}</p>
 {birdFields.map((field, i) => (
 <div key={field.id} className="space-y-2 pb-3 mb-2 border-b border-slate-200 last:border-0">
 <div className="flex items-center justify-between">
 <span className="text-xs font-semibold text-slate-500">{t('operations.house', 'Galpón')} {i + 1}</span>
 {i > 0 && (
 <button type="button" onClick={() => removeBird(i)}
 className="text-red-400 hover:text-red-600 p-0.5"><Trash2 size={14} /></button>
 )}
 </div>
 <div>
 <label className="text-xs font-medium text-slate-500">{t('operations.sourceHouse', 'Galpón origen (si hubo movimiento)')}</label>
 <SearchSelect
 value={watch(`bird_movements.${i}.source_house_id` as any) ?? ''}
 onChange={(v) => setValue(`bird_movements.${i}.source_house_id` as any, v ? Number(v) : undefined)}
 items={farmHouses.length > 0 ? farmHouses : houses}
 placeholder={t('operations.selectSourceHouse', 'Opcional — solo si moviste aves...')}

 renderLabel={(h: any) => `${h.name}${h.capacity ? ` (cap. ${h.capacity})` : ''}`}
 />
 </div>
 <div>
 <label className="text-xs font-medium text-slate-500">{t('operations.targetHouse', 'Galpón destino')}</label>
 <SearchSelect
 value={watch(`bird_movements.${i}.target_house_id` as any) ?? ''}
 onChange={(v) => setValue(`bird_movements.${i}.target_house_id` as any, v ? Number(v) : undefined)}
 items={farmHouses.length > 0 ? farmHouses : houses}
 placeholder={t('operations.selectHouse', 'Seleccionar galpón...')}

 renderLabel={(h: any) => `${h.name}${h.capacity ? ` (cap. ${h.capacity})` : ''}`}
 />
 </div>
 <div className="grid grid-cols-1 gap-2">
 <div>
 <label className="text-xs font-medium text-slate-500">{t('operations.sex', 'Sexo')}</label>
 <select {...register(`bird_movements.${i}.sex`)} className={ic}>
 <option value="male">{t('operations.male', 'Macho')}</option>
 <option value="female">{t('operations.female', 'Hembra')}</option>
 <option value="mixed">{t('operations.mixed', 'Mixto')}</option>
 </select>
 </div>
 <div>
 <label className="text-xs font-medium text-slate-500">{t('operations.quantity', 'Cantidad')}</label>
 <input type="number" inputMode="decimal" min="0" {...register(`bird_movements.${i}.quantity`, { valueAsNumber: true })} className={ic} />
 </div>
 <div>
 <label className="text-xs font-medium text-slate-500">{t('operations.avgWeightG', 'Peso prom. (g)')}</label>
 <input type="number" inputMode="decimal" step="0.1" min="0" {...register(`bird_movements.${i}.avg_weight`, { valueAsNumber: true })} className={ic} />
 </div>
 </div>
 </div>
 ))}
 <button type="button" onClick={() => appendBird({ sex: 'mixed' })}
 className="flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-800 font-medium">
 <Plus size={14} /> {t('operations.addHouse', 'Añadir galpón')}
 </button>
 </div>
 )

 case 'bird_transfer': return (
 <div className="space-y-4">
 <div className="flex flex-col gap-3 lg:grid lg:grid-cols-2">
 <div>
 <label className={lc}>{t('operations.sourceHouse', 'Galpón origen')}</label>
 <SearchSelect
 value={watch('bird_movements.0.source_house_id' as any) ?? ''}
 onChange={(v) => setValue('bird_movements.0.source_house_id' as any, v ? Number(v) : undefined)}
 items={farmHouses.length > 0 ? farmHouses : houses}
 placeholder={t('operations.selectHouse', 'Seleccionar galpón...')}

 renderLabel={(h: any) => `${h.name}${h.capacity ? ` (cap. ${h.capacity})` : ''}`}
 />
 </div>
 <div>
 <label className={lc}>{t('operations.targetHouse', 'Galpón destino')}</label>
 <SearchSelect
 value={watch('bird_movements.0.target_house_id' as any) ?? ''}
 onChange={(v) => setValue('bird_movements.0.target_house_id' as any, v ? Number(v) : undefined)}
 items={farmHouses.length > 0 ? farmHouses : houses}
 placeholder={t('operations.selectHouse', 'Seleccionar galpón...')}

 renderLabel={(h: any) => `${h.name}${h.capacity ? ` (cap. ${h.capacity})` : ''}`}
 />
 </div>
 </div>
 {renderMFRows(true)}
 </div>
 )

 case 'bird_exit': {
 const transportId = watch('transport_id' as any)
 return (
 <div className="space-y-4">
 <p className="text-xs text-slate-500">{t('operations.birdExitHint', 'Registra la salida de aves para traslado o cierre de ciclo de cría. Si las aves no se mueven físicamente, deja los campos de destino y transporte vacíos para el cierre de ciclo.')}</p>

 {/* Destination & Transport */}
 <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
 <div>
 <label className={lc}>{t('operations.destinationFarm', 'Granja destino')}</label>
 <SearchSelect
 value={watch('destination_farm_id' as any) ?? ''}
 onChange={(v) => setValue('destination_farm_id' as any, v ? Number(v) : undefined)}
 items={farms}
 placeholder={t('operations.selectFarm', 'Seleccionar granja...')}

 renderLabel={(f: any) => `${f.name}${f.code ? ` (${f.code})` : ''}`}
 />
 </div>
 <div>
 <label className={lc}>{t('operations.destinationPlant', 'Planta procesadora')}</label>
 <SearchSelect
 value={watch('destination_plant_id' as any) ?? ''}
 onChange={(v) => setValue('destination_plant_id' as any, v ? Number(v) : undefined)}
 items={processingPlants}
 placeholder={t('operations.selectType', 'Seleccionar planta...')}

 renderLabel={(p: any) => p.name}
 />
 </div>
 <div>
 <label className={lc}>{t('operations.transport', 'Transporte')}</label>
 <SearchSelect
 value={transportId ?? ''}
 onChange={(v) => setValue('transport_id' as any, v ? Number(v) : undefined)}
 items={transports}
 placeholder={t('operations.selectTransport', 'Seleccionar transporte...')}

 renderLabel={(x: any) => `${x.plate} — ${x.name}`}
 />
 </div>
 <div>
 <label className={lc}>{t('operations.sapOrderRef', 'Ref. OC SAP')}</label>
 {/* `GA-TD-014` / `GA-REM-035 AC13`. El selector escribía en `extra_data.sap_order_ref`
 y el campo tipado `sap_document_ref` quedaba nulo, de modo que `BR-18` salía por su
 primera línea y el comparativo SAP salía vacío. Se escriben ambos: el tipado, que es
 el que el dominio mira, y el de `extra_data`, que otras partes del formulario leen
 para mostrar la cantidad declarada. */}
 <SearchSelect
 value={(() => { const o = sapPurchaseOrders.find((x: any) => identificadorDeOrdenSap(x) === watch('sap_document_ref' as any)); return o ? String(o.id) : '' })()}
 onChange={(v) => {
 const order = sapPurchaseOrders.find((o: any) => String(o.id) === String(v))
 // `R-209`: siempre el código canónico; sin código ⇒ ausente (nunca `String(id)`).
 const referencia = order ? identificadorDeOrdenSap(order) : ''
 setValue('sap_document_ref' as any, (referencia || undefined) as any)
 setValue('extra_data.sap_order_ref' as any, (referencia || undefined) as any)
 }}
 items={sapPurchaseOrders}
 placeholder={t('operations.selectSapOrder', 'Seleccionar orden SAP...')}

 renderLabel={(o: any) => `${o.doc_number || o.ref_id || o.sap_code || o.id}${o.extra_data?.vendor_name ? ` — ${o.extra_data.vendor_name}` : ''}`}
 />
 </div>
 </div>

 {/* ── Transport inspection (only when transport is selected) ── */}
 {transportId && (
 <div className="bg-amber-50 border border-amber-100 rounded-lg p-3 space-y-3">
 <p className="text-sm font-semibold text-amber-800">{t('operations.transportInspection', 'Inspección del transporte')}</p>
 <div className="grid grid-cols-1 gap-3">
 <div>
 <label className="text-xs font-medium text-amber-700">{t('operations.cageCondition', 'Estado de jaulas')}</label>
 <select {...register('extra_data.transport_cage_condition' as any)} className="w-full h-10 px-2 border border-amber-200 rounded-lg text-sm bg-white">
 <option value="">{t('operations.selectType', 'Seleccionar...')}</option>
 <option value="good">{t('operations.good', 'Bueno')}</option>
 <option value="regular">{t('operations.regular', 'Regular')}</option>
 <option value="bad">{t('operations.bad', 'Malo')}</option>
 </select>
 </div>
 <div>
 <label className="text-xs font-medium text-amber-700">{t('operations.densityBirdsM2', 'Densidad (aves/m²)')}</label>
 <input type="number" inputMode="decimal" step="0.1" min="0" {...register('extra_data.transport_density' as any, { valueAsNumber: true })} className="w-full h-10 px-2 border border-amber-200 rounded-lg text-sm bg-white" />
 </div>
 <div>
 <label className="text-xs font-medium text-amber-700">{t('operations.temperature', 'Temperatura (°C)')}</label>
 <input type="number" inputMode="decimal" step="0.1" min="0" max="50" {...register('extra_data.transport_temperature' as any, { valueAsNumber: true })} className="w-full h-10 px-2 border border-amber-200 rounded-lg text-sm bg-white" placeholder="22" />
 </div>
 <div>
 <label className="text-xs font-medium text-amber-700">{t('operations.ventilation', 'Ventilación')}</label>
 <select {...register('extra_data.transport_ventilation' as any)} className="w-full h-10 px-2 border border-amber-200 rounded-lg text-sm bg-white">
 <option value="">{t('operations.selectType', 'Seleccionar...')}</option>
 <option value="good">{t('operations.good', 'Buena')}</option>
 <option value="regular">{t('operations.regular', 'Regular')}</option>
 <option value="bad">{t('operations.bad', 'Mala')}</option>
 </select>
 </div>
 <div>
 <label className="text-xs font-medium text-amber-700">{t('operations.hygiene', 'Higiene del vehículo')}</label>
 <select {...register('extra_data.transport_hygiene' as any)} className="w-full h-10 px-2 border border-amber-200 rounded-lg text-sm bg-white">
 <option value="">{t('operations.selectType', 'Seleccionar...')}</option>
 <option value="good">{t('operations.good', 'Buena')}</option>
 <option value="regular">{t('operations.regular', 'Regular')}</option>
 <option value="bad">{t('operations.bad', 'Mala')}</option>
 </select>
 </div>
 <div>
 <label className="text-xs font-medium text-amber-700">{t('operations.durationMin', 'Duración viaje (min)')}</label>
 <input type="number" inputMode="decimal" min="0" {...register('extra_data.transport_duration_min' as any, { valueAsNumber: true })} className="w-full h-10 px-2 border border-amber-200 rounded-lg text-sm bg-white" placeholder="30" />
 </div>
 </div>
 </div>
 )}

 {/* Same-house transition note */}
 {!transportId && (
 <div className="bg-blue-50 border border-blue-100 rounded-lg p-3 text-xs text-blue-700">
 {t('operations.sameHouseTransition', 'Sin transporte ni destino = cierre de ciclo de cría e inicio de producción en el mismo galpón. Las aves saldrán y reingresarán al mismo lote para marcar la transición.')}
 </div>
 )}

 {/* M/F rows */}
 {renderMFRows(true)}
 </div>
 )}

 case 'water_consumption': return (
 <div className="flex flex-col gap-3 lg:grid lg:grid-cols-2">
 <div>
 <label className={lc}>{t('operations.waterLiters', 'Consumo de agua (L)')}</label>
 <input type="number" inputMode="decimal" step="0.1" min="0.1" {...register('water_liters', { valueAsNumber: true })} className={ic} />
 </div>
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
 <input type="number" inputMode="decimal" min="1" {...register('feed_movements.0.week_number', { valueAsNumber: true })} className={ic} placeholder="1" />
 </div>
 </div>
 <div className="flex flex-col gap-3 lg:grid lg:grid-cols-3">
 <div>
 <label className={lc}>{t('operations.quantityKg', 'Cantidad (kg)')}</label>
 <input type="number" inputMode="decimal" step="0.1" min="0" {...register('feed_movements.0.quantity_kg', { valueAsNumber: true })} className={ic} />
 </div>
 <div>
 <label className={lc}>{t('operations.sacks', 'Sacos / bultos')}</label>
 <input type="number" inputMode="decimal" min="0" {...register('feed_movements.0.sacks_count', { valueAsNumber: true })} className={ic} />
 </div>
 <div>
 <label className={lc}>{t('operations.sapOrder', 'Orden SAP')}</label>
 <SearchSelect
 value={(() => { const o = sapOrders.find((x: any) => identificadorDeOrdenSap(x) === watch('feed_movements.0.sap_order_id' as any)); return o ? String(o.id) : '' })()}
 onChange={(v) => {
 const order = sapOrders.find((o: any) => String(o.id) === String(v))
 // `R-209`: la OT de alimento viaja por su código — nunca por el id de UI.
 const referencia = order ? identificadorDeOrdenSap(order) : ''
 setValue('feed_movements.0.sap_order_id' as any, (referencia || undefined) as any)
 }}
 items={sapOrders}
 placeholder={t('operations.noOrder', 'Sin orden')}

 renderLabel={(s: any) => s.sap_code || s.reference || s.id}
 />
 </div>
 </div>
 </div>
 )

 case 'egg_collection':
 case 'egg_classification':
 case 'egg_reception_classification': {
 const eggTypes = [
 { key: 'fertile', label: t('operations.fertile', 'Fértiles') },
 { key: 'dirty', label: t('operations.dirty', 'Sucios') },
 { key: 'broken', label: t('operations.broken', 'Rotos') },
 { key: 'infertile', label: t('operations.infertile', 'Infértiles') },
 { key: 'discarded', label: t('operations.discarded', 'Descartados') },
 ]
 return (
 <div className="space-y-4">
 <div>
 <div className="grid grid-cols-1 sm:grid-cols-2 px-1 py-2 border-b border-slate-200">
 <span className="text-xs font-semibold text-slate-500">{t('operations.eggType', 'Tipo de huevo')}</span>
 <span className="text-xs font-semibold text-slate-500">{t('operations.quantity', 'Cantidad')}</span>
 </div>
 {eggTypes.map(({ key, label }, i) => (
 <div key={key} className="grid grid-cols-1 sm:grid-cols-2 px-1 py-2.5 gap-2 items-center border-b border-slate-100 last:border-0">
 <div>
 <input type="hidden" {...register(`egg_movements.${i}.egg_type`)} defaultValue={key} />
 <span className="text-sm text-slate-700">{label}</span>
 </div>
 <input type="number" inputMode="decimal" min="0" {...register(`egg_movements.${i}.quantity`, { valueAsNumber: true })} className={ic} />
 </div>
 ))}
 </div>
 {eventType === 'egg_collection' && (
 <div className="flex flex-col gap-3">
 <label className="text-sm font-medium text-slate-600">{t('operations.avgWeight', 'Peso prom. huevo (g)')}</label>
 <input type="number" inputMode="decimal" step="0.1" min="0" {...register('egg_movements.0.avg_weight', { valueAsNumber: true })} className={ic} placeholder="60.0" />
 </div>
 )}
 </div>
 )
 }

 case 'egg_dispatch': {
 const transportId = watch('transport_id' as any)
 return (
 <div className="space-y-4">
 <p className="text-xs text-slate-500">{t('operations.eggDispatchHint', 'Registra el despacho de huevos a la incubadora con la orden de traslado SAP y los datos del transporte')}</p>

 {/* Incubator & Transport */}
 <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
 <div>
 <label className={lc}>{t('operations.destinationIncubator', 'Incubadora destino')}</label>
 <SearchSelect
 value={watch('hatchery_params.0.incubator_id' as any) ?? ''}
 onChange={(v) => setValue('hatchery_params.0.incubator_id' as any, v ? Number(v) : undefined)}
 items={incubators}
 placeholder={t('operations.selectIncubator', 'Seleccionar incubadora...')}

 renderLabel={(x: any) => `${x.name}${x.code ? ` (${x.code})` : ''}`}
 />
 </div>
 <div>
 <label className={lc}>{t('operations.transport', 'Transporte')}</label>
 <SearchSelect
 value={transportId ?? ''}
 onChange={(v) => setValue('transport_id' as any, v ? Number(v) : undefined)}
 items={transports}
 placeholder={t('operations.selectTransport', 'Seleccionar transporte...')}

 renderLabel={(x: any) => `${x.plate} — ${x.name}`}
 />
 </div>
 </div>

 {/* ── Transport inspection (only when transport is selected) ── */}
 {transportId && (
 <div className="bg-amber-50 border border-amber-100 rounded-lg p-3 space-y-3">
 <p className="text-sm font-semibold text-amber-800">{t('operations.transportInspection', 'Inspección del transporte')}</p>
 <div className="grid grid-cols-1 gap-3">
 <div>
 <label className="text-xs font-medium text-amber-700">{t('operations.cageCondition', 'Estado de jaulas')}</label>
 <select {...register('extra_data.transport_cage_condition' as any)} className="w-full h-10 px-2 border border-amber-200 rounded-lg text-sm bg-white">
 <option value="">{t('operations.selectType', 'Seleccionar...')}</option>
 <option value="good">{t('operations.good', 'Bueno')}</option>
 <option value="regular">{t('operations.regular', 'Regular')}</option>
 <option value="bad">{t('operations.bad', 'Malo')}</option>
 </select>
 </div>
 <div>
 <label className="text-xs font-medium text-amber-700">{t('operations.eggDensity', 'Huevos por bandeja')}</label>
 <input type="number" inputMode="decimal" step="0.1" min="0" {...register('extra_data.transport_density' as any, { valueAsNumber: true })} className="w-full h-10 px-2 border border-amber-200 rounded-lg text-sm bg-white" />
 </div>
 <div>
 <label className="text-xs font-medium text-amber-700">{t('operations.temperature', 'Temperatura (°C)')}</label>
 <input type="number" inputMode="decimal" step="0.1" min="0" max="50" {...register('extra_data.transport_temperature' as any, { valueAsNumber: true })} className="w-full h-10 px-2 border border-amber-200 rounded-lg text-sm bg-white" placeholder="18" />
 </div>
 <div>
 <label className="text-xs font-medium text-amber-700">{t('operations.ventilation', 'Ventilación')}</label>
 <select {...register('extra_data.transport_ventilation' as any)} className="w-full h-10 px-2 border border-amber-200 rounded-lg text-sm bg-white">
 <option value="">{t('operations.selectType', 'Seleccionar...')}</option>
 <option value="good">{t('operations.good', 'Buena')}</option>
 <option value="regular">{t('operations.regular', 'Regular')}</option>
 <option value="bad">{t('operations.bad', 'Mala')}</option>
 </select>
 </div>
 <div>
 <label className="text-xs font-medium text-amber-700">{t('operations.hygiene', 'Higiene del vehículo')}</label>
 <select {...register('extra_data.transport_hygiene' as any)} className="w-full h-10 px-2 border border-amber-200 rounded-lg text-sm bg-white">
 <option value="">{t('operations.selectType', 'Seleccionar...')}</option>
 <option value="good">{t('operations.good', 'Buena')}</option>
 <option value="regular">{t('operations.regular', 'Regular')}</option>
 <option value="bad">{t('operations.bad', 'Mala')}</option>
 </select>
 </div>
 <div>
 <label className="text-xs font-medium text-amber-700">{t('operations.durationMin', 'Duración viaje (min)')}</label>
 <input type="number" inputMode="decimal" min="0" {...register('extra_data.transport_duration_min' as any, { valueAsNumber: true })} className="w-full h-10 px-2 border border-amber-200 rounded-lg text-sm bg-white" placeholder="30" />
 </div>
 </div>
 </div>
 )}

 {/* Egg type rows */}
 <div>
 <div className="grid grid-cols-1 sm:grid-cols-2 px-1 py-2 border-b border-slate-200">
 <span className="text-xs font-semibold text-slate-500">{t('operations.eggType', 'Tipo de huevo')}</span>
 <span className="text-xs font-semibold text-slate-500">{t('operations.quantity', 'Cantidad')}</span>
 </div>
 {/* `GA-REM-005-F` · `R-172` · `RR-17`: a la incubadora solo se despacha huevo fértil (`Bases` p.7-9,
     `docs/02 §3.6.4/§3.7.1`); el backend rechaza cualquier otra fila (`BR-02`). */}
 {[
 { key: 'fertile', label: t('operations.fertile', 'Fértiles') },
 ].map(({ key, label }, i) => (
 <div key={key} className="grid grid-cols-1 sm:grid-cols-2 px-1 py-2.5 gap-2 items-center border-b border-slate-100 last:border-0">
 <div>
 <input type="hidden" {...register(`egg_movements.${i}.egg_type`)} defaultValue={key} />
 <span className="text-sm text-slate-700">{label}</span>
 </div>
 <input type="number" inputMode="decimal" min="0" {...register(`egg_movements.${i}.quantity`, { valueAsNumber: true })} className={ic} />
 </div>
 ))}
 </div>
 </div>
 )
 }

 case 'egg_reception_hatchery': return (
 <div className="space-y-4">
 <p className="text-xs text-slate-500">{t('operations.eggReceptionHint', 'Registra la recepción de huevos en la incubadora. Referencia la orden de traslado SAP del despacho.')}</p>
 <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
 <div>
 <label className={lc}>{t('operations.sourceOriginFarm', 'Granja de origen')}</label>
 <SearchSelect
 value={watch('extra_data.source_farm_id' as any) ?? ''}
 onChange={(v) => setValue('extra_data.source_farm_id' as any, v ? Number(v) : undefined)}
 items={farms}
 placeholder={t('operations.selectFarm', 'Seleccionar granja...')}

 renderLabel={(f: any) => `${f.name}${f.code ? ` (${f.code})` : ''}`}
 />
 </div>
 <div>
 <label className={lc}>{t('operations.transport', 'Transporte')}</label>
 <SearchSelect
 value={watch('transport_id' as any) ?? ''}
 onChange={(v) => setValue('transport_id' as any, v ? Number(v) : undefined)}
 items={transports}
 placeholder={t('operations.selectTransport', 'Seleccionar...')}

 renderLabel={(x: any) => `${x.plate} — ${x.name}`}
 />
 </div>
 <div>
 <label className={lc}>{t('operations.dispatchOrder', 'No. de orden de despacho')}</label>
 <input {...register('extra_data.dispatch_order' as any)} className={ic} placeholder="D-2024-001" />
 </div>
 <div>
 <label className={lc}>{t('operations.quantity', 'Huevos recibidos')}</label>
 <input type="number" inputMode="decimal" min="0" {...register('egg_storage_records.0.eggs_received', { valueAsNumber: true })} className={ic} />
 </div>
 <div>
 <label className={lc}>{t('operations.tempTransport', 'Temp. transporte (°C)')}</label>
 <input type="number" inputMode="decimal" step="0.1" {...register('egg_storage_records.0.transport_temp_c', { valueAsNumber: true })} className={ic} placeholder="15.0" />
 </div>
 <div>
 <label className={lc}>{t('operations.durationTransport', 'Duración transporte (min)')}</label>
 <input type="number" inputMode="decimal" min="0" {...register('egg_storage_records.0.transport_duration_min', { valueAsNumber: true })} className={ic} placeholder="60" />
 </div>
 <div>
 <label className={lc}>{t('operations.storageTemp', 'Temp. almacén (°C)')}</label>
 <input type="number" inputMode="decimal" step="0.1" {...register('egg_storage_records.0.storage_temp_c', { valueAsNumber: true })} className={ic} placeholder="15.0" />
 </div>
 <div>
 <label className={lc}>{t('operations.storageHumidity', 'Humedad almacén (%)')}</label>
 <input type="number" inputMode="decimal" step="0.1" {...register('egg_storage_records.0.storage_humidity_pct', { valueAsNumber: true })} className={ic} placeholder="75" />
 </div>
 </div>
 </div>
 )

 case 'farm_inspection': {
 const EQUIPMENT_TYPES = [
 'bebedero', 'comedero', 'ventilador', 'calefactor',
 'nebulizador', 'iluminación', 'cortina', 'extractor', 'otro',
 ]
 return (
 <div className="space-y-4">
 <p className="text-xs text-slate-500">{t('operations.inspectionPerHouse', 'Registra T°, H° y estado de cama por cada galpón inspeccionado')}</p>
 {houseInspFields.map((field, i) => {
 const eqCount = watch(`house_inspections.${i}.equipment_count` as any) || 0
 return (
 <div key={field.id} className="space-y-3 pb-4 mb-3 border-b border-slate-200 last:border-0">
 <div className="flex items-center justify-between mb-1">
 <span className="text-sm font-semibold text-slate-600">{t('operations.house', 'Galpón')} {i + 1}</span>
 {i > 0 && (
 <button type="button" onClick={() => removeHouseInsp(i)}
 className="text-red-400 hover:text-red-600 p-1"><Trash2 size={16} /></button>
 )}
 </div>
 {/* House selector — SearchSelect for large farm lists */}
 <div>
 <label className={lc}>{t('operations.selectHouse', 'Galpón')}</label>
 <SearchSelect
 value={watch(`house_inspections.${i}.house_id` as any) ?? ''}
 onChange={(v) => setValue(`house_inspections.${i}.house_id` as any, v ? Number(v) : undefined as any)}
 items={farmHouses.length > 0 ? farmHouses : houses}
 placeholder={t('operations.selectHouse', 'Seleccionar galpón...')}

 renderLabel={(h: any) => `${h.name}${h.capacity ? ` (cap. ${h.capacity})` : ''}`}
 />
 </div>
 {/* T° and H° row */}
 <div className="flex flex-col gap-3">
 <div>
 <label className={lc}>{t('operations.tempC', 'Temperatura (°C)')}</label>
 <input type="number" inputMode="decimal" step="0.1" min="0" max="60"
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
 <input type="number" inputMode="decimal" step="0.1" min="0" max="100"
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
 {/* ── Equipment items per house ── */}
 <div className="bg-slate-50 rounded-lg p-3 space-y-3">
 <label className={lc}>{t('operations.equipmentCount', '¿Cuántos equipos inspeccionar?')}</label>
 <input type="number" inputMode="decimal" min="0" max="20"
 {...register(`house_inspections.${i}.equipment_count`, { valueAsNumber: true })}
 className={ic} />
 {Array.from({ length: Math.min(eqCount, 20) }).map((_, j) => (
 <div key={j} className="flex items-start gap-2 pl-2 border-l-2 border-blue-200">
 <span className="text-xs font-bold text-blue-500 mt-3 shrink-0 w-5">{j + 1}</span>
 <div className="flex-1 space-y-2">
 <select {...register(`house_inspections.${i}.equipment_items.${j}.equipment_type`)} className={ic}>
 <option value="">{t('operations.selectEquipment', 'Tipo de equipo...')}</option>
 {EQUIPMENT_TYPES.map(eq => (
 <option key={eq} value={eq}>{t(`operations.equipment.${eq}`, eq.charAt(0).toUpperCase() + eq.slice(1))}</option>
 ))}
 </select>
 <input type="text"
 {...register(`house_inspections.${i}.equipment_items.${j}.observation`)}
 className={ic}
 placeholder={t('operations.equipmentObservation', 'Observación del equipo...')} />
 </div>
 </div>
 ))}
 {eqCount > 0 && (
 <p className="text-xs text-slate-400">{t('operations.equipmentHint', 'Selecciona el tipo de equipo y registra su estado para cada uno')}</p>
 )}
 </div>
 </div>
 )})}
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
 <SearchSelect
 value={watch('transport_id' as any) ?? ''}
 onChange={(v) => setValue('transport_id' as any, v ? Number(v) : undefined)}
 items={transports}
 placeholder={t('operations.selectTransport', 'Seleccionar...')}

 renderLabel={(x: any) => `${x.plate} — ${x.name}`}
 />
 </div>
 {params.map((param, i) => (
 <div key={param.key} className="flex flex-wrap items-center gap-3">
 <input type="hidden" {...register(`inspection_details.${i}.parameter`)} defaultValue={param.key} />
 <span className="text-sm text-slate-600 w-full sm:w-44 shrink-0">{param.label}</span>
 {param.numeric ? (
 <input type="number" inputMode="decimal" step="0.1" {...register(`inspection_details.${i}.value`)}
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
 <p className="text-xs text-slate-500">{t('operations.addMachineRows', 'Registra los parámetros de cada máquina (incubadora o nacedora)')}</p>
 {incubatorFields.map((field, i) => {
 const machineType = watch(`hatchery_params.${i}.machine_type` as any)
 return (
 <div key={field.id} className="relative space-y-3 pb-4 mb-3 border-b border-slate-200 last:border-0">{/* `R-220` · B9 (F G-22): ancestro posicionado del botón eliminar */}
 <p className="text-sm font-semibold text-slate-600">{t('operations.machine', 'Máquina')} {i + 1}</p>
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
 ? (
 <SearchSelect
 value={watch(`hatchery_params.${i}.hatcher_id` as any) ?? ''}
 onChange={(v) => setValue(`hatchery_params.${i}.hatcher_id` as any, v ? Number(v) : undefined)}
 items={hatchers}
 placeholder={t('operations.selectHatcher', 'Seleccionar nacedora...')}

 renderLabel={(x: any) => `${x.name}${x.code ? ` (${x.code})` : ''}`}
 />
 )
 : (
 <SearchSelect
 value={watch(`hatchery_params.${i}.incubator_id` as any) ?? ''}
 onChange={(v) => setValue(`hatchery_params.${i}.incubator_id` as any, v ? Number(v) : undefined)}
 items={incubators}
 placeholder={t('operations.selectIncubator', 'Seleccionar incubadora...')}

 renderLabel={(x: any) => `${x.name}${x.code ? ` (${x.code})` : ''}`}
 />
 )
 }
 </div>
 <div>
 <label className={lc}>{t('operations.temp', 'T° (°C)')}</label>
 <input type="number" inputMode="decimal" step="0.1" {...register(`hatchery_params.${i}.temperature`, { valueAsNumber: true })} className={ic} placeholder="37.5" />
 {(() => {
 const v = watch(`hatchery_params.${i}.temperature` as any)
 const [tMin, tMax] = machineType === 'hatcher' ? HATCHER_TEMP_RANGE : INCUBATOR_TEMP_RANGE
 return <RangeIndicator value={v} min={tMin} max={tMax} unit="°C" />
 })()}
 </div>
 <div>
 <label className={lc}>{t('operations.humidity', 'H° (%)')}</label>
 <input type="number" inputMode="decimal" step="0.1" min="0" max="100" {...register(`hatchery_params.${i}.humidity`, { valueAsNumber: true })} className={ic} placeholder="56" />
 {(() => {
 const v = watch(`hatchery_params.${i}.humidity` as any)
 const [hMin, hMax] = machineType === 'hatcher' ? HATCHER_HUM_RANGE : INCUBATOR_HUM_RANGE
 return <RangeIndicator value={v} min={hMin} max={hMax} unit="%" />
 })()}
 </div>
 <div>
 <label className={lc}>{t('operations.co2', 'CO₂ (%)')}</label>
 <input type="number" inputMode="decimal" step="0.01" min="0" {...register(`hatchery_params.${i}.co2`, { valueAsNumber: true })} className={ic} placeholder="0.50" />
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
 <SearchSelect
 value={watch('hatchery_params.0.incubator_id' as any) ?? ''}
 onChange={(v) => setValue('hatchery_params.0.incubator_id' as any, v ? Number(v) : undefined)}
 items={incubators}
 placeholder={t('operations.selectIncubator', 'Seleccionar incubadora...')}

 renderLabel={(x: any) => `${x.name}${x.code ? ` (${x.code})` : ''}`}
 />
 </div>
 <div>
 <label className={lc}>{t('operations.quantityLoaded', 'Cantidad cargada')}</label>
 <input type="number" inputMode="decimal" min="0" {...register('hatchery_params.0.quantity_loaded', { valueAsNumber: true })} className={ic} />
 </div>
 <div>
 <label className={lc}>{t('operations.temp', 'Temperatura (°C)')}</label>
 <input type="number" inputMode="decimal" step="0.1" {...register('hatchery_params.0.temperature', { valueAsNumber: true })} className={ic} placeholder="37.5" />
 </div>
 <div>
 <label className={lc}>{t('operations.humidity', 'Humedad (%)')}</label>
 <input type="number" inputMode="decimal" step="0.1" {...register('hatchery_params.0.humidity', { valueAsNumber: true })} className={ic} placeholder="55" />
 </div>
 <div>
 <label className={lc}>{t('operations.co2', 'CO₂ (%)')}</label>
 <input type="number" inputMode="decimal" step="0.01" {...register('hatchery_params.0.co2', { valueAsNumber: true })} className={ic} placeholder="0.5" />
 </div>
 <div className="flex items-center gap-2 pt-5">
 <input type="checkbox" id="turning" {...register('hatchery_params.0.turning')}
 className="h-4 w-4 rounded border-slate-300 text-blue-600" />
 <label htmlFor="turning" className="text-sm text-slate-700">{t('operations.turning', 'Volteo activo')}</label>
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
 <input type="number" inputMode="decimal" min="1" {...register('bird_movements.0.week_number', { valueAsNumber: true })} className={ic} placeholder="10" />
 <input type="hidden" {...register('bird_movements.0.sex')} defaultValue="mixed" />
 </div>
 <div>
 {types.map(({ key, label }, i) => (
 <div key={key} className="grid grid-cols-1 sm:grid-cols-2 px-1 py-2.5 gap-2 items-center border-b border-slate-100 last:border-0">
 <div>
 <input type="hidden" {...register(`egg_movements.${i}.egg_type`)} defaultValue={key} />
 <span className="text-sm text-slate-700">{label}</span>
 </div>
 <input type="number" inputMode="decimal" min="0" {...register(`egg_movements.${i}.quantity`, { valueAsNumber: true })} className={ic} />
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
 <SearchSelect
 value={watch('hatchery_params.0.hatcher_id' as any) ?? ''}
 onChange={(v) => setValue('hatchery_params.0.hatcher_id' as any, v ? Number(v) : undefined)}
 items={hatchers}
 placeholder={t('operations.selectHatcher', 'Seleccionar nacedora...')}

 renderLabel={(x: any) => `${x.name}${x.code ? ` (${x.code})` : ''}`}
 />
 </div>
 <div>
 <label className={lc}>{t('operations.incubationDay', 'Día de incubación')}</label>
 <input type="number" inputMode="decimal" min="1" max="21" {...register('extra_data.incubation_day' as any, { valueAsNumber: true })} className={ic} placeholder="18" />
 </div>
 <div>
 <label className={lc}>{t('operations.qtyTransferred', 'Cantidad transferida')}</label>
 <input type="number" inputMode="decimal" min="0" {...register('hatchery_params.0.quantity_transferred', { valueAsNumber: true })} className={ic} />
 </div>
 <div>
 <label className={lc}>{t('operations.temp', 'Temperatura (°C)')}</label>
 <input type="number" inputMode="decimal" step="0.1" {...register('hatchery_params.0.temperature', { valueAsNumber: true })} className={ic} placeholder="37.0" />
 </div>
 <div>
 <label className={lc}>{t('operations.humidity', 'Humedad (%)')}</label>
 <input type="number" inputMode="decimal" step="0.1" {...register('hatchery_params.0.humidity', { valueAsNumber: true })} className={ic} placeholder="68" />
 </div>
 </div>
 </div>
 )

 case 'birth_registration': {
 // `R-170` (`GA-REM-005-C`, BR-21): los nacidos son la suma de las filas, una por sexo; no hay fila «total»
 // (se deriva). `B13` (`GA-REM-021-C`): sanos y débiles son datos del nacimiento, no filas de nacidos.
 const rows = [
 { sex: 'male', label: t('operations.hatchedMale', 'Nacidos machos'), idx: 0 },
 { sex: 'female', label: t('operations.hatchedFemale', 'Nacidos hembras'), idx: 1 },
 { sex: 'mixed', label: t('operations.hatchedUnsexed', 'Nacidos sin sexar'), idx: 2 },
 ]
 const hatchedTotal = rows.reduce((sum, { idx }) => sum + Number(watch(`bird_movements.${idx}.quantity` as any) || 0), 0)
 return (
 <div className="space-y-5">
 {/* Birth counts */}
 <div>
 <p className="text-sm font-semibold text-slate-700 mb-2">{t('operations.birthCounts', 'Conteo de nacimientos')}</p>
 {rows.map(({ sex, label, idx }) => (
 <div key={idx} className="grid grid-cols-1 sm:grid-cols-2 px-1 py-2.5 gap-2 items-center border-b border-slate-100 last:border-0">
 <div>
 <input type="hidden" {...register(`bird_movements.${idx}.sex`)} defaultValue={sex} />
 <span className="text-sm text-slate-700">{label}</span>
 </div>
 <input type="number" inputMode="decimal" min="0" {...register(`bird_movements.${idx}.quantity`, { valueAsNumber: true })} className={ic} />
 </div>
 ))}
 <p className="text-xs text-slate-500 mt-2">{t('operations.hatchedTotalHint', { total: hatchedTotal })}</p>
 <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2">
 <div>
 <label className="text-xs font-medium text-slate-500">{t('operations.chicksHealthy', 'Pollitos sanos')}</label>
 <input type="number" inputMode="decimal" min="0" step="1" {...register('chicks_healthy' as any, { valueAsNumber: true })} className={ic} />
 </div>
 <div>
 <label className="text-xs font-medium text-slate-500">{t('operations.chicksWeak', 'Pollitos débiles')}</label>
 <input type="number" inputMode="decimal" min="0" step="1" {...register('chicks_weak' as any, { valueAsNumber: true })} className={ic} />
 </div>
 </div>
 </div>

 {/* Vaccination at birth */}
 <div className="bg-green-50 border border-green-100 rounded-lg p-3 space-y-3">
 <p className="text-sm font-semibold text-green-800">{t('operations.birthVaccination', 'Vacunación al nacimiento')}</p>
 <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
 <div>
 <label className="text-xs font-medium text-green-700">{t('operations.vaccine', 'Vacuna')}</label>
 <SearchSelect
 value={watch('vaccine_id' as any) ?? ''}
 onChange={(v) => setValue('vaccine_id' as any, v ? Number(v) : undefined)}
 items={vaccines}
 placeholder={t('operations.selectVaccine', 'Seleccionar vacuna...')}

 renderLabel={(v: any) => v.name}
 />
 </div>
 <div>
 <label className="text-xs font-medium text-green-700">{t('operations.vaccinationRoute', 'Vía de aplicación')}</label>
 <select {...register('vaccination_route' as any)} className="w-full h-10 px-2 border border-green-200 rounded-lg text-sm bg-white">
 <option value="">{t('operations.selectRoute', 'Seleccionar vía...')}</option>
 <option value="spray">{t('operations.routeSpray', 'Spray')}</option>
 <option value="water">{t('operations.routeWater', 'Agua de bebida')}</option>
 <option value="injection">{t('operations.routeInjection', 'Inyección')}</option>
 <option value="eye">{t('operations.routeEye', 'Ocular')}</option>
 <option value="gel">{t('operations.routeGel', 'Gel')}</option>
 </select>
 </div>
 <div>
 <label className="text-xs font-medium text-green-700">{t('operations.vaccineLotNumber', 'Lote de la vacuna')}</label>
 <input type="text" {...register('vaccine_lot_number' as any)} className="w-full h-10 px-2 border border-green-200 rounded-lg text-sm bg-white" placeholder="L-001" />
 </div>
 <div>
 <label className="text-xs font-medium text-green-700">{t('operations.dosePerBird', 'Dosis por ave')}</label>
 <input type="number" inputMode="decimal" step="0.001" {...register('dosage_per_bird' as any, { valueAsNumber: true })} className="w-full h-10 px-2 border border-green-200 rounded-lg text-sm bg-white" placeholder="0.2" />
 {errors.dosage_per_bird && <p className="text-red-500 text-xs mt-1">{t('operations.dosageInvalid', 'La dosis debe ser un número ≥ 0')}</p>}
 </div>
 </div>
 </div>
 </div>
 )
 }

 case 'chick_dispatch': return (
 <div className="space-y-4">
 <p className="text-xs text-slate-500">{t('operations.chickDispatchHint', 'Registra el despacho de pollitos desde la incubadora a la granja de engorde')}</p>
 <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
 <div>
 <label className={lc}>{t('operations.destinationFarm', 'Granja destino')}</label>
 <SearchSelect
 value={watch('destination_farm_id' as any) ?? ''}
 onChange={(v) => setValue('destination_farm_id' as any, v ? Number(v) : undefined)}
 items={farms}
 placeholder={t('operations.selectFarm', 'Seleccionar granja...')}

 renderLabel={(f: any) => `${f.name}${f.code ? ` (${f.code})` : ''}`}
 />
 </div>
 <div>
 <label className={lc}>{t('operations.transport', 'Transporte')}</label>
 <SearchSelect
 value={watch('transport_id' as any) ?? ''}
 onChange={(v) => setValue('transport_id' as any, v ? Number(v) : undefined)}
 items={transports}
 placeholder={t('operations.selectTransport', 'Seleccionar transporte...')}

 renderLabel={(x: any) => `${x.plate} — ${x.name}`}
 />
 </div>
 <div>
 <label className={lc}>{t('operations.sanitaryCert', 'Certificado sanitario')}</label>
 <input {...register('extra_data.sanitary_cert' as any)} className={ic} placeholder={t('operations.sanitaryCertPlaceholder')} />
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
 <input type="number" inputMode="decimal" min="0" {...register('bird_movements.0.quantity', { valueAsNumber: true })} className={ic} />
 <input type="hidden" {...register('bird_movements.0.sex')} defaultValue="mixed" />
 </div>
 <div>
 <label className={lc}>{t('operations.avgWeight', 'Peso final prom. (g)')}</label>
 <input type="number" inputMode="decimal" step="1" {...register('bird_movements.0.avg_weight', { valueAsNumber: true })} className={ic} />
 </div>
 <div>
 <label className={lc}>{t('operations.fcr', 'FCR (Conversión alimenticia)')}</label>
 <input type="number" inputMode="decimal" step="0.001" {...register('extra_data.fcr' as any, { valueAsNumber: true })} className={ic} placeholder="2.000" />
 </div>
 <div>
 <label className={lc}>{t('operations.totalMortality', 'Mortalidad total (%)')}</label>
 <input type="number" inputMode="decimal" step="0.01" {...register('extra_data.mortality_pct' as any)} className={ic} />
 </div>
 </div>
 </div>
 )

 case 'grandparent_import': return (
   // `GA-REM-042` · `R-152` · `BR-22`: el plan de importación de `docs/02 §3.4.1` con claves tipadas bajo
   // `extra_data.import_plan.*`; OC (bloque común), proveedor y transporte de la empresa; ♂/♀ recibidas.
   <div className="space-y-4">
     <p className="text-xs text-slate-500">{t('operations.importPlanTitle', 'Plan de importación')} · {t('operations.importIdentityHint', 'Embarcada = recibida + mortalidad en traslado; recibida = machos + hembras')}</p>
     <div className="flex flex-col gap-3 lg:grid lg:grid-cols-2">
       <div>
         <label className={lc}>{t('operations.supplier', 'Proveedor')}</label>
         <SearchSelect
           value={watch('supplier_id' as any) ?? ''}
           onChange={(v) => setValue('supplier_id' as any, v ? Number(v) : undefined)}
           items={suppliers}
           placeholder={t('operations.selectSupplier', 'Seleccionar proveedor...')}
           renderLabel={(x: any) => x.name}
         />
       </div>
       <div>
         <label className={lc}>{t('operations.transport', 'Transporte')}</label>
         <SearchSelect
           value={watch('transport_id' as any) ?? ''}
           onChange={(v) => setValue('transport_id' as any, v ? Number(v) : undefined)}
           items={transports}
           placeholder={t('operations.selectTransport', 'Seleccionar transporte...')}
           renderLabel={(x: any) => `${x.plate ? `${x.plate} — ` : ''}${x.name}`}
         />
       </div>
       <div>
         <label className={lc}>{t('operations.importOriginCountry', 'País de origen')}</label>
         <input {...register('extra_data.import_plan.origin_country' as any)} className={ic} placeholder={t('operations.importCountryPlaceholder')} />
       </div>
       <div>
         <label className={lc}>{t('operations.importPurchasedTotal', 'Cantidad comprada')}</label>
         <input type="number" inputMode="decimal" min="1" {...register('extra_data.import_plan.purchased_total' as any, { valueAsNumber: true })} className={ic} />
       </div>
       <div>
         <label className={lc}>{t('operations.importShippedTotal', 'Cantidad embarcada')}</label>
         <input type="number" inputMode="decimal" min="1" {...register('extra_data.import_plan.shipped_total' as any, { valueAsNumber: true })} className={ic} />
       </div>
       <div>
         <label className={lc}>{t('operations.importReceivedTotal', 'Cantidad recibida')}</label>
         <input type="number" inputMode="decimal" min="0" {...register('extra_data.import_plan.received_total' as any, { valueAsNumber: true })} className={ic} />
       </div>
       <div>
         <label className={lc}>{t('operations.importTransitMortality', 'Mortalidad en traslado')}</label>
         <input type="number" inputMode="decimal" min="0" {...register('extra_data.import_plan.transit_mortality' as any, { valueAsNumber: true })} className={ic} />
       </div>
       <div>
         <label className={lc}>{t('operations.importDepartureDate', 'Fecha de salida (origen)')}</label>
         <input type="date" {...register('extra_data.import_plan.departure_date' as any)} className={ic} />
       </div>
       <div>
         <label className={lc}>{t('operations.importArrivalDate', 'Fecha de llegada (destino)')}</label>
         <input type="date" {...register('extra_data.import_plan.arrival_date' as any)} className={ic} />
       </div>
       <div>
         <label className={lc}>{t('operations.importReceptionCondition', 'Condición de recepción')}</label>
         <input {...register('extra_data.import_plan.reception_condition' as any)} className={ic} />
       </div>
       <div>
         <label className={lc}>{t('operations.importQuarantineDays', 'Cuarentena (días)')}</label>
         <input type="number" inputMode="decimal" min="0" {...register('extra_data.import_plan.quarantine_days' as any, { valueAsNumber: true })} className={ic} placeholder="21" />
       </div>
       <div>
         <label className={lc}>{t('operations.importQuarantineEndDate', 'Cuarentena (fecha fin)')}</label>
         <input type="date" {...register('extra_data.import_plan.quarantine_end_date' as any)} className={ic} />
       </div>
       <div className="lg:col-span-2">
         <label className={lc}>{t('operations.importInitialHealthInspection', 'Inspección sanitaria inicial')}</label>
         <input {...register('extra_data.import_plan.initial_health_inspection' as any)} className={ic} />
       </div>
     </div>
     <p className="text-xs font-semibold text-slate-600">{t('operations.importReceivedBySex', 'Aves recibidas por sexo')}</p>
     {renderMFRows(true)}
   </div>
 )

default: return (
 <div className="py-6 text-sm text-slate-900 text-center italic">
 {t('operations.noSpecificFields', 'Registra tus observaciones en el campo de abajo.')}
 </div>
 )
 }
 }

 const selectedStageMeta = PROCESS_STAGES.find(s => s.key === stage)
 const SelectedEventIcon = eventType ? (EVENT_ICON_MAP[eventType] ?? EVENT_ICONS[eventType]) : null
 const SelectedStageIcon = selectedStageMeta?.Icon

 return (
 <div className="py-4 sm:py-6 text-slate-900">
 {/* Stepper */}
 <nav className="flex items-center gap-1.5 text-sm font-semibold mb-5 select-none">
 <button type="button" onClick={() => setStep(1)} className={step >= 1 ? 'text-[#5a9bba]' : 'text-slate-900'}>
 {t('process.step1', '1 · Proceso')}
 </button>
 <span className="text-slate-900">/</span>
 <button type="button" disabled={!stage} onClick={() => stage && setStep(2)}
 className={`${step >= 2 ? 'text-[#5a9bba]' : 'text-slate-900'} disabled:cursor-not-allowed`}>
 {t('process.step2', '2 · Operación')}
 </button>
 <span className="text-slate-900">/</span>
 <button type="button" disabled={!eventType} onClick={() => eventType && setStep(3)}
 className={`${step >= 3 ? 'text-[#5a9bba]' : 'text-slate-900'} disabled:cursor-not-allowed`}>
 {t('process.step3', '3 · Datos')}
 </button>
 </nav>

 {/* ===================== STEP 1 — PROCESS ===================== */}
 {step === 1 && (
 <div>
 <h1 className="text-xl font-bold text-slate-900">{t('process.title', 'Registrar Operación')}</h1>
 <p className="text-sm text-slate-900 mt-1 mb-5">{t('process.subtitle', '¿Qué proceso vas a registrar?')}</p>
 <div className="flex flex-col gap-3 lg:grid lg:grid-cols-2">
 {PROCESS_STAGES.map(s => {
 const Icon = s.Icon
 return (
 <button key={s.key} type="button" onClick={() => goToStep2(s.key)}
 className={`flex items-center gap-3 p-4 min-h-[5rem] rounded-xl border border-slate-200 bg-white text-left active:bg-slate-50 transition-colors ${s.accent}`}>
 <div className={`shrink-0 w-12 h-12 rounded-lg flex items-center justify-center ${s.iconBg}`}>
 <Icon size={26} className={s.iconColor} />
 </div>
 <div className="min-w-0">
 <p className="font-semibold text-slate-900 leading-tight">{t(s.labelKey, s.fallback)}</p>
 <p className="text-sm text-slate-500 leading-snug mt-1">{t(s.descKey, s.descFallback)}</p>
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
 className="inline-flex items-center gap-1 text-sm text-slate-900 hover:text-[#5a9bba] mb-3">
 <ChevronLeft size={16} /> {t('common.back', 'Atrás')}
 </button>
 <div className="flex items-center gap-3 mb-5">
 <div className={`shrink-0 w-10 h-10 rounded-lg flex items-center justify-center ${selectedStageMeta.iconBg}`}>
 {SelectedStageIcon && <SelectedStageIcon size={22} className={selectedStageMeta.iconColor} />}
 </div>
 <h1 className="text-lg font-bold text-slate-900">{t(selectedStageMeta.labelKey, selectedStageMeta.fallback)}</h1>
 </div>

 <p className="text-sm font-semibold text-slate-700 mt-1 mb-1">{t('process.chooseOperation', 'Elige la operación')}</p>
 <div className="space-y-5 mt-3">
 {categoriesForStage(stage).map(({ category, events }) => {
 const CatIcon = category.Icon
 return (
 <div key={category.key}>
 <div className="flex items-center gap-2 mb-2">
 <CatIcon size={16} className={category.color} />
 <span className="text-sm font-bold uppercase tracking-wide text-slate-600">
 {t(category.labelKey, category.fallback)}
 </span>
 </div>
 <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
 {events.map(evt => {
 const EvIcon = EVENT_ICON_MAP[evt] ?? EVENT_ICONS[evt]
 return (
 <button key={evt} type="button" onClick={() => chooseOperation(evt)}
 className="flex flex-col items-center gap-1.5 p-3 min-h-[4.5rem] rounded-lg border border-slate-200 bg-white hover:border-[#5a9bba] hover:bg-blue-50:bg-blue-900/20 transition-colors text-center group">
 {EvIcon && <EvIcon size={22} className="text-[#5a9bba] group-hover:scale-110 transition-transform" />}
 <span className="text-sm text-slate-700 leading-tight">{t(`eventsShort.${evt}`, evt)}</span>
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
 // `004` · UX-01: la entrada legacy `/poultry` ya no existe (redirect). Solo se aceptan
 // destinos de etapa profundos y hubs del menú estándar; cualquier otra cosa cae al hub actual.
 const target = sessionStorage.getItem('operationBackTarget')
 if (target && (target.startsWith('/poultry/') || target.startsWith('/menu/'))) {
 navigate(target)
 return
 }
 navigate('/menu/poultry')
 return
 }
 setStep(stage ? 2 : 1)
 }}
 className="inline-flex items-center gap-1 text-sm text-slate-900 hover:text-[#5a9bba] mb-3"
 >
 <ChevronLeft size={16} /> {t('common.back', 'Volver')}
 </button>

 {eventType && (
 <div className="flex items-center gap-3 mb-4 p-3 rounded-lg bg-blue-50 border border-blue-100">
 {SelectedEventIcon && <SelectedEventIcon size={22} className="text-[#5a9bba]" />}
 <div>
 <p className="text-sm font-bold text-slate-900">{t(`events.${eventType}`, eventType)}</p>
 {selectedStageMeta && (
 <p className="text-xs text-slate-900">{t(selectedStageMeta.labelKey, selectedStageMeta.fallback)}</p>
 )}
 </div>
 </div>
 )}

 {result && (
 <div className={`px-4 py-3 rounded-lg text-sm font-medium mb-4 ${result.ok ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
 {result.message}
 </div>
 )}

 <form id="operation-form" onSubmit={handleSubmit(onSubmit)} className="space-y-5">
 {/* ── SAP Order selector (grandparent_import, bird_reception, bird_exit, egg_dispatch, egg_reception_hatchery & chick_dispatch: must be first) ── */}
 {(eventType === 'grandparent_import' || eventType === 'bird_reception' || eventType === 'bird_exit' || eventType === 'egg_dispatch' || eventType === 'egg_reception_hatchery' || eventType === 'chick_dispatch') && (
 <div>
 {/* For breeder bird_reception: source type selector (transfer vs purchase) */}
 {eventType === 'bird_reception' && stage?.startsWith('breeder') ? (
 <>
 <label className="block text-sm font-semibold text-slate-700 mb-1.5">{t('operations.receptionSource', 'Origen de las aves')}</label>
 <div className="flex gap-3 mb-3">
 <label className={`flex-1 flex items-center justify-center gap-2 p-2.5 rounded-lg border-2 cursor-pointer transition text-sm font-medium ${
 watch('extra_data.reception_source' as any) === 'transfer'
 ? 'border-[#5a9bba] bg-blue-50 text-[#5a9bba]'
 : 'border-slate-200 text-slate-600'
 }`}>
 <input type="radio" name="reception_source" value="transfer"
 checked={watch('extra_data.reception_source' as any) === 'transfer'}
 onChange={() => { setValue('extra_data.reception_source' as any, 'transfer'); setValue('extra_data.sap_order_ref' as any, ''); setValue('sap_document_ref' as any, '') }}
 className="sr-only" />
 <span>{t('operations.receptionTransfer', 'Transferencia')}</span>
 </label>
 <label className={`flex-1 flex items-center justify-center gap-2 p-2.5 rounded-lg border-2 cursor-pointer transition text-sm font-medium ${
 (watch('extra_data.reception_source' as any) || 'purchase') === 'purchase'
 ? 'border-[#5a9bba] bg-blue-50 text-[#5a9bba]'
 : 'border-slate-200 text-slate-600'
 }`}>
 <input type="radio" name="reception_source" value="purchase"
 checked={!watch('extra_data.reception_source' as any) || watch('extra_data.reception_source' as any) === 'purchase'}
 onChange={() => { setValue('extra_data.reception_source' as any, 'purchase'); setValue('extra_data.sap_order_ref' as any, ''); setValue('sap_document_ref' as any, '') }}
 className="sr-only" />
 <span>{t('operations.receptionPurchase', 'Orden de compra')}</span>
 </label>
 </div>
 <label className="block text-sm font-semibold text-slate-700 mb-1">
 {watch('extra_data.reception_source' as any) === 'transfer'
 ? t('operations.sapTransferOrder', 'Orden de transferencia SAP')
 : t('operations.sapImportOrder', 'Orden de compra / importación SAP')}
 </label>
 <SearchSelect
 value={(() => {
 // `R-189 (F-01)`: `SearchSelect` trabaja con el id; el valor canónico guardado es el CÓDIGO.
 const lista = watch('extra_data.reception_source' as any) === 'transfer' ? sapOrders : sapPurchaseOrders
 const actual = lista.find((o: any) => identificadorDeOrdenSap(o) === watch('extra_data.sap_order_ref' as any))
 return actual ? String(actual.id) : ''
 })()}
 onChange={(v) => {
 const sourceList = watch('extra_data.reception_source' as any) === 'transfer' ? sapOrders : sapPurchaseOrders
 const order = sourceList.find((o: any) => String(o.id) === String(v))
 // `R-189 (F-01)`: el código canónico viaja al campo tipado que el dominio valida (`GA-TD-014`).
 const referencia = identificadorDeOrdenSap(order)
 setValue('extra_data.sap_order_ref' as any, referencia)
 setValue('sap_document_ref' as any, referencia)
 if (order) {
 if (order.quantity) setValue('extra_data.declared_quantity' as any, order.quantity)
 if (order.extra_data?.vendor_name) setValue('extra_data.vendor_name' as any, order.extra_data.vendor_name)
 if (order.extra_data?.breed_name) setValue('extra_data.breed_name' as any, order.extra_data.breed_name)
 if (order.extra_data?.dispatch_date) setValue('extra_data.dispatch_date' as any, order.extra_data.dispatch_date)
 if (order.extra_data?.avg_weight_male) setValue('extra_data.declared_avg_weight_m' as any, order.extra_data.avg_weight_male)
 if (order.extra_data?.avg_weight_female) setValue('extra_data.declared_avg_weight_f' as any, order.extra_data.avg_weight_female)
 }
 }}
 items={watch('extra_data.reception_source' as any) === 'transfer' ? sapOrders : sapPurchaseOrders}
 placeholder={t('operations.selectSapOrder', 'Seleccionar orden SAP...')}
 searchPlaceholder={watch('extra_data.reception_source' as any) === 'transfer' ? t('operations.searchTransfer', 'Buscar transferencia...') : t('operations.searchPurchaseOrder', 'Buscar orden de compra...')}
 renderLabel={(o: any) => `${o.doc_number || o.ref_id || o.sap_code || o.id}${o.extra_data?.vendor_name ? ` — ${o.extra_data.vendor_name}` : ''}${o.description ? ` · ${o.description}` : ''}`}
 />
 </>
 ) : (
 <>
 <label className="block text-sm font-semibold text-slate-700 mb-1">
 {(eventType === 'egg_dispatch' || eventType === 'egg_reception_hatchery')
 ? t('operations.sapTransferOrder', 'Orden de traslado SAP')
 : t('operations.sapImportOrder', 'Orden de compra / importación SAP')}
 </label>
 <SearchSelect
 value={(() => {
 // `R-189 (F-01)`: `SearchSelect` trabaja con el id; el valor canónico guardado es el CÓDIGO.
 const lista = (eventType === 'egg_dispatch' || eventType === 'egg_reception_hatchery') ? sapOrders : sapPurchaseOrders
 const actual = lista.find((o: any) => identificadorDeOrdenSap(o) === watch('extra_data.sap_order_ref' as any))
 return actual ? String(actual.id) : ''
 })()}
 onChange={(v) => {
 const lista = (eventType === 'egg_dispatch' || eventType === 'egg_reception_hatchery') ? sapOrders : sapPurchaseOrders
 const order = lista.find((o: any) => String(o.id) === String(v))
 // `R-189 (F-01)`: el código canónico viaja al campo tipado que el dominio valida (`GA-TD-014`).
 const referencia = identificadorDeOrdenSap(order)
 setValue('extra_data.sap_order_ref' as any, referencia)
 setValue('sap_document_ref' as any, referencia)
 if (order) {
 if (order.quantity) setValue('extra_data.declared_quantity' as any, order.quantity)
 if (order.extra_data?.vendor_name) setValue('extra_data.vendor_name' as any, order.extra_data.vendor_name)
 if (order.extra_data?.breed_name) setValue('extra_data.breed_name' as any, order.extra_data.breed_name)
 if (order.extra_data?.dispatch_date) setValue('extra_data.dispatch_date' as any, order.extra_data.dispatch_date)
 if (order.extra_data?.avg_weight_male) setValue('extra_data.declared_avg_weight_m' as any, order.extra_data.avg_weight_male)
 if (order.extra_data?.avg_weight_female) setValue('extra_data.declared_avg_weight_f' as any, order.extra_data.avg_weight_female)
 }
 }}
 items={(eventType === 'egg_dispatch' || eventType === 'egg_reception_hatchery') ? sapOrders : sapPurchaseOrders}
 placeholder={t('operations.selectSapOrder', 'Seleccionar orden SAP...')}
 searchPlaceholder={(eventType === 'egg_dispatch' || eventType === 'egg_reception_hatchery') ? t('operations.searchTransferOrder', 'Buscar orden de traslado...') : t('operations.searchPurchaseOrder', 'Buscar orden de compra...')}
 renderLabel={(o: any) => `${o.doc_number || o.ref_id || o.sap_code || o.id}${o.extra_data?.vendor_name ? ` — ${o.extra_data.vendor_name}` : ''}${o.description ? ` · ${o.description}` : ''}`}
 />
 </>
 )}
 </div>
 )}
 {/* ── Farm or Hatchery selector (multi-company scoped) ── */}
 {isHatcheryStage ? (
 <div>
 <label className="block text-sm font-semibold text-slate-700 mb-1">{t('masters.hatcheries', 'Incubadora')}</label>
 <SearchSelect
 value={selectedHatcheryId ?? ''}
 onChange={(v) => {
 const id = v ? Number(v) : null
 setSelectedHatcheryId(id)
 setValue('lot_id', undefined as any)
 }}
 items={hatcheries}
 placeholder={t('operations.selectHatchery', 'Seleccionar incubadora...')}

 renderLabel={(h: any) => h.name}
 />
 </div>
 ) : (
 <div>
 <label className="block text-sm font-semibold text-slate-700 mb-1">{t('masters.farms', 'Granja')}</label>
 <SearchSelect
 value={selectedFarmId ?? ''}
 onChange={(v) => {
 const id = v ? Number(v) : null
 setSelectedFarmId(id)
 setValue('lot_id', undefined as any)
 }}
 items={farms}
 placeholder={t('operations.selectFarm', 'Seleccionar granja...')}

 renderLabel={(f: any) => `${f.name}${f.code ? ` (${f.code})` : ''}`}
 />
 </div>
 )}

 {/* ── Lot selector (optional for inspection forms) ── */}
 {!isLotOptionalInspection && (
 <div>
 <label className="block text-sm font-semibold text-slate-700 mb-1">{t('operations.lot')}</label>
 <SearchSelect
 value={lotId}
 onChange={(v) => setValue('lot_id', v ? Number(v) : undefined as any)}
 items={filteredLots}
 placeholder={t('operations.selectLot', 'Seleccionar lote...')}

 renderLabel={(l: any) => `${l.lot_code}${l.status && l.status !== 'active' ? ` · ${l.status}` : ''}`}
 error={!!errors.lot_id}
 />
 {lotsLoadError && <p className="text-xs text-red-600 mt-1">{t('operations.errorLoadingLots', 'Error al cargar lotes')}</p>}
 {errors.lot_id && <p className="text-red-500 text-xs mt-1">{t(errors.lot_id.message ?? '')}</p>}
 {eventType === 'grandparent_import' && (
 <p className="text-xs text-slate-500 mt-1">{t('operations.importLotAutoNote', 'Si no selecciona un lote, se creará automáticamente al aprobar la importación.')}</p>
 )}
 </div>
 )}

 {/* `R-190` · C-05: «Galpón del evento» — la ubicación cuando el lote no declara galpón */}
 {EVENTOS_CON_SELECTOR_GALPON.has(eventType) && (
 <div>
 <label className="block text-sm font-semibold text-slate-700 mb-1">{t('operations.eventHouse', 'Galpón del evento')}</label>
 <SearchSelect
 value={eventHouseId ?? selectedLot?.house_id ?? ''}
 onChange={(v) => { if (!selectedLot?.house_id) setEventHouseId(v ? Number(v) : null) }}
 items={farmHouses.length > 0 ? farmHouses : houses}
 placeholder={t('operations.eventHouse', 'Galpón del evento')}
 renderLabel={(h: any) => `${h.name}${h.capacity ? ` (cap. ${h.capacity})` : ''}`}
 disabled={!!selectedLot?.house_id}
 />
 </div>
 )}

 <div>
 <label className="block text-sm font-semibold text-slate-700 mb-1">{t('operations.date')}</label>
 <input type="date" {...register('event_date')}
 className="w-full h-11 px-3 border border-slate-300 rounded-lg text-sm text-slate-900 bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none" />
 </div>

 {/* Operation-specific fields */}
 <div>
 {renderOperationFields()}
 </div>

 {ubicacionError && (
 <p className="text-red-500 text-sm">{t(ubicacionError)}</p>
 )}

 <div>
 <label className="block text-sm font-semibold text-slate-700 mb-1">{t('operations.observations')}</label>
 <textarea {...register('observations')} rows={2}
 className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm text-slate-900 bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none" />
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
