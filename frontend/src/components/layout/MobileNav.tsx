import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Home, Bird, TrendingUp, PlusCircle, ArrowLeft, Save, Menu } from 'lucide-react'
import { useUiStore } from '../../stores/ui.store'

type NavContext = 'default' | 'form' | 'detail'

interface MobileNavItem {
  id: string
  path?: string
  action?: 'back' | 'drawer' | 'register'
  labelKey: string
  fallback: string
  Icon: any
  primary?: boolean
}

export default function MobileNav() {
  const { t } = useTranslation()
  const { openDrawer } = useUiStore()
  const navigate = useNavigate()
  const location = useLocation()

  const getContext = (): NavContext => {
    if (location.pathname.startsWith('/operations/new')) return 'form'
    if (location.pathname.match(/^\/(lots|operations)\/\d+/)) return 'detail'
    return 'default'
  }

  const context = getContext()

  const getItems = (): MobileNavItem[] => {
    switch (context) {
      case 'form':
        return [
          { id: 'back',  action: 'back',   labelKey: 'common.back',    fallback: 'Atrás',     Icon: ArrowLeft },
          { id: 'save',  path: '#',         labelKey: 'common.save',    fallback: 'Guardar',   Icon: Save, primary: true },
          { id: 'menu',  action: 'drawer',  labelKey: 'nav.menu',       fallback: 'Menú',      Icon: Menu },
        ]
      case 'detail':
        return [
          { id: 'back',     action: 'back',          labelKey: 'common.back',     fallback: 'Atrás',      Icon: ArrowLeft },
          { id: 'register', path: '/operations/new', labelKey: 'nav.register',    fallback: 'Registrar',  Icon: PlusCircle, primary: true },
          { id: 'kpis',     path: '/reports',         labelKey: 'nav.reports',     fallback: 'KPIs',       Icon: TrendingUp },
          { id: 'menu',     action: 'drawer',         labelKey: 'nav.menu',        fallback: 'Menú',       Icon: Menu },
        ]
      default:
        return [
          { id: 'home',     path: '/',               labelKey: 'nav.home',        fallback: 'Inicio',     Icon: Home },
          { id: 'register', action: 'register',      labelKey: 'nav.register',    fallback: 'Registrar',  Icon: PlusCircle, primary: true },
          { id: 'lots',     path: '/lots',            labelKey: 'nav.lots',        fallback: 'Lotes',      Icon: Bird },
          { id: 'kpis',     path: '/reports',         labelKey: 'nav.reports',     fallback: 'KPIs',       Icon: TrendingUp },
          { id: 'menu',     action: 'drawer',         labelKey: 'nav.menu',        fallback: 'Menú',       Icon: Menu },
        ]
    }
  }

  const handleAction = (item: MobileNavItem) => {
    switch (item.action) {
      case 'back':     navigate(-1); break
      case 'drawer':   openDrawer(); break
      case 'register': navigate('/operations/new'); break
    }
  }

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/'
    return location.pathname.startsWith(path)
  }

  const items = getItems()

  return (
    <nav
      className="lg:hidden fixed bottom-0 left-0 right-0 z-30 flex justify-around items-center bg-white dark:bg-dark-surface safe-area-bottom"
      style={{
        borderTop: '1px solid rgba(15,23,42,0.07)',
        boxShadow: '0 -4px 20px -4px rgba(15,23,42,0.08)',
        paddingTop: '6px',
      }}
    >
      {items.map((item) => {
        if (item.primary) {
          // Primary action — elevated pill
          const el = (
            <span className="flex flex-col items-center gap-0.5">
              <span
                className="w-11 h-11 flex items-center justify-center rounded-2xl text-white mb-0.5"
                style={{ background: 'linear-gradient(135deg, #0B2340 0%, #154F94 100%)', boxShadow: '0 4px 12px -2px rgba(15,51,97,0.45)' }}
              >
                <item.Icon size={20} strokeWidth={2.2} />
              </span>
              <span className="text-[9px] font-semibold text-brand-700 dark:text-brand-300 leading-none">
                {t(item.labelKey, item.fallback)}
              </span>
            </span>
          )

          if (item.path) {
            return <Link key={item.id} to={item.path} className="px-2 py-1">{el}</Link>
          }
          return (
            <button key={item.id} onClick={() => handleAction(item)} className="px-2 py-1">
              {el}
            </button>
          )
        }

        if (item.path) {
          const active = isActive(item.path)
          return (
            <Link
              key={item.id}
              to={item.path}
              className="flex flex-col items-center gap-1 px-3 py-1.5 min-w-[52px] transition-all"
            >
              <item.Icon
                size={20}
                strokeWidth={active ? 2.3 : 1.8}
                className={active ? 'text-brand-700 dark:text-brand-400' : 'text-slate-400 dark:text-slate-500'}
              />
              <span
                className={`text-[9px] leading-none font-semibold transition-all ${ active
                  ? 'text-brand-700 dark:text-brand-400'
                  : 'text-slate-400 dark:text-slate-500'
                }`}
              >
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
        }

        return (
          <button
            key={item.id}
            onClick={() => handleAction(item)}
            className="flex flex-col items-center gap-1 px-3 py-1.5 min-w-[52px] transition-all active:scale-95"
          >
            <item.Icon size={20} strokeWidth={1.8} className="text-slate-400 dark:text-slate-500" />
            <span className="text-[9px] leading-none font-semibold text-slate-400 dark:text-slate-500">
              {t(item.labelKey, item.fallback)}
            </span>
          </button>
        )
      })}
    </nav>
  )
}

