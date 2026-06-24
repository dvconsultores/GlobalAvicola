/**
 * MobileDrawer — slide-in lateral menu para operadores móviles
 * Se activa con el botón hamburger en Header.tsx
 * Overlay + 150ms slide, cierra con Escape o click fuera
 *
 * REDISEÑADO: Muestra la misma jerarquía completa que el Sidebar desktop,
 * con secciones, submenús colapsables y navegación completa.
 */
import { useEffect, useRef, useMemo } from 'react'
import { useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '../../stores/auth.store'
import { X, Globe, LogOut } from 'lucide-react'
import { NAV_SECTIONS, NAV_ITEMS, getSectionKeyForPath, type NavItem } from '../../data/navigationConfig'
import { useSidebar } from '../../hooks/useSidebar'
import SidebarSection from './SidebarSection'
import SidebarItem from './SidebarItem'
import SidebarSubmenu from './SidebarSubmenu'

interface MobileDrawerProps {
  open: boolean
  onClose: () => void
}

function DrawerNavItem({ item, expandedSections, toggleSection, onClose }: {
  item: NavItem
  expandedSections: Record<string, boolean>
  toggleSection: (key: string) => void
  onClose: () => void
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
        onChildClick={onClose}
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
        onClick={onClose}
      />
    )
  }

  return null
}

export default function MobileDrawer({ open, onClose }: MobileDrawerProps) {
  const { t, i18n } = useTranslation()
  const { user, logout } = useAuthStore()
  const location = useLocation()
  const closeRef = useRef<HTMLButtonElement>(null)
  const { isExpanded, toggleSection, expandContaining } = useSidebar()

  // Expandir automáticamente la sección de la ruta activa
  useMemo(() => {
    const sectionKey = getSectionKeyForPath(location.pathname)
    if (sectionKey) {
      expandContaining(sectionKey)
    }
  }, [location.pathname, expandContaining])

  // Close on Escape
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [open, onClose])

  // Prevent body scroll
  useEffect(() => {
    document.body.style.overflow = open ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [open])

  // Focus close button when opens
  useEffect(() => {
    if (open) setTimeout(() => closeRef.current?.focus(), 50)
  }, [open])

  // Close on location change (after nav)
  useEffect(() => { onClose() }, [location.pathname, onClose])

  // Agrupar items por sección
  const sections = useMemo(() => {
    return NAV_SECTIONS.map(section => ({
      section,
      items: NAV_ITEMS.filter(item => item.section === section.key),
    })).filter(s => s.items.length > 0)
  }, [])

  return (
    <>
      {/* Overlay */}
      <div
        aria-hidden="true"
        onClick={onClose}
        className={[
          'lg:hidden fixed inset-0 z-40 bg-black/40 backdrop-blur-[2px]',
          'transition-opacity duration-150',
          open ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none',
        ].join(' ')}
      />

      {/* Drawer panel */}
      <nav
        role="navigation"
        aria-label={t('nav.menu', 'Menú')}
        className={[
          'lg:hidden fixed top-0 left-0 h-full w-[80vw] max-w-sm z-50',
          'bg-[#1E3A5F] text-white flex flex-col',
          'transition-transform duration-150 ease-out',
          open ? 'translate-x-0' : '-translate-x-full',
        ].join(' ')}
      >
        {/* Drawer header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/10">
          <div>
            <p className="font-bold text-sm">{t('brand.name', 'Global Avícola')}</p>
            {user && <p className="text-xs text-blue-300 mt-0.5">{[user.first_name, user.last_name].filter(Boolean).join(' ') || user.username}</p>}
          </div>
          <button
            ref={closeRef}
            onClick={onClose}
            aria-label={t('common.close', 'Cerrar')}
            className="w-8 h-8 flex items-center justify-center rounded-lg text-blue-300 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Navigation — jerarquía completa como sidebar desktop */}
        <div className="flex-1 overflow-y-auto px-3 py-3">
          {sections.map(({ section, items }) => (
            <div key={section.key}>
              <SidebarSection labelKey={section.labelKey} fallback={section.fallback} />
              <div className="space-y-0.5">
                {items.map(item => (
                  <DrawerNavItem
                    key={item.key}
                    item={item}
                    expandedSections={isExpanded}
                    toggleSection={toggleSection}
                    onClose={onClose}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Footer actions */}
        <div className="px-4 py-4 border-t border-white/10 space-y-1">
          <button
            onClick={() => i18n.changeLanguage(i18n.language === 'es' ? 'en' : 'es')}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-blue-200 hover:bg-white/10 hover:text-white transition-colors"
          >
            <Globe size={16} />
            {i18n.language === 'es' ? 'English' : 'Español'}
          </button>
          <button
            onClick={logout}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-blue-200 hover:bg-white/10 hover:text-white transition-colors"
          >
            <LogOut size={16} />
            {t('auth.logout', 'Cerrar sesión')}
          </button>
        </div>
      </nav>
    </>
  )
}
