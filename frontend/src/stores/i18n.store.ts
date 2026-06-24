import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type SupportedLocale = 'es' | 'en'

interface I18nState {
  /** Currently selected locale */
  locale: SupportedLocale
  /** Set locale and persist preference */
  setLocale: (locale: SupportedLocale) => void
  /** Toggle between es/en */
  toggleLocale: () => void
}

/**
 * Store for persisting i18n language preference.
 * Actual i18n rendering is handled by react-i18next;
 * this store syncs the selected language for persistence and initial load.
 */
export const useI18nStore = create<I18nState>()(
  persist(
    (set) => ({
      locale: 'es',
      setLocale: (locale) => {
        set({ locale })
        // Sync with i18next instance if available
        if (typeof window !== 'undefined') {
          const i18n = (window as any).__i18n
          i18n?.changeLanguage(locale)
        }
      },
      toggleLocale: () =>
        set((state) => {
          const next = state.locale === 'es' ? 'en' : 'es'
          if (typeof window !== 'undefined') {
            const i18n = (window as any).__i18n
            i18n?.changeLanguage(next)
          }
          return { locale: next }
        }),
    }),
    { name: 'locale-storage' },
  ),
)
