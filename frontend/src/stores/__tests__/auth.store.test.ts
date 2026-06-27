import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock API before importing the store
vi.mock('../../services/api', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
    defaults: { headers: { common: {} } },
  },
}))

import { useAuthStore } from '../auth.store'

describe('auth.store', () => {
  beforeEach(() => {
    // Clear sessionStorage and reset store
    sessionStorage.clear()
    useAuthStore.setState({
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
    })
  })

  it('starts unauthenticated when no token in storage', () => {
    const state = useAuthStore.getState()
    expect(state.isAuthenticated).toBe(false)
    expect(state.user).toBeNull()
    expect(state.token).toBeNull()
  })

  it('setTokens updates state and sessionStorage', () => {
    const { setTokens } = useAuthStore.getState()
    setTokens('access-abc', 'refresh-xyz')

    const state = useAuthStore.getState()
    expect(state.token).toBe('access-abc')
    expect(state.refreshToken).toBe('refresh-xyz')
    expect(sessionStorage.getItem('access_token')).toBe('access-abc')
    expect(sessionStorage.getItem('refresh_token')).toBe('refresh-xyz')
  })

  it('getAccessToken returns the current token', () => {
    const { setTokens, getAccessToken } = useAuthStore.getState()
    setTokens('tok-123', 'ref-456')
    expect(getAccessToken()).toBe('tok-123')
  })

  it('getRefreshToken returns the current refresh token', () => {
    const { setTokens, getRefreshToken } = useAuthStore.getState()
    setTokens('tok-123', 'ref-789')
    expect(getRefreshToken()).toBe('ref-789')
  })

  it('logout clears state and sessionStorage', () => {
    const { setTokens, logout } = useAuthStore.getState()
    setTokens('tok', 'ref')
    logout()

    const state = useAuthStore.getState()
    expect(state.isAuthenticated).toBe(false)
    expect(state.user).toBeNull()
    expect(state.token).toBeNull()
    expect(state.refreshToken).toBeNull()
    expect(sessionStorage.getItem('access_token')).toBeNull()
  })

  it('logout clears state and marks unauthenticated', () => {
    const { setTokens, logout } = useAuthStore.getState()
    setTokens('tok', 'ref')
    logout()
    const state = useAuthStore.getState()
    expect(state.isAuthenticated).toBe(false)
    expect(state.user).toBeNull()
  })
})
