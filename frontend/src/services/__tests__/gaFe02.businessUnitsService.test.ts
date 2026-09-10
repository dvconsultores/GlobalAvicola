/**
 * GA-FE-02 · Servicio tipado de unidades — contrato EXACTO del backend
 * (`GA_FE_02_BACKEND_CONTRACT_MATRIX.md` B04–B10). Método, ruta y payload, punto por punto.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const get = vi.fn()
const patch = vi.fn()
const post = vi.fn()
const del = vi.fn()

vi.mock('../../services/api', () => ({
  default: {
    get: (...a: any[]) => get(...a),
    patch: (...a: any[]) => patch(...a),
    post: (...a: any[]) => post(...a),
    delete: (...a: any[]) => del(...a),
  },
}))

import { businessUnitsService } from '../businessUnits.service'

beforeEach(() => {
  get.mockReset(); patch.mockReset(); post.mockReset(); del.mockReset()
})

describe('GA-FE-02 · businessUnitsService', () => {
  it('lista las unidades de la empresa por GET /business-units', async () => {
    get.mockResolvedValue({ data: [{ code: 'grandparent', name_key: 'businessUnits.grandparent', is_enabled: true }] })
    const list = await businessUnitsService.getCompanyBusinessUnits()
    expect(get).toHaveBeenCalledWith('/business-units')
    expect(list[0].code).toBe('grandparent')
  })

  it('habilita por PATCH /business-units/{code}/enable sin cuerpo', async () => {
    patch.mockResolvedValue({ data: { code: 'breeder', name_key: 'businessUnits.breeder', is_enabled: true } })
    await businessUnitsService.enableCompanyBusinessUnit('breeder')
    expect(patch).toHaveBeenCalledWith('/business-units/breeder/enable')
  })

  it('deshabilita por PATCH /business-units/{code}/disable', async () => {
    patch.mockResolvedValue({ data: { code: 'breeder', name_key: 'businessUnits.breeder', is_enabled: false } })
    await businessUnitsService.disableCompanyBusinessUnit('breeder')
    expect(patch).toHaveBeenCalledWith('/business-units/breeder/disable')
  })

  it('lee las concesiones del usuario por GET /users/{id}/business-units', async () => {
    get.mockResolvedValue({ data: [] })
    await businessUnitsService.getUserBusinessUnits(7)
    expect(get).toHaveBeenCalledWith('/users/7/business-units')
  })

  it('lee candidatos por GET /business-units/{code}/grant-candidates', async () => {
    get.mockResolvedValue({ data: [] })
    await businessUnitsService.getGrantCandidates('hatchery')
    expect(get).toHaveBeenCalledWith('/business-units/hatchery/grant-candidates')
  })

  it('concede por POST /users/{id}/business-units con {code} y SIN company_id', async () => {
    post.mockResolvedValue({ data: {} })
    await businessUnitsService.grantBusinessUnit(7, 'broiler')
    expect(post).toHaveBeenCalledWith('/users/7/business-units', { code: 'broiler' })
  })

  it('revoca por DELETE /users/{id}/business-units/{code}', async () => {
    del.mockResolvedValue({ data: {} })
    await businessUnitsService.revokeBusinessUnit(7, 'broiler')
    expect(del).toHaveBeenCalledWith('/users/7/business-units/broiler')
  })
})
