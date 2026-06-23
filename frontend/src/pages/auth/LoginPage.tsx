import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../stores/auth.store'
import { useTranslation } from 'react-i18next'
import { useToast, getErrorMessage } from '../../components/Toast'

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
    <div className="min-h-screen bg-gradient-to-br from-[#1E3A5F] to-[#3B82F6] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <div className="text-center mb-8">
            <h1 className="text-2xl font-bold text-[#1E3A5F]">{t('brand.name')}</h1>
            <p className="text-slate-500 text-sm mt-1">{t('brand.tagline')}</p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            {error && (
              <div className="bg-red-50 text-red-700 px-4 py-3 rounded-lg text-sm font-medium">
                {error}
              </div>
            )}

            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1.5">
                {t('auth.username')}
              </label>
              <input
                {...register('username')}
                className="w-full h-11 px-4 border border-slate-300 rounded-lg focus:border-[#2563EB] focus:ring-2 focus:ring-blue-200 outline-none transition"
                placeholder="admin"
              />
              {errors.username && (
                <p className="text-red-500 text-xs mt-1">{t(errors.username.message)}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1.5">
                {t('auth.password')}
              </label>
              <input
                {...register('password')}
                type="password"
                className="w-full h-11 px-4 border border-slate-300 rounded-lg focus:border-[#2563EB] focus:ring-2 focus:ring-blue-200 outline-none transition"
                placeholder="••••••••"
              />
              {errors.password && (
                <p className="text-red-500 text-xs mt-1">{t(errors.password.message)}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full h-11 bg-[#2563EB] hover:bg-blue-700 text-white font-semibold rounded-lg transition disabled:opacity-50"
            >
              {loading ? t('common.loading') : t('auth.login')}
            </button>
          </form>

          <div className="mt-6 text-center">
            <button
              onClick={toggleLang}
              className="text-sm text-slate-400 hover:text-slate-600 transition"
            >
              {i18n.language === 'es' ? t('lang.toggleEn') : t('lang.toggleEs')}
            </button>
          </div>
        </div>

        <p className="text-center text-blue-200 text-xs mt-6">
          {t('brand.footer')}
        </p>
      </div>
    </div>
  )
}
