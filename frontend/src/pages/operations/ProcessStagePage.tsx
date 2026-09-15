import { useState, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useParams, useNavigate, Navigate, useLocation } from 'react-router-dom'
import { ChevronLeft, ArrowRight, LayoutGrid, ListOrdered, Building2 } from 'lucide-react'
import { useAuthStore } from '../../stores/auth.store'
import { useCan } from '../../auth/actionAuthority'
import { useCompanyStore } from '../../stores/company.store'
import {
 PROCESS_STAGES, flowForStage,
 type StageKey,
} from '../../data/processCatalog'
import { StageTimeline, OperationTile } from '../../components/operations'

const VALID_STAGES = PROCESS_STAGES.map(s => s.key)

type ViewMode = 'grid' | 'sequence'

/**
 * Stage detail — shows the ordered, real-world operation flow for one stage.
 *
 * REDESIGN: A modern, scroll-friendly screen. A colorful stage header (with the
 * selected lot's summary) sits above a 2-column grid of large, numbered icon
 * tiles — one per operation in the sequence. Operators tap a tile to register
 * that operation. A toggle switches to a vertical numbered "sequence" view.
 */
export default function ProcessStagePage() {
 const { t } = useTranslation()
 const navigate = useNavigate()
 const location = useLocation()
 const { user } = useAuthStore()
 const { activeCompanyName } = useCompanyStore()
 const isMobileUser = user?.view_type === 'mobile'
 // `R-220` · B6 (F G-20): la página es legible con `operations:read`, pero el registro
 // de operación exige la autoridad de ACCIÓN `operations:create` (misma política que la
 // ruta `/operations/new`). Sin ella: tiles read-only y timeline sin "Registrar" ⇒ sin callejón.
 const can = useCan()
 const puedeRegistrar = can({ permission: 'operations:create' })
 const { stage: stageParam, birdType, phase } = useParams<{ stage?: string; birdType?: string; phase?: string }>()
 // Compatibilidad: soporta tanto :stage (legacy) como :birdType/:phase? (nuevo ruteo)
 const stage = stageParam || (birdType && phase ? `${birdType}_${phase}` : birdType || '')
 const [view, setView] = useState<ViewMode>('grid')

 const stageKey = stage as StageKey
 const isValid = !!stage && VALID_STAGES.includes(stageKey)

 const stageMeta = PROCESS_STAGES.find(s => s.key === stageKey)
 const flow = useMemo(() => (isValid ? flowForStage(stageKey) : []), [isValid, stageKey])

 if (!isValid || !stageMeta) return <Navigate to="/menu/poultry" replace />

 const StageIcon = stageMeta.Icon

 const goToOperation = (event: string) => {
 sessionStorage.setItem('operationBackTarget', location.pathname)
 navigate(`/operations/new?type=${event}`)
 }

 return (
 <>
 {/* Page header — spacing from global app content shell */}
 <div className="pt-5 pb-4">
 <Link to="/menu/poultry" className="inline-flex items-center gap-1 text-xs text-slate-400 hover mb-3 transition-colors">
 <ChevronLeft size={14} /> {t('process.stage.back', 'Procesos')}
 </Link>
 <div className="flex items-center gap-3">
 <span className="w-9 h-9 rounded-lg bg-blue-50 flex items-center justify-center text-blue-600 shrink-0">
 <StageIcon size={18} strokeWidth={2} />
 </span>
 <div className="min-w-0">
 <h1 className="text-xl font-bold text-slate-900 leading-tight">{t(stageMeta.labelKey, stageMeta.fallback)}</h1>
 {(activeCompanyName || user?.company_name) && (
 <span className="inline-flex items-center gap-1 text-xs text-slate-500 mt-0.5">
 <Building2 size={11} />
 {activeCompanyName || user?.company_name}
 </span>
 )}
 </div>
 </div>
 </div>

 <div>
 {/* View toggle + step count */}
 <div className="flex items-center justify-between mb-4">
 <span className="text-sm font-bold text-slate-700">
 {flow.length} {t('process.stage.operations', 'operaciones')}
 </span>
 <div className="inline-flex bg-slate-100 rounded-xl p-1">
 <button
 onClick={() => setView('grid')}
 className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${view === 'grid' ? 'bg-white text-[#5a9bba] shadow-sm' : 'text-slate-500'}`}
 aria-pressed={view === 'grid'}
 >
 <LayoutGrid size={15} /> {t('process.stage.viewGrid', 'Cuadrícula')}
 </button>
 <button
 onClick={() => setView('sequence')}
 className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${view === 'sequence' ? 'bg-white text-[#5a9bba] shadow-sm' : 'text-slate-500'}`}
 aria-pressed={view === 'sequence'}
 >
 <ListOrdered size={15} /> {t('process.stage.viewSequence', 'Secuencia')}
 </button>
 </div>
 </div>

 {/* Operation surface */}
 {view === 'grid' ? (
 <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-6">
 {flow.map((s, i) => (
 <OperationTile key={s.event} step={s} index={i + 1} readOnly={!puedeRegistrar} />
 ))}
 </div>
 ) : (
 <div className="mb-6">
 <StageTimeline
 stages={flow}
 onStageSelect={puedeRegistrar ? goToOperation : undefined}
 completedStages={[]}
 currentStage={undefined}
 />
 </div>
 )}

 {/* History shortcut — web only */}
 {!isMobileUser && (
 <div className="text-center pt-4 border-t border-slate-200">
 <Link to="/operations" className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-600 hover:text-blue-600 transition-colors">
 {t('process.stage.viewHistory', 'Ver historial de operaciones')} <ArrowRight size={14} />
 </Link>
 </div>
 )}
 </div>
 </>
 )
}
