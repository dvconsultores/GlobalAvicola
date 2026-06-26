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
  iconBg: string
  iconColor: string
  accentClass: string
  trendUp: string
  trendDown: string
}> = {
  blue:   { iconBg: 'bg-blue-50 dark:bg-blue-950/40',   iconColor: 'text-blue-600 dark:text-blue-400',   accentClass: 'accent-bar-blue',   trendUp: 'text-emerald-600', trendDown: 'text-red-500' },
  green:  { iconBg: 'bg-emerald-50 dark:bg-emerald-950/40', iconColor: 'text-emerald-600 dark:text-emerald-400', accentClass: 'accent-bar-green', trendUp: 'text-emerald-600', trendDown: 'text-red-500' },
  amber:  { iconBg: 'bg-amber-50 dark:bg-amber-950/40', iconColor: 'text-amber-600 dark:text-amber-400', accentClass: 'accent-bar-amber', trendUp: 'text-emerald-600', trendDown: 'text-red-500' },
  red:    { iconBg: 'bg-red-50 dark:bg-red-950/40',    iconColor: 'text-red-600 dark:text-red-400',    accentClass: 'accent-bar-red',   trendUp: 'text-emerald-600', trendDown: 'text-red-500' },
  slate:  { iconBg: 'bg-slate-100 dark:bg-slate-800',  iconColor: 'text-slate-600 dark:text-slate-400', accentClass: 'accent-bar-slate',  trendUp: 'text-emerald-600', trendDown: 'text-red-500' },
  indigo: { iconBg: 'bg-indigo-50 dark:bg-indigo-950/40', iconColor: 'text-indigo-600 dark:text-indigo-400', accentClass: 'accent-bar-indigo', trendUp: 'text-emerald-600', trendDown: 'text-red-500' },
  teal:   { iconBg: 'bg-teal-50 dark:bg-teal-950/40',  iconColor: 'text-teal-600 dark:text-teal-400',  accentClass: 'accent-bar-teal',   trendUp: 'text-emerald-600', trendDown: 'text-red-500' },
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
        'relative bg-white dark:bg-dark-card rounded-2xl overflow-hidden accent-bar',
        cfg.accentClass,
        'border border-slate-100 dark:border-dark-border shadow-card',
        onClick ? 'cursor-pointer card-hover' : '',
        className,
      ].join(' ')}
    >
      <div className="px-5 pt-5 pb-4">
        <div className="flex items-start justify-between gap-3">
          {/* Value + label */}
          <div className="min-w-0 flex-1">
            <p className="text-[28px] font-bold text-slate-900 dark:text-white leading-none tracking-tight animate-number">
              {value}
            </p>
            <p className="text-xs font-medium text-slate-500 dark:text-slate-400 mt-1.5 leading-snug">
              {label}
            </p>
            {subtitle && (
              <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-0.5">{subtitle}</p>
            )}
          </div>

          {/* Icon */}
          {Icon && (
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${cfg.iconBg}`}>
              <Icon size={18} className={cfg.iconColor} />
            </div>
          )}
        </div>

        {/* Trend */}
        {trend && (
          <div className="flex items-center gap-1.5 mt-3 pt-3 border-t border-slate-100 dark:border-dark-border">
            {trend.direction === 'up'     && <TrendingUp  size={13} className="text-emerald-500 shrink-0" />}
            {trend.direction === 'down'   && <TrendingDown size={13} className="text-red-500 shrink-0" />}
            {trend.direction === 'stable' && <Minus       size={13} className="text-slate-400 shrink-0" />}
            <span className={`text-xs font-semibold ${
              trend.direction === 'up'     ? 'text-emerald-600 dark:text-emerald-400' :
              trend.direction === 'down'   ? 'text-red-600 dark:text-red-400' :
              'text-slate-500 dark:text-slate-400'
            }`}>
              {trend.value}
            </span>
          </div>
        )}
      </div>
    </div>
  )
}

