/**
 * GA-FE-02 · Sesión extendida y cambio de empresa (AC-COMP-01/03/04/08).
 *
 * `/me` expone la verdad del contexto (`effective_company_id`, permisos y las tres listas de
 * unidades). El cambio de empresa reemplaza AMBOS tokens y refetchea `/me` (contrato
 * `GA_FE_02_BACKEND_CONTRACT_MATRIX.md` B02/B03). Contexto desplazado (OD-11): el nombre de la
 * empresa efectiva se resuelve por el catálogo cuando difiere de la persistida.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const get = vi.fn()
const post = vi.fn()

vi.mock('../../services/api', () => ({
  default: {
    get: (...a: any[]) => get(...a),
    post: (...a: any[]) => post(...a),
  },
}))

import { useAuthStore } from '../auth.store'
import { useCompanyStore } from '../company.store'

const ME_BASE = {
  id: 5, username: 'ana', first_name: 'Ana', last_name: 'Díaz', email: 'a@x.com',
  role_id: 2, view_type: 'web', is_active: true, is_super_admin: false,
  company_id: 1, company_name: 'Empresa Alfa',
  effective_company_id: 1,
  permissions: ['business_units:read', 'business_units:update'],
  company_business_units: ['grandparent', 'broiler'],
  granted_business_units: ['grandparent'],
  effective_business_units: ['grandparent'],
}

beforeEach(() => {
  get.mockReset(); post.mockReset()
  useAuthStore.setState({ user: null })
  useCompanyStore.setState({ activeCompanyId: null, activeCompanyName: null, companies: [], isSwitching: false })
})

describe('GA-FE-02 · fetchMe conserva la sesión extendida', () => {
  it('guarda permisos y las listas de unidades del contrato', async () => {
    get.mockResolvedValue({ data: { ...ME_BASE } })
    await useAuthStore.getState().fetchMe()
    const user: any = useAuthStore.getState().user
    expect(user.permissions).toContain('business_units:read')
    expect(user.company_business_units).toEqual(['grandparent', 'broiler'])
    expect(user.effective_business_units).toEqual(['grandparent'])
  })

  it('usuario de empresa: la empresa efectiva es la persistida y NO consulta el catálogo', async () => {
    get.mockImplementation((url: string) => {
      if (url === '/me') return Promise.resolve({ data: { ...ME_BASE } })
      return Promise.resolve({ data: [] })
    })
    await useAuthStore.getState().fetchMe()
    expect(useCompanyStore.getState().activeCompanyId).toBe(1)
    expect(useCompanyStore.getState().activeCompanyName).toBe('Empresa Alfa')
    expect(get.mock.calls.some(([u]) => String(u).startsWith('/masters/companies'))).toBe(false)
  })

  it('contexto desplazado: resuelve el nombre de la empresa efectiva por el catálogo', async () => {
    get.mockImplementation((url: string) => {
      if (url === '/me') {
        return Promise.resolve({
          data: { ...ME_BASE, is_super_admin: true, effective_company_id: 2 },
        })
      }
      if (String(url).startsWith('/masters/companies')) {
        return Promise.resolve({
          data: [
            { id: 1, name: 'Empresa Alfa', is_active: true },
            { id: 2, name: 'Empresa Beta', is_active: true },
          ],
        })
      }
      return Promise.resolve({ data: [] })
    })
    await useAuthStore.getState().fetchMe()
    expect(useCompanyStore.getState().activeCompanyId).toBe(2)
    expect(useCompanyStore.getState().activeCompanyName).toBe('Empresa Beta')
  })

  it('actor global sin empresa seleccionada: sin empresa activa (fail-closed, OD-14.d)', async () => {
    get.mockImplementation((url: string) => {
      if (url === '/me') {
        return Promise.resolve({
          data: { ...ME_BASE, is_super_admin: true, effective_company_id: null, company_id: null },
        })
      }
      return Promise.resolve({ data: [] })
    })
    await useAuthStore.getState().fetchMe()
    expect(useCompanyStore.getState().activeCompanyId).toBeNull()
    expect(useCompanyStore.getState().activeCompanyName).toBeNull()
  })
})

describe('GA-FE-02 · switchCompany', () => {
  it('publica /switch-company, reemplaza tokens y refetchea /me', async () => {
    post.mockResolvedValue({ data: { access_token: 'nuevo-a', refresh_token: 'nuevo-r' } })
    get.mockResolvedValue({ data: { ...ME_BASE, effective_company_id: 2, company_id: 1 } })

    const setTokensSpy = vi.spyOn(useAuthStore.getState(), 'setTokens').mockImplementation(() => {})
    const fetchMeSpy = vi.spyOn(useAuthStore.getState(), 'fetchMe')

    await useCompanyStore.getState().switchCompany(2, 'Empresa Beta')

    expect(post).toHaveBeenCalledWith('/switch-company', { company_id: 2 })
    expect(setTokensSpy).toHaveBeenCalledWith('nuevo-a', 'nuevo-r')
    expect(fetchMeSpy).toHaveBeenCalled()
    expect(useCompanyStore.getState().activeCompanyId).toBe(2)
    expect(useCompanyStore.getState().activeCompanyName).toBe('Empresa Beta')
    expect(useCompanyStore.getState().isSwitching).toBe(false)

    setTokensSpy.mockRestore(); fetchMeSpy.mockRestore()
  })
})
