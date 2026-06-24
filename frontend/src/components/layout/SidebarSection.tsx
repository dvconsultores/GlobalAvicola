import { useTranslation } from 'react-i18next'

interface SidebarSectionProps {
  labelKey: string
  fallback: string
  /** Si está vacío, no renderizar separador (para la sección principal) */
}

/**
 * Separador visual de secciones en el sidebar.
 * Muestra un texto pequeño uppercase entre dos líneas tenues.
 */
export default function SidebarSection({ labelKey, fallback }: SidebarSectionProps) {
  const { t } = useTranslation()
  const label = t(labelKey, fallback)

  // No renderizar si no hay label (sección principal)
  if (!label) return null

  return (
    <div className="px-6 pt-5 pb-1.5">
      <span className="text-[10px] font-bold text-blue-300/50 uppercase tracking-[0.15em] select-none">
        {label}
      </span>
    </div>
  )
}
