import { create } from 'zustand'
import { isTMA } from '@telegram-apps/sdk'
import api from '../services/api'

interface JwtClaims {
  sub?: string | number
  username?: string
  role_id?: number | null
  view_type?: string
  company_id?: string | number | null
}

// Decode JWT payload without verification (view_type is in the token)
function decodeJWT(token: string): JwtClaims | null {
  try {
    const payload = token.split('.')[1]
    return JSON.parse(atob(payload)) as JwtClaims
  } catch {
    return null
  }
}

interface User {
  id: number
  username: string
  first_name: string
  last_name: string
  email: string
  role_id: number | null
  view_type?: string
  is_super_admin?: boolean
  company_id?: number | null
  company_name?: string | null
  /** GA-FE-02 · sesión extendida de `/me` (`OD-11`/`OD-14`/`OD-16`). Opcionales para no
   * romper sesiones hidratadas del token antes de que llegue `/me`. */
  effective_company_id?: number | null
  permissions?: string[]
  company_business_units?: string[]
  granted_business_units?: string[]
  effective_business_units?: string[]
}

interface AuthState {
  user: User | null
  token: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  fetchMe: () => Promise<void>
  setTokens: (access: string, refresh: string) => void
  getAccessToken: () => string | null
  getRefreshToken: () => string | null
}

// S-01: Tokens stored in memory for runtime.
// In Telegram Mini App use localStorage so closing/reopening the mini app keeps session.
// Outside Telegram keep sessionStorage behavior.
const tokenStorage: Storage = (() => {
  try {
    return isTMA() ? localStorage : sessionStorage
  } catch {
    return sessionStorage
  }
})()

let accessToken: string | null = tokenStorage.getItem('access_token')
let refreshToken: string | null = tokenStorage.getItem('refresh_token')

// Hydrate initial user from sessionStorage if available
function getInitialUser(): User | null {
  if (!accessToken) return null
  const claims = decodeJWT(accessToken)
  if (!claims) return null
  return {
    id: Number(claims.sub) || 0,
    username: claims.username || '',
    first_name: '',
    last_name: '',
    email: '',
    role_id: claims.role_id ?? null,
    view_type: claims.view_type || 'web',
    company_id: claims.company_id != null ? Number(claims.company_id) : null,
    company_name: null,
  }
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: getInitialUser(),
  token: accessToken,
  refreshToken: refreshToken,
  isAuthenticated: !!accessToken,
  // D1 · GA-FE-02-A: con token en storage la sesión arranca EN RESTAURACIÓN; el efecto de
  // `App` («fetchMe always runs when token exists») llama a `fetchMe()` y `/me` hidrata
  // `is_super_admin`/`permissions`/`effective_company_id` antes de que los guards decidan.
  // Con `false`, el efecto no corría nunca: tras un refresh, el super admin quedaba
  // denegado en `/admin/unit-access` (`PermissionRoute`) y las superficies GA-FE-02
  // perdían la sesión extendida. Defecto D1 detectado en la certificación (ENV-01).
  isLoading: !!accessToken,

  setTokens: (access: string, refresh: string) => {
    accessToken = access
    refreshToken = refresh
    tokenStorage.setItem('access_token', access)
    tokenStorage.setItem('refresh_token', refresh)
    const claims = decodeJWT(access)
    const immediateUser: User = {
      id: Number(claims?.sub) || 0,
      username: claims?.username || '',
      first_name: '',
      last_name: '',
      email: '',
      role_id: claims?.role_id ?? null,
      view_type: claims?.view_type || 'web',
      company_id: claims?.company_id != null ? Number(claims.company_id) : null,
      company_name: null,
    }
    set({ token: access, refreshToken: refresh, isAuthenticated: true, user: immediateUser })
  },

  getAccessToken: () => accessToken,
  getRefreshToken: () => refreshToken,

  login: async (username: string, password: string) => {
    const response = await api.post('/login', { username, password })
    const { access_token, refresh_token } = response.data
    get().setTokens(access_token, refresh_token)
    // Fetch full user profile after login
    await get().fetchMe()
  },

  logout: () => {
    accessToken = null
    refreshToken = null
    tokenStorage.removeItem('access_token')
    tokenStorage.removeItem('refresh_token')
    set({ user: null, token: null, refreshToken: null, isAuthenticated: false, isLoading: false })
  },

  fetchMe: async () => {
    try {
      const { data } = await api.get('/me')
      const user = { ...data, view_type: data.view_type || 'web' }
      set({ user, isLoading: false })
      // Keep company store in sync — la empresa ACTIVA es la EFECTIVA (`OD-11`).
      const { useCompanyStore } = await import('./company.store')
      const companyStore = useCompanyStore.getState()
      const effectiveId: number | null = user.effective_company_id ?? user.company_id ?? null
      let effectiveName: string | null = effectiveId == null ? null : user.company_name ?? null
      if (effectiveId != null && user.company_id != null && effectiveId !== user.company_id) {
        // Contexto desplazado por `switch-company`: el nombre se resuelve por el catálogo
        // (la fila del usuario sigue siendo la persistida; `OD-11.b`).
        await companyStore.fetchCompanies()
        effectiveName = useCompanyStore.getState().companies.find(c => c.id === effectiveId)?.name ?? `#${effectiveId}`
      }
      useCompanyStore.getState().initFromUser(effectiveId, effectiveName)
    } catch {
      // If /me fails, we still have basic user from JWT claims
      set({ isLoading: false })
    }
  },
}))

