import { create } from 'zustand'
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

// S-01: Tokens stored in memory for runtime. sessionStorage used only for
// page-refresh survival (cleared on tab close — better than localStorage).
// Access token expiry reduced to 15min recommendation from security audit.
let accessToken: string | null = sessionStorage.getItem('access_token')
let refreshToken: string | null = sessionStorage.getItem('refresh_token')

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
  isLoading: false,

  setTokens: (access: string, refresh: string) => {
    accessToken = access
    refreshToken = refresh
    // sessionStorage backup for page-refresh survival
    sessionStorage.setItem('access_token', access)
    sessionStorage.setItem('refresh_token', refresh)
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
    sessionStorage.removeItem('access_token')
    sessionStorage.removeItem('refresh_token')
    set({ user: null, token: null, refreshToken: null, isAuthenticated: false, isLoading: false })
  },

  fetchMe: async () => {
    try {
      const { data } = await api.get('/me')
      const user = { ...data, view_type: data.view_type || 'web' }
      set({ user, isLoading: false })
      // Keep company store in sync
      const { useCompanyStore } = await import('./company.store')
      useCompanyStore.getState().initFromUser(user.company_id, user.company_name)
    } catch {
      // If /me fails, we still have basic user from JWT claims
      set({ isLoading: false })
    }
  },
}))

