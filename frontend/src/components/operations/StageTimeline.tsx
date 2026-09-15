import { useTranslation } from 'react-i18next'
import { ChevronDown, Check } from 'lucide-react'
import { useState } from 'react'
import type { FlowStep } from '../../data/processCatalog'
import { EVENT_ICON_MAP } from '../../data/processCatalog'
import { EVENT_ICONS } from '../Icon'

interface StageTimelineProps {
 stages: FlowStep[]
 /** `R-220` · B6: sin autoridad de acción el consumidor lo omite y no se ofrece el botón. */
 onStageSelect?: (event: string) => void
 completedStages?: string[]
 currentStage?: string
}

/**
 * StageTimeline — Vertical timeline showing the sequential flow of operations
 * Each stage is an expandable card showing what happens at that step
 * Color-coded with progress indicators
 */
export default function StageTimeline({
 stages,
 onStageSelect,
 completedStages = [],
 currentStage,
}: StageTimelineProps) {
 const { t } = useTranslation()
 const [expandedIndex, setExpandedIndex] = useState<number | null>(null)

 const STAGE_COLORS = [
 'from-blue-50 border-blue-200 bg-blue-50',
 'from-teal-50 border-teal-200 bg-teal-50',
 'from-amber-50 border-amber-200 bg-amber-50',
 'from-orange-50 border-orange-200 bg-orange-50',
 'from-indigo-50 border-indigo-200 bg-indigo-50',
 'from-green-50 border-green-200 bg-green-50',
 'from-rose-50 border-rose-200 bg-rose-50',
 'from-violet-50 border-violet-200 bg-violet-50',
 ]

 const STAGE_BORDER_COLORS = [
 'border-blue-300',
 'border-teal-300',
 'border-amber-300',
 'border-orange-300',
 'border-indigo-300',
 'border-green-300',
 'border-rose-300',
 'border-violet-300',
 ]

 return (
 <div className="space-y-2 animate-stagger">
 {stages.map((stage, index) => {
 const Icon = EVENT_ICON_MAP[stage.event] ?? EVENT_ICONS[stage.event]
 const isCompleted = completedStages.includes(stage.event)
 const isCurrent = currentStage === stage.event
 const isExpanded = expandedIndex === index
 const colorIndex = index % STAGE_COLORS.length
 const statusLabel = isCompleted
 ? t('common.completed', 'Completed')
 : isCurrent
 ? t('common.current', 'In progress')
 : t('common.pending', 'Pending')

 return (
 <div key={stage.event} className="relative">
 {/* Connector line (not on last) */}
 {index < stages.length - 1 && (
 <div className="absolute left-6 top-16 bottom-0 w-1 bg-gradient-to-b from-slate-300 to-slate-100" />
 )}

 {/* Timeline item */}
 <button
 type="button"
 onClick={() => setExpandedIndex(isExpanded ? null : index)}
 className={`w-full relative group transition-all rounded-xl border overflow-hidden ${
 isExpanded ? 'ring-2 ring-blue-400 shadow-md' : 'hover:shadow-sm'
 } ${isCompleted ? 'border-green-300 bg-green-50' : isCurrent ? STAGE_BORDER_COLORS[colorIndex] : 'border-slate-200'}`}
 aria-expanded={isExpanded}
 aria-controls={`stage-content-${index}`}
 aria-label={`${t(`events.${stage.event}`, stage.event)} - ${statusLabel}`}
 >
 <div className={`relative p-4 ${isCompleted ? 'bg-gradient-to-br from-green-50 to-emerald-50' : ''}`}>
 <div className="flex items-start gap-4">
 {/* Circle with step number or checkmark */}
 <div className="relative shrink-0 mt-1">
 <div
 className={`w-10 h-10 rounded-full flex items-center justify-center font-bold transition-all transform group-hover:scale-110 ${
 isCompleted
 ? 'bg-green-500 text-white'
 : isCurrent
 ? 'bg-blue-600 scale-110 shadow-md text-white'
 : 'bg-slate-200 text-slate-500'
 }`}
 aria-hidden="true"
 >
 {isCompleted ? (
 <Check size={20} />
 ) : (
 <span className="text-xs">{index + 1}</span>
 )}
 </div>
 </div>

 {/* Content */}
 <div className="flex-1 min-w-0 text-left">
 <div className="flex items-center gap-2 mb-1">
 {Icon && (
 <div className="shrink-0">
 <Icon
 size={20}
 className={
 isCompleted
 ? 'text-green-600'
 : isCurrent
 ? 'text-blue-600'
 : 'text-slate-600'
 }
 aria-hidden="true"
 />
 </div>
 )}
 <h4 className={`font-semibold text-slate-800 leading-tight`}>
 {t(`events.${stage.event}`, stage.event)}
 </h4>
 {isCompleted && (
 <span className="inline-flex items-center text-xs font-bold text-green-700 bg-green-100 px-2 py-0.5 rounded-full" aria-label={t('common.completed')}>
 ✓ {t('common.completed', 'Completado')}
 </span>
 )}
 {isCurrent && !isCompleted && (
 <span className="inline-flex items-center text-xs font-bold text-blue-700 bg-blue-100 px-2 py-0.5 rounded-full" aria-label={t('common.current')}>
 → {t('common.current', 'En progreso')}
 </span>
 )}
 </div>
 <p className={`text-xs text-slate-600 leading-snug`}>
 {t(stage.descKey, stage.descFallback)}
 </p>
 </div>

 {/* Chevron indicator */}
 <ChevronDown
 size={18}
 className={`shrink-0 text-slate-400 transition-transform ${
 isExpanded ? 'rotate-180' : ''
 }`}
 aria-hidden="true"
 />
 </div>

 {/* Expanded content */}
 {isExpanded && onStageSelect && (
 <div id={`stage-content-${index}`} className="mt-4 pt-4 border-t border-slate-200">
 <button
 onClick={(e) => {
 e.stopPropagation()
 onStageSelect(stage.event)
 }}
 className="w-full py-2.5 px-3 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700:from-blue-700:to-blue-800 text-white font-semibold rounded-lg transition-all hover:shadow-md active:scale-95"
 aria-label={`${t('process.stage.registerOperation', 'Registrar operación')} ${t(`events.${stage.event}`, stage.event)}`}
 >
 {t('process.stage.registerOperation', 'Registrar operación')} →
 </button>
 </div>
 )}
 </div>
 </button>
 </div>
 )
 })}
 </div>
 )
}
