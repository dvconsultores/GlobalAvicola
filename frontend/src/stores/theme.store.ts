import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface ThemeStore {
  isDark: boolean
  setIsDark: (isDark: boolean) => void
  toggleDarkMode: () => void
}

/**
 * Theme Store — Modo claro único (dark mode deshabilitado por requerimiento)
 */
export const useThemeStore = create<ThemeStore>()(
  persist(
    (set) => ({
      isDark: false,
      setIsDark: () => {
        set({ isDark: false })
        document.documentElement.classList.remove('dark')
      },
      toggleDarkMode: () => {
        // Deshabilitado — siempre modo claro
        set({ isDark: false })
        document.documentElement.classList.remove('dark')
      },
    }),
    {
      name: 'theme-storage',
      partialize: () => ({ isDark: false }),
    }
  )
)

export const useDarkMode = () => {
  const { isDark } = useThemeStore()
  return { isDark, setIsDark: () => {}, toggleDarkMode: () => {} }
}
