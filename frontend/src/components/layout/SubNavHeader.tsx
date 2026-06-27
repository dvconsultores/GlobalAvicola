import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ArrowLeft } from 'lucide-react'
import Breadcrumbs, { type BreadcrumbItem } from '../ui/Breadcrumbs'

interface SubNavHeaderProps {
  /** Título de la página actual */
  title: string
  /** Clave i18n o texto directo */
  titleKey?: string
  /** Breadcrumbs opcionales */
  breadcrumbs?: BreadcrumbItem[]
  /** Acción al hacer clic en "Atrás" (por defecto: navigate(-1)) */
  onBack?: () => void
  /** Ocultar botón de retroceso */
  hideBack?: boolean
  /** Acciones adicionales en el header (botones, etc.) */
  actions?: React.ReactNode
}

/**
 * SubNavHeader — Header de subpágina con botón de retroceso,
 * breadcrumbs y título.
 *
 * Útil para páginas internas (detalle de lote, formulario, etc.)
 * donde el usuario necesita contexto de dónde está.
 */
export default function SubNavHeader({
  title,
  titleKey,
  breadcrumbs,
  onBack,
  hideBack = false,
  actions,
}: SubNavHeaderProps) {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const displayTitle = titleKey ? t(titleKey, title) : title

  const handleBack = onBack || (() => navigate(-1))

  return (
    <div className="mb-5">
      {/* Breadcrumbs */}
      {breadcrumbs && breadcrumbs.length > 0 && (
        <Breadcrumbs items={breadcrumbs} className="mb-2" />
      )}

      {/* Title row */}
      <div className="flex items-center gap-3">
        {!hideBack && (
          <button
            onClick={handleBack}
            className="w-8 h-8 flex items-center justify-center rounded-lg text-slate-500 hover:text-blue-600 hover:bg-blue-50 transition-all active:scale-95"
            aria-label={t('common.back', 'Atrás')}
          >
            <ArrowLeft size={18} />
          </button>
        )}
        <h1 className="text-xl lg:text-2xl font-extrabold text-slate-900 dark:text-slate-50 leading-tight">
          {displayTitle}
        </h1>
        {actions && (
          <div className="ml-auto flex items-center gap-2">
            {actions}
          </div>
        )}
      </div>
    </div>
  )
}
