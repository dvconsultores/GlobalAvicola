import { useTranslation } from 'react-i18next'
import { ChevronDown, Check } from 'lucide-react'
import { useState } from 'react'
import type { FlowStep } from '../../data/processCatalog'
import { EVENT_ICON_MAP } from '../../data/processCatalog'
import { EVENT_ICONS } from '../Icon'

interface StageTimelineProps {
  stages: FlowStep[]
  onStageSelect: (event: string) => void
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
              className={`w-full relative group transition-all rounded-xl border-2 overflow-hidden ${
                isExpanded ? 'ring-2 ring-blue-400 shadow-md' : 'hover:shadow-sm'
              } ${isCompleted ? 'border-green-300 bg-green-50 dark:bg-green-900/20 dark:border-green-700' : isCurrent ? STAGE_BORDER_COLORS[colorIndex] : 'border-slate-200 dark:border-slate-700'}`}
              aria-expanded={isExpanded}
              aria-controls={`stage-content-${index}`}
              aria-label={`${t(`events.${stage.event}`, stage.event)} - ${t('common.' + (isCompleted ? 'completed' : isCurrent ? 'current' : 'pending'), isCompleted ? 'Completado' : isCurrent ? 'En progreso' : 'Pendiente')}`}
            >
              <div className={`relative p-4 ${isCompleted ? 'bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20' : ''}`}>
                <div className="flex items-start gap-4">
                  {/* Circle with step number or checkmark */}
                  <div className="relative shrink-0 mt-1">
                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center font-bold transition-all transform group-hover:scale-110 ${
                        isCompleted
                          ? 'bg-green-500 dark:bg-green-600 text-white'
                          : isCurrent
                            ? 'bg-blue-600 dark:bg-blue-500 scale-110 shadow-md text-white'
                          : 'bg-slate-200 dark:bg-slate-600 text-slate-500 dark:text-slate-400 dark:text-slate-300'
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
                                ? 'text-green-600 dark:text-green-400'
                                : isCurrent
                                  ? 'text-blue-600 dark:text-blue-400'
                                  : 'text-slate-600 dark:text-slate-300 dark:text-slate-400'
                            }
                            aria-hidden="true"
                          />
                        </div>
                      )}
                      <h4 className={`font-semibold text-slate-800 dark:text-slate-200 dark:text-slate-100 leading-tight dark:text-slate-100`}>
                        {t(`events.${stage.event}`, stage.event)}
                      </h4>
                      {isCompleted && (
                        <span className="inline-flex items-center text-[11px] font-bold text-green-700 dark:text-green-400 bg-green-100 dark:bg-green-900/50 px-2 py-0.5 rounded-full" aria-label="Completado">
                          ✓ {t('common.completed', 'Completado')}
                        </span>
                      )}
                      {isCurrent && !isCompleted && (
                        <span className="inline-flex items-center text-[11px] font-bold text-blue-700 dark:text-blue-400 bg-blue-100 dark:bg-blue-900/50 px-2 py-0.5 rounded-full" aria-label="En progreso">
                          → {t('common.current', 'En progreso')}
                        </span>
                      )}
                    </div>
                    <p className={`text-xs text-slate-600 dark:text-slate-300 dark:text-slate-400 leading-snug`}>
                      {t(stage.descKey, stage.descFallback)}
                    </p>
                  </div>

                  {/* Chevron indicator */}
                  <ChevronDown
                    size={18}
                    className={`shrink-0 text-slate-400 dark:text-slate-500 dark:text-slate-400 transition-transform ${
                      isExpanded ? 'rotate-180' : ''
                    }`}
                    aria-hidden="true"
                  />
                </div>

                {/* Expanded content */}
                {isExpanded && (
                  <div id={`stage-content-${index}`} className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-600">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        onStageSelect(stage.event)
                      }}
                      className="w-full py-2.5 px-3 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 dark:from-blue-600 dark:to-blue-700 dark:hover:from-blue-700 dark:hover:to-blue-800 text-white font-semibold rounded-lg transition-all hover:shadow-md active:scale-95"
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
