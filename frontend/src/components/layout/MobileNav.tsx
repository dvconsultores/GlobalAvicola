import { Link, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { BarChart3, Home, Sprout } from 'lucide-react'

interface MobileNavItem {
  id: string
  path: string
  labelKey: string
  fallback: string
  Icon: any
}

export default function MobileNav() {
  const { t } = useTranslation()
  const location = useLocation()

  const handleNavClick = (itemId: string) => {
    if (itemId === 'poultry') {
      // Siempre abrir Gestión Avícola desde su nivel inicial.
      sessionStorage.removeItem('menuHubStack:poultry')
    }
  }

  const items: MobileNavItem[] = [
    { id: 'poultry', path: '/menu/poultry', labelKey: 'nav.poultry', fallback: 'Gestión Avícola', Icon: Sprout },
    { id: 'home', path: '/', labelKey: 'nav.home', fallback: 'Home', Icon: Home },
    { id: 'kpi', path: '/kpi', labelKey: 'nav.kpi', fallback: 'KPI', Icon: BarChart3 },
  ]

  const isActive = (path: string) => {
    if (path === '/menu/poultry') return location.pathname.startsWith('/menu/poultry') || location.pathname.startsWith('/poultry')
    if (path === '/') return location.pathname === '/'
    if (path === '/kpi') return location.pathname === '/kpi'
    return location.pathname.startsWith(path)
  }

  return (
    <nav
      className="lg:hidden fixed bottom-0 left-0 right-0 z-30 grid grid-cols-3 bg-white dark:bg-slate-900 safe-area-bottom"
      style={{
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
            className="flex flex-col items-center gap-1 px-3 py-2 transition-all"
          >
            <item.Icon
              size={20}
              strokeWidth={active ? 2.3 : 1.8}
              className={active ? 'text-brand-700 dark:text-brand-400' : 'text-slate-900 dark:text-slate-100'}
            />
            <span className={`text-[10px] leading-none font-semibold transition-all ${active ? 'text-brand-700 dark:text-brand-400' : 'text-slate-900 dark:text-slate-100'}`}>
              {t(item.labelKey, item.fallback)}
            </span>
            {active && (
              <span
                className="w-1 h-1 rounded-full"
                style={{ background: 'linear-gradient(135deg, #0B2340, #154F94)' }}
              />
            )}
          </Link>
        )
      })}
    </nav>
  )
}

