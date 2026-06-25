import { useMemo } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '../../stores/auth.store'
import { User } from 'lucide-react'
import { NAV_SECTIONS, NAV_ITEMS, getSectionKeyForPath, type NavItem } from '../../data/navigationConfig'
import { useSidebar } from '../../hooks/useSidebar'
import SidebarSection from './SidebarSection'
import SidebarItem from './SidebarItem'
import SidebarSubmenu from './SidebarSubmenu'

/**
 * Renderiza un item del menú que puede ser:
 * - Item simple (con ruta)
 * - Submenú colapsable (con hijos)
 */
function NavItemRenderer({ item, expandedSections, toggleSection }: {
  item: NavItem
  expandedSections: Record<string, boolean>
  toggleSection: (key: string) => void
}) {
  const hasChildren = item.children && item.children.length > 0

  if (hasChildren) {
    return (
      <SidebarSubmenu
        icon={item.icon}
        labelKey={item.labelKey}
        fallback={item.fallback}
        children={item.children!}
        expanded={expandedSections[item.key]}
        onToggle={() => toggleSection(item.key)}
      />
    )
  }

  if (item.to) {
    return (
      <SidebarItem
        icon={item.icon}
        labelKey={item.labelKey}
        fallback={item.fallback}
        to={item.to}
        badge={item.badge}
      />
    )
  }

  return null
}

export default function Sidebar() {
  const { t } = useTranslation()
  const location = useLocation()
  const { logout, user } = useAuthStore()
  const { expandedSections, toggleSection, expandContaining } = useSidebar()

  // Expandir automáticamente la sección que contiene la ruta activa
  useMemo(() => {
    const sectionKey = getSectionKeyForPath(location.pathname)
    if (sectionKey) {
      expandContaining(sectionKey)
    }
  }, [location.pathname, expandContaining])

  // Agrupar items por sección
  const sections = useMemo(() => {
    return NAV_SECTIONS.map(section => ({
      section,
      items: NAV_ITEMS.filter(item => item.section === section.key),
    })).filter(s => s.items.length > 0)
  }, [])

  return (
    <aside className="hidden lg:flex flex-col w-64 bg-[#1E3A5F] text-white min-h-screen fixed left-0 top-0 z-30">
      {/* Logo */}
      <div className="px-6 py-5 border-b border-blue-900">
        <h1 className="text-lg font-bold tracking-tight">{t('brand.name')}</h1>
        <p className="text-xs text-blue-300">{t('brand.tagline')}</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-2 overflow-y-auto scrollbar-thin scrollbar-thumb-blue-800 scrollbar-track-transparent">
        {sections.map(({ section, items }) => (
          <div key={section.key}>
            <SidebarSection labelKey={section.labelKey} fallback={section.fallback} />
            <div className="space-y-0.5">
              {items.map(item => (
                <NavItemRenderer
                  key={item.key}
                  item={item}
                  expandedSections={expandedSections}
                  toggleSection={toggleSection}
                />
              ))}
            </div>
          </div>
        ))}
      </nav>

      {/* User section */}
      <div className="px-4 py-4 border-t border-blue-900/60">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-xs font-bold shrink-0">
            {user?.first_name?.charAt(0) || user?.username?.charAt(0) || '?'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{user?.first_name || user?.username || ''}</p>
            <p className="text-xs text-blue-300 truncate">{user?.username || ''}</p>
          </div>
        </div>
        <Link to="/profile" className="block text-xs text-blue-300 hover:text-white transition mb-1.5 flex items-center gap-1.5">
          <User size={14} aria-hidden="true" /> {t('nav.profile')}
        </Link>
        <button
          onClick={logout}
          className="w-full text-left text-xs text-blue-300 hover:text-white transition"
        >
          {t('auth.logout')} →
        </button>
      </div>
    </aside>
  )
}
