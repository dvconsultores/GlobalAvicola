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
 blue: { dot: 'bg-blue-500', iconBg: 'bg-blue-50', iconColor: 'text-blue-600' },
 green: { dot: 'bg-emerald-500', iconBg: 'bg-emerald-50', iconColor: 'text-emerald-600' },
 amber: { dot: 'bg-amber-500', iconBg: 'bg-amber-50', iconColor: 'text-amber-600' },
 red: { dot: 'bg-red-500', iconBg: 'bg-red-50', iconColor: 'text-red-600' },
 slate: { dot: 'bg-slate-400', iconBg: 'bg-slate-100', iconColor: 'text-slate-600' },
 indigo: { dot: 'bg-indigo-500', iconBg: 'bg-indigo-50/40', iconColor: 'text-indigo-600' },
 teal: { dot: 'bg-teal-500', iconBg: 'bg-teal-50/40', iconColor: 'text-teal-600' },
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
 'bg-white rounded-xl border border-slate-200/80',
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
 <p className="text-xs font-semibold uppercase tracking-wide text-slate-400 leading-none">
 {label}
 </p>
 </div>
 {/* Value */}
 <p className="text-2xl font-semibold text-slate-900 stat-value">
 {value}
 </p>
 {subtitle && (
 <p className="text-xs text-slate-400 mt-1">{subtitle}</p>
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
 <div className="flex items-center gap-1 mt-3 pt-3 border-t border-slate-100">
 {trend.direction === 'up' && <TrendingUp size={12} className="text-emerald-500 shrink-0" />}
 {trend.direction === 'down' && <TrendingDown size={12} className="text-red-500 shrink-0" />}
 {trend.direction === 'stable' && <Minus size={12} className="text-slate-400 shrink-0" />}
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
 </div>
 )
}

