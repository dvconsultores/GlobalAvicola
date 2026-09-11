import { useMemo } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '../../stores/auth.store'
import { canAccessCapability, type CapabilitySpec } from '../../auth/navigation'
import { BarChart3, Home, Sprout } from 'lucide-react'

interface MobileNavItem {
 id: string
 path: string
 labelKey: string
 fallback: string
 Icon: any
 /** GA-FE-03 · política única de descubribilidad (RBAC + unidades). */
 spec: CapabilitySpec
}

const ITEMS: MobileNavItem[] = [
 { id: 'poultry', path: '/menu/poultry', labelKey: 'nav.poultry', fallback: 'Gestión Avícola', Icon: Sprout, spec: { permission: 'operations:read', requiresUnits: true } },
 { id: 'home', path: '/', labelKey: 'nav.home', fallback: 'Home', Icon: Home, spec: { permission: 'dashboard:read' } },
 { id: 'kpi', path: '/kpi', labelKey: 'nav.kpi', fallback: 'KPI', Icon: BarChart3, spec: { permission: 'dashboard:read' } },
]

export default function MobileNav() {
 const { t } = useTranslation()
 const location = useLocation()
 const { user } = useAuthStore()

 // GA-FE-03 (§35): la barra inferior no es un modelo aparte — evalúa la MISMA política.
 const items = useMemo(() => ITEMS.filter((it) => canAccessCapability(it.spec, user)), [user])

 const handleNavClick = (itemId: string) => {
 if (itemId === 'poultry') {
 // Siempre abrir Gestión Avícola desde su nivel inicial.
 sessionStorage.removeItem('menuHubStack:poultry')
 }
 }

 const isActive = (path: string) => {
 if (path === '/menu/poultry') return location.pathname.startsWith('/menu/poultry') || location.pathname.startsWith('/poultry')
 if (path === '/') return location.pathname === '/'
 if (path === '/kpi') return location.pathname === '/kpi'
 return location.pathname.startsWith(path)
 }

 // Nada accionable ⇒ nada que pintar (fail-closed; sin barra vacía).
 if (items.length === 0) return null

 return (
 <nav
 className="lg:hidden fixed bottom-0 left-0 right-0 z-30 grid bg-white safe-area-bottom"
 style={{
 gridTemplateColumns: `repeat(${items.length}, minmax(0, 1fr))`,
 borderTop: '1px solid rgba(15,23,42,0.07)',
 boxShadow: '0 -4px 20px -4px rgba(15,23,42,0.08)',
 paddingTop: '4px',
 }}
 >
 {items.map((item) => {
 const active = isActive(item.path)
 return (
 <Link
 key={item.id}
 to={item.path}
 onClick={() => handleNavClick(item.id)}
 className="flex flex-col items-center gap-1 px-3 py-2.5 transition-all"
 >
 <item.Icon
 size={22}
 strokeWidth={active ? 2.3 : 1.8}
 className={active ? 'text-brand-700' : 'text-slate-900'}
 />
 <span className={`text-xs leading-none font-semibold transition-all ${active ? 'text-brand-700' : 'text-slate-900'}`}>
 {t(item.labelKey, item.fallback)}
 </span>
 {active && (
 <span
 className="w-1 h-1 rounded-full"
 style={{ background: 'linear-gradient(135deg, #305e75, #4e8fad)' }}
 />
 )}
 </Link>
 )
 })}
 </nav>
 )
}

