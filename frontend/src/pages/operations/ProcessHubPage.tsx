import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { ChevronRight, ListChecks } from 'lucide-react'
import { PROCESS_STAGES, flowForStage } from '../../data/processCatalog'

/**
 * Process hub — the main, clear entry point for registering operations.
 * The user picks a production stage (Incubadora, Reproductoras, etc.) and
 * is taken to that stage's ordered list of operations.
 */
export default function ProcessHubPage() {
  const { t } = useTranslation()

  return (
    <div className="p-4 sm:p-6 max-w-4xl mx-auto">
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-slate-800">{t('process.hub.title', 'Procesos')}</h1>
        <p className="text-sm text-slate-500 mt-1">
          {t('process.hub.subtitle', 'Elige una etapa de producción para ver sus operaciones')}
        </p>
      </header>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {PROCESS_STAGES.map(s => {
          const Icon = s.Icon
          const count = flowForStage(s.key).length
          return (
            <Link
              key={s.key}
              to={`/processes/${s.key}`}
              className={`group flex items-center gap-4 p-5 rounded-2xl border border-slate-200 bg-white shadow-sm transition-all hover:shadow-md hover:-translate-y-0.5 ${s.accent}`}
            >
              <div className={`shrink-0 w-14 h-14 rounded-xl flex items-center justify-center ${s.iconBg}`}>
                <Icon size={30} className={s.iconColor} />
              </div>
              <div className="min-w-0 flex-1">
                <p className="font-semibold text-slate-800 leading-tight">{t(s.labelKey, s.fallback)}</p>
                <p className="text-xs text-slate-500 leading-snug mt-1">{t(s.descKey, s.descFallback)}</p>
                <span className="inline-flex items-center gap-1 mt-2 text-xs font-medium text-slate-400">
                  <ListChecks size={13} />
                  {count} {t('process.hub.operations', 'operaciones')}
                </span>
              </div>
              <ChevronRight size={20} className="shrink-0 text-slate-300 group-hover:text-slate-500 transition-colors" />
            </Link>
          )
        })}
      </div>
    </div>
  )
}
