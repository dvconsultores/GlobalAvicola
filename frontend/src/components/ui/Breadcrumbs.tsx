import { Fragment } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ChevronRight, Home } from 'lucide-react'

export interface BreadcrumbItem {
  /** Clave i18n para el label */
  label: string
  /** Texto fallback si no hay traducción */
  fallback?: string
  /** Ruta (opcional — el último item no tiene link) */
  to?: string
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[]
  /** Mostrar icono de casa al inicio */
  showHomeIcon?: boolean
  /** Clase adicional */
  className?: string
}

/**
 * Breadcrumbs — Migas de pan jerárquicas.
 *
 * Muestra la ruta de navegación actual con links clickeables
 * y el último item como texto plano (posición actual).
 */
export default function Breadcrumbs({
  items,
  showHomeIcon = true,
  className = '',
}: BreadcrumbsProps) {
  const { t } = useTranslation()

  if (!items || items.length === 0) return null

  return (
    <nav aria-label="Breadcrumb" className={`flex items-center gap-1 text-xs font-medium ${className}`}>
      {showHomeIcon && items.length > 1 && (
        <>
          <Link to="/" className="text-slate-400 hover:text-blue-600 transition-colors shrink-0">
            <Home size={14} />
          </Link>
          <ChevronRight size={12} className="text-slate-300 shrink-0" />
        </>
      )}
      {items.map((item, index) => {
        const isLast = index === items.length - 1
        const label = t(item.label, item.fallback ?? item.label)

        return (
          <Fragment key={index}>
            {isLast ? (
              <span className="text-slate-900 dark:text-slate-50 font-semibold truncate max-w-[200px]" aria-current="page">
                {label}
              </span>
            ) : (
              <Link
                to={item.to || '#'}
                className="text-slate-500 hover:text-blue-600 transition-colors truncate max-w-[160px] shrink-0"
              >
                {label}
              </Link>
            )}
            {!isLast && (
              <ChevronRight size={12} className="text-slate-300 shrink-0" />
            )}
          </Fragment>
        )
      })}
    </nav>
  )
}
