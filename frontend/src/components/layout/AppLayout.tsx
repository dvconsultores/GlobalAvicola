import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import Header from './Header'
import MobileNav from './MobileNav'
import { useAuthStore } from '../../stores/auth.store'

export default function AppLayout() {
  const { user } = useAuthStore()
  const isMobileUser = user?.view_type === 'mobile'

  return (
    <div className="min-h-screen bg-[#F7F8FA] dark:bg-slate-950">
      {!isMobileUser && <Sidebar />}
      <Header />
      <main className={`pb-20 lg:pb-0 ${!isMobileUser ? 'lg:ml-64' : ''}`}>
        {/* Mobile: minimal padding for native-like experience. Desktop: generous padding */}
        <div className={`mx-auto ${isMobileUser ? 'px-2 py-2' : 'max-w-7xl px-4 sm:px-6 lg:px-8 py-4 lg:py-5 page-enter'}`}>
          <Outlet />
        </div>
      </main>
      {isMobileUser && <MobileNav />}
    </div>
  )
}

