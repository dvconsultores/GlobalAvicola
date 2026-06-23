import { create } from 'zustand'
import api from '../services/api'

interface JwtClaims {
  sub?: string | number
  username?: string
  role_id?: number | null
  view_type?: string
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
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  fetchMe: () => Promise<void>
}

// Read initial view_type from cached token if available
function getInitialUser(): User | null {
  const token = localStorage.getItem('access_token')
  if (!token) return null
  const claims = decodeJWT(token)
  if (!claims) return null
  return {
    id: Number(claims.sub) || 0,
    username: claims.username || '',
    first_name: '',
    last_name: '',
    email: '',
    role_id: claims.role_id ?? null,
    view_type: claims.view_type || 'web',
  }
}

export const useAuthStore = create<AuthState>((set) => ({
  user: getInitialUser(),
  token: localStorage.getItem('access_token'),
  isAuthenticated: !!localStorage.getItem('access_token'),
  // Only show loading if we have a token but couldn't decode basic user data
  isLoading: !!localStorage.getItem('access_token') && !getInitialUser(),

  login: async (username: string, password: string) => {
    const response = await api.post('/login', { username, password })
    const { access_token, refresh_token } = response.data
    localStorage.setItem('access_token', access_token)
    localStorage.setItem('refresh_token', refresh_token)
    // Decode JWT to get immediate user data (view_type needed before /me completes)
    const claims = decodeJWT(access_token)
    const immediateUser: User = {
      id: Number(claims?.sub) || 0,
      username: claims?.username || username,
      first_name: '',
      last_name: '',
      email: '',
      role_id: claims?.role_id ?? null,
      view_type: claims?.view_type || 'web',
    }
    set({ token: access_token, user: immediateUser, isAuthenticated: true, isLoading: false })
  },

  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    set({ user: null, token: null, isAuthenticated: false, isLoading: false })
  },

  fetchMe: async () => {
    try {
      const response = await api.get('/me')
      set({ user: response.data, isAuthenticated: true, isLoading: false })
    } catch {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      set({ user: null, token: null, isAuthenticated: false, isLoading: false })
    }
  },
}))
