import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ChevronRight, ListChecks } from 'lucide-react'
import { stagePathForKey, type ProcessStage } from '../../data/processCatalog'

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
 to={stagePathForKey(process.key)}
 className={`group block relative overflow-hidden rounded-2xl border border-slate-200 bg-gradient-to-br shadow-sm transition-all hover:shadow-lg hover:scale-105 hover:-translate-y-1 ${process.accent} animate-scale-in hover-lift`}
 >
 {/* Background accent */}
 <div className={`absolute top-0 right-0 w-32 h-32 opacity-10 rounded-full -translate-y-16 translate-x-16 ${process.iconBg}`} />
 
 <div className="relative p-6">
 {/* Icon badge */}
 <div className={`mb-4 w-16 h-16 rounded-2xl flex items-center justify-center transition-transform group-hover:scale-110 group-hover:rotate-6 ${process.iconBg}`}>
 <Icon size={36} className={`${process.iconColor}`} />
 </div>

 {/* Content */}
 <h3 className="text-lg font-bold text-slate-800 mb-1 leading-tight">
 {t(process.labelKey, process.fallback)}
 </h3>
 <p className="text-sm text-slate-600 leading-snug mb-4">
 {t(process.descKey, process.descFallback)}
 </p>

 {/* Footer: count and arrow */}
 <div className="flex items-center justify-between pt-3 border-t border-slate-100">
 <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-500">
 <ListChecks size={14} />
 <span>{operationCount} {t('process.hub.operations', 'operaciones')}</span>
 </div>
 <ChevronRight size={20} className="text-slate-400 group-hover group-hover:translate-x-1 transition-all" />
 </div>
 </div>
 </Link>
 )
}
