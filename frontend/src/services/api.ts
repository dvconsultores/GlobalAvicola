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
let onForbidden: (() => void) | null = null

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

// AC-SS-02 (SPEC 013 · AR-21): un 403 significa que la UI y el backend divergieron (permisos,
// menús). El handler rehidrata la sesión desde `/me`, pero ACOTADO: como máximo una vez cada
// 30 s, para que una ráfaga de 403 no genere una tormenta de peticiones.
const FORBIDDEN_RECONCILE_INTERVAL_MS = 30_000
let lastForbiddenAt: number | null = null

export function registerForbiddenHandler(fn: () => void) {
  onForbidden = fn
}

// Rutas de sesión: `/me` ES la rehidratación, y `/login`/`/refresh` fallan por credenciales,
// no por permisos — reconciliar ahí sería inútil o un bucle.
const SESSION_ROUTES = ['/me', '/login', '/refresh']

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
    // AC-SS-02: reconciliación acotada ante 403 (máx. 1 cada 30 s, nunca por rutas de sesión).
    // El error se propaga igual al llamante: sólo se añade la rehidratación.
    if (error.response?.status === 403) {
      const url = String(originalRequest?.url ?? '').split('?')[0].split('#')[0]
      const isSessionRoute = SESSION_ROUTES.some((route) => url.endsWith(route))
      const now = Date.now()
      if (!isSessionRoute && (lastForbiddenAt === null || now - lastForbiddenAt >= FORBIDDEN_RECONCILE_INTERVAL_MS)) {
        lastForbiddenAt = now
        onForbidden?.()
      }
    }
    return Promise.reject(error)
  }
)

export default api
