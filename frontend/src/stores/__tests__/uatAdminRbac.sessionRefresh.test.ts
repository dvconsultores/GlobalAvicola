/**
 * SPEC 013 · AC-SS-01 (AR-19) — sesión tras refresh automático.
 *
 * El interceptor de `api.ts` refresca el token cada ~30 min y llama a `setTokens`. Ese camino
 * NO debe borrar la sesión extendida que hidrató `/me` (`permissions`, listas de unidades,
 * `is_super_admin`, nombre/correo): el token sólo aporta `role_id` y `view_type`. Si el usuario
 * se reemplaza por los claims, `hasPermission(user, 'review:approve')` pasa de `true` a `false`
 * y la UI oculta acciones y menús hasta recargar.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const get = vi.fn()
const post = vi.fn()

vi.mock('../../services/api', () => ({
  default: {
    get: (...a: any[]) => get(...a),
    post: (...a: any[]) => post(...a),
  },
  registerTokenAccessors: vi.fn(),
  registerForbiddenHandler: vi.fn(),
}))

import { useAuthStore } from '../auth.store'
import { useCompanyStore } from '../company.store'
import { hasPermission } from '../../auth/permissions'

/** JWT de prueba sin firma: `decodeJWT` del store sólo hace `atob` del payload. */
function jwt(payload: Record<string, unknown>): string {
  return `header.${btoa(JSON.stringify(payload))}.signature`
}

const ME = {
  id: 7,
  username: 'uat.admin',
  first_name: 'Uat',
  last_name: 'Admin',
  email: 'uat.admin@globalavicola.com',
  role_id: 2,
  view_type: 'web',
  is_active: true,
  is_super_admin: false,
  company_id: 1,
  company_name: 'Empresa Alfa',
  effective_company_id: 1,
  permissions: ['review:approve', 'cutover:read'],
  company_business_units: ['grandparent', 'broiler'],
  granted_business_units: ['grandparent'],
  effective_business_units: ['grandparent'],
}

beforeEach(() => {
  get.mockReset()
  post.mockReset()
  useAuthStore.setState({
    user: null,
    token: null,
    refreshToken: null,
    isAuthenticated: false,
    isLoading: false,
  })
  useCompanyStore.setState({ activeCompanyId: null, activeCompanyName: null, companies: [], isSwitching: false })
})

describe('SPEC 013 · AC-SS-01 · setTokens conserva la sesión hidratada por /me', () => {
  it('mismo sujeto: conserva permisos, unidades, nombre y correo; refresca role_id y view_type del token', async () => {
    get.mockImplementation((url: string) => {
      if (url === '/me') return Promise.resolve({ data: { ...ME } })
      return Promise.resolve({ data: [] })
    })
    await useAuthStore.getState().fetchMe()

    useAuthStore.getState().setTokens(
      jwt({ sub: 7, username: 'uat.admin', role_id: 3, view_type: 'tma', company_id: 1 }),
      'refresh-nuevo',
    )

    const user: any = useAuthStore.getState().user
    // Lo que el token NO aporta sigue viniendo de `/me`.
    expect(user.permissions).toEqual(['review:approve', 'cutover:read'])
    expect(user.effective_business_units).toEqual(['grandparent'])
    expect(user.granted_business_units).toEqual(['grandparent'])
    expect(user.company_business_units).toEqual(['grandparent', 'broiler'])
    expect(user.is_super_admin).toBe(false)
    expect(user.first_name).toBe('Uat')
    expect(user.last_name).toBe('Admin')
    expect(user.email).toBe('uat.admin@globalavicola.com')
    expect(user.effective_company_id).toBe(1)
    // AC-SS-01 · RED antes del fix: aquí el usuario era sólo claims ⇒ `false`.
    expect(hasPermission(user, 'review:approve')).toBe(true)
    // Lo que el token sí aporta se refresca.
    expect(user.role_id).toBe(3)
    expect(user.view_type).toBe('tma')
    expect(user.id).toBe(7)
    // El resto del estado del store no cambia de contrato.
    expect(useAuthStore.getState().token).toBeDefined()
    expect(useAuthStore.getState().refreshToken).toBe('refresh-nuevo')
    expect(useAuthStore.getState().isAuthenticated).toBe(true)
  })

  it('otro sujeto: NO se conserva el usuario previo (queda el derivado de claims)', async () => {
    get.mockImplementation((url: string) => {
      if (url === '/me') return Promise.resolve({ data: { ...ME } })
      return Promise.resolve({ data: [] })
    })
    await useAuthStore.getState().fetchMe()

    useAuthStore.getState().setTokens(
      jwt({ sub: 99, username: 'otra.persona', role_id: 5, view_type: 'web', company_id: null }),
      'refresh-otro',
    )

    const user: any = useAuthStore.getState().user
    expect(user.id).toBe(99)
    expect(user.username).toBe('otra.persona')
    expect(user.role_id).toBe(5)
    expect(user.view_type).toBe('web')
    expect(user.permissions).toBeUndefined()
    expect(user.effective_business_units).toBeUndefined()
    expect(user.first_name).toBe('')
    expect(user.email).toBe('')
    expect(hasPermission(user, 'review:approve')).toBe(false)
  })

  it('sin usuario previo: se comporta como antes (usuario derivado de los claims)', () => {
    useAuthStore.getState().setTokens(
      jwt({ sub: 12, username: 'nuevo', role_id: 4, view_type: 'tma', company_id: 2 }),
      'refresh-inicial',
    )

    const user: any = useAuthStore.getState().user
    expect(user).toMatchObject({
      id: 12,
      username: 'nuevo',
      first_name: '',
      last_name: '',
      email: '',
      role_id: 4,
      view_type: 'tma',
      company_id: 2,
      company_name: null,
    })
    expect(useAuthStore.getState().refreshToken).toBe('refresh-inicial')
  })
})
