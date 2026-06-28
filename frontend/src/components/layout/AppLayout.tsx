import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import Header from './Header'
import MobileNav from './MobileNav'
import { useAuthStore } from '../../stores/auth.store'

export default function AppLayout() {
 const { user } = useAuthStore()
 const isMobileUser = user?.view_type === 'mobile'

 return (
 <div className="min-h-screen bg-[#F7F8FA] dark:bg-dark-bg">
 {!isMobileUser && <Sidebar />}
 <Header />
 <main className={`pb-24 lg:pb-0 ${!isMobileUser ? 'lg:ml-64' : ''}`}>
 {/* Mobile: edge-to-edge for native feel. Desktop: generous padding */}
 <div className={isMobileUser ? 'px-1 page-enter' : 'max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 lg:py-5 page-enter'}>
 <Outlet />
 </div>
 </main>
 {isMobileUser && <MobileNav />}
 </div>
 )
}

