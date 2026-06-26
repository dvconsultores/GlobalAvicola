import { useState, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '../../stores/auth.store'
import { useCompanyStore } from '../../stores/company.store'
import { Menu, Globe, Sun, Moon, Bird, Building2, ChevronDown, Check } from 'lucide-react'
import { useThemeStore } from '../../stores/theme.store'
import MobileDrawer from './MobileDrawer'

export default function Header() {
  const { t, i18n } = useTranslation()
  const { user, logout } = useAuthStore()
  const { isDark, toggleDarkMode } = useThemeStore()
  const { activeCompanyId, activeCompanyName, companies, isSwitching, fetchCompanies, switchCompany } = useCompanyStore()
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [companyOpen, setCompanyOpen] = useState(false)
  const companyRef = useRef<HTMLDivElement>(null)

  const isSuperAdmin = user?.is_super_admin === true

  // Load companies list when super_admin opens the dropdown
  useEffect(() => {
    if (companyOpen && isSuperAdmin && companies.length === 0) {
      fetchCompanies()
    }
  }, [companyOpen, isSuperAdmin]) // eslint-disable-line react-hooks/exhaustive-deps

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (companyRef.current && !companyRef.current.contains(e.target as Node)) {
        setCompanyOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const handleSwitchCompany = async (id: number, name: string) => {
    setCompanyOpen(false)
    await switchCompany(id, name)
  }

  const toggleLang = () => i18n.changeLanguage(i18n.language === 'es' ? 'en' : 'es')

  const initials = [user?.first_name?.charAt(0), user?.last_name?.charAt(0)]
    .filter(Boolean).join('').toUpperCase() || user?.username?.charAt(0)?.toUpperCase() || '?'

  return (
    <>
      {/* ── Desktop Header ───────────────────────────────── */}
      <header className="hidden lg:flex h-14 bg-white dark:bg-dark-surface border-b border-slate-200/80 dark:border-dark-border items-center justify-end px-6 gap-3 sticky top-0 z-20">
        {/* Language toggle */}
        <button
          onClick={toggleLang}
          className="inline-flex items-center gap-1.5 h-8 px-3 rounded-lg text-xs font-semibold text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-dark-card hover:text-slate-700 dark:hover:text-slate-200 transition-all border border-slate-200 dark:border-dark-border"
          title={i18n.language === 'es' ? 'Switch to English' : 'Cambiar a Español'}
        >
          <Globe size={13} />
          {i18n.language === 'es' ? 'EN' : 'ES'}
        </button>

        {/* Dark mode toggle */}
        <button
          onClick={toggleDarkMode}
          className="w-8 h-8 flex items-center justify-center rounded-lg text-slate-400 dark:text-slate-500 hover:bg-slate-100 dark:hover:bg-dark-card hover:text-slate-600 dark:hover:text-slate-300 transition-all"
          aria-label={isDark ? 'Modo claro' : 'Modo oscuro'}
        >
          {isDark ? <Sun size={15} /> : <Moon size={15} />}
        </button>

        {/* Divider */}
        <div className="w-px h-5 bg-slate-200 dark:bg-dark-border" />

        {/* Company selector (super_admin) or badge (regular user) */}
        {(activeCompanyName || user?.company_name) && (
          <div ref={companyRef} className="relative">
            {isSuperAdmin ? (
              /* ── Dropdown selector for super_admin ── */
              <button
                onClick={() => setCompanyOpen(v => !v)}
                disabled={isSwitching}
                className="flex items-center gap-1.5 h-8 px-3 rounded-lg bg-blue-50 dark:bg-blue-950/20 border border-blue-100 dark:border-blue-900/40 hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-all disabled:opacity-60"
                title={t('company.selector')}
              >
                <Building2 size={12} className="text-blue-500 dark:text-blue-400 shrink-0" />
                <span className="text-xs font-semibold text-blue-700 dark:text-blue-300 max-w-[130px] truncate">
                  {isSwitching ? t('company.switching') : (activeCompanyName || user?.company_name)}
                </span>
                <ChevronDown size={11} className={`text-blue-400 transition-transform ${companyOpen ? 'rotate-180' : ''}`} />
              </button>
            ) : (
              /* ── Static badge for regular users ── */
              <div className="flex items-center gap-1.5 h-8 px-3 rounded-lg bg-blue-50 dark:bg-blue-950/20 border border-blue-100 dark:border-blue-900/40">
                <Building2 size={12} className="text-blue-500 dark:text-blue-400 shrink-0" />
                <span className="text-xs font-semibold text-blue-700 dark:text-blue-300 max-w-[140px] truncate">
                  {activeCompanyName || user?.company_name}
                </span>
              </div>
            )}

            {/* Dropdown panel */}
            {companyOpen && isSuperAdmin && (
              <div className="absolute right-0 top-10 z-50 w-56 rounded-xl bg-white dark:bg-dark-surface border border-slate-200 dark:border-dark-border shadow-lg overflow-hidden">
                <p className="px-3 py-2 text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider border-b border-slate-100 dark:border-dark-border">
                  {t('company.selector')}
                </p>
                {companies.length === 0 ? (
                  <p className="px-3 py-3 text-xs text-slate-400 dark:text-slate-500">{t('common.loading', 'Cargando...')}</p>
                ) : (
                  <ul>
                    {companies.map(c => (
                      <li key={c.id}>
                        <button
                          onClick={() => handleSwitchCompany(c.id, c.name)}
                          className="w-full flex items-center gap-2.5 px-3 py-2.5 text-left text-xs hover:bg-slate-50 dark:hover:bg-dark-card transition-colors"
                        >
                          <Building2 size={13} className="text-slate-400 dark:text-slate-500 shrink-0" />
                          <span className="flex-1 text-slate-700 dark:text-slate-200 truncate">{c.name}</span>
                          {c.id === activeCompanyId && (
                            <Check size={13} className="text-blue-500 shrink-0" />
                          )}
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>
        )}

        {/* User chip */}
        {user && (
          <div className="flex items-center gap-2.5">
            {/* Avatar */}
            <div
              className="w-7 h-7 rounded-lg flex items-center justify-center text-[11px] font-bold text-white shrink-0"
              style={{ background: 'linear-gradient(135deg, #0B2340 0%, #154F94 100%)' }}
            >
              {initials}
            </div>
            <div className="text-xs">
              <p className="font-semibold text-slate-700 dark:text-slate-200 leading-none">
                {user.first_name ? `${user.first_name} ${user.last_name ?? ''}`.trim() : user.username}
              </p>
              <p className="text-slate-400 dark:text-slate-500 mt-0.5 leading-none">{user.username}</p>
            </div>
            <button
              onClick={logout}
              className="h-7 px-2.5 text-xs font-medium text-slate-400 dark:text-slate-500 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/20 rounded-lg transition-all"
            >
              {t('auth.logout')}
            </button>
          </div>
        )}
      </header>

      {/* ── Mobile Header ────────────────────────────────── */}
      <header
        className="lg:hidden text-white px-4 py-0 flex items-center justify-between sticky top-0 z-20"
        style={{ background: 'linear-gradient(135deg, #071829 0%, #0F3361 100%)', height: '56px' }}
      >
        <div className="flex items-center gap-3">
          {/* Hamburger */}
          <button
            onClick={() => setDrawerOpen(true)}
            aria-label={t('nav.menu')}
            aria-expanded={drawerOpen}
            className="w-9 h-9 flex items-center justify-center rounded-xl transition-all"
            style={{ background: 'rgba(255,255,255,0.08)' }}
            onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.14)' }}
            onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.08)' }}
          >
            <Menu size={20} />
          </button>
          <div className="flex items-center gap-2">
            <div
              className="w-7 h-7 rounded-lg flex items-center justify-center"
              style={{ background: 'rgba(26,109,204,0.7)' }}
            >
              <Bird size={15} className="text-white" strokeWidth={1.8} />
            </div>
            <div>
              <h1 className="text-[13px] font-bold leading-none">{t('brand.name')}</h1>
              <p className="text-[10px] mt-0.5 leading-none" style={{ color: 'rgba(147,197,253,0.7)' }}>
                {t('brand.tagline')}
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          {/* Language */}
          <button
            onClick={toggleLang}
            className="text-[11px] font-semibold px-2.5 py-1.5 rounded-lg flex items-center gap-1 transition-all"
            style={{ background: 'rgba(255,255,255,0.08)', color: 'rgba(147,197,253,0.9)' }}
            title={i18n.language === 'es' ? 'Switch to English' : 'Cambiar a Español'}
          >
            <Globe size={12} />
            {i18n.language === 'es' ? 'EN' : 'ES'}
          </button>

          {/* Dark mode */}
          <button
            onClick={toggleDarkMode}
            className="w-8 h-8 flex items-center justify-center rounded-lg transition-all"
            style={{ color: 'rgba(147,197,253,0.8)' }}
            aria-label={isDark ? 'Modo claro' : 'Modo oscuro'}
          >
            {isDark ? <Sun size={15} /> : <Moon size={15} />}
          </button>

          {/* User avatar */}
          {user && (
            <button
              onClick={logout}
              className="w-8 h-8 flex items-center justify-center rounded-lg text-[11px] font-bold text-white transition-all"
              style={{ background: 'rgba(26,109,204,0.5)' }}
              title={t('auth.logout')}
            >
              {initials}
            </button>
          )}
        </div>
      </header>

      <MobileDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} />
    </>
  )
}

