import { type LucideIcon, ChevronRight } from 'lucide-react'

interface MenuCardProps {
  /** Icono Lucide */
  icon: LucideIcon
  /** Título de la opción */
  title: string
  /** Descripción / subtítulo opcional */
  description?: string
  /** Número de paso (badge circular arriba a la derecha) */
  step?: number
  /** Badge numérico (ej. pendientes) */
  badge?: number
  /** Estado activo (resaltado) */
  isActive?: boolean
  /** Acción al hacer clic */
  onClick: () => void
}

/**
 * MenuCard — Tarjeta de menú reutilizable (patrón grilla de opciones).
 *
 * Inspirada en el patrón atenea: icono en recuadro, título, descripción,
 * estados normal / hover / activo, soporte completo de dark mode.
 * Se usa en los hubs de sección para que el usuario elija una operación
 * antes de llegar al formulario.
 */
export default function MenuCard({
  icon: Icon,
  title,
  description,
  step,
  badge,
  isActive = false,
  onClick,
}: MenuCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`group relative flex flex-col items-start text-left p-5 rounded-2xl border-2 transition-all duration-200 active:scale-[0.98] hover:-translate-y-0.5
        ${isActive
          ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-500 shadow-lg shadow-blue-500/10'
          : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 hover:border-blue-300 dark:hover:border-blue-700 shadow-sm hover:shadow-md'
        }`}
    >
      {/* Step number badge */}
      {step !== undefined && (
        <span className="absolute top-3 right-3 inline-flex items-center justify-center w-7 h-7 rounded-full bg-blue-600 text-white text-xs font-bold shadow-md shadow-blue-500/30">
          {step}
        </span>
      )}

      {/* Count badge */}
      {badge !== undefined && badge > 0 && step === undefined && (
        <span className="absolute top-3 right-3 inline-flex items-center justify-center min-w-[22px] h-5 px-1.5 rounded-full bg-rose-500 text-white text-[11px] font-bold">
          {badge > 99 ? '99+' : badge}
        </span>
      )}

      {/* Icon */}
      <span
        className={`inline-flex p-3 rounded-xl mb-4 transition-colors
          ${isActive
            ? 'bg-gradient-to-br from-blue-500 to-blue-700 text-white shadow-md shadow-blue-500/30'
            : 'bg-slate-100 dark:bg-slate-700 text-slate-900 dark:text-slate-100 group-hover:bg-blue-50 dark:group-hover:bg-blue-900/30 group-hover:text-blue-600 dark:group-hover:text-blue-400'
          }`}
      >
        <Icon size={22} strokeWidth={2} />
      </span>

      {/* Title */}
      <h3
        className={`text-sm font-bold leading-tight mb-1
          ${isActive
            ? 'text-blue-700 dark:text-blue-300'
            : 'text-slate-900 dark:text-slate-100'
          }`}
      >
        {title}
      </h3>

      {/* Description */}
      {description && (
        <p className="text-xs text-slate-900 dark:text-slate-100 leading-snug line-clamp-2">
          {description}
        </p>
      )}

      {/* Footer arrow */}
      <span className="mt-auto pt-3 inline-flex items-center gap-0.5 text-xs font-bold text-blue-600 dark:text-blue-400 group-hover:gap-1.5 transition-all">
        <ChevronRight size={14} className="opacity-0 group-hover:opacity-100 transition-opacity" />
      </span>
    </button>
  )
}
