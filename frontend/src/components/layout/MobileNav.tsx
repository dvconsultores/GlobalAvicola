import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Home, Bird, TrendingUp, Clock, PlusCircle, ArrowLeft, Save, Menu } from 'lucide-react'
import { useAuthStore } from '../../stores/auth.store'
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

/**
 * MobileNav — Barra de navegación inferior contextual.
 *
 * Cambia sus items según la ruta activa:
 * - default: Inicio, Registrar, Lotes, KPIs, Menú
 * - form (en /operations/new): Atrás, Guardar, Menú
 * - detail (en /lots/xxx o /operations/xxx): Atrás, Registrar, Lote, KPIs, Menú
 */
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
          { id: 'back', action: 'back', labelKey: 'common.back', fallback: 'Atrás', Icon: ArrowLeft },
          { id: 'save', path: '#', labelKey: 'common.save', fallback: 'Guardar', Icon: Save, primary: true },
          { id: 'menu', action: 'drawer', labelKey: 'nav.menu', fallback: 'Menú', Icon: Menu },
        ]
      case 'detail':
        return [
          { id: 'back', action: 'back', labelKey: 'common.back', fallback: 'Atrás', Icon: ArrowLeft },
          { id: 'register', path: '/operations/new', labelKey: 'nav.register', fallback: 'Registrar', Icon: PlusCircle },
          { id: 'kpis', path: '/reports', labelKey: 'nav.reports', fallback: 'KPIs', Icon: TrendingUp },
          { id: 'menu', action: 'drawer', labelKey: 'nav.menu', fallback: 'Menú', Icon: Menu },
        ]
      default:
        return [
          { id: 'home', path: '/', labelKey: 'nav.home', fallback: 'Inicio', Icon: Home },
          { id: 'register', action: 'register', labelKey: 'nav.register', fallback: 'Registrar', Icon: PlusCircle },
          { id: 'lots', path: '/lots', labelKey: 'nav.lots', fallback: 'Lotes', Icon: Bird },
          { id: 'kpis', path: '/reports', labelKey: 'nav.reports', fallback: 'KPIs', Icon: TrendingUp },
          { id: 'menu', action: 'drawer', labelKey: 'nav.menu', fallback: 'Menú', Icon: Menu },
        ]
    }
  }

  const handleAction = (item: MobileNavItem) => {
    switch (item.action) {
      case 'back':
        navigate(-1)
        break
      case 'drawer':
        openDrawer()
        break
      case 'register':
        navigate('/operations/new')
        break
    }
  }

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/'
    return location.pathname.startsWith(path)
  }

  const items = getItems()

  return (
    <nav className="lg:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 z-30 flex justify-around items-center py-1 safe-area-bottom shadow-[0_-2px_10px_rgba(0,0,0,0.05)]">
      {items.map((item) => {
        if (item.path) {
          const active = isActive(item.path)
          return (
            <Link
              key={item.id}
              to={item.path}
              className={`flex flex-col items-center gap-0.5 px-3 py-1.5 rounded-xl text-xs transition min-w-[56px] ${
                active
                  ? 'text-[#2563EB] font-semibold bg-blue-50'
                  : 'text-slate-500'
              } ${item.primary ? 'bg-[#1E3A5F] text-white px-5 py-2 shadow-md' : ''}`}
            >
              <item.Icon size={item.primary ? 20 : 22} />
              <span className="text-[10px] leading-tight text-center font-medium">{t(item.labelKey, item.fallback)}</span>
            </Link>
          )
        }
        return (
          <button
            key={item.id}
            onClick={() => handleAction(item)}
            className={`flex flex-col items-center gap-0.5 px-3 py-1.5 rounded-xl text-xs transition min-w-[56px] text-slate-500 active:bg-slate-100 ${
              item.primary ? 'bg-[#1E3A5F] text-white px-5 py-2 shadow-md' : ''
            }`}
          >
            <item.Icon size={item.primary ? 20 : 22} />
            <span className="text-[10px] leading-tight text-center font-medium">{t(item.labelKey, item.fallback)}</span>
          </button>
        )
      })}
    </nav>
  )
}
