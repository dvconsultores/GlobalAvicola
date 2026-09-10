import { useMemo } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '../../stores/auth.store'
import { Bird, LogOut, Settings } from 'lucide-react'
import {
 getNavItemsForViewType,
 getNavSectionsForItems,
 isAnyChildActive,
 filterNavItemsByPermissions,
 type NavItem,
} from '../../data/navigationConfig'
import SidebarSection from './SidebarSection'
import SidebarItem from './SidebarItem'

function NavItemRenderer({ item, pathname }: {
 item: NavItem
 pathname: string
}) {
 const hasChildren = item.children && item.children.length > 0

 // Áreas con sub-opciones → enlazan a su hub en grilla (/menu/:key)
 if (hasChildren) {
 const hubPath = `/menu/${item.key}`
 const active = pathname.startsWith(hubPath) || isAnyChildActive(pathname, item)
 return (
 <SidebarItem
 icon={item.icon}
 labelKey={item.labelKey}
 fallback={item.fallback}
 to={hubPath}
 badge={item.badge}
 forceActive={active}
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

 const navItems = useMemo(() => filterNavItemsByPermissions(getNavItemsForViewType(user?.view_type), user), [user])

 const sections = useMemo(() => {
 const visibleSections = getNavSectionsForItems(navItems)
 return visibleSections.map(section => ({
 section,
 items: navItems.filter(item => item.section === section.key),
 })).filter(s => s.items.length > 0)
 }, [navItems])

 const initials = [user?.first_name?.charAt(0), user?.last_name?.charAt(0)]
 .filter(Boolean).join('').toUpperCase() || user?.username?.charAt(0)?.toUpperCase() || '?'

 return (
 <aside
 className="hidden lg:flex flex-col w-64 min-h-screen fixed left-0 top-0 z-30"
 style={{ background: 'linear-gradient(180deg, #162e3a 0%, #264c5f 50%, #3d748f 100%)' }}
 >
 {/* Subtle inner highlight */}
 <div className="absolute inset-0 pointer-events-none" style={{ background: 'linear-gradient(90deg, rgba(255,255,255,0.03) 0%, transparent 100%)' }} />

 {/* ── Brand area ──────────────────────────────────── */}
 <div className="relative px-5 py-5">
 <div className="flex items-center gap-3">
 <div
 className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0"
 style={{ background: 'linear-gradient(135deg, #5a9bba 0%, #6fabc5 100%)', boxShadow: '0 2px 8px rgba(90,155,186,0.4)' }}
 >
 <Bird size={19} className="text-white" strokeWidth={2} />
 </div>
 <div className="min-w-0">
 <h1 className="text-white text-sm font-bold leading-none tracking-tight truncate">
 {t('brand.name', 'Global Avícola')}
 </h1>
 <p className="text-xs mt-0.5 truncate" style={{ color: 'rgba(111,171,197,0.7)' }}>
 {t('brand.tagline', 'Gestión Operativa')}
 </p>
 </div>
 </div>
 {/* Divider */}
 <div className="mt-4" style={{ height: '1px', background: 'linear-gradient(90deg, rgba(255,255,255,0.1), transparent)' }} />
 </div>

 {/* ── Navigation ──────────────────────────────────── */}
 <nav className="flex-1 px-3 py-1 overflow-y-auto sidebar-scroll">
 {sections.map(({ section, items }) => (
 <div key={section.key}>
 <SidebarSection labelKey={section.labelKey} fallback={section.fallback} />
 <div className="space-y-0.5 mb-2">
 {items.map(item => (
 <NavItemRenderer
 key={item.key}
 item={item}
 pathname={location.pathname}
 />
 ))}
 </div>
 </div>
 ))}
 </nav>

 {/* ── User section ────────────────────────────────── */}
 <div className="relative px-3 py-3">
 {/* Top border */}
 <div className="mb-3" style={{ height: '1px', background: 'rgba(255,255,255,0.08)' }} />

 <div className="flex items-center gap-2.5 px-2 mb-2">
 {/* Avatar */}
 <div
 className="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold text-white shrink-0"
 style={{ background: 'linear-gradient(135deg, #5a9bba 0%, #6fabc5 100%)' }}
 >
 {initials}
 </div>
 <div className="flex-1 min-w-0">
 <p className="text-sm font-semibold text-white truncate leading-none">
 {user?.first_name ? `${user.first_name} ${user.last_name ?? ''}`.trim() : user?.username ?? ''}
 </p>
 <p className="text-xs mt-0.5 truncate" style={{ color: 'rgba(111,171,197,0.6)' }}>
 {user?.username ?? ''}
 </p>
 </div>
 </div>

 <div className="flex gap-1">
 <Link
 to="/profile"
 className="flex-1 flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all"
 style={{ color: 'rgba(111,171,197,0.8)' }}
 onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.07)'; (e.currentTarget as HTMLElement).style.color = 'white' }}
 onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'transparent'; (e.currentTarget as HTMLElement).style.color = 'rgba(111,171,197,0.8)' }}
 >
 <Settings size={13} />
 {t('nav.profile')}
 </Link>
 <button
 onClick={logout}
 className="flex-1 flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all"
 style={{ color: 'rgba(111,171,197,0.8)' }}
 onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = 'rgba(239,68,68,0.15)'; (e.currentTarget as HTMLElement).style.color = '#FCA5A5' }}
 onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'transparent'; (e.currentTarget as HTMLElement).style.color = 'rgba(111,171,197,0.8)' }}
 >
 <LogOut size={13} />
 {t('auth.logout')}
 </button>
 </div>
 </div>
 </aside>
 )
}

