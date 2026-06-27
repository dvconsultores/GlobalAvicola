import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ChevronRight, ListChecks } from 'lucide-react'
import type { ProcessStage } from '../../data/processCatalog'

interface ProcessCardProps {
  process: ProcessStage
  operationCount: number
  onClick?: () => void
}

/**
 * ProcessCard — Enhanced visual card for a single process (stage)
 * Shows icon, title, description, and operation count
 * Used in ProcessHubPage and mobile dashboard
 */
export default function ProcessCard({ process, operationCount }: ProcessCardProps) {
  const { t } = useTranslation()
  const Icon = process.Icon

  return (
    <Link
      to={`/poultry/${process.key}`}
      className={`group block relative overflow-hidden rounded-2xl border-2 border-slate-200 bg-gradient-to-br shadow-sm transition-all hover:shadow-lg hover:scale-105 hover:-translate-y-1 dark:border-slate-700 dark:shadow-md ${process.accent} animate-scale-in hover-lift`}
    >
      {/* Background accent */}
      <div className={`absolute top-0 right-0 w-32 h-32 opacity-10 rounded-full -translate-y-16 translate-x-16 ${process.iconBg} dark:opacity-5`} />
      
      <div className="relative p-6 dark:bg-slate-800">
        {/* Icon badge */}
        <div className={`mb-4 w-16 h-16 rounded-2xl flex items-center justify-center transition-transform group-hover:scale-110 group-hover:rotate-6 ${process.iconBg} dark:opacity-80`}>
          <Icon size={36} className={`${process.iconColor} dark:brightness-110`} />
        </div>

        {/* Content */}
        <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100 mb-1 leading-tight dark:text-slate-100">
          {t(process.labelKey, process.fallback)}
        </h3>
        <p className="text-sm text-slate-600 leading-snug mb-4 dark:text-slate-400">
          {t(process.descKey, process.descFallback)}
        </p>

        {/* Footer: count and arrow */}
        <div className="flex items-center justify-between pt-3 border-t border-slate-100 dark:border-slate-700">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 dark:text-slate-400">
            <ListChecks size={14} />
            <span>{operationCount} {t('process.hub.operations', 'operaciones')}</span>
          </div>
          <ChevronRight size={20} className="text-slate-400 group-hover:text-slate-700 group-hover:translate-x-1 transition-all dark:text-slate-500 dark:group-hover:text-slate-300" />
        </div>
      </div>
    </Link>
  )
}
