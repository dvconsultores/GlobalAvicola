import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { ChevronRight, LayoutGrid } from 'lucide-react'
import { PROCESS_STAGES, flowForStage } from '../../data/processCatalog'

/**
 * Process hub — the main, visual entry point for registering operations.
 *
 * REDESIGN: A modern, scroll-friendly grid of large, colorful process tiles.
 * Each of the 6 production stages is shown as a vivid gradient card with a big
 * icon, its name, a step count, and a preview of the first operations in its
 * sequence — so any operator can recognize and pick a process at a glance.
 */
export default function ProcessHubPage() {
  const { t } = useTranslation()
  const totalOps = PROCESS_STAGES.reduce((acc, s) => acc + flowForStage(s.key).length, 0)

  return (
    <div className="min-h-screen bg-[#F7F8FA] dark:bg-dark-bg pb-24 lg:pb-8 transition-colors duration-200">
      {/* Page header */}
      <div className="max-w-5xl mx-auto px-4 pt-5 pb-4">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
              <LayoutGrid size={13} />
              {t('process.hub.eyebrow', 'Centro de Operaciones')}
            </p>
            <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100 leading-tight">
              {t('process.hub.title', 'Elige un Proceso')}
            </h1>
            <p className="text-sm text-slate-400 dark:text-slate-500 mt-0.5">
              {t('process.hub.subtitle', 'Toca un proceso para ver su secuencia de operaciones')}
            </p>
          </div>
          <div className="hidden sm:flex items-center gap-4 shrink-0 pt-1">
            <div className="text-right">
              <div className="text-xl font-bold text-slate-900 dark:text-slate-100 leading-none">6</div>
              <div className="text-[11px] text-slate-400 uppercase tracking-wide mt-0.5">{t('process.hub.processes', 'Procesos')}</div>
            </div>
            <div className="w-px h-8 bg-slate-200 dark:bg-slate-700" />
            <div className="text-right">
              <div className="text-xl font-bold text-slate-900 dark:text-slate-100 leading-none">{totalOps}</div>
              <div className="text-[11px] text-slate-400 uppercase tracking-wide mt-0.5">{t('process.hub.operations', 'Operaciones')}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Process grid */}
      <div className="max-w-5xl mx-auto px-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {PROCESS_STAGES.map((stage) => {
            const flow = flowForStage(stage.key)
            const preview = flow.slice(0, 3).map(s => t(`events.${s.event}`, s.event))
            return (
              <Link
                key={stage.key}
                to={`/poultry/${stage.key}`}
                className="group relative overflow-hidden rounded-xl bg-white dark:bg-dark-card shadow-sm hover:shadow-md border border-slate-200 dark:border-slate-700 transition-all active:scale-[0.98]"
              >
                <div className="p-4">
                  {/* Icon + title */}
                  <div className="flex items-start gap-3 mb-3">
                    <span className="w-9 h-9 rounded-lg bg-blue-50 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400 shrink-0">
                      <stage.Icon size={20} strokeWidth={2} />
                    </span>
                    <div className="min-w-0 pt-0.5">
                      <h2 className="text-sm font-bold text-slate-800 dark:text-slate-100 leading-tight">
                        {t(stage.labelKey, stage.fallback)}
                      </h2>
                      <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5 line-clamp-2">
                        {t(stage.descKey, stage.descFallback)}
                      </p>
                    </div>
                  </div>

                  {/* Sequence preview chips */}
                  <div className="flex flex-wrap items-center gap-1.5 mb-3">
                    {preview.map((label, i) => (
                      <span
                        key={i}
                        className="inline-flex items-center text-[10px] font-semibold px-2 py-0.5 rounded-full bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300"
                      >
                        {label}
                      </span>
                    ))}
                    {flow.length > 3 && (
                      <span className="text-[10px] font-bold text-slate-400 dark:text-slate-500">
                        +{flow.length - 3}
                      </span>
                    )}
                  </div>

                  {/* Footer */}
                  <div className="flex items-center justify-between pt-3 border-t border-slate-100 dark:border-slate-700">
                    <span className="text-xs font-semibold text-slate-400 dark:text-slate-500">
                      {flow.length} {t('process.hub.steps', 'pasos')}
                    </span>
                    <span className="inline-flex items-center gap-0.5 text-xs font-bold text-blue-600 group-hover:gap-1.5 transition-all">
                      {t('process.hub.open', 'Abrir')}
                      <ChevronRight size={14} />
                    </span>
                  </div>
                </div>
              </Link>
            )
          })}
        </div>
      </div>
    </div>
  )
}
