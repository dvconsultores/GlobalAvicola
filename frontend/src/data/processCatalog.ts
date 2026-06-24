import {
  Bird, Egg, Flame, Drumstick, Feather,
  Truck, Package, ArrowUpRight, Wheat, Scale, Skull, Trash2,
  Syringe, Pill, Building2, ClipboardList, ArrowDownRight,
  Eye, RefreshCw, Baby, Lock, Plane, Thermometer,
  type LucideIcon,
} from 'lucide-react'

// ============================================================
// PROCESS CATALOG — Shared stage + operation taxonomy
// Used by the guided operation wizard and lot detail quick-actions
// so both surfaces present the SAME stage-aware, grouped operations.
// ============================================================

export type StageKey =
  | 'grandparent'
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
}

// Visual, high-level process cards (the first choice the user makes)
export const PROCESS_STAGES: ProcessStage[] = [
  {
    key: 'grandparent',
    labelKey: 'process.stages.grandparent',
    fallback: 'Progenitoras / Abuelas',
    descKey: 'process.stagesDesc.grandparent',
    descFallback: 'Importación, crianza y producción de huevos de abuelas',
    Icon: Plane,
    accent: 'hover:border-amber-400 hover:bg-amber-50',
    iconBg: 'bg-amber-100',
    iconColor: 'text-amber-600',
  },
  {
    key: 'breeder_rearing',
    labelKey: 'process.stages.breeder_rearing',
    fallback: 'Reproductoras — Cría',
    descKey: 'process.stagesDesc.breeder_rearing',
    descFallback: 'Levante de reproductoras antes de producción',
    Icon: Feather,
    accent: 'hover:border-teal-400 hover:bg-teal-50',
    iconBg: 'bg-teal-100',
    iconColor: 'text-teal-600',
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
  },
  {
    key: 'hatchery',
    labelKey: 'process.stages.hatchery',
    fallback: 'Incubadora',
    descKey: 'process.stagesDesc.hatchery',
    descFallback: 'Recepción de huevo, incubación y nacimiento de pollitos',
    Icon: Flame,
    accent: 'hover:border-orange-400 hover:bg-orange-50',
    iconBg: 'bg-orange-100',
    iconColor: 'text-orange-600',
  },
  {
    key: 'broiler',
    labelKey: 'process.stages.broiler',
    fallback: 'Pollo de Engorde',
    descKey: 'process.stagesDesc.broiler',
    descFallback: 'Recepción, crianza y cierre de lotes de engorde',
    Icon: Drumstick,
    accent: 'hover:border-green-400 hover:bg-green-50',
    iconBg: 'bg-green-100',
    iconColor: 'text-green-600',
  },
]

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
  grandparent: [
    'grandparent_import', 'farm_inspection', 'bird_reception', 'bird_distribution',
    'transport_inspection', 'feed_registration', 'weight_recording', 'mortality_recording',
    'cull_recording', 'vaccination', 'medication', 'egg_collection', 'egg_classification',
    'egg_dispatch', 'bird_exit',
  ],
  breeder_rearing: [
    'farm_inspection', 'bird_reception', 'bird_distribution', 'transport_inspection',
    'feed_registration', 'weight_recording', 'mortality_recording', 'cull_recording',
    'vaccination', 'medication', 'bird_exit',
  ],
  breeder_production: [
    'farm_inspection', 'transport_inspection', 'feed_registration', 'weight_recording',
    'mortality_recording', 'cull_recording', 'vaccination', 'medication', 'egg_collection',
    'egg_classification', 'egg_dispatch', 'bird_exit',
  ],
  hatchery: [
    'egg_reception_hatchery', 'hatchery_inspection', 'transport_inspection', 'incubation_load',
    'ovoscopy', 'transfer_to_hatcher', 'birth_registration', 'chick_dispatch',
  ],
  broiler: [
    'farm_inspection', 'bird_reception', 'bird_distribution', 'transport_inspection',
    'feed_registration', 'weight_recording', 'mortality_recording', 'cull_recording',
    'vaccination', 'medication', 'bird_exit', 'lot_closure',
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
 * Resolve which stage a lot belongs to, from its bird_type and active phase.
 * Mirrors the legacy logic in LotDetailPage so wizard + lot detail agree.
 */
export function resolveStageKey(birdType: string, activePhase: string | null): StageKey {
  if (birdType === 'breeder') {
    if (activePhase && /producc|production|hf|huevo/i.test(activePhase)) {
      return 'breeder_production'
    }
    return 'breeder_rearing'
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
