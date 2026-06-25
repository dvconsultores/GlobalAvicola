import { useState, useEffect, useRef } from 'react'
import { useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ChevronDown, type LucideIcon } from 'lucide-react'
import { isAnyChildActive, type NavItem } from '../../data/navigationConfig'
import SidebarItem from './SidebarItem'

interface SidebarSubmenuProps {
  icon: LucideIcon
  labelKey: string
  fallback: string
  /** Items hijos del submenú */
  children: NavItem[]
  /** Si está expandido inicialmente (control externo) */
  expanded?: boolean
  /** Callback para toggle externo */
  onToggle?: () => void
  /** Callback al hacer clic en un hijo (para cerrar drawer) */
  onChildClick?: () => void
}

/**
 * Submenú colapsable del sidebar.
 * Muestra un header clickeable con chevron animado y expande/colapsa hijos.
 * Se expande automáticamente si algún hijo está activo.
 *
 * NOTA: El control de expansión puede ser externo (vía props `expanded` + `onToggle`)
 * o interno (auto-gestionado). Si se proporciona `expanded`, se ignora el estado interno.
 */
export default function SidebarSubmenu({
  icon: Icon,
  labelKey,
  fallback,
  children: items,
  expanded: externalExpanded,
  onToggle,
  onChildClick,
}: SidebarSubmenuProps) {
  const { t } = useTranslation()
  const location = useLocation()
  const contentRef = useRef<HTMLDivElement>(null)

  // Control interno SOLO si no hay control externo
  const [internalExpanded, setInternalExpanded] = useState(
    () => items.some(item => isAnyChildActive(location.pathname, item)),
  )

  // Si hay control externo, usamos ese; si no, el interno
  const isControlled = externalExpanded !== undefined
  const isExpanded = isControlled ? externalExpanded : internalExpanded
  const anyChildActive = items.some(item => isAnyChildActive(location.pathname, item))

  // Auto-expandir si un hijo está activo (solo en modo no controlado)
  useEffect(() => {
    if (!isControlled && anyChildActive) {
      setInternalExpanded(true)
    }
  }, [location.pathname, isControlled, anyChildActive])

  const handleToggle = () => {
    if (isControlled && onToggle) {
      onToggle()
    } else if (!isControlled) {
      setInternalExpanded(prev => !prev)
    }
  }

  return (
    <div className="select-none">
      {/* Header clickeable */}
      <button
        onClick={handleToggle}
        className={`
          w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-150
          ${anyChildActive
            ? 'bg-blue-600/20 text-white'
            : 'text-blue-100/80 hover:bg-blue-700/40 hover:text-white'
          }
        `}
        aria-expanded={isExpanded}
      >
        <span className="shrink-0 flex items-center justify-center" style={{ width: 20, height: 20 }}>
          <Icon size={18} strokeWidth={anyChildActive ? 2.2 : 1.8} />
        </span>
        <span className="flex-1 truncate text-left">{t(labelKey, fallback)}</span>
        <span className="text-[10px] font-bold text-blue-300/50 mr-1">{items.length}</span>
        <ChevronDown
          size={16}
          className={`shrink-0 text-blue-300/60 transition-transform duration-200 ${
            isExpanded ? 'rotate-0' : '-rotate-90'
          }`}
        />
      </button>

      {/* Contenido colapsable con animación de altura */}
      <div
        ref={contentRef}
        className="overflow-hidden transition-all duration-200 ease-in-out"
        style={{
          maxHeight: isExpanded ? contentRef.current?.scrollHeight ?? 500 : 0,
          opacity: isExpanded ? 1 : 0,
        }}
      >
        <div className="py-1 space-y-0.5">
          {items.map((child) => {
            // Si el hijo tiene más hijos, renderizar como SidebarSubmenu anidado
            if (child.children && child.children.length > 0) {
              return (
                <SidebarSubmenu
                  key={child.key}
                  icon={child.icon}
                  labelKey={child.labelKey}
                  fallback={child.fallback}
                  children={child.children}
                  onChildClick={onChildClick}
                />
              )
            }
            // Si es un item hoja, renderizar SidebarItem
            if (child.to) {
              return (
                <SidebarItem
                  key={child.key}
                  icon={child.icon}
                  labelKey={child.labelKey}
                  fallback={child.fallback}
                  to={child.to}
                  depth={1}
                  badge={child.badge}
                  onClick={onChildClick}
                />
              )
            }
            return null
          })}
        </div>
      </div>
    </div>
  )
}
