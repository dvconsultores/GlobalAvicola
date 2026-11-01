/**
 * SPEC 013 · AC-SS-01/AC-SS-02 — cableado de sesión (`sessionWiring`).
 *
 * `wireSession()` es el ÚNICO punto que conecta `api.ts` con el store: registra los cuatro
 * accesores de token y, además, el manejador de `403`. Tras un refresh el store debe rehidratar
 * desde `/me` (AC-SS-01) y un `403` también debe rehidratar (AC-SS-02).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mocks = vi.hoisted(() => ({
  registerTokenAccessors: vi.fn(),
  registerForbiddenHandler: vi.fn(),
  setTokens: vi.fn(),
  fetchMe: vi.fn(),
  logout: vi.fn(),
  state: { token: 'tok-1', refreshToken: 'ref-1' },
}))

vi.mock('../../services/api', () => ({
  default: {},
  registerTokenAccessors: (...a: any[]) => mocks.registerTokenAccessors(...a),
  registerForbiddenHandler: (...a: any[]) => mocks.registerForbiddenHandler(...a),
}))

vi.mock('../../stores/auth.store', () => ({
  useAuthStore: {
    getState: () => ({
      token: mocks.state.token,
      refreshToken: mocks.state.refreshToken,
      setTokens: mocks.setTokens,
      fetchMe: mocks.fetchMe,
      logout: mocks.logout,
    }),
  },
}))

import { wireSession } from '../sessionWiring'

beforeEach(() => {
  vi.clearAllMocks()
})

describe('SPEC 013 · wireSession', () => {
  it('registra los cuatro accesores de token y el manejador de 403', () => {
    wireSession()

    expect(mocks.registerTokenAccessors).toHaveBeenCalledTimes(1)
    const args = mocks.registerTokenAccessors.mock.calls[0]
    expect(args).toHaveLength(4)
    expect(args[0]()).toBe('tok-1')
    expect(args[1]()).toBe('ref-1')
    args[3]()
    expect(mocks.logout).toHaveBeenCalledTimes(1)

    expect(mocks.registerForbiddenHandler).toHaveBeenCalledTimes(1)
    expect(typeof mocks.registerForbiddenHandler.mock.calls[0][0]).toBe('function')
  })

  it('el callback de refresh llama a setTokens y DESPUÉS a fetchMe', () => {
    wireSession()
    const onRefresh = mocks.registerTokenAccessors.mock.calls[0][2]

    onRefresh('access-nuevo', 'refresh-nuevo')

    expect(mocks.setTokens).toHaveBeenCalledWith('access-nuevo', 'refresh-nuevo')
    // AC-SS-01 · RED antes del fix: nadie volvía a llamar a `/me` tras el refresh.
    expect(mocks.fetchMe).toHaveBeenCalledTimes(1)
    expect(mocks.setTokens.mock.invocationCallOrder[0]).toBeLessThan(
      mocks.fetchMe.mock.invocationCallOrder[0],
    )
  })

  it('el manejador de 403 rehidrata desde /me', () => {
    wireSession()
    const onForbidden = mocks.registerForbiddenHandler.mock.calls[0][0]

    onForbidden()

    expect(mocks.fetchMe).toHaveBeenCalledTimes(1)
    expect(mocks.setTokens).not.toHaveBeenCalled()
  })
})
