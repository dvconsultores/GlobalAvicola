import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import Header from './Header'
import MobileNav from './MobileNav'
import { useAuthStore } from '../../stores/auth.store'

export default function AppLayout() {
  const { user } = useAuthStore()
  const isMobileUser = user?.view_type === 'mobile'

  return (
    <div className="min-h-screen bg-[#F4F6F9] dark:bg-dark-bg">
      {/* Desktop sidebar: only for web/admin users */}
      {!isMobileUser && <Sidebar />}
      <Header />
      <main className={`pb-20 lg:pb-0 ${!isMobileUser ? 'lg:ml-64' : ''}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5 lg:py-6 page-enter">
          <Outlet />
        </div>
      </main>
      {/* Bottom nav: only for mobile field operators */}
      {isMobileUser && <MobileNav />}
    </div>
  )
}

