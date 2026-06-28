import { useState, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { useAuthStore } from '../../stores/auth.store'
import { useCompanyStore } from '../../stores/company.store'
import { Globe, Sun, Moon, Bird, Building2, ChevronDown, Check, Menu, X, Home, BarChart3 } from 'lucide-react'
import { useThemeStore } from '../../stores/theme.store'

export default function Header() {
  const { t, i18n } = useTranslation()
  const { user, logout } = useAuthStore()
  const { isDark, toggleDarkMode } = useThemeStore()
  const { activeCompanyId, activeCompanyName, companies, isSwitching, fetchCompanies, switchCompany } = useCompanyStore()
  const [companyOpen, setCompanyOpen] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
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

  // Keep html.dark in sync with persisted/theme-store state.
  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDark)
  }, [isDark])

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
      <header className="hidden lg:flex h-12 bg-white/95 dark:bg-dark-surface backdrop-blur border-b border-slate-200/70 dark:border-dark-border items-center justify-end px-5 gap-2.5 sticky top-0 z-20">
        {/* Language toggle */}
        <button
          onClick={toggleLang}
          className="inline-flex items-center gap-1 h-7 px-2.5 rounded-md text-[11px] font-semibold text-slate-400 dark:text-slate-500 hover:bg-slate-100 dark:hover:bg-dark-card hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
          title={i18n.language === 'es' ? 'Switch to English' : 'Cambiar a Español'}
        >
          <Globe size={12} />
          {i18n.language === 'es' ? 'EN' : 'ES'}
        </button>

        {/* Dark mode toggle */}
        <button
          onClick={toggleDarkMode}
          className="w-7 h-7 flex items-center justify-center rounded-md text-slate-400 dark:text-slate-500 hover:bg-slate-100 dark:hover:bg-dark-card transition-colors"
          aria-label={isDark ? 'Modo claro' : 'Modo oscuro'}
        >
          {isDark ? <Sun size={14} /> : <Moon size={14} />}
        </button>

        {/* Divider */}
        <div className="w-px h-4 bg-slate-200/80 dark:bg-dark-border" />

        {/* Company selector (super_admin) or badge (regular user) */}
        {(activeCompanyName || user?.company_name) && (
          <div ref={companyRef} className="relative">
            {isSuperAdmin ? (
              /* ── Dropdown selector for super_admin ── */
              <button
                onClick={() => setCompanyOpen(v => !v)}
                disabled={isSwitching}
                className="flex items-center gap-1.5 h-7 px-2.5 rounded-md bg-slate-50 dark:bg-slate-800 dark:bg-dark-card border border-slate-200/80 dark:border-dark-border hover:bg-slate-100 dark:hover:bg-dark-card/80 transition-colors disabled:opacity-60"
                title={t('company.selector')}
              >
                <Building2 size={11} className="text-slate-400 dark:text-slate-500 shrink-0" />
                <span className="text-[11px] font-medium text-slate-600 dark:text-slate-300 max-w-[130px] truncate">
                  {isSwitching ? t('company.switching') : (activeCompanyName || user?.company_name)}
                </span>
                <ChevronDown size={10} className={`text-slate-400 transition-transform ${companyOpen ? 'rotate-180' : ''}`} />
              </button>
            ) : (
              /* ── Static badge for regular users ── */
              <div className="flex items-center gap-1.5 h-7 px-2.5 rounded-md bg-slate-50 dark:bg-slate-800 dark:bg-dark-card border border-slate-200/80 dark:border-dark-border">
                <Building2 size={11} className="text-slate-400 dark:text-slate-500 shrink-0" />
                <span className="text-[11px] font-medium text-slate-600 dark:text-slate-300 max-w-[140px] truncate">
                  {activeCompanyName || user?.company_name}
                </span>
              </div>
            )}

            {/* Dropdown panel */}
            {companyOpen && isSuperAdmin && (
              <div className="absolute right-0 top-9 z-50 w-52 rounded-xl bg-white dark:bg-dark-surface border border-slate-200 dark:border-dark-border shadow-lg overflow-hidden">
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
                          className="w-full flex items-center gap-2 px-3 py-2 text-left text-xs hover:bg-slate-50 dark:hover:bg-dark-card transition-colors"
                        >
                          <Building2 size={12} className="text-slate-400 dark:text-slate-500 shrink-0" />
                          <span className="flex-1 text-slate-700 dark:text-slate-200 dark:text-slate-200 truncate">{c.name}</span>
                          {c.id === activeCompanyId && (
                            <Check size={12} className="text-blue-500 shrink-0" />
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
          <div className="flex items-center gap-2">
            {/* Avatar */}
            <div
              className="w-7 h-7 rounded-lg flex items-center justify-center text-[10px] font-bold text-white shrink-0"
              style={{ background: 'linear-gradient(135deg, #0B2340 0%, #154F94 100%)' }}
            >
              {initials}
            </div>
            <div className="text-xs">
              <p className="font-semibold text-slate-700 dark:text-slate-200 dark:text-slate-200 leading-none">
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
        <div className="flex items-center gap-2">
          {/* Hamburger */}
          <button
            onClick={() => setMenuOpen(v => !v)}
            className="w-8 h-8 flex items-center justify-center rounded-lg"
            style={{ background: 'rgba(255,255,255,0.08)' }}
            aria-label={t('nav.menu', 'Menú')}
          >
            {menuOpen ? <X size={18} /> : <Menu size={18} />}
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
        </div>
      </header>

      {/* ── Mobile Slide-in Menu ────────────────────────── */}
      {menuOpen && (
        <>
          <div className="lg:hidden fixed inset-0 z-30 bg-black/40" onClick={() => setMenuOpen(false)} />
          <nav
            className="lg:hidden fixed top-0 left-0 bottom-0 w-64 z-40 p-4 overflow-y-auto"
            style={{ background: 'linear-gradient(180deg, #071829 0%, #0F3361 100%)' }}
          >
            <div className="flex items-center justify-between mb-6">
              <span className="text-sm font-bold text-white">{t('nav.menu', 'Menú')}</span>
              <button onClick={() => setMenuOpen(false)} className="text-white/60 hover:text-white">
                <X size={18} />
              </button>
            </div>
            <div className="space-y-1">
              <Link to="/" onClick={() => setMenuOpen(false)}
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-white/80 hover:bg-white/10 transition-colors">
                <Home size={16} /> {t('nav.home', 'Inicio')}
              </Link>
              <Link to="/menu/poultry" onClick={() => setMenuOpen(false)}
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-white/80 hover:bg-white/10 transition-colors">
                <Bird size={16} /> {t('nav.poultry', 'Gestión Avícola')}
              </Link>
              <Link to="/kpi" onClick={() => setMenuOpen(false)}
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-white/80 hover:bg-white/10 transition-colors">
                <BarChart3 size={16} /> {t('nav.kpi', 'KPI')}
              </Link>
            </div>
            <div className="mt-6 pt-4 border-t border-white/10">
              <button
                onClick={() => { logout(); setMenuOpen(false); }}
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-red-300 hover:bg-white/10 transition-colors w-full text-left"
              >
                {t('auth.logout')}
              </button>
            </div>
          </nav>
        </>
      )}

    </>
  )
}

