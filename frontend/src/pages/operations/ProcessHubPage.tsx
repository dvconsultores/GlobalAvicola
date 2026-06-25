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
    <div className="min-h-screen bg-slate-50 dark:bg-dark-bg pb-24 lg:pb-8 transition-colors duration-200">
      {/* Hero header */}
      <div className="bg-gradient-to-br from-[#1E3A5F] via-[#234876] to-[#2563EB] text-white px-5 pt-8 pb-10 rounded-b-[2rem] shadow-lg">
        <div className="max-w-5xl mx-auto">
          <div className="flex items-center gap-2 text-blue-100 text-xs font-semibold uppercase tracking-wider mb-2">
            <LayoutGrid size={15} />
            {t('process.hub.eyebrow', 'Centro de Operaciones')}
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold leading-tight">
            {t('process.hub.title', 'Elige un Proceso')}
          </h1>
          <p className="text-blue-100 text-sm mt-1.5">
            {t('process.hub.subtitle', 'Toca un proceso para ver su secuencia de operaciones')}
          </p>
          <div className="flex gap-3 mt-5">
            <div className="bg-white/15 backdrop-blur rounded-2xl px-4 py-2.5">
              <div className="text-2xl font-extrabold leading-none">6</div>
              <div className="text-[11px] text-blue-100 mt-0.5">{t('process.hub.processes', 'Procesos')}</div>
            </div>
            <div className="bg-white/15 backdrop-blur rounded-2xl px-4 py-2.5">
              <div className="text-2xl font-extrabold leading-none">{totalOps}</div>
              <div className="text-[11px] text-blue-100 mt-0.5">{t('process.hub.operations', 'Operaciones')}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Process grid */}
      <div className="max-w-5xl mx-auto px-4 -mt-5">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {PROCESS_STAGES.map((stage, idx) => {
            const flow = flowForStage(stage.key)
            const preview = flow.slice(0, 3).map(s => t(`events.${s.event}`, s.event))
            return (
              <Link
                key={stage.key}
                to={`/poultry/${stage.key}`}
                className="group relative overflow-hidden rounded-3xl bg-white dark:bg-dark-card shadow-sm hover:shadow-xl border border-slate-100 dark:border-slate-700 transition-all active:scale-[0.98]"
              >
                {/* Colored header band */}
                <div className={`relative bg-gradient-to-br ${stage.gradient} p-5 pb-12`}>
                  <span className="absolute top-4 right-4 text-white/40 text-5xl font-black leading-none select-none">
                    {idx + 1}
                  </span>
                  <span className="inline-flex w-14 h-14 rounded-2xl bg-white/25 backdrop-blur items-center justify-center text-white shadow-inner ring-1 ring-white/30">
                    <stage.Icon size={30} strokeWidth={2.2} />
                  </span>
                </div>

                {/* Body, overlapping the band */}
                <div className="px-5 pb-5 -mt-7">
                  <div className="bg-white dark:bg-dark-card rounded-2xl shadow-sm border border-slate-100 dark:border-slate-700 p-4">
                    <h2 className="text-base font-extrabold text-slate-800 dark:text-slate-100 leading-tight">
                      {t(stage.labelKey, stage.fallback)}
                    </h2>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">
                      {t(stage.descKey, stage.descFallback)}
                    </p>

                    {/* Sequence preview chips */}
                    <div className="flex flex-wrap items-center gap-1.5 mt-3">
                      {preview.map((label, i) => (
                        <span
                          key={i}
                          className="inline-flex items-center text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300"
                        >
                          {label}
                        </span>
                      ))}
                      {flow.length > 3 && (
                        <span className="text-[10px] font-bold text-slate-400">
                          +{flow.length - 3}
                        </span>
                      )}
                    </div>

                    {/* Footer */}
                    <div className="flex items-center justify-between mt-4 pt-3 border-t border-slate-100 dark:border-slate-700">
                      <span className="text-xs font-bold text-slate-500 dark:text-slate-400">
                        {flow.length} {t('process.hub.steps', 'pasos')}
                      </span>
                      <span className="inline-flex items-center gap-0.5 text-xs font-bold text-[#2563EB] group-hover:gap-1.5 transition-all">
                        {t('process.hub.open', 'Abrir')}
                        <ChevronRight size={15} />
                      </span>
                    </div>
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
