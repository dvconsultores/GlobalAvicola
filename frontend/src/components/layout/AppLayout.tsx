import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import Header from './Header'
import MobileNav from './MobileNav'
import { useAuthStore } from '../../stores/auth.store'

export default function AppLayout() {
 const { user } = useAuthStore()
 const isMobileUser = user?.view_type === 'mobile'

 return (
 <div className="min-h-screen bg-slate-100">
 {!isMobileUser && <Sidebar />}
 <Header />
 <main className={`pb-24 lg:pb-0 ${!isMobileUser ? 'lg:ml-64' : ''}`}>
 {/* 
   Global content wrapper — consistent margins for ALL web views.
   Mobile: tight edge-to-edge (12px). Desktop: generous centered (24px).
   Pattern matches the approvals panel reference.
 */}
 <div className={isMobileUser
   ? 'px-3 pt-6 page-enter'
   : 'max-w-7xl mx-auto px-4 sm:px-5 lg:px-6 pt-6 pb-4 page-enter'
 }>
 <Outlet />
 </div>
 </main>
 {isMobileUser && <MobileNav />}
 </div>
 )
}

