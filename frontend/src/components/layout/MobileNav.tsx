import { Link, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Home, Bird, FileText, TrendingUp, Clock } from 'lucide-react'

// Mobile nav: field operators — Home, Lots, Operations, KPIs, My Pending
const mobileItems = [
  { path: '/',            labelKey: 'nav.home',       Icon: Home,       fallback: 'Home' },
  { path: '/lots',        labelKey: 'nav.lots',        Icon: Bird,       fallback: 'Lotes' },
  { path: '/operations',  labelKey: 'nav.operations',  Icon: FileText,   fallback: 'Registrar' },
  { path: '/reports',     labelKey: 'nav.reports',     Icon: TrendingUp, fallback: 'KPIs' },
  { path: '/my-pending',  labelKey: 'nav.myPending',   Icon: Clock,      fallback: 'Pendientes' },
]

export default function MobileNav() {
  const { t } = useTranslation()
  const location = useLocation()
  // Determine if a path is active (including nested routes)
  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/'
    return location.pathname.startsWith(path)
  }

  return (
    <nav className="lg:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 z-30 flex justify-around py-2 safe-area-bottom">
      {mobileItems.map((item) => {
        const active = isActive(item.path)
        return (
          <Link
            key={item.path}
            to={item.path}
            className={`flex flex-col items-center gap-0.5 px-2 py-1 rounded-lg text-xs transition min-w-[56px] ${
              active
                ? 'text-[#2563EB] font-semibold'
                : 'text-slate-500'
            }`}
          >
            <item.Icon size={22} />
            <span className="text-[10px] leading-tight text-center">{t(item.labelKey, item.fallback)}</span>
          </Link>
        )
      })}
    </nav>
  )
}
