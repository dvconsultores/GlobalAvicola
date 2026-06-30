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
 <div className={`app-content-shell ${isMobileUser ? 'app-content-shell-mobile' : 'app-content-shell-web'} pt-6 pb-4 page-enter`}>
 <Outlet />
 </div>
 </main>
 {isMobileUser && <MobileNav />}
 </div>
 )
}

