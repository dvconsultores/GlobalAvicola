import { Link, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { type LucideIcon } from 'lucide-react'
import { isPathActive } from '../../data/navigationConfig'

interface SidebarItemProps {
  icon?: LucideIcon
  labelKey: string
  fallback: string
  to: string
  /** Nivel de indentación: 0=principal, 1=sub, 2=sub-sub */
  depth?: number
  /** Badge numérico opcional */
  badge?: number
  /** Callback al hacer clic (útil en drawer para cerrar) */
  onClick?: () => void
}

/**
 * Item individual de navegación en el sidebar.
 * Soporta icono, label, ruta, indentación por profundidad y badge.
 */
export default function SidebarItem({
  icon: Icon,
  labelKey,
  fallback,
  to,
  depth = 0,
  badge,
  onClick,
}: SidebarItemProps) {
  const { t } = useTranslation()
  const location = useLocation()
  const active = isPathActive(location.pathname, to)

  const depthStyles = [
    'pl-4 pr-3',
    'pl-11 pr-3',
    'pl-16 pr-3',
  ]

  return (
    <Link
      to={to}
      onClick={onClick}
      className={`
        flex items-center gap-3 py-2 rounded-lg text-sm font-medium transition-all duration-150
        ${depthStyles[depth] ?? depthStyles[0]}
        ${active
          ? 'bg-blue-600/30 text-white border-l-2 border-blue-400 shadow-sm'
          : 'text-blue-100/80 hover:bg-blue-700/40 hover:text-white border-l-2 border-transparent'
        }
      `}
      aria-current={active ? 'page' : undefined}
    >
      {Icon && (
        <span className="shrink-0 flex items-center justify-center" style={{ width: 20, height: 20 }}>
          <Icon size={18} strokeWidth={active ? 2.2 : 1.8} />
        </span>
      )}
      <span className="flex-1 truncate text-sm">{t(labelKey, fallback)}</span>
      {badge !== undefined && badge > 0 && (
        <span className="inline-flex items-center justify-center min-w-[20px] h-5 px-1.5 rounded-full bg-blue-500/40 text-[10px] font-bold text-white">
          {badge > 99 ? '99+' : badge}
        </span>
      )}
    </Link>
  )
}
