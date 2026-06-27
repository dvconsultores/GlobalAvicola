import { useState, useEffect, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useParams, useNavigate, Navigate } from 'react-router-dom'
import { ChevronLeft, ArrowRight, Info, Bird, LayoutGrid, ListOrdered, Sprout, Egg, Flame, Drumstick } from 'lucide-react'
import api from '../../services/api'
import { useToast } from '../../components/Toast'
import {
  PROCESS_STAGES, flowForStage,
  type StageKey,
} from '../../data/processCatalog'
import { StageTimeline, OperationTile } from '../../components/operations'

// Which lot bird_type(s) each stage draws from
const STAGE_BIRD_TYPES: Record<StageKey, string[]> = {
  grandparent_rearing: ['grandparent'],
  grandparent_production: ['grandparent'],
  breeder_rearing: ['breeder'],
  breeder_production: ['breeder'],
  hatchery: ['hatchery'],
  broiler: ['broiler'],
}

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
  const toast = useToast()
  const navigate = useNavigate()
  const { stage: stageParam, birdType, phase } = useParams<{ stage?: string; birdType?: string; phase?: string }>()
  // Compatibilidad: soporta tanto :stage (legacy) como :birdType/:phase? (nuevo ruteo)
  const stage = stageParam || (birdType && phase ? `${birdType}_${phase}` : birdType || '')
  const [lots, setLots] = useState<any[]>([])
  const [lotId, setLotId] = useState('')
  const [view, setView] = useState<ViewMode>('grid')

  const stageKey = stage as StageKey
  const isValid = !!stage && VALID_STAGES.includes(stageKey)

  useEffect(() => {
    if (!isValid) return
    api.get('/lots?limit=100')
      .then(r => setLots(r.data || []))
      .catch(() => toast.error(t('operations.errorLoadingLots', 'Error al cargar lotes')))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isValid])

  const stageMeta = PROCESS_STAGES.find(s => s.key === stageKey)
  const flow = useMemo(() => (isValid ? flowForStage(stageKey) : []), [isValid, stageKey])
  const stageLots = useMemo(() => {
    const allowed = STAGE_BIRD_TYPES[stageKey] ?? []
    return lots.filter((l: any) => allowed.includes(l.bird_type))
  }, [lots, stageKey])
  const selectedLot = useMemo(
    () => stageLots.find((l: any) => String(l.id) === lotId),
    [stageLots, lotId],
  )

  if (!isValid || !stageMeta) return <Navigate to="/poultry" replace />

  const StageIcon = stageMeta.Icon

  // Determinar badge de fase (Cría/Producción/Incubación/Engorde)
  const phaseBadge = (() => {
    if (stageKey.includes('rearing')) return { label: 'Cría', icon: Sprout, color: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300' }
    if (stageKey.includes('production')) return { label: 'Producción', icon: Egg, color: 'bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300' }
    if (stageKey === 'hatchery') return { label: 'Incubación', icon: Flame, color: 'bg-orange-50 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300' }
    if (stageKey === 'broiler') return { label: 'Engorde', icon: Drumstick, color: 'bg-teal-50 text-teal-700 dark:bg-teal-900/30 dark:text-teal-300' }
    return null
  })()

  const goToOperation = (event: string) => {
    const q = new URLSearchParams({ type: event })
    if (lotId) q.set('lot_id', lotId)
    navigate(`/operations/new?${q.toString()}`)
  }

  return (
    <div className="min-h-screen bg-[#F7F8FA] dark:bg-dark-bg pb-24 lg:pb-8 transition-colors duration-200">
      {/* Page header */}
      <div className="max-w-2xl mx-auto px-4 pt-5 pb-4">
        <Link to="/poultry" className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300 mb-3 transition-colors">
          <ChevronLeft size={14} /> {t('process.stage.back', 'Procesos')}
        </Link>
        <div className="flex items-start gap-3">
          <span className="w-9 h-9 rounded-lg bg-blue-50 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400 shrink-0 mt-0.5">
            <StageIcon size={18} strokeWidth={2} />
          </span>
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100 leading-tight">{t(stageMeta.labelKey, stageMeta.fallback)}</h1>
              {phaseBadge && (
                <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold ${phaseBadge.color}`}>
                  <phaseBadge.icon size={11} />
                  {phaseBadge.label}
                </span>
              )}
            </div>
            <p className="text-sm text-slate-400 dark:text-slate-500 mt-0.5 leading-snug">{t(stageMeta.descKey, stageMeta.descFallback)}</p>
          </div>
        </div>
        {/* Selected lot chip */}
        {selectedLot && (
          <div className="mt-3 inline-flex items-center gap-2.5 bg-white dark:bg-dark-card border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-2 text-sm">
            <Bird size={14} className="text-slate-400" />
            <span className="font-semibold text-slate-800 dark:text-slate-100">{selectedLot.lot_code}</span>
            {selectedLot.current_quantity != null && (
              <span className="text-slate-400">{Number(selectedLot.current_quantity).toLocaleString()} {t('process.stage.birds', 'aves')}</span>
            )}
            {selectedLot.status && (
              <span className="text-slate-400 capitalize">{String(selectedLot.status)}</span>
            )}
          </div>
        )}
      </div>

      <div className="max-w-2xl mx-auto px-4">
        {/* Lot selector */}
        <div className="bg-white dark:bg-dark-card rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm p-4 mb-4">
          <label className="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-2 uppercase tracking-wide">
            {t('process.stage.lotLabel', 'Lote (opcional)')}
          </label>
          <select
            value={lotId}
            onChange={e => setLotId(e.target.value)}
            className="w-full h-12 px-4 bg-slate-50 dark:bg-slate-800 border-2 border-slate-200 dark:border-slate-700 rounded-xl text-sm font-semibold text-slate-700 dark:text-slate-100 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition-all"
          >
            <option value="">{t('process.stage.allLots', 'Sin lote — elegir al registrar')}</option>
            {stageLots.map((l: any) => (
              <option key={l.id} value={l.id}>
                {l.lot_code} {l.status && l.status !== 'active' ? `(${String(l.status)})` : ''}
              </option>
            ))}
          </select>
          {stageLots.length === 0 && (
            <div className="flex items-start gap-2 mt-3 p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800">
              <Info size={16} className="text-amber-600 shrink-0 mt-0.5" />
              <p className="text-xs text-amber-700 dark:text-amber-300 font-medium">{t('process.noLots', 'No hay lotes activos para este proceso.')}</p>
            </div>
          )}
        </div>

        {/* View toggle + step count */}
        <div className="flex items-center justify-between mb-4">
          <span className="text-sm font-bold text-slate-700 dark:text-slate-200">
            {flow.length} {t('process.stage.operations', 'operaciones')}
          </span>
          <div className="inline-flex bg-slate-100 dark:bg-slate-800 rounded-xl p-1">
            <button
              onClick={() => setView('grid')}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${view === 'grid' ? 'bg-white dark:bg-dark-card text-[#2563EB] shadow-sm' : 'text-slate-500 dark:text-slate-400'}`}
              aria-pressed={view === 'grid'}
            >
              <LayoutGrid size={15} /> {t('process.stage.viewGrid', 'Cuadrícula')}
            </button>
            <button
              onClick={() => setView('sequence')}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${view === 'sequence' ? 'bg-white dark:bg-dark-card text-[#2563EB] shadow-sm' : 'text-slate-500 dark:text-slate-400'}`}
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
              <OperationTile key={s.event} step={s} index={i + 1} lotId={lotId || undefined} />
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

        {/* History shortcut */}
        <div className="text-center pt-4 border-t border-slate-200 dark:border-slate-700">
          <Link to="/operations" className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-600 dark:text-slate-300 hover:text-blue-600 transition-colors">
            {t('process.stage.viewHistory', 'Ver historial de operaciones')} <ArrowRight size={14} />
          </Link>
        </div>
      </div>
    </div>
  )
}
