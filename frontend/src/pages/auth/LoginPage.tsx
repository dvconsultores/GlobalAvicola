import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../stores/auth.store'
import { useTranslation } from 'react-i18next'
import { normalizeLanguage, nextLanguage } from '../../i18n'
import { useToast, getErrorMessage } from '../../components/Toast'
import { Globe, Bird, ArrowRight, Lock, User, Eye, EyeOff } from 'lucide-react'

const loginSchema = z.object({
 username: z.string().min(3, 'auth.usernameMinLength'),
 password: z.string().min(6, 'auth.passwordMinLength'),
})

type LoginForm = z.infer<typeof loginSchema>

export default function LoginPage() {
 const { t, i18n } = useTranslation()
 const navigate = useNavigate()
 const { login } = useAuthStore()
 const toast = useToast()
 const [error, setError] = useState('')
 const [loading, setLoading] = useState(false)
 const [showPassword, setShowPassword] = useState(false)
 const currentLang = normalizeLanguage(i18n.resolvedLanguage || i18n.language)

 const { register, handleSubmit, formState: { errors } } = useForm<LoginForm>({
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

 const toggleLang = () => i18n.changeLanguage(nextLanguage(i18n.resolvedLanguage || i18n.language))

 return (
 <div className="min-h-screen bg-slate-100 flex flex-col items-center justify-center px-4">
 <div className="w-full max-w-[380px]">

 {/* Brand mark */}
 <div className="flex flex-col items-center mb-8">
 <div
 className="w-12 h-12 rounded-2xl flex items-center justify-center mb-4"
 style={{ background: 'linear-gradient(135deg, #264c5f 0%, #3d748f 50%, #4e8fad 100%)', boxShadow: '0 4px 16px -4px rgba(38,76,95,0.4)' }}
 >
 <Bird size={24} className="text-white" strokeWidth={1.8} />
 </div>
 <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
 {t('brand.name', 'Global Avícola')}
 </h1>
 <p className="text-sm text-slate-500 mt-1">
 {t('auth.loginSubtitle', 'Ingresa tus credenciales para continuar')}
 </p>
 </div>

 {/* Form card */}
 <div className="bg-white rounded-2xl shadow-card-md p-7">
 <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>

 {/* Error */}
 {error && (
 <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-600 px-3.5 py-2.5 rounded-xl text-xs font-medium">
 <div className="w-1.5 h-1.5 rounded-full bg-red-500 shrink-0" />
 {error}
 </div>
 )}

 {/* Username */}
 <div className="space-y-1.5">
 <label htmlFor="login-username" className="block text-xs font-semibold text-slate-500 uppercase tracking-wide">
 {t('auth.username', 'Usuario')}
 </label>
 <div className="relative">
 <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-300 pointer-events-none">
 <User size={15} />
 </span>
 <input
 id="login-username"
 {...register('username')}
 autoComplete="username"
 autoFocus
 className="w-full h-11 pl-10 pr-4 border border-slate-200 rounded-xl text-sm text-slate-900 bg-slate-50 placeholder focus:outline-none focus:ring-2 focus:ring-brand-400/30 focus:border-brand-500 transition-all"
 placeholder={t('auth.usernamePlaceholder', 'username')}
 />
 </div>
 {errors.username && <p className="text-red-500 text-xs">{t(errors.username.message ?? '')}</p>}
 </div>

 {/* Password */}
 <div className="space-y-1.5">
 <label htmlFor="login-password" className="block text-xs font-semibold text-slate-500 uppercase tracking-wide">
 {t('auth.password', 'Contraseña')}
 </label>
 <div className="relative">
 <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-300 pointer-events-none">
 <Lock size={15} />
 </span>
 <input
 id="login-password"
 {...register('password')}
 type={showPassword ? 'text' : 'password'}
 autoComplete="current-password"
 className="w-full h-11 pl-10 pr-10 border border-slate-200 rounded-xl text-sm text-slate-900 bg-slate-50 placeholder focus:outline-none focus:ring-2 focus:ring-brand-400/30 focus:border-brand-500 transition-all"
 placeholder="••••••••"
 />
 <button
 type="button"
 onClick={() => setShowPassword(v => !v)}
 className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover"
 tabIndex={-1}
 aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
 >
 {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
 </button>
 </div>
 {errors.password && <p className="text-red-500 text-xs">{t(errors.password.message ?? '')}</p>}
 </div>

 {/* Submit */}
 <button
 type="submit"
 disabled={loading}
 className="group w-full h-11 flex items-center justify-center gap-2 rounded-xl text-sm font-semibold text-white mt-2 transition-all disabled:opacity-60 disabled:cursor-not-allowed"
 style={{ background: 'linear-gradient(135deg, #305e75 0%, #5a9bba 100%)', boxShadow: loading ? 'none' : '0 2px 12px -2px rgba(90,155,186,0.45)' }}
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
 <ArrowRight size={15} className="transition-transform group-hover:translate-x-0.5" />
 </>
 )}
 </button>
 </form>
 </div>

 {/* Language toggle */}
 <div className="flex justify-center mt-6">
 <button
 onClick={toggleLang}
 className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover transition-colors"
 >
 <Globe size={12} />
 {currentLang === 'es' ? t('lang.toggleEn') : t('lang.toggleEs')}
 </button>
 </div>

 </div>
 </div>
 )
}
