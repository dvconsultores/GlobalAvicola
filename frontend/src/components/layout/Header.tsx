import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '../../stores/auth.store'
import { Menu } from 'lucide-react'
import MobileDrawer from './MobileDrawer'

export default function Header() {
  const { t, i18n } = useTranslation()
  const { user, logout } = useAuthStore()
  const [drawerOpen, setDrawerOpen] = useState(false)

  return (
    <>
      <header className="lg:hidden bg-[#1E3A5F] text-white px-4 py-3 flex items-center justify-between shadow-md">
        <div className="flex items-center gap-3">
          {/* Hamburger — opens MobileDrawer */}
          <button
            onClick={() => setDrawerOpen(true)}
            aria-label={t('nav.menu', 'Menú')}
            aria-expanded={drawerOpen}
            className="w-9 h-9 flex items-center justify-center rounded-lg text-white hover:bg-white/10 transition-colors"
          >
            <Menu size={22} />
          </button>
          <div>
            <h1 className="text-base font-bold">{t('brand.name')}</h1>
            <p className="text-xs text-blue-300">{t('brand.tagline')}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => i18n.changeLanguage(i18n.language === 'es' ? 'en' : 'es')}
            className="text-xs bg-blue-700 px-2 py-1 rounded"
          >
            {i18n.language === 'es' ? t('lang.shortEn') : t('lang.shortEs')}
          </button>
          {user && (
            <button onClick={logout} className="text-xs text-blue-200">
              {t('auth.logout')}
            </button>
          )}
        </div>
      </header>

      <MobileDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} />
    </>
  )
}
