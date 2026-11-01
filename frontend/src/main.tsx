import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './i18n'
import { wireSession } from './services/sessionWiring'
import { initTelegramEarly } from './hooks/useTelegram'
import './index.css'
import App from './App'
import { ErrorBoundary } from './components/ErrorBoundary'

// Telegram Mini App: initialize SDK early to set header color and expand
initTelegramEarly()

// S-01/02: Wire in-memory token accessors so api.ts can read/refresh tokens
// without touching localStorage. Must happen before any API call.
// SPEC 013 · AC-SS-01/02: `wireSession()` además rehidrata `/me` tras cada refresh y
// reconcilia la sesión ante un `403` acotado.

// Dark mode initialization — apply class before first render to avoid FOUC
try {
 const stored = JSON.parse(localStorage.getItem('theme-storage') || '{}')
 if (stored?.state?.isDark) {
 document.documentElement.classList.add('dark')
 }
} catch { /* ignore */ }
wireSession()

createRoot(document.getElementById('root')!).render(
 <StrictMode>
  {/* R-215: una excepción de render ya no deja la app en blanco. */}
  <ErrorBoundary>
   <BrowserRouter>
    <App />
   </BrowserRouter>
  </ErrorBoundary>
 </StrictMode>,
)
