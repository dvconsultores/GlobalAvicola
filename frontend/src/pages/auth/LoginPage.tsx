import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../stores/auth.store'
import { useTranslation } from 'react-i18next'
import { useToast, getErrorMessage } from '../../components/Toast'
import { Globe, Bird, CheckCircle2, ArrowRight, Lock, User } from 'lucide-react'

const loginSchema = z.object({
  username: z.string().min(3, 'auth.usernameMinLength'),
  password: z.string().min(6, 'auth.passwordMinLength'),
})

type LoginForm = z.infer<typeof loginSchema>

/** Brand features shown in the hero panel */
const FEATURES = [
  { icon: CheckCircle2, text: 'Gestión operativa avícola integral' },
  { icon: CheckCircle2, text: 'Integración SAP desacoplada' },
  { icon: CheckCircle2, text: 'Flujo de aprobación multinivel' },
  { icon: CheckCircle2, text: 'Auditoría inmutable completa' },
]

export default function LoginPage() {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const { login } = useAuthStore()
  const toast = useToast()
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  })

  const onSubmit = async (data: LoginForm) => {
    setError('')
    setLoading(true)
    try {
      await login(data.username, data.password)
      toast.success(`${t('dashboard.welcome')}, ${data.username}`)
      navigate('/')
    } catch (err: any) {
      const msg = getErrorMessage(err, t('auth.loginError'))
      setError(msg)
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  const toggleLang = () => {
    i18n.changeLanguage(i18n.language === 'es' ? 'en' : 'es')
  }

  return (
    <div className="min-h-screen flex">
      {/* ── Left panel — Brand Hero ─────────────────────────── */}
      <div
        className="hidden lg:flex lg:w-[52%] xl:w-[55%] relative overflow-hidden flex-col justify-between p-10"
        style={{ background: 'linear-gradient(160deg, #071829 0%, #0F3361 60%, #154F94 100%)' }}
      >
        {/* Background geometric shapes */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div
            className="absolute -top-32 -right-32 w-[520px] h-[520px] rounded-full opacity-[0.06]"
            style={{ background: 'radial-gradient(circle, #60A5FA 0%, transparent 70%)' }}
          />
          <div
            className="absolute bottom-0 -left-20 w-[400px] h-[400px] rounded-full opacity-[0.05]"
            style={{ background: 'radial-gradient(circle, #3B82F6 0%, transparent 70%)' }}
          />
          {/* Grid dots pattern */}
          <svg className="absolute inset-0 w-full h-full opacity-[0.04]" aria-hidden="true">
            <defs>
              <pattern id="grid" x="0" y="0" width="32" height="32" patternUnits="userSpaceOnUse">
                <circle cx="1" cy="1" r="1" fill="white" />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
          </svg>
        </div>

        {/* Logo / Brand */}
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-1">
            <div className="w-10 h-10 rounded-xl bg-white/10 border border-white/20 flex items-center justify-center backdrop-blur-sm">
              <Bird size={22} className="text-white" strokeWidth={1.8} />
            </div>
            <div>
              <h1 className="text-white font-bold text-lg leading-none tracking-tight">
                {t('brand.name', 'Global Avícola')}
              </h1>
              <p className="text-brand-300 text-xs mt-0.5">{t('brand.tagline', 'Plataforma operativa')}</p>
            </div>
          </div>
        </div>

        {/* Hero content */}
        <div className="relative z-10 flex-1 flex flex-col justify-center py-10">
          <div className="max-w-sm">
            <p className="text-brand-300 text-xs font-semibold uppercase tracking-[0.2em] mb-4">
              Enterprise · SAP Integration · Bilingual
            </p>
            <h2 className="text-white text-3xl xl:text-4xl font-bold leading-tight mb-4">
              Gestión avícola<br />
              <span className="text-transparent bg-clip-text"
                style={{ backgroundImage: 'linear-gradient(90deg, #60A5FA, #93C5FD)' }}>
                de clase mundial
              </span>
            </h2>
            <p className="text-blue-200/80 text-sm leading-relaxed mb-8">
              Plataforma de gestión operativa integrada para la industria avícola.
              Control total desde la crianza hasta la producción final.
            </p>

            <ul className="space-y-3">
              {FEATURES.map((f, i) => (
                <li key={i} className="flex items-center gap-3">
                  <f.icon size={16} className="text-brand-300 shrink-0" strokeWidth={2.5} />
                  <span className="text-blue-100/90 text-sm">{f.text}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Footer */}
        <div className="relative z-10">
          <p className="text-blue-300/50 text-xs">{t('brand.footer', '© 2025 Global Avícola')}</p>
        </div>
      </div>

      {/* ── Right panel — Form ──────────────────────────────── */}
      <div className="flex-1 bg-white dark:bg-dark-surface flex flex-col justify-center items-center px-6 sm:px-10 lg:px-16 xl:px-20 py-12">
        {/* Mobile brand header */}
        <div className="lg:hidden flex flex-col items-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-brand-800 flex items-center justify-center mb-3 shadow-card-md">
            <Bird size={28} className="text-white" strokeWidth={1.8} />
          </div>
          <h1 className="text-xl font-bold text-brand-800 dark:text-white">
            {t('brand.name', 'Global Avícola')}
          </h1>
          <p className="text-slate-400 text-xs mt-0.5">{t('brand.tagline', 'Plataforma operativa')}</p>
        </div>

        <div className="w-full max-w-sm">
          {/* Form header */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white leading-tight">
              {t('auth.loginTitle', 'Iniciar sesión')}
            </h2>
            <p className="text-slate-500 dark:text-slate-400 text-sm mt-1.5">
              {t('auth.loginSubtitle', 'Ingresa tus credenciales para continuar')}
            </p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
            {/* Error banner */}
            {error && (
              <div className="flex items-start gap-2.5 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800/50 text-red-700 dark:text-red-400 px-4 py-3 rounded-xl text-sm">
                <div className="w-1.5 h-1.5 rounded-full bg-red-500 mt-1.5 shrink-0" />
                {error}
              </div>
            )}

            {/* Username field */}
            <div className="space-y-1.5">
              <label
                htmlFor="login-username"
                className="block text-sm font-semibold text-slate-700 dark:text-slate-300"
              >
                {t('auth.username', 'Usuario')}
              </label>
              <div className="relative">
                <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none">
                  <User size={16} />
                </span>
                <input
                  id="login-username"
                  {...register('username')}
                  autoComplete="username"
                  autoFocus
                  className="w-full h-11 pl-10 pr-4 border border-slate-200 dark:border-slate-700 rounded-xl text-sm text-slate-900 dark:text-white bg-slate-50 dark:bg-dark-card placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-400/30 focus:border-brand-500 dark:focus:border-brand-400 transition-all"
                  placeholder="admin"
                />
              </div>
              {errors.username && (
                <p className="text-red-500 text-xs">{t(errors.username.message ?? '')}</p>
              )}
            </div>

            {/* Password field */}
            <div className="space-y-1.5">
              <label
                htmlFor="login-password"
                className="block text-sm font-semibold text-slate-700 dark:text-slate-300"
              >
                {t('auth.password', 'Contraseña')}
              </label>
              <div className="relative">
                <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none">
                  <Lock size={16} />
                </span>
                <input
                  id="login-password"
                  {...register('password')}
                  type="password"
                  autoComplete="current-password"
                  className="w-full h-11 pl-10 pr-4 border border-slate-200 dark:border-slate-700 rounded-xl text-sm text-slate-900 dark:text-white bg-slate-50 dark:bg-dark-card placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-400/30 focus:border-brand-500 dark:focus:border-brand-400 transition-all"
                  placeholder="••••••••"
                />
              </div>
              {errors.password && (
                <p className="text-red-500 text-xs">{t(errors.password.message ?? '')}</p>
              )}
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="group w-full h-11 flex items-center justify-center gap-2.5 rounded-xl text-sm font-semibold text-white transition-all disabled:opacity-60 disabled:cursor-not-allowed"
              style={{ background: loading ? '#1A6DCC' : 'linear-gradient(135deg, #1A6DCC 0%, #3B82F6 100%)', boxShadow: loading ? 'none' : '0 2px 12px -2px rgba(26, 109, 204, 0.5)' }}
            >
              {loading ? (
                <>
                  <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                  </svg>
                  {t('common.loading', 'Cargando...')}
                </>
              ) : (
                <>
                  {t('auth.login', 'Iniciar sesión')}
                  <ArrowRight size={16} className="transition-transform group-hover:translate-x-0.5" />
                </>
              )}
            </button>
          </form>

          {/* Language toggle */}
          <div className="mt-8 flex items-center justify-center">
            <button
              onClick={toggleLang}
              className="inline-flex items-center gap-2 text-xs font-medium text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
            >
              <Globe size={13} />
              {i18n.language === 'es' ? t('lang.toggleEn', 'Switch to English') : t('lang.toggleEs', 'Cambiar a Español')}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

