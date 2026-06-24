import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import Header from './Header'
import MobileNav from './MobileNav'
import { useAuthStore } from '../../stores/auth.store'

export default function AppLayout() {
  const { user } = useAuthStore()
  const isMobileUser = user?.view_type === 'mobile'

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Desktop sidebar: only for web/admin users */}
      {!isMobileUser && <Sidebar />}
      <Header />
      <main className={`pb-16 lg:pb-0 ${!isMobileUser ? 'lg:ml-64' : ''} transition-all duration-200`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 lg:py-6">
          <Outlet />
        </div>
      </main>
      {/* Bottom nav: only for mobile field operators */}
      {isMobileUser && <MobileNav />}
    </div>
  )
}
