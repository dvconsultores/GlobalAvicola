import { useState, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useParams, useNavigate, Navigate, useLocation } from 'react-router-dom'
import { ChevronLeft, ArrowRight, LayoutGrid, ListOrdered, Sprout, Egg, Flame, Drumstick } from 'lucide-react'
import { useAuthStore } from '../../stores/auth.store'
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
  const isMobileUser = user?.view_type === 'mobile'
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

  // Determinar badge de fase (Cría/Producción/Incubación/Engorde)
  const phaseBadge = (() => {
    if (stageKey.includes('rearing')) return { label: 'Cría', icon: Sprout, color: 'bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 dark:text-emerald-400 dark:bg-emerald-900/30 dark:text-emerald-300 dark:text-emerald-400' }
    if (stageKey.includes('production')) return { label: 'Producción', icon: Egg, color: 'bg-amber-50 dark:bg-amber-950 text-amber-700 dark:text-amber-300 dark:bg-amber-900/30 dark:text-amber-300' }
    if (stageKey === 'hatchery') return { label: 'Incubación', icon: Flame, color: 'bg-orange-50 dark:bg-orange-950 text-orange-700 dark:text-orange-300 dark:bg-orange-900/30 dark:text-orange-300' }
    if (stageKey === 'broiler') return { label: 'Engorde', icon: Drumstick, color: 'bg-teal-50 dark:bg-teal-950 text-teal-700 dark:text-teal-300 dark:bg-teal-900/30 dark:text-teal-300' }
    return null
  })()

  const goToOperation = (event: string) => {
    sessionStorage.setItem('operationBackTarget', location.pathname)
    navigate(`/operations/new?type=${event}`)
  }

  return (
    <div className="min-h-screen bg-[#F7F8FA] dark:bg-dark-bg pb-24 lg:pb-8 transition-colors duration-200">
      {/* Page header */}
      <div className="max-w-2xl mx-auto px-4 pt-5 pb-4">
        <Link to="/menu/poultry" className="inline-flex items-center gap-1 text-xs text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:text-slate-300 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500 dark:hover:text-slate-300 dark:text-slate-500 mb-3 transition-colors">
          <ChevronLeft size={14} /> {t('process.stage.back', 'Procesos')}
        </Link>
        <div className="flex items-start gap-3">
          <span className="w-9 h-9 rounded-lg bg-blue-50 dark:bg-blue-950 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400 shrink-0 mt-0.5">
            <StageIcon size={18} strokeWidth={2} />
          </span>
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100 dark:text-slate-50 dark:text-slate-100 leading-tight">{t(stageMeta.labelKey, stageMeta.fallback)}</h1>
              {phaseBadge && (
                <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${phaseBadge.color}`}>
                  <phaseBadge.icon size={11} />
                  {phaseBadge.label}
                </span>
              )}
            </div>
            <p className="text-sm text-slate-400 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500 mt-0.5 leading-snug">{t(stageMeta.descKey, stageMeta.descFallback)}</p>
          </div>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-4">
        {/* View toggle + step count */}
        <div className="flex items-center justify-between mb-4">
          <span className="text-sm font-bold text-slate-700 dark:text-slate-200">
            {flow.length} {t('process.stage.operations', 'operaciones')}
          </span>
          <div className="inline-flex bg-slate-100 dark:bg-slate-700 dark:bg-slate-800 rounded-xl p-1">
            <button
              onClick={() => setView('grid')}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${view === 'grid' ? 'bg-white dark:bg-slate-800 dark:bg-slate-700 text-[#2563EB] dark:text-brand-400 shadow-sm' : 'text-slate-500 dark:text-slate-400 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500'}`}
              aria-pressed={view === 'grid'}
            >
              <LayoutGrid size={15} /> {t('process.stage.viewGrid', 'Cuadrícula')}
            </button>
            <button
              onClick={() => setView('sequence')}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${view === 'sequence' ? 'bg-white dark:bg-slate-800 dark:bg-slate-700 text-[#2563EB] dark:text-brand-400 shadow-sm' : 'text-slate-500 dark:text-slate-400 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500'}`}
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
              <OperationTile key={s.event} step={s} index={i + 1} />
            ))}
          </div>
        ) : (
          <div className="mb-6">
            <StageTimeline
              stages={flow}
              onStageSelect={goToOperation}
              completedStages={[]}
              currentStage={undefined}
            />
          </div>
        )}

        {/* History shortcut — web only */}
        {!isMobileUser && (
        <div className="text-center pt-4 border-t border-slate-200 dark:border-slate-700">
          <Link to="/operations" className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-600 dark:text-slate-300 dark:text-slate-500 dark:text-slate-300 dark:text-slate-500 hover:text-blue-600 dark:text-blue-400 transition-colors">
            {t('process.stage.viewHistory', 'Ver historial de operaciones')} <ArrowRight size={14} />
          </Link>
        </div>
        )}
      </div>
    </div>
  )
}
