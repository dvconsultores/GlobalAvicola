import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import i18n, { normalizeLanguage, nextLanguage, type AppLanguage } from '../i18n'

type SupportedLocale = AppLanguage

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
      locale: normalizeLanguage(i18n.resolvedLanguage || i18n.language),
      setLocale: (locale) => {
        set({ locale })
        const current = normalizeLanguage(i18n.resolvedLanguage || i18n.language)
        if (current !== locale) {
          void i18n.changeLanguage(locale)
        }
      },
      toggleLocale: () => {
        const next = nextLanguage(i18n.resolvedLanguage || i18n.language)
        set({ locale: next })
        void i18n.changeLanguage(next)
      },
    }),
    { name: 'locale-storage' },
  ),
)
