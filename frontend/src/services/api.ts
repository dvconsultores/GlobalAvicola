import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

// S-01: Token accessor from memory (not localStorage)
let getAccessToken: (() => string | null) | null = null
let getRefreshToken: (() => string | null) | null = null
let onTokenRefreshed: ((access: string, refresh: string) => void) | null = null
let forceLogout: (() => void) | null = null

export function registerTokenAccessors(
  access: () => string | null,
  refresh: () => string | null,
  onRefresh: (access: string, refresh: string) => void,
  logout: () => void,
) {
  getAccessToken = access
  getRefreshToken = refresh
  onTokenRefreshed = onRefresh
  forceLogout = logout
}

// S-02: Track refresh attempts to avoid infinite loops
let isRefreshing = false
let refreshPromise: Promise<string | null> | null = null

async function attemptTokenRefresh(): Promise<string | null> {
  const refreshTok = getRefreshToken?.()
  if (!refreshTok) return null
  if (isRefreshing) return refreshPromise
  isRefreshing = true
  refreshPromise = (async () => {
    try {
      const { data } = await axios.post('/api/v1/refresh', { refresh_token: refreshTok })
      onTokenRefreshed?.(data.access_token, data.refresh_token)
      return data.access_token
    } catch {
      forceLogout?.()
      return null
    } finally {
      isRefreshing = false
      refreshPromise = null
    }
  })()
  return refreshPromise
}

// Request interceptor: attach JWT token from memory
api.interceptors.request.use((config) => {
  const token = getAccessToken?.()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// S-02: Response interceptor — auto-refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    // Only attempt refresh once per request
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      const newToken = await attemptTokenRefresh()
      if (newToken) {
        originalRequest.headers.Authorization = `Bearer ${newToken}`
        return api(originalRequest)
      }
    }
    // If refresh fails or already retried, force logout
    if (error.response?.status === 401 && originalRequest._retry) {
      forceLogout?.()
    }
    return Promise.reject(error)
  }
)

export default api
