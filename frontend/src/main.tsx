import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './i18n'
import { useAuthStore } from './stores/auth.store'
import { registerTokenAccessors } from './services/api'
import { initTelegramEarly } from './hooks/useTelegram'
import './index.css'
import App from './App'

// Telegram Mini App: initialize SDK early to set header color and expand
initTelegramEarly()

// S-01/02: Wire in-memory token accessors so api.ts can read/refresh tokens
// without touching localStorage. Must happen before any API call.

// Dark mode initialization — apply class before first render to avoid FOUC
try {
 const stored = JSON.parse(localStorage.getItem('theme-storage') || '{}')
 if (stored?.state?.isDark) {
 document.documentElement.classList.add('dark')
 }
} catch { /* ignore */ }
registerTokenAccessors(
 () => useAuthStore.getState().token,
 () => useAuthStore.getState().refreshToken,
 (access, refresh) => useAuthStore.getState().setTokens(access, refresh),
 () => useAuthStore.getState().logout(),
)

createRoot(document.getElementById('root')!).render(
 <StrictMode>
 <BrowserRouter>
 <App />
 </BrowserRouter>
 </StrictMode>,
)
