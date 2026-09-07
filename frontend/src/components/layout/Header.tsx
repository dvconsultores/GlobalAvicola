import { useState, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '../../stores/auth.store'
import { useCompanyStore } from '../../stores/company.store'
import { normalizeLanguage, nextLanguage } from '../../i18n'
import { Globe, Bird, Building2, ChevronDown, Check } from 'lucide-react'
import NotificationBell from '../notifications/NotificationBell'

export default function Header() {
 const { t, i18n } = useTranslation()
 const { user, logout } = useAuthStore()
 const { activeCompanyId, activeCompanyName, companies, isSwitching, fetchCompanies, switchCompany } = useCompanyStore()
 const [companyOpen, setCompanyOpen] = useState(false)
 const companyRef = useRef<HTMLDivElement>(null)
 const currentLang = normalizeLanguage(i18n.resolvedLanguage || i18n.language)

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

 const toggleLang = () => i18n.changeLanguage(nextLanguage(i18n.resolvedLanguage || i18n.language))

 const initials = [user?.first_name?.charAt(0), user?.last_name?.charAt(0)]
 .filter(Boolean).join('').toUpperCase() || user?.username?.charAt(0)?.toUpperCase() || '?'

 return (
 <>
 {/* ── Desktop Header ───────────────────────────────── */}
 <header className="hidden lg:flex h-12 bg-white backdrop-blur border-b border-slate-200/70 items-center justify-end px-5 gap-2.5 sticky top-0 z-20">
 {/* `OD-07` / `GA-REM-038`. El canal de P-14 es interno: esta campana es la única
 superficie por la que un usuario se entera de que su registro fue rechazado. */}
 <NotificationBell />

 {/* Divider */}
 <div className="w-px h-4 bg-slate-200/80" />

 {/* Language toggle */}
 <button
 onClick={toggleLang}
 className="inline-flex items-center gap-1 h-7 px-2.5 rounded-md text-xs font-semibold text-slate-400 hover:bg-slate-100:bg-dark-card hover:text-slate-600:text-slate-300 transition-colors"
 title={currentLang === 'es' ? 'Switch to English' : 'Cambiar a Español'}
 >
 <Globe size={12} />
 {currentLang === 'es' ? 'EN' : 'ES'}
 </button>

 {/* Divider */}
 <div className="w-px h-4 bg-slate-200/80" />

 {/* Company selector (super_admin) or badge (regular user) */}
 {(activeCompanyName || user?.company_name) && (
 <div ref={companyRef} className="relative">
 {isSuperAdmin ? (
 /* ── Dropdown selector for super_admin ── */
 <button
 onClick={() => setCompanyOpen(v => !v)}
 disabled={isSwitching}
 className="flex items-center gap-1.5 h-7 px-2.5 rounded-md bg-slate-50 border border-slate-200/80 hover:bg-slate-100:bg-dark-card/80 transition-colors disabled:opacity-60"
 title={t('company.selector')}
 >
 <Building2 size={11} className="text-slate-400 shrink-0" />
 <span className="text-xs font-medium text-slate-600 max-w-[130px] truncate">
 {isSwitching ? t('company.switching') : (activeCompanyName || user?.company_name)}
 </span>
 <ChevronDown size={10} className={`text-slate-400 transition-transform ${companyOpen ? 'rotate-180' : ''}`} />
 </button>
 ) : (
 /* ── Static badge for regular users ── */
 <div className="flex items-center gap-1.5 h-7 px-2.5 rounded-md bg-slate-50 border border-slate-200/80">
 <Building2 size={11} className="text-slate-400 shrink-0" />
 <span className="text-xs font-medium text-slate-600 max-w-[140px] truncate">
 {activeCompanyName || user?.company_name}
 </span>
 </div>
 )}

 {/* Dropdown panel */}
 {companyOpen && isSuperAdmin && (
 <div className="absolute right-0 top-9 z-50 w-52 rounded-xl bg-white border border-slate-200 shadow-lg overflow-hidden">
 <p className="px-3 py-2 text-xs font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-100">
 {t('company.selector')}
 </p>
 {companies.length === 0 ? (
 <p className="px-3 py-3 text-xs text-slate-400">{t('common.loading', 'Cargando...')}</p>
 ) : (
 <ul>
 {companies.map(c => (
 <li key={c.id}>
 <button
 onClick={() => handleSwitchCompany(c.id, c.name)}
 className="w-full flex items-center gap-2 px-3 py-2 text-left text-xs hover:bg-slate-50:bg-dark-card transition-colors"
 >
 <Building2 size={12} className="text-slate-400 shrink-0" />
 <span className="flex-1 text-slate-700 truncate">{c.name}</span>
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
 className="w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold text-white shrink-0"
 style={{ background: 'linear-gradient(135deg, #264c5f 0%, #3d748f 50%, #4e8fad 100%)' }}
 >
 {initials}
 </div>
 <div className="text-xs">
 <p className="font-semibold text-slate-700 leading-none">
 {user.first_name ? `${user.first_name} ${user.last_name ?? ''}`.trim() : user.username}
 </p>
 <p className="text-slate-400 mt-0.5 leading-none">{user.username}</p>
 </div>
 <button
 onClick={logout}
 className="h-7 px-2.5 text-xs font-medium text-slate-400 hover:text-red-600:text-red-400 hover:bg-red-50:bg-red-950/20 rounded-lg transition-all"
 >
 {t('auth.logout')}
 </button>
 </div>
 )}
 </header>

 {/* ── Mobile Header ────────────────────────────────── */}
 <header
 className="lg:hidden text-white px-4 py-0 flex items-center justify-between sticky top-0 z-20"
 style={{ background: 'linear-gradient(135deg, #264c5f 0%, #3d748f 50%, #4e8fad 100%)', height: '56px' }}
 >
 <div className="flex items-center gap-2 min-w-0 flex-1">
 <div
 className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0"
 style={{ background: 'rgba(90,155,186,0.7)' }}
 >
 <Bird size={15} className="text-white" strokeWidth={1.8} />
 </div>
 <div className="min-w-0">
 <h1 className="text-sm font-bold leading-none truncate">{t('brand.name')}</h1>
 {/* Company badge — multi-company indicator */}
 {(activeCompanyName || user?.company_name) && (
 <p className="text-xs mt-0.5 leading-none truncate flex items-center gap-1" style={{ color: 'rgba(180,210,230,0.9)' }}>
 <Building2 size={10} className="shrink-0" />
 {activeCompanyName || user?.company_name}
 </p>
 )}
 </div>
 </div>

 <div className="flex items-center gap-1.5 shrink-0">
 {/* La misma campana en móvil: `OD-07` no distingue dispositivo. */}
 <div className="text-white">
 <NotificationBell />
 </div>

 {/* Language */}
 <button
 onClick={toggleLang}
 className="text-xs font-semibold px-2.5 py-1.5 rounded-lg flex items-center gap-1 transition-all"
 style={{ background: 'rgba(255,255,255,0.08)', color: 'rgba(111,171,197,0.9)' }}
 title={currentLang === 'es' ? 'Switch to English' : 'Cambiar a Español'}
 >
 <Globe size={15} />
 {currentLang === 'es' ? 'EN' : 'ES'}
 </button>
 </div>
 </header>

 </>
 )
}

