/**
 * MobileDrawer — slide-in grid menu para operadores móviles
 * Secciones como tarjetas en grilla → sub-sección con back button → items grid
 */
import { useState, useEffect, useRef, useMemo } from 'react'
import { useLocation, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '../../stores/auth.store'
import { normalizeLanguage, nextLanguage } from '../../i18n'
import { X, Globe, LogOut, ArrowLeft, Bird, Sprout, Home, ShieldCheck, RefreshCw, BarChart3, Database, Settings, Users, ClipboardList, CheckCircle } from 'lucide-react'
import { getNavItemsForViewType, getNavSectionsForItems, type NavItem } from '../../data/navigationConfig'
import { filterNavItemsBySession } from '../../auth/navigation'

interface MobileDrawerProps { open: boolean; onClose: () => void }

// Section icon mapping
const SECTION_ICONS: Record<string, React.ComponentType<{size?: number; className?: string}>> = {
 operational: Sprout,
 review: ShieldCheck,
 integration: RefreshCw,
 reports: BarChart3,
 administration: Settings,
}

const ITEM_ICON_MAP: Record<string, React.ComponentType<{size?: number; className?: string}>> = {
 poultry: Bird,
 review: ClipboardList,
 approvals: CheckCircle,
 sap: RefreshCw,
 reports: BarChart3,
 audit: ShieldCheck,
 masters: Database,
 settings: Settings,
 users: Users,
 profile: Users,
}

export default function MobileDrawer({ open, onClose }: MobileDrawerProps) {
 const { t, i18n } = useTranslation()
 const { user, logout } = useAuthStore()
 const location = useLocation()
 const [selectedSection, setSelectedSection] = useState<string | null>(null)
 const [itemStack, setItemStack] = useState<NavItem[]>([])
 const closeRef = useRef<HTMLButtonElement>(null)
 const currentLang = normalizeLanguage(i18n.resolvedLanguage || i18n.language)

 const navItems = useMemo(() => filterNavItemsBySession(getNavItemsForViewType(user?.view_type), user), [user])
 const navSections = useMemo(
 () => getNavSectionsForItems(navItems).filter((s) => s.key !== 'main'),
 [navItems],
 )

 // Build section index (excluding "main" because dashboard is shown as shortcut card)
 const sectionMap = useMemo(() => {
 const map: Record<string, NavItem[]> = {}
 for (const s of navSections) {
 const items = navItems.filter((i) => i.section === s.key)
 if (items.length > 0) map[s.key] = items
 }
 return map
 }, [navSections, navItems])

 useEffect(() => { if (!open) return; const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }; document.addEventListener('keydown', onKey); return () => document.removeEventListener('keydown', onKey) }, [open, onClose])
 useEffect(() => { document.body.style.overflow = open ? 'hidden' : ''; return () => { document.body.style.overflow = '' } }, [open])
 useEffect(() => { if (open) setTimeout(() => closeRef.current?.focus(), 50) }, [open])
 useEffect(() => { onClose(); setSelectedSection(null); setItemStack([]) }, [location.pathname])
 useEffect(() => {
 if (!open) {
 setSelectedSection(null)
 setItemStack([])
 }
 }, [open])

 const sectionEntries = Object.entries(sectionMap)
 const currentSection = selectedSection ? navSections.find(s => s.key === selectedSection) : null
 const currentNode = itemStack.length > 0 ? itemStack[itemStack.length - 1] : null
 const currentItems = currentNode
 ? (currentNode.children ?? [])
 : (selectedSection ? sectionMap[selectedSection] || [] : [])

 const handleBack = () => {
 if (itemStack.length > 0) {
 setItemStack((prev) => prev.slice(0, -1))
 return
 }
 setSelectedSection(null)
 }

 return (
 <>
 {/* Overlay */}
 <div aria-hidden="true" onClick={onClose}
 className={`lg:hidden fixed inset-0 z-40 bg-black/50 backdrop-blur-sm transition-opacity duration-200 ${open ? 'opacity-100' : 'opacity-0 pointer-events-none'}`} />

 {/* Panel */}
 <nav data-state={open ? 'open' : 'closed'} className={`lg:hidden fixed top-0 left-0 h-full w-[88vw] max-w-[340px] z-50 flex flex-col bg-white transition-transform duration-200 ease-out ${open ? 'translate-x-0' : '-translate-x-full'}`}>
 {/* Header */}
 <div className="flex items-center justify-between px-4 py-3.5 border-b border-slate-100">
 {selectedSection ? (
 <button onClick={handleBack}
 className="flex items-center gap-2 text-slate-900">
 <ArrowLeft size={18} />
 <span className="text-sm font-semibold">
 {currentNode
 ? t(currentNode.labelKey, currentNode.fallback)
 : t(currentSection?.labelKey || '', currentSection?.fallback || '')}
 </span>
 </button>
 ) : (
 <div className="flex items-center gap-2.5">
 <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#5a9bba] to-[#6fabc5] flex items-center justify-center">
 <Bird size={15} className="text-white" />
 </div>
 <span className="font-bold text-slate-900 text-sm">{t('brand.name', 'Global Avícola')}</span>
 </div>
 )}
 <button ref={closeRef} onClick={onClose} aria-label={t('common.close', 'Cerrar')} className="w-8 h-8 flex items-center justify-center rounded-lg text-slate-900 hover:bg-slate-100:bg-slate-800">
 <X size={18} />
 </button>
 </div>

 {/* Body */}
 <div className="flex-1 overflow-y-auto p-3">
 {!selectedSection ? (
 /* ── SECTION GRID ── */
 <div className="grid grid-cols-2 gap-2.5">
 {/* Dashboard shortcut */}
 <Link to="/" onClick={onClose}
 className="col-span-2 flex items-center gap-3 p-3.5 rounded-xl bg-slate-50 border border-slate-100 active:bg-slate-100 transition-colors">
 <Home size={20} className="text-blue-600 shrink-0" />
 <span className="text-sm font-semibold text-slate-900">{t('nav.home', 'Inicio')}</span>
 </Link>

 {sectionEntries.map(([key, items]) => {
 const section = navSections.find(s => s.key === key)
 if (!section) return null
 const Icon = SECTION_ICONS[key]
 return (
 <button key={key} onClick={() => setSelectedSection(key)}
 className="flex flex-col items-center gap-2 p-4 rounded-xl bg-slate-50 border border-slate-100 active:bg-slate-100:bg-slate-700 transition-colors text-center">
 {Icon && <Icon size={22} className="text-blue-600" />}
 <div>
 <span className="text-xs font-semibold text-slate-900 block">{t(section.labelKey, section.fallback)}</span>
 <span className="text-xs text-slate-900">{items.length} {t('common.options', 'opciones')}</span>
 </div>
 </button>
 )
 })}
 </div>
 ) : (
 /* ── ITEMS GRID ── */
 <div className="space-y-2">
 {currentItems.map(item => {
 const Icon = item.icon || ITEM_ICON_MAP[item.key]
 if (item.children && item.children.length > 0) {
 return (
 <div key={item.key} className="space-y-1">
 <button
 type="button"
 onClick={() => setItemStack((prev) => [...prev, item])}
 className="w-full flex items-center gap-3 p-3 rounded-lg bg-slate-50 border border-slate-100 active:bg-slate-100:bg-slate-700 transition-colors"
 >
 {Icon && <Icon size={18} className="text-blue-600 shrink-0" />}
 <div className="flex-1 min-w-0 text-left">
 <span className="text-sm font-semibold text-slate-900 block truncate">{t(item.labelKey, item.fallback)}</span>
 <span className="text-xs text-slate-900">{item.children.length} {t('common.options', 'opciones')}</span>
 </div>
 <ArrowLeft size={14} className="text-slate-900 rotate-180" />
 </button>
 </div>
 )
 }

 if (!item.to) return null

 return (
 <Link key={item.key} to={item.to || '#'} onClick={onClose}
 className="flex items-center gap-3 p-3 rounded-lg bg-slate-50 border border-slate-100 active:bg-slate-100:bg-slate-700 transition-colors">
 {Icon && <Icon size={18} className="text-blue-600 shrink-0" />}
 <div className="flex-1 min-w-0">
 <span className="text-sm font-semibold text-slate-900">{t(item.labelKey, item.fallback)}</span>
 </div>
 {item.badge && <span className="text-xs font-bold bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded-full">{item.badge}</span>}
 </Link>
 )
 })}
 </div>
 )}
 </div>

 {/* Footer */}
 <div className="border-t border-slate-100 px-3 py-2 space-y-1">
 <button onClick={() => i18n.changeLanguage(nextLanguage(i18n.resolvedLanguage || i18n.language))}
 className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium text-slate-900 hover:bg-slate-50:bg-slate-800 transition-colors">
 <Globe size={14} />
 {currentLang === 'es' ? t('lang.toggleEn', 'English') : t('lang.toggleEs', 'Español')}
 </button>
 {user && (
 <p className="text-xs text-slate-900 px-3 text-center">
 {[user.first_name, user.last_name].filter(Boolean).join(' ') || user.username}
 </p>
 )}
 <button onClick={logout}
 className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium text-red-500 hover:bg-red-50:bg-red-950/30 transition-colors">
 <LogOut size={14} />
 {t('auth.logout', 'Cerrar sesión')}
 </button>
 </div>
 </nav>
 </>
 )
}
