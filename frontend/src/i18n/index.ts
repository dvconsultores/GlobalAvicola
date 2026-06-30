import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'
import Backend from 'i18next-http-backend'

export type AppLanguage = 'es' | 'en'

export function normalizeLanguage(lng?: string | null): AppLanguage {
  const normalized = (lng || '').toLowerCase()
  return normalized.startsWith('en') ? 'en' : 'es'
}

export function nextLanguage(lng?: string | null): AppLanguage {
  return normalizeLanguage(lng) === 'es' ? 'en' : 'es'
}

function syncDocumentLanguage(lng?: string | null) {
  if (typeof document !== 'undefined') {
    document.documentElement.lang = normalizeLanguage(lng)
  }
}

i18n
  .use(Backend)
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    fallbackLng: 'es',
    supportedLngs: ['es', 'en'],
    nonExplicitSupportedLngs: true,
    load: 'languageOnly',
    cleanCode: true,
    debug: false,
    interpolation: {
      escapeValue: false,
    },
    backend: {
      loadPath: '/locales/{{lng}}/translation.json',
    },
    detection: {
      order: ['localStorage', 'htmlTag', 'navigator'],
      caches: ['localStorage'],
    },
    react: {
      useSuspense: false,
    },
  })

if (typeof window !== 'undefined') {
  ;(window as any).__i18n = i18n
}

syncDocumentLanguage(i18n.resolvedLanguage || i18n.language)
i18n.on('languageChanged', syncDocumentLanguage)

export default i18n
