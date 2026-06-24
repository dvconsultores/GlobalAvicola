import { type LucideIcon, Plus } from 'lucide-react'
import { useTranslation } from 'react-i18next'

interface EmptyStateProps {
  icon: LucideIcon
  title: string
  description?: string
  action?: {
    label: string
    onClick: () => void
  }
  className?: string
}

/**
 * EmptyState — Estado vacío con icono, mensaje y acción sugerida.
 *
 * Uso: cuando no hay datos en tablas, listas o resultados de búsqueda.
 */
export default function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className = '',
}: EmptyStateProps) {
  const { t } = useTranslation()

  return (
    <div className={`flex flex-col items-center justify-center py-12 px-4 ${className}`}>
      <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mb-4">
        <Icon size={28} className="text-slate-400" />
      </div>
      <h3 className="text-sm font-bold text-slate-600 text-center mb-1">{title}</h3>
      {description && (
        <p className="text-xs text-slate-400 text-center max-w-sm mb-4">{description}</p>
      )}
      {action && (
        <button
          onClick={action.onClick}
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white text-sm font-semibold rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus size={16} />
          {action.label}
        </button>
      )}
    </div>
  )
}
