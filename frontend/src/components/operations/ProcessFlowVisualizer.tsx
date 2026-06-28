import { useTranslation } from 'react-i18next'
import { ChevronRight } from 'lucide-react'
import type { FlowStep } from '../../data/processCatalog'
import { EVENT_ICON_MAP } from '../../data/processCatalog'
import { EVENT_ICONS } from '../Icon'

interface ProcessFlowVisualizerProps {
 stages: FlowStep[]
 completedCount?: number
 totalCount?: number
}

/**
 * ProcessFlowVisualizer — Shows a compact, visual overview of the entire process flow
 * Used as a progress indicator or header visualization
 */
export default function ProcessFlowVisualizer({
 stages,
 completedCount = 0,
 totalCount,
}: ProcessFlowVisualizerProps) {
 const { t } = useTranslation()
 const total = totalCount || stages.length
 const progressPercent = Math.round((completedCount / total) * 100)

 const MINI_COLORS = [
 'bg-blue-100 text-blue-600',
 'bg-teal-100 text-teal-600',
 'bg-amber-100 text-amber-600',
 'bg-orange-100 text-orange-600',
 'bg-indigo-100 text-indigo-600',
 'bg-green-100 text-green-600',
 'bg-rose-100 text-rose-600',
 'bg-violet-100 text-violet-600',
 ]

 return (
 <div className="space-y-3">
 {/* Progress header */}
 <div className="flex items-center justify-between">
 <div>
 <h3 className="text-sm font-bold text-slate-800">
 {t('process.progress', 'Progreso del proceso')}
 </h3>
 <p className="text-xs text-slate-500 mt-1">
 {completedCount} de {total} {t('process.stagesCompleted', 'etapas completadas')}
 </p>
 </div>
 <div className="text-right">
 <div className="text-2xl font-bold text-blue-600">{progressPercent}%</div>
 <div className="text-xs text-slate-500">{t('common.complete', 'Completado')}</div>
 </div>
 </div>

 {/* Progress bar */}
 <div className="relative h-2 bg-slate-200 rounded-full overflow-hidden">
 <div
 className="absolute top-0 left-0 h-full bg-gradient-to-r from-blue-400 to-blue-600 transition-all duration-500 progress-animated"
 style={{ width: `${progressPercent}%` }}
 />
 </div>

 {/* Flow visualization */}
 <div className="flex items-center gap-2 overflow-x-auto pb-2 pt-2">
 {stages.map((stage, index) => {
 const Icon = EVENT_ICON_MAP[stage.event] ?? EVENT_ICONS[stage.event]
 const colorIndex = index % MINI_COLORS.length
 const isCompleted = index < completedCount

 return (
 <div key={stage.event} className="relative flex items-center gap-1 shrink-0">
 {/* Mini badge */}
 <div
 className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 transition-all ${
 isCompleted
 ? 'bg-green-100 text-green-600 scale-110'
 : MINI_COLORS[colorIndex]
 }`}
 title={t(`events.${stage.event}`, stage.event)}
 >
 {isCompleted ? (
 <span className="text-lg">✓</span>
 ) : Icon ? (
 <Icon size={16} />
 ) : (
 <span className="text-xs font-bold">{index + 1}</span>
 )}
 </div>

 {/* Connector (not on last) */}
 {index < stages.length - 1 && (
 <ChevronRight size={16} className="text-slate-300 shrink-0" />
 )}
 </div>
 )
 })}
 </div>
 </div>
 )
}
