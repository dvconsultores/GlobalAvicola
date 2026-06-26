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
  const { expandedSections, toggleSection, expandContaining } = useSidebar()

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
          'lg:hidden fixed inset-0 z-40 bg-black/50 backdrop-blur-sm',
          'transition-opacity duration-200',
          open ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none',
        ].join(' ')}
      />

      {/* Drawer panel */}
      <nav
        role="navigation"
        aria-label={t('nav.menu', 'Menú')}
        className={[
          'lg:hidden fixed top-0 left-0 h-full w-[82vw] max-w-[300px] z-50',
          'text-white flex flex-col',
          'transition-transform duration-200 ease-out',
          open ? 'translate-x-0' : '-translate-x-full',
        ].join(' ')}
        style={{ background: 'linear-gradient(180deg, #071829 0%, #0F3361 100%)' }}
      >
        {/* Inner highlight */}
        <div className="absolute inset-0 pointer-events-none" style={{ background: 'linear-gradient(90deg, rgba(255,255,255,0.03) 0%, transparent 100%)' }} />

        {/* Drawer header */}
        <div className="relative flex items-center justify-between px-4 py-4">
          <div className="flex items-center gap-2.5">
            <div
              className="w-8 h-8 rounded-xl flex items-center justify-center shrink-0"
              style={{ background: 'linear-gradient(135deg, #1A6DCC 0%, #3B82F6 100%)' }}
            >
              <span className="text-white font-bold text-xs">GA</span>
            </div>
            <div>
              <p className="font-bold text-[13px] leading-none">{t('brand.name', 'Global Avícola')}</p>
              {user && (
                <p className="text-[11px] mt-0.5" style={{ color: 'rgba(147,197,253,0.7)' }}>
                  {[user.first_name, user.last_name].filter(Boolean).join(' ') || user.username}
                </p>
              )}
            </div>
          </div>
          <button
            ref={closeRef}
            onClick={onClose}
            aria-label={t('common.close', 'Cerrar')}
            className="w-8 h-8 flex items-center justify-center rounded-lg transition-all"
            style={{ color: 'rgba(147,197,253,0.7)' }}
            onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.1)'; (e.currentTarget as HTMLElement).style.color = 'white' }}
            onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'transparent'; (e.currentTarget as HTMLElement).style.color = 'rgba(147,197,253,0.7)' }}
          >
            <X size={16} />
          </button>
        </div>

        {/* Divider */}
        <div className="mx-4" style={{ height: '1px', background: 'rgba(255,255,255,0.08)' }} />

        {/* Navigation */}
        <div className="relative flex-1 overflow-y-auto px-3 py-2 sidebar-scroll">
          {sections.map(({ section, items }) => (
            <div key={section.key}>
              <SidebarSection labelKey={section.labelKey} fallback={section.fallback} />
              <div className="space-y-0.5">
                {items.map(item => (
                  <DrawerNavItem
                    key={item.key}
                    item={item}
                    expandedSections={expandedSections}
                    toggleSection={toggleSection}
                    onClose={onClose}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Footer actions */}
        <div className="relative px-3 py-3">
          <div className="mb-3" style={{ height: '1px', background: 'rgba(255,255,255,0.08)' }} />
          <button
            onClick={() => i18n.changeLanguage(i18n.language === 'es' ? 'en' : 'es')}
            className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-[12px] font-medium transition-all mb-1"
            style={{ color: 'rgba(147,197,253,0.75)' }}
            onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.07)'; (e.currentTarget as HTMLElement).style.color = 'white' }}
            onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'transparent'; (e.currentTarget as HTMLElement).style.color = 'rgba(147,197,253,0.75)' }}
          >
            <Globe size={14} />
            {i18n.language === 'es' ? 'Switch to English' : 'Cambiar a Español'}
          </button>
          <button
            onClick={logout}
            className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-[12px] font-medium transition-all"
            style={{ color: 'rgba(147,197,253,0.75)' }}
            onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = 'rgba(239,68,68,0.15)'; (e.currentTarget as HTMLElement).style.color = '#FCA5A5' }}
            onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'transparent'; (e.currentTarget as HTMLElement).style.color = 'rgba(147,197,253,0.75)' }}
          >
            <LogOut size={14} />
            {t('auth.logout', 'Cerrar sesión')}
          </button>
        </div>
      </nav>
    </>
  )
}
