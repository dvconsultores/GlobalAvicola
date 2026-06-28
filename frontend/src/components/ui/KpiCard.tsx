import { type LucideIcon, TrendingUp, TrendingDown, Minus } from 'lucide-react'

type KpiColor = 'blue' | 'green' | 'amber' | 'red' | 'slate' | 'indigo' | 'teal'

interface KpiCardProps {
  icon?: LucideIcon
  label: string
  value: string | number
  trend?: {
    direction: 'up' | 'down' | 'stable'
    value: string
  }
  color?: KpiColor
  subtitle?: string
  onClick?: () => void
  className?: string
}

const COLOR_CONFIG: Record<KpiColor, {
  dot: string
  iconBg: string
  iconColor: string
}> = {
  blue:   { dot: 'bg-blue-500',    iconBg: 'bg-blue-50 dark:bg-blue-950/40',       iconColor: 'text-blue-600 dark:text-blue-400' },
  green:  { dot: 'bg-emerald-500', iconBg: 'bg-emerald-50 dark:bg-emerald-950/40', iconColor: 'text-emerald-600 dark:text-emerald-400' },
  amber:  { dot: 'bg-amber-500',   iconBg: 'bg-amber-50 dark:bg-amber-950/40',     iconColor: 'text-amber-600 dark:text-amber-400' },
  red:    { dot: 'bg-red-500',     iconBg: 'bg-red-50 dark:bg-red-950/40',         iconColor: 'text-red-600 dark:text-red-400' },
  slate:  { dot: 'bg-slate-400 dark:bg-slate-600',   iconBg: 'bg-slate-100 dark:bg-slate-700 dark:bg-slate-800',       iconColor: 'text-slate-600 dark:text-slate-300 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500' },
  indigo: { dot: 'bg-indigo-500',  iconBg: 'bg-indigo-50 dark:bg-indigo-950 dark:bg-indigo-950/40',   iconColor: 'text-indigo-600 dark:text-indigo-400 dark:text-indigo-400' },
  teal:   { dot: 'bg-teal-500',    iconBg: 'bg-teal-50 dark:bg-teal-950 dark:bg-teal-950/40',       iconColor: 'text-teal-600 dark:text-teal-400 dark:text-teal-400' },
}

export default function KpiCard({
  icon: Icon,
  label,
  value,
  trend,
  color = 'blue',
  subtitle,
  onClick,
  className = '',
}: KpiCardProps) {
  const cfg = COLOR_CONFIG[color]

  return (
    <div
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      className={[
        'bg-white dark:bg-slate-800 dark:bg-dark-card rounded-xl border border-slate-200 dark:border-slate-700/80 dark:border-dark-border',
        onClick ? 'cursor-pointer transition-shadow hover:shadow-card' : '',
        className,
      ].join(' ')}
    >
      <div className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            {/* Label + dot indicator */}
            <div className="flex items-center gap-1.5 mb-2">
              <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${cfg.dot}`} />
              <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500 leading-none">
                {label}
              </p>
            </div>
            {/* Value */}
            <p className="text-2xl font-semibold text-slate-900 dark:text-slate-100 dark:text-slate-50 dark:text-white stat-value">
              {value}
            </p>
            {subtitle && (
              <p className="text-[11px] text-slate-400 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500 mt-1">{subtitle}</p>
            )}
          </div>
          {/* Icon */}
          {Icon && (
            <div className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${cfg.iconBg}`}>
              <Icon size={16} className={cfg.iconColor} />
            </div>
          )}
        </div>

        {/* Trend */}
        {trend && (
          <div className="flex items-center gap-1 mt-3 pt-3 border-t border-slate-100 dark:border-dark-border">
            {trend.direction === 'up'     && <TrendingUp  size={12} className="text-emerald-500 dark:text-emerald-400 shrink-0" />}
            {trend.direction === 'down'   && <TrendingDown size={12} className="text-red-500 dark:text-red-400 shrink-0" />}
            {trend.direction === 'stable' && <Minus       size={12} className="text-slate-400 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500 shrink-0" />}
            <span className={`text-[11px] font-semibold ${
              trend.direction === 'up'   ? 'text-emerald-600 dark:text-emerald-400' :
              trend.direction === 'down' ? 'text-red-600 dark:text-red-400' :
              'text-slate-500 dark:text-slate-400 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500'
            }`}>
              {trend.value}
            </span>
          </div>
        )}
      </div>
    </div>
  )
}

