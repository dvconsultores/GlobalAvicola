import { useState, useEffect, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useParams, useNavigate, Navigate } from 'react-router-dom'
import { ChevronLeft, ArrowRight, Info, Bird, ClipboardList } from 'lucide-react'
import api from '../../services/api'
import { useToast } from '../../components/Toast'
import {
  PROCESS_STAGES, flowForStage,
  type StageKey,
} from '../../data/processCatalog'
import { StageTimeline, ProcessFlowVisualizer } from '../../components/operations'

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

/**
 * Stage detail — shows the ordered, real-world operation flow for one stage.
 * REDESIGN: Uses visual timeline component and flow visualizer for better UX.
 * The user optionally picks a lot, then expands/taps an operation in sequence to
 * register it. This provides a clear, intuitive process the operator can follow.
 */
export default function ProcessStagePage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const toast = useToast()
  const { stage } = useParams<{ stage: string }>()
  const [lots, setLots] = useState<any[]>([])
  const [lotId, setLotId] = useState('')

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

  if (!isValid || !stageMeta) return <Navigate to="/processes" replace />

  const StageIcon = stageMeta.Icon

  const goToOperation = (event: string) => {
    const q = new URLSearchParams({ type: event })
    if (lotId) q.set('lot_id', lotId)
    navigate(`/operations/new?${q.toString()}`)
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <div className="p-4 sm:p-6 max-w-2xl mx-auto">
        {/* Back button */}
        <Link to="/processes" className="inline-flex items-center gap-1 text-sm font-medium text-slate-600 hover:text-blue-600 mb-6 transition-colors">
          <ChevronLeft size={16} /> {t('process.hub.title', 'Volver a Procesos')}
        </Link>

        {/* Stage header with visual branding */}
        <div className={`relative rounded-2xl overflow-hidden mb-6 p-6 text-white ${stageMeta.iconBg}`}>
          {/* Subtle background pattern */}
          <div className="absolute inset-0 opacity-10">
            <div className="absolute top-0 right-0 w-40 h-40 rounded-full blur-3xl" style={{ background: 'rgba(255,255,255,0.5)' }} />
          </div>

          <div className="relative flex items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-white/20 flex items-center justify-center backdrop-blur">
              <StageIcon size={32} />
            </div>
            <div>
              <h1 className="text-2xl font-bold leading-tight">{t(stageMeta.labelKey, stageMeta.fallback)}</h1>
              <p className="text-white/80 text-sm mt-1 leading-snug">{t(stageMeta.descKey, stageMeta.descFallback)}</p>
            </div>
          </div>
        </div>

        {/* Lot selector */}
        <div className="bg-white rounded-2xl border-2 border-slate-200 shadow-sm p-5 mb-6">
          <label className="block text-sm font-bold text-slate-700 mb-2">
            <Bird size={16} className="inline-block mr-1.5 -mt-0.5 text-blue-600" aria-hidden="true" />
            {t('process.stage.lotLabel', 'Selecciona un lote (opcional)')}
          </label>
          <select
            value={lotId}
            onChange={e => setLotId(e.target.value)}
            className="w-full h-12 px-4 border-2 border-slate-300 rounded-xl text-sm font-medium focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition-all"
          >
            <option value="">{t('process.stage.allLots', 'Sin lote — elegir al registrar')}</option>
            {stageLots.map((l: any) => (
              <option key={l.id} value={l.id}>
                {l.lot_code} {l.status && l.status !== 'active' ? `(${String(l.status)})` : ''}
              </option>
            ))}
          </select>
          {stageLots.length === 0 && (
            <div className="flex items-start gap-2 mt-3 p-3 bg-amber-50 rounded-lg border border-amber-200">
              <Info size={16} className="text-amber-600 shrink-0 mt-0.5" />
              <p className="text-xs text-amber-700 font-medium">{t('process.noLots', 'No hay lotes activos para este proceso.')}</p>
            </div>
          )}
        </div>

        {/* Progress visualization */}
        <div className="bg-white rounded-2xl border-2 border-slate-200 shadow-sm p-5 mb-6">
          <ProcessFlowVisualizer stages={flow} completedCount={0} totalCount={flow.length} />
        </div>

        {/* Sequential operation flow - using new timeline component */}
        <div className="mb-6">
          <h2 className="text-lg font-bold text-slate-800 mb-4">
            <ClipboardList size={20} className="inline-block mr-1.5 -mt-0.5 text-blue-600" aria-hidden="true" />
            {t('process.stage.flowTitle', 'Flujo de Operaciones')}
          </h2>
          <StageTimeline
            stages={flow}
            onStageSelect={goToOperation}
            completedStages={[]}
            currentStage={undefined}
          />
        </div>

        {/* History shortcut */}
        <div className="text-center pt-4 border-t border-slate-200">
          <Link to="/operations" className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-600 hover:text-blue-600 transition-colors">
            {t('process.stage.viewHistory', 'Ver historial de operaciones')} <ArrowRight size={14} />
          </Link>
        </div>
      </div>
    </div>
  )
}
