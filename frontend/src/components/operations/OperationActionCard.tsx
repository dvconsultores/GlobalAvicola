import { ArrowRight } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

interface OperationActionCardProps {
  title: string
  description: string
  icon: LucideIcon
  bgColor: string
  borderColor: string
  textColor: string
  onClick: () => void
  actionLabel?: string
  badge?: string
  disabled?: boolean
}

/**
 * OperationActionCard — Visual card for a single operation/action
 * Designed to be tappable on mobile, with icon, title, description
 */
export default function OperationActionCard({
  title,
  description,
  icon: Icon,
  bgColor,
  borderColor,
  textColor,
  onClick,
  actionLabel,
  badge,
  disabled = false,
}: OperationActionCardProps) {

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`group w-full text-left transition-all rounded-xl border-2 overflow-hidden ${
        disabled
          ? 'opacity-50 cursor-not-allowed'
          : `hover:shadow-lg hover:scale-102 active:scale-98 ${borderColor}`
      }`}
    >
      <div className={`p-4 ${bgColor} dark:bg-slate-800`}>
        <div className="flex items-start gap-3">
          {/* Icon */}
          <div
            className={`shrink-0 w-12 h-12 rounded-xl flex items-center justify-center transition-transform group-hover:scale-110 group-hover:-rotate-6 ${textColor} dark:brightness-110`}
          >
            <Icon size={24} />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-0.5">
              <h4 className="font-bold text-slate-800 dark:text-slate-100 leading-tight dark:text-slate-100">{title}</h4>
              {badge && (
                <span className="inline-flex text-[10px] font-bold text-blue-700 dark:text-blue-300 bg-blue-100 dark:bg-blue-900/50 px-1.5 py-0.5 rounded-full">
                  {badge}
                </span>
              )}
            </div>
            <p className="text-xs text-slate-600 leading-snug dark:text-slate-400">{description}</p>
          </div>

          {/* Arrow */}
          <ArrowRight
            size={18}
            className={`shrink-0 ${textColor} dark:brightness-110 group-hover:translate-x-1 transition-transform`}
          />
        </div>
      </div>

      {/* Action label at bottom */}
      {actionLabel && (
        <div className="px-4 py-2.5 bg-white dark:bg-slate-800 border-t border-slate-100 dark:border-slate-700 flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-600 dark:text-slate-400">{actionLabel}</span>
          <span className={`text-xs font-bold ${textColor} dark:brightness-110`}>→</span>
        </div>
      )}
    </button>
  )
}
