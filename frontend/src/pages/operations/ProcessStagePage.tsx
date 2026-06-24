import { useState, useEffect, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useParams, useNavigate, Navigate } from 'react-router-dom'
import { ChevronLeft, ChevronRight, ArrowRight } from 'lucide-react'
import api from '../../services/api'
import { useToast } from '../../components/Toast'
import { EVENT_ICONS } from '../../components/Icon'
import {
  PROCESS_STAGES, EVENT_ICON_MAP, flowForStage,
  type StageKey,
} from '../../data/processCatalog'

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
 * The user optionally picks a lot, then taps an operation in sequence to
 * register it. This replaces the abstract category grouping with a clear,
 * numbered process the operator can follow top to bottom.
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
    <div className="p-4 sm:p-6 max-w-2xl mx-auto">
      <Link to="/processes" className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-[#2563EB] mb-4">
        <ChevronLeft size={16} /> {t('process.hub.title', 'Procesos')}
      </Link>

      {/* Stage header */}
      <div className="flex items-center gap-4 mb-5">
        <div className={`shrink-0 w-12 h-12 rounded-xl flex items-center justify-center ${stageMeta.iconBg}`}>
          <StageIcon size={26} className={stageMeta.iconColor} />
        </div>
        <div>
          <h1 className="text-xl font-bold text-slate-800 leading-tight">{t(stageMeta.labelKey, stageMeta.fallback)}</h1>
          <p className="text-sm text-slate-500 leading-snug">{t(stageMeta.descKey, stageMeta.descFallback)}</p>
        </div>
      </div>

      {/* Lot selector */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 mb-6">
        <label className="block text-sm font-semibold text-slate-700 mb-1.5">
          {t('process.stage.lotLabel', 'Lote (opcional)')}
        </label>
        <select
          value={lotId}
          onChange={e => setLotId(e.target.value)}
          className="w-full h-11 px-3 border border-slate-300 rounded-lg text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none"
        >
          <option value="">{t('process.stage.allLots', 'Sin lote — elegir al registrar')}</option>
          {stageLots.map((l: any) => (
            <option key={l.id} value={l.id}>
              {l.lot_code}{l.status && l.status !== 'active' ? ` · ${String(l.status)}` : ''}
            </option>
          ))}
        </select>
        {stageLots.length === 0 && (
          <p className="text-xs text-amber-600 mt-2">{t('process.noLots', 'No hay lotes para este proceso.')}</p>
        )}
      </div>

      {/* Sequential operation flow */}
      <p className="text-xs font-bold uppercase tracking-wide text-slate-400 mb-3">
        {t('process.stage.flowTitle', 'Operaciones del proceso')}
      </p>
      <ol className="relative space-y-2">
        {flow.map((s, i) => {
          const Icon = EVENT_ICON_MAP[s.event] ?? EVENT_ICONS[s.event]
          return (
            <li key={s.event} className="relative">
              {/* connector line */}
              {i < flow.length - 1 && (
                <span className="absolute left-[1.45rem] top-12 bottom-[-0.5rem] w-px bg-slate-200" aria-hidden />
              )}
              <button
                type="button"
                onClick={() => goToOperation(s.event)}
                className="group w-full flex items-center gap-3 p-3 rounded-xl border border-slate-200 bg-white shadow-sm text-left transition-all hover:border-[#2563EB] hover:bg-blue-50/50"
              >
                {/* step number + icon */}
                <div className="relative shrink-0">
                  <div className="w-12 h-12 rounded-xl bg-slate-100 group-hover:bg-blue-100 flex items-center justify-center transition-colors">
                    {Icon && <Icon size={22} className="text-[#2563EB]" />}
                  </div>
                  <span className="absolute -top-1.5 -left-1.5 w-5 h-5 rounded-full bg-[#1E3A5F] text-white text-[11px] font-bold flex items-center justify-center">
                    {i + 1}
                  </span>
                </div>
                <div className="min-w-0 flex-1">
                  <p className="font-semibold text-slate-800 leading-tight">{t(`events.${s.event}`, s.event)}</p>
                  <p className="text-xs text-slate-500 leading-snug mt-0.5">{t(s.descKey, s.descFallback)}</p>
                </div>
                <ChevronRight size={18} className="shrink-0 text-slate-300 group-hover:text-[#2563EB] transition-colors" />
              </button>
            </li>
          )
        })}
      </ol>

      {/* History shortcut */}
      <div className="mt-6 text-center">
        <Link to="/operations" className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-[#2563EB]">
          {t('process.stage.viewHistory', 'Ver historial de operaciones')} <ArrowRight size={14} />
        </Link>
      </div>
    </div>
  )
}
