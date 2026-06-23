import { useTranslation } from 'react-i18next'
import { useAuthStore } from '../../stores/auth.store'

export default function Header() {
  const { t, i18n } = useTranslation()
  const { user, logout } = useAuthStore()

  return (
    <header className="lg:hidden bg-[#1E3A5F] text-white px-4 py-3 flex items-center justify-between shadow-md">
      <div>
        <h1 className="text-base font-bold">{t('brand.name')}</h1>
        <p className="text-xs text-blue-300">{t('brand.tagline')}</p>
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
  )
}
