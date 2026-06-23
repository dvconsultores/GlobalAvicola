import { Link, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '../../stores/auth.store'
import { Home, Bird, FileText, Database, Search, CheckCircle, TrendingUp, Shield, RefreshCw, Users } from 'lucide-react'

const navItems = [
  { path: '/', label: 'home', Icon: Home },
  { path: '/lots', label: 'lots', Icon: Bird },
  { path: '/operations', label: 'operations', Icon: FileText },
  { path: '/masters', label: 'masters', Icon: Database },
  { path: '/review', label: 'review', Icon: Search },
  { path: '/approvals', label: 'approvals', Icon: CheckCircle },
  { path: '/reports', label: 'reports', Icon: TrendingUp },
  { path: '/audit', label: 'audit', Icon: Shield },
  { path: '/sap', label: 'sap', Icon: RefreshCw },
  { path: '/users', label: 'users', Icon: Users },
]

export default function Sidebar() {
  const { t } = useTranslation()
  const location = useLocation()
  const { logout, user } = useAuthStore()

  return (
    <aside className="hidden lg:flex flex-col w-64 bg-[#1E3A5F] text-white min-h-screen fixed left-0 top-0 z-30">
      {/* Logo */}
      <div className="px-6 py-5 border-b border-blue-900">
        <h1 className="text-lg font-bold tracking-tight">Global Avícola</h1>
        <p className="text-xs text-blue-300">Gestión Operativa</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path || location.pathname.startsWith(item.path + '/')
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition ${
                isActive
                  ? 'bg-blue-700 text-white'
                  : 'text-blue-100 hover:bg-blue-800 hover:text-white'
              }`}
            >
              <item.Icon size={20} />
              {t(`nav.${item.label}`)}
            </Link>
          )
        })}
      </nav>

      {/* User section */}
      <div className="px-4 py-4 border-t border-blue-900">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-xs font-bold">
            {user?.first_name?.charAt(0) || 'U'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{user?.first_name || 'Usuario'}</p>
            <p className="text-xs text-blue-300 truncate">{user?.username || ''}</p>
          </div>
        </div>
          <Link to="/profile" className="block text-xs text-blue-300 hover:text-white transition mb-1">
            👤 {t('nav.profile') || 'Perfil'}
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
