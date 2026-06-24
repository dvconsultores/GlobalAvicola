import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './i18n'
import { useAuthStore } from './stores/auth.store'
import { registerTokenAccessors } from './services/api'
import './index.css'
import App from './App'

// S-01/02: Wire in-memory token accessors so api.ts can read/refresh tokens
// without touching localStorage. Must happen before any API call.
registerTokenAccessors(
  () => useAuthStore.getState().token,
  () => useAuthStore.getState().refreshToken,
  (access, refresh) => useAuthStore.getState().setTokens(access, refresh),
  () => useAuthStore.getState().logout(),
)

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
