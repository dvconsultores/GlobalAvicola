import {
  Bird, Egg, Flame, Drumstick, Feather,
  Truck, Package, ArrowUpRight, Wheat, Scale, Skull, Trash2,
  Syringe, Pill, Building2, ClipboardList, ClipboardCheck, ArrowDownRight,
  Eye, RefreshCw, Baby, Lock, Plane, Thermometer,
  type LucideIcon,
} from 'lucide-react'

// ============================================================
// PROCESS CATALOG — Shared stage + operation taxonomy
// Used by the guided operation wizard and lot detail quick-actions
// so both surfaces present the SAME stage-aware, grouped operations.
// ============================================================

export type StageKey =
  | 'grandparent_rearing'
  | 'grandparent_production'
  | 'breeder_rearing'
  | 'breeder_production'
  | 'hatchery'
  | 'broiler'

export interface ProcessStage {
  key: StageKey
  /** i18n key under `process.stages.*` */
  labelKey: string
  fallback: string
  descKey: string
  descFallback: string
  Icon: LucideIcon
  /** Tailwind accent classes for the selection card */
  accent: string
  iconBg: string
  iconColor: string
  /** Vibrant gradient (from-…/to-…) for the redesigned hub tiles */
  gradient: string
}

// Visual, high-level process cards (the first choice the user makes)
export const PROCESS_STAGES: ProcessStage[] = [
  {
    key: 'grandparent_rearing',
    labelKey: 'process.stages.grandparent_rearing',
    fallback: 'Progenitoras — Cría',
    descKey: 'process.stagesDesc.grandparent_rearing',
    descFallback: 'Importación y levante de aves abuelas',
    Icon: Plane,
    accent: 'hover:border-blue-400 hover:bg-blue-50',
    iconBg: 'bg-blue-100',
    iconColor: 'text-blue-600',
    gradient: 'from-[#1E3A5F] to-[#2563EB]',
  },
  {
    key: 'grandparent_production',
    labelKey: 'process.stages.grandparent_production',
    fallback: 'Progenitoras — Producción',
    descKey: 'process.stagesDesc.grandparent_production',
    descFallback: 'Producción y recolección de huevos de abuelas',
    Icon: Egg,
    accent: 'hover:border-blue-400 hover:bg-blue-50',
    iconBg: 'bg-blue-100',
    iconColor: 'text-blue-600',
    gradient: 'from-[#1E3A5F] to-[#2563EB]',
  },
  {
    key: 'breeder_rearing',
    labelKey: 'process.stages.breeder_rearing',
    fallback: 'Reproductoras — Cría',
    descKey: 'process.stagesDesc.breeder_rearing',
    descFallback: 'Levante de reproductoras antes de producción',
    Icon: Feather,
    accent: 'hover:border-blue-400 hover:bg-blue-50',
    iconBg: 'bg-blue-100',
    iconColor: 'text-blue-600',
    gradient: 'from-[#1E3A5F] to-[#2563EB]',
  },
  {
    key: 'breeder_production',
    labelKey: 'process.stages.breeder_production',
    fallback: 'Reproductoras — Producción',
    descKey: 'process.stagesDesc.breeder_production',
    descFallback: 'Producción y recolección diaria de huevo fértil',
    Icon: Egg,
    accent: 'hover:border-blue-400 hover:bg-blue-50',
    iconBg: 'bg-blue-100',
    iconColor: 'text-blue-600',
    gradient: 'from-[#1E3A5F] to-[#2563EB]',
  },
  {
    key: 'hatchery',
    labelKey: 'process.stages.hatchery',
    fallback: 'Incubadora',
    descKey: 'process.stagesDesc.hatchery',
    descFallback: 'Recepción de huevo, incubación y nacimiento de pollitos',
    Icon: Flame,
    accent: 'hover:border-blue-400 hover:bg-blue-50',
    iconBg: 'bg-blue-100',
    iconColor: 'text-blue-600',
    gradient: 'from-[#1E3A5F] to-[#2563EB]',
  },
  {
    key: 'broiler',
    labelKey: 'process.stages.broiler',
    fallback: 'Pollo de Engorde',
    descKey: 'process.stagesDesc.broiler',
    descFallback: 'Recepción, crianza y cierre de lotes de engorde',
    Icon: Drumstick,
    accent: 'hover:border-blue-400 hover:bg-blue-50',
    iconBg: 'bg-blue-100',
    iconColor: 'text-blue-600',
    gradient: 'from-[#1E3A5F] to-[#2563EB]',
  },
]

export const STAGE_PATH_MAP: Record<StageKey, string> = {
  grandparent_rearing: '/poultry/grandparent/rearing',
  grandparent_production: '/poultry/grandparent/production',
  breeder_rearing: '/poultry/breeder/rearing',
  breeder_production: '/poultry/breeder/production',
  hatchery: '/poultry/hatchery',
  broiler: '/poultry/broiler',
}

export function stagePathForKey(stage: StageKey): string {
  return STAGE_PATH_MAP[stage]
}

// ============================================================
// OPERATION CATEGORIES — group the 24 event types by purpose
// ============================================================

export interface OperationCategory {
  key: string
  labelKey: string
  fallback: string
  Icon: LucideIcon
  color: string
  /** event types belonging to this category */
  events: string[]
}

export const OPERATION_CATEGORIES: OperationCategory[] = [
  {
    key: 'movement',
    labelKey: 'process.categories.movement',
    fallback: 'Movimiento de Aves',
    Icon: Truck,
    color: 'text-blue-600',
    events: ['bird_reception', 'bird_distribution', 'bird_transfer', 'bird_exit'],
  },
  {
    key: 'daily',
    labelKey: 'process.categories.daily',
    fallback: 'Registros Diarios',
    Icon: ClipboardList,
    color: 'text-amber-600',
    events: ['feed_registration', 'weight_recording', 'mortality_recording', 'cull_recording'],
  },
  {
    key: 'health',
    labelKey: 'process.categories.health',
    fallback: 'Sanidad',
    Icon: Syringe,
    color: 'text-rose-600',
    events: ['vaccination', 'medication'],
  },
  {
    key: 'inspection',
    labelKey: 'process.categories.inspection',
    fallback: 'Inspección',
    Icon: Building2,
    color: 'text-cyan-600',
    events: ['farm_inspection', 'transport_inspection', 'hatchery_inspection'],
  },
  {
    key: 'eggs',
    labelKey: 'process.categories.eggs',
    fallback: 'Huevos',
    Icon: Egg,
    color: 'text-indigo-600',
    events: ['egg_collection', 'egg_classification', 'egg_dispatch', 'egg_reception_hatchery'],
  },
  {
    key: 'incubation',
    labelKey: 'process.categories.incubation',
    fallback: 'Incubación',
    Icon: Flame,
    color: 'text-orange-600',
    events: ['incubation_load', 'ovoscopy', 'transfer_to_hatcher', 'birth_registration', 'chick_dispatch'],
  },
  {
    key: 'lifecycle',
    labelKey: 'process.categories.lifecycle',
    fallback: 'Ciclo de Vida',
    Icon: Lock,
    color: 'text-slate-600',
    events: ['grandparent_import', 'lot_closure'],
  },
]

// ============================================================
// STAGE → allowed event types
// ============================================================

export const STAGE_OPERATIONS: Record<StageKey, string[]> = {
  grandparent_rearing: [
    'grandparent_import', 'farm_inspection', 'bird_reception', 'bird_distribution',
    'bird_transfer', 'transport_inspection', 'feed_registration', 'weight_recording',
    'mortality_recording', 'cull_recording', 'vaccination', 'medication', 'bird_exit',
  ],
  grandparent_production: [
    'farm_inspection', 'bird_transfer', 'transport_inspection', 'feed_registration',
    'weight_recording', 'mortality_recording', 'cull_recording', 'vaccination',
    'medication', 'egg_collection', 'egg_classification', 'egg_dispatch', 'bird_exit',
  ],
  breeder_rearing: [
    'farm_inspection', 'bird_reception', 'bird_distribution', 'bird_transfer',
    'transport_inspection', 'feed_registration', 'weight_recording', 'mortality_recording',
    'cull_recording', 'vaccination', 'medication', 'bird_exit',
  ],
  breeder_production: [
    'farm_inspection', 'bird_transfer', 'transport_inspection', 'feed_registration',
    'weight_recording', 'mortality_recording', 'cull_recording', 'vaccination',
    'medication', 'egg_collection', 'egg_classification', 'egg_dispatch', 'bird_exit',
  ],
  hatchery: [
    'hatchery_inspection', 'egg_reception_hatchery', 'egg_reception_classification', 'transport_inspection',
    'incubation_load', 'ovoscopy', 'transfer_to_hatcher', 'birth_registration', 'chick_dispatch',
  ],
  broiler: [
    'farm_inspection', 'bird_reception', 'bird_distribution', 'bird_transfer',
    'transport_inspection', 'feed_registration', 'weight_recording', 'mortality_recording',
    'cull_recording', 'vaccination', 'medication', 'bird_exit', 'lot_closure',
  ],
}

// Icons per event type (single source — re-exported for convenience)
export const EVENT_ICON_MAP: Record<string, LucideIcon> = {
  bird_reception: Bird,
  bird_distribution: Package,
  bird_transfer: Truck,
  bird_exit: ArrowUpRight,
  feed_registration: Wheat,
  weight_recording: Scale,
  mortality_recording: Skull,
  cull_recording: Trash2,
  vaccination: Syringe,
  medication: Pill,
  farm_inspection: Building2,
  transport_inspection: Truck,
  hatchery_inspection: Thermometer,
  egg_collection: Egg,
  egg_classification: ClipboardList,
  egg_reception_classification: ClipboardCheck,
  egg_dispatch: ArrowUpRight,
  egg_reception_hatchery: ArrowDownRight,
  incubation_load: Flame,
  ovoscopy: Eye,
  transfer_to_hatcher: RefreshCw,
  birth_registration: Baby,
  chick_dispatch: Truck,
  lot_closure: Lock,
  grandparent_import: Plane,
}

/**
 * Vibrant per-event color palette (solid icon bg + text), used by the
 * icon-grid operation tiles. Each event has a distinctive, friendly color
 * so operators of any age can recognize an action by its color + icon.
 */
export const EVENT_COLOR_MAP: Record<string, { bg: string; ring: string; text: string }> = {
  grandparent_import:     { bg: 'bg-amber-500',   ring: 'ring-amber-200',   text: 'text-amber-600' },
  farm_inspection:        { bg: 'bg-cyan-500',    ring: 'ring-cyan-200',    text: 'text-cyan-600' },
  hatchery_inspection:    { bg: 'bg-cyan-600',    ring: 'ring-cyan-200',    text: 'text-cyan-700' },
  transport_inspection:   { bg: 'bg-sky-500',     ring: 'ring-sky-200',     text: 'text-sky-600' },
  bird_reception:         { bg: 'bg-blue-500',    ring: 'ring-blue-200',    text: 'text-blue-600' },
  bird_distribution:      { bg: 'bg-indigo-500',  ring: 'ring-indigo-200',  text: 'text-indigo-600' },
  bird_transfer:          { bg: 'bg-violet-500',  ring: 'ring-violet-200',  text: 'text-violet-600' },
  bird_exit:              { bg: 'bg-purple-500',  ring: 'ring-purple-200',  text: 'text-purple-600' },
  feed_registration:      { bg: 'bg-amber-500',   ring: 'ring-amber-200',   text: 'text-amber-600' },
  weight_recording:       { bg: 'bg-teal-500',    ring: 'ring-teal-200',    text: 'text-teal-600' },
  vaccination:            { bg: 'bg-rose-500',    ring: 'ring-rose-200',    text: 'text-rose-600' },
  medication:             { bg: 'bg-pink-500',    ring: 'ring-pink-200',    text: 'text-pink-600' },
  mortality_recording:    { bg: 'bg-slate-600',   ring: 'ring-slate-200',   text: 'text-slate-600' },
  cull_recording:         { bg: 'bg-stone-500',   ring: 'ring-stone-200',   text: 'text-stone-600' },
  egg_collection:         { bg: 'bg-yellow-500',  ring: 'ring-yellow-200',  text: 'text-yellow-600' },
  egg_classification:              { bg: 'bg-orange-500',  ring: 'ring-orange-200',  text: 'text-orange-600' },
  egg_reception_classification:    { bg: 'bg-teal-500',    ring: 'ring-teal-200',    text: 'text-teal-600' },
  egg_dispatch:                    { bg: 'bg-orange-600',  ring: 'ring-orange-200',  text: 'text-orange-700' },
  egg_reception_hatchery:          { bg: 'bg-amber-600',   ring: 'ring-amber-200',   text: 'text-amber-700' },
  incubation_load:        { bg: 'bg-orange-500',  ring: 'ring-orange-200',  text: 'text-orange-600' },
  ovoscopy:               { bg: 'bg-fuchsia-500', ring: 'ring-fuchsia-200', text: 'text-fuchsia-600' },
  transfer_to_hatcher:    { bg: 'bg-red-500',     ring: 'ring-red-200',     text: 'text-red-600' },
  birth_registration:     { bg: 'bg-green-500',   ring: 'ring-green-200',   text: 'text-green-600' },
  chick_dispatch:         { bg: 'bg-emerald-500', ring: 'ring-emerald-200', text: 'text-emerald-600' },
  lot_closure:            { bg: 'bg-slate-700',   ring: 'ring-slate-200',   text: 'text-slate-700' },
}

export function eventColor(event: string) {
  return EVENT_COLOR_MAP[event] ?? { bg: 'bg-blue-500', ring: 'ring-blue-200', text: 'text-blue-600' }
}

/**
 * Resolve which stage a lot belongs to, from its bird_type and active phase.
 * Mirrors the legacy logic in LotDetailPage so wizard + lot detail agree.
 */
export function resolveStageKey(birdType: string, activePhase: string | null): StageKey {
  const isProduction = !!activePhase && /producc|production|hf|huevo/i.test(activePhase)
  if (birdType === 'grandparent') {
    return isProduction ? 'grandparent_production' : 'grandparent_rearing'
  }
  if (birdType === 'breeder') {
    return isProduction ? 'breeder_production' : 'breeder_rearing'
  }
  if (birdType in STAGE_OPERATIONS) return birdType as StageKey
  return 'broiler'
}

/** Return the categories (with their events) applicable to a given stage. */
export function categoriesForStage(stage: StageKey): { category: OperationCategory; events: string[] }[] {
  const allowed = STAGE_OPERATIONS[stage] ?? []
  return OPERATION_CATEGORIES
    .map(category => ({
      category,
      events: category.events.filter(e => allowed.includes(e)),
    }))
    .filter(group => group.events.length > 0)
}

// ============================================================
// STAGE FLOWS — the REAL production sequence for each stage.
// This is what the user sees: an ordered, numbered list of the
// operations that happen in that stage, each with a short
// plain-language description of what it does.
// ============================================================

export interface FlowStep {
  /** event type — links to the operation form */
  event: string
  /** i18n key under `process.flowDesc.*` */
  descKey: string
  descFallback: string
}

function step(event: string, descFallback: string): FlowStep {
  return { event, descKey: `process.flowDesc.${event}`, descFallback }
}

export const STAGE_FLOWS: Record<StageKey, FlowStep[]> = {
  grandparent_rearing: [
    step('grandparent_import', 'Registrar la importación y llegada de aves abuelas'),
    step('farm_inspection', 'Inspeccionar la granja antes de recibir las aves'),
    step('bird_reception', 'Recepcionar las aves y registrar cantidades'),
    step('bird_distribution', 'Distribuir las aves a los galpones'),
    step('feed_registration', 'Registrar el consumo de alimento'),
    step('weight_recording', 'Registrar el pesaje semanal del lote'),
    step('vaccination', 'Aplicar y registrar vacunas'),
    step('medication', 'Aplicar y registrar medicación'),
    step('mortality_recording', 'Registrar mortalidad diaria'),
    step('cull_recording', 'Registrar descarte de aves'),
    step('bird_exit', 'Trasladar el lote a la etapa de producción'),
  ],
  grandparent_production: [
    step('farm_inspection', 'Inspeccionar condiciones de la granja'),
    step('feed_registration', 'Registrar el consumo de alimento'),
    step('weight_recording', 'Registrar el pesaje del lote'),
    step('vaccination', 'Aplicar y registrar vacunas'),
    step('medication', 'Aplicar y registrar medicación'),
    step('mortality_recording', 'Registrar mortalidad diaria'),
    step('cull_recording', 'Registrar descarte de aves'),
    step('egg_collection', 'Recolectar los huevos producidos'),
    step('egg_classification', 'Clasificar los huevos por tipo y calidad'),
    step('egg_dispatch', 'Despachar los huevos a su destino'),
    step('bird_exit', 'Registrar la salida o cierre del lote'),
  ],
  breeder_rearing: [
    step('farm_inspection', 'Inspeccionar la granja antes de recibir las pollitas'),
    step('bird_reception', 'Recepcionar las pollitas y registrar cantidades'),
    step('bird_distribution', 'Distribuir las pollitas a los galpones'),
    step('feed_registration', 'Registrar el consumo de alimento'),
    step('weight_recording', 'Registrar el pesaje semanal'),
    step('vaccination', 'Aplicar y registrar vacunas'),
    step('medication', 'Aplicar y registrar medicación'),
    step('mortality_recording', 'Registrar mortalidad diaria'),
    step('cull_recording', 'Registrar descarte de aves'),
    step('bird_exit', 'Trasladar el lote a la etapa de producción'),
  ],
  breeder_production: [
    step('farm_inspection', 'Inspeccionar condiciones de la granja'),
    step('feed_registration', 'Registrar el consumo de alimento'),
    step('weight_recording', 'Registrar el pesaje del lote'),
    step('vaccination', 'Aplicar y registrar vacunas'),
    step('medication', 'Aplicar y registrar medicación'),
    step('mortality_recording', 'Registrar mortalidad diaria'),
    step('cull_recording', 'Registrar descarte de aves'),
    step('egg_collection', 'Recolectar el huevo fértil diario'),
    step('egg_classification', 'Clasificar los huevos por tipo y calidad'),
    step('egg_dispatch', 'Despachar el huevo fértil a la incubadora'),
    step('bird_exit', 'Registrar la salida o cierre del lote'),
  ],
  hatchery: [
    step('hatchery_inspection', 'Inspeccionar la incubadora antes de operar'),
    step('egg_reception_hatchery', 'Recepcionar los huevos que llegan a la planta'),
    step('egg_reception_classification', 'Clasificar los huevos recibidos (aptos/no aptos)'),
    step('incubation_load', 'Cargar los huevos a las máquinas de incubación'),
    step('ovoscopy', 'Realizar ovoscopía para verificar fertilidad'),
    step('transfer_to_hatcher', 'Transferir los huevos a la nacedora'),
    step('birth_registration', 'Registrar el nacimiento de los pollitos'),
    step('chick_dispatch', 'Despachar los pollitos nacidos'),
  ],
  broiler: [
    step('farm_inspection', 'Inspeccionar la granja antes de recibir los pollitos'),
    step('bird_reception', 'Recepcionar los pollitos y registrar cantidades'),
    step('bird_distribution', 'Distribuir los pollitos a los galpones'),
    step('feed_registration', 'Registrar el consumo de alimento'),
    step('weight_recording', 'Registrar el pesaje del lote'),
    step('vaccination', 'Aplicar y registrar vacunas'),
    step('medication', 'Aplicar y registrar medicación'),
    step('mortality_recording', 'Registrar mortalidad diaria'),
    step('cull_recording', 'Registrar descarte de aves'),
    step('bird_exit', 'Registrar la salida de aves a planta'),
    step('lot_closure', 'Cerrar el lote al finalizar el ciclo'),
  ],
}

/** Ordered operation flow for a stage (only events allowed in that stage). */
export function flowForStage(stage: StageKey): FlowStep[] {
  const allowed = STAGE_OPERATIONS[stage] ?? []
  return (STAGE_FLOWS[stage] ?? []).filter(s => allowed.includes(s.event))
}
