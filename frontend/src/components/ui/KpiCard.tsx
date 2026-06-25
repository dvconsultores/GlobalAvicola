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
  /** Clase adicional */
  className?: string
}

const COLOR_STYLES: Record<KpiColor, { bg: string; icon: string; text: string; border: string }> = {
  blue:   { bg: 'bg-blue-50',   icon: 'text-blue-600',   text: 'text-blue-700',   border: 'border-blue-200' },
  green:  { bg: 'bg-emerald-50',icon: 'text-emerald-600',text: 'text-emerald-700', border: 'border-emerald-200' },
  amber:  { bg: 'bg-amber-50',  icon: 'text-amber-600',  text: 'text-amber-700',  border: 'border-amber-200' },
  red:    { bg: 'bg-red-50',    icon: 'text-red-600',    text: 'text-red-700',    border: 'border-red-200' },
  slate:  { bg: 'bg-slate-50',  icon: 'text-slate-600',  text: 'text-slate-700',  border: 'border-slate-200' },
  indigo: { bg: 'bg-indigo-50', icon: 'text-indigo-600', text: 'text-indigo-700', border: 'border-indigo-200' },
  teal:   { bg: 'bg-teal-50',   icon: 'text-teal-600',   text: 'text-teal-700',   border: 'border-teal-200' },
}

/**
 * KpiCard — Tarjeta de indicador KPI con icono, valor, label y tendencia.
 *
 * Uso: dashboard, paneles de resumen, SAP manager, etc.
 */
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
  const c = COLOR_STYLES[color]

  return (
    <div
      onClick={onClick}
      className={`
        relative bg-white dark:bg-dark-card rounded-xl border ${c.border} dark:border-slate-700 p-4
        ${onClick ? 'cursor-pointer hover:shadow-md hover:border-blue-300 dark:hover:border-blue-600' : ''}
        transition-all duration-200
        ${className}
      `}
    >
      {/* Icono decorativo */}
      {Icon && (
        <div className={`absolute top-3 right-3 w-10 h-10 rounded-lg ${c.bg} flex items-center justify-center`}>
          <Icon size={20} className={c.icon} />
        </div>
      )}

      {/* Valor principal */}
      <p className="text-2xl font-extrabold text-slate-900 leading-none mb-1">{value}</p>

      {/* Label */}
      <p className="text-xs font-medium text-slate-500">{label}</p>

      {/* Subtítulo opcional */}
      {subtitle && (
        <p className="text-[11px] text-slate-400 mt-0.5">{subtitle}</p>
      )}

      {/* Tendencia */}
      {trend && (
        <div className="flex items-center gap-1 mt-2 pt-2 border-t border-slate-100">
          {trend.direction === 'up' && <TrendingUp size={14} className="text-emerald-500" />}
          {trend.direction === 'down' && <TrendingDown size={14} className="text-red-500" />}
          {trend.direction === 'stable' && <Minus size={14} className="text-slate-400" />}
          <span className={`text-xs font-semibold ${
            trend.direction === 'up' ? 'text-emerald-600' :
            trend.direction === 'down' ? 'text-red-600' :
            'text-slate-500'
          }`}>
            {trend.value}
          </span>
        </div>
      )}
    </div>
  )
}
