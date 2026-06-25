import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '../../stores/auth.store'
import { Menu, Globe, Sun, Moon } from 'lucide-react'
import { useThemeStore } from '../../stores/theme.store'
import MobileDrawer from './MobileDrawer'

export default function Header() {
  const { t, i18n } = useTranslation()
  const { user, logout } = useAuthStore()
  const { isDark, toggleDarkMode } = useThemeStore()
  const [drawerOpen, setDrawerOpen] = useState(false)

  const toggleLang = () => i18n.changeLanguage(i18n.language === 'es' ? 'en' : 'es')

  return (
    <>
      {/* Desktop Header — visible on lg+ */}
      <header className="hidden lg:flex h-14 bg-white dark:bg-dark-surface border-b border-slate-200 dark:border-slate-700 items-center justify-end px-6 gap-2 sticky top-0 z-20">
        {/* Language toggle */}
        <button
          onClick={toggleLang}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors border border-slate-200 dark:border-slate-600"
          title={i18n.language === 'es' ? 'Switch to English' : 'Cambiar a Español'}
        >
          <Globe size={14} />
          {i18n.language === 'es' ? 'EN' : 'ES'}
        </button>

        {/* Dark mode toggle */}
        <button
          onClick={toggleDarkMode}
          className="inline-flex items-center justify-center w-8 h-8 rounded-lg text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
          aria-label={isDark ? 'Modo claro' : 'Modo oscuro'}
          title={isDark ? 'Modo claro' : 'Modo oscuro'}
        >
          {isDark ? <Sun size={16} /> : <Moon size={16} />}
        </button>

        {/* User info + logout */}
        {user && (
          <>
            <span className="text-xs text-slate-400 dark:text-slate-500">|</span>
            <span className="text-xs font-medium text-slate-600 dark:text-slate-300">
              {user.first_name || user.username}
            </span>
            <button
              onClick={logout}
              className="text-xs font-medium text-slate-500 dark:text-slate-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
            >
              {t('auth.logout')}
            </button>
          </>
        )}
      </header>

      {/* Mobile Header */}
      <header className="lg:hidden bg-[#1E3A5F] text-white px-4 py-3 flex items-center justify-between shadow-md dark:bg-[#0F172A]">
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
        <div className="flex items-center gap-2">
          <button
            onClick={toggleLang}
            className="text-xs bg-blue-700/80 hover:bg-blue-700 px-2.5 py-1.5 rounded-lg flex items-center gap-1.5 transition-colors"
            title={i18n.language === 'es' ? 'Switch to English' : 'Cambiar a Español'}
          >
            <Globe size={14} />
            {i18n.language === 'es' ? 'EN' : 'ES'}
          </button>
          <button
            onClick={toggleDarkMode}
            className="w-8 h-8 flex items-center justify-center rounded-lg text-blue-200 hover:bg-white/10 transition-colors"
            aria-label={isDark ? 'Modo claro' : 'Modo oscuro'}
          >
            {isDark ? <Sun size={16} /> : <Moon size={16} />}
          </button>
          {user && (
            <button onClick={logout} className="text-xs text-blue-200 hover:text-white px-2 py-1.5 transition-colors">
              {t('auth.logout')}
            </button>
          )}
        </div>
      </header>

      <MobileDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} />
    </>
  )
}
