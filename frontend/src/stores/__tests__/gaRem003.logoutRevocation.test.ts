/**
 * `GA-REM-003` · AC04 — el logout **revoca en el servidor**, no sólo limpia el cliente.
 *
 * RED en HEAD: `logout()` limpia almacenamiento y estado pero no llama a
 * `POST /api/v1/logout`; el refresh token sigue siendo canjeable 7 días.
 * Control: el estado local queda limpio igualmente (verde antes y después).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../../services/api', () => ({
  default: {
    post: vi.fn(() => Promise.resolve({ data: {} })),
    get: vi.fn(() => Promise.resolve({ data: {} })),
    defaults: { headers: { common: {} } },
  },
}))

import api from '../../services/api'
import { useAuthStore } from '../auth.store'

describe('GA-REM-003 AC04 · logout con revocación', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useAuthStore.setState({
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
    })
  })

  it('logout envía el refresh token a POST /logout antes de limpiar', () => {
    const { setTokens, logout } = useAuthStore.getState()
    setTokens('tok', 'ref-123')
    logout()
    expect(api.post).toHaveBeenCalledWith('/logout', { refresh_token: 'ref-123' })
  })

  it('control: el estado local queda limpio y sin sesión', () => {
    const { setTokens, logout } = useAuthStore.getState()
    setTokens('tok', 'ref-123')
    logout()
    const state = useAuthStore.getState()
    expect(state.isAuthenticated).toBe(false)
    expect(state.token).toBeNull()
    expect(state.refreshToken).toBeNull()
  })
})
