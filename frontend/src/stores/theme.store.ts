import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface ThemeStore {
  isDark: boolean
  setIsDark: (isDark: boolean) => void
  toggleDarkMode: () => void
}

/**
 * Dark Mode Store
 * Persists user's theme preference
 */
export const useThemeStore = create<ThemeStore>()(
  persist(
    (set) => ({
      isDark: false,
      setIsDark: (isDark) => {
        set({ isDark })
        // Aplicar clase 'dark' al elemento html
        if (isDark) {
          document.documentElement.classList.add('dark')
        } else {
          document.documentElement.classList.remove('dark')
        }
      },
      toggleDarkMode: () => {
        set((state) => {
          const newDarkState = !state.isDark
          if (newDarkState) {
            document.documentElement.classList.add('dark')
          } else {
            document.documentElement.classList.remove('dark')
          }
          return { isDark: newDarkState }
        })
      },
    }),
    {
      name: 'theme-storage',
      partialize: (state) => ({ isDark: state.isDark }),
    }
  )
)

/**
 * Hook para usar dark mode
 */
export const useDarkMode = () => {
  const { isDark, setIsDark, toggleDarkMode } = useThemeStore()

  // Aplicar tema al cargar
  if (typeof window !== 'undefined') {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    const storedDark = localStorage.getItem('theme-storage')
    const initialDark = storedDark ? JSON.parse(storedDark).isDark : prefersDark

    if (initialDark !== isDark) {
      setIsDark(initialDark)
    }
  }

  return { isDark, setIsDark, toggleDarkMode }
}
