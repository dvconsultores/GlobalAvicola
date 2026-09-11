import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock API before importing the store
vi.mock('../../services/api', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
    defaults: { headers: { common: {} } },
  },
}))

/**
 * D1 · GA-FE-02-A — restauración de sesión en arranque.
 *
 * El efecto de `App` («fetchMe always runs when token exists») exige que el store nazca
 * EN RESTAURACIÓN cuando hay token en storage (`isLoading === true`). Si nace resuelto
 * (`false`), `fetchMe()` no corre nunca en un hard reload, la sesión queda hidratada solo
 * desde claims del JWT (sin `is_super_admin`/`permissions`/`effective_company_id`) y los
 * guards basados en permiso —`PermissionRoute` de `/admin/unit-access`— deniegan a un
 * usuario legítimo tras el refresh. Observado en ENV-01 el 2026-09-11.
 */

function fakeJwt(claims: Record<string, unknown>): string {
  const payload = btoa(JSON.stringify(claims)).replace(/=+$/, '')
  return `x.${payload}.y`
}

describe('GA-FE-02 · arranque de sesión (D1)', () => {
  beforeEach(() => {
    vi.resetModules()
    sessionStorage.clear()
  })

  afterEach(() => {
    vi.resetModules()
    sessionStorage.clear()
  })

  it('con token en storage el store arranca en restauración (isLoading=true) para que /me hidrate la sesión extendida', async () => {
    sessionStorage.setItem('access_token', fakeJwt({ sub: 2, username: 'u', role_id: 2, view_type: 'web' }))
    sessionStorage.setItem('refresh_token', 'r')

    const { useAuthStore } = await import('../auth.store')
    const state = useAuthStore.getState()

    expect(state.isAuthenticated).toBe(true)
    // RED (antes del fix): false ⇒ App nunca llama a fetchMe ⇒ PermissionRoute deniega tras refresh.
    expect(state.isLoading).toBe(true)
  })

  it('sin token el store arranca resuelto (isLoading=false)', async () => {
    const { useAuthStore } = await import('../auth.store')
    expect(useAuthStore.getState().isLoading).toBe(false)
  })
})
