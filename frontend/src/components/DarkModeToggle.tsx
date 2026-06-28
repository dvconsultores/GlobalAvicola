import { Moon, Sun } from 'lucide-react'
import { useDarkMode } from '../stores/theme.store'

/**
 * Dark Mode Toggle Button
 * Permite cambiar entre tema claro y oscuro
 */
export default function DarkModeToggle() {
 const { isDark, toggleDarkMode } = useDarkMode()

 return (
 <button
 onClick={toggleDarkMode}
 className={`p-2.5 rounded-lg transition-all hover:shadow-md ${
 isDark
 ? 'bg-slate-800 text-yellow-400 hover:bg-slate-700'
 : 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-200 hover:bg-slate-200'
 }`}
 title={isDark ? 'Light mode' : 'Dark mode'}
 aria-label={isDark ? 'Light mode' : 'Dark mode'}
 >
 {isDark ? <Sun size={20} /> : <Moon size={20} />}
 </button>
 )
}
