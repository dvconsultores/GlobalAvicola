/**
 * GA-FE-02 · Servicio tipado de Business Units — contrato EXACTO del backend
 * (`GA_FE_02_BACKEND_CONTRACT_MATRIX.md` B04–B10).
 *
 * Ninguna llamada acepta `company_id`: la empresa efectiva la resuelve el servidor
 * (`router.py:58-73`; sin ella → 403). El frontend no inventa contexto.
 */
import api from './api'

export interface CompanyBusinessUnit {
  code: string
  name_key: string
  is_enabled: boolean
}

export interface UserBusinessUnit {
  user_id: number
  code: string
  company_id: number
  granted_at: string
  revoked_at: string | null
  is_effective: boolean
}

export interface GrantCandidate {
  user_id: number
  username: string
  display_name: string
  already_granted: boolean
}

export const businessUnitsService = {
  /** GET `/business-units` — las cuatro unidades con su estado para la empresa efectiva. */
  async getCompanyBusinessUnits(): Promise<CompanyBusinessUnit[]> {
    const { data } = await api.get<CompanyBusinessUnit[]>('/business-units')
    return data
  },

  /** PATCH `/business-units/{code}/enable` — sin cuerpo. */
  async enableCompanyBusinessUnit(code: string): Promise<CompanyBusinessUnit> {
    const { data } = await api.patch<CompanyBusinessUnit>(`/business-units/${code}/enable`)
    return data
  },

  /** PATCH `/business-units/{code}/disable` — sin cuerpo. Apagar NO borra concesiones. */
  async disableCompanyBusinessUnit(code: string): Promise<CompanyBusinessUnit> {
    const { data } = await api.patch<CompanyBusinessUnit>(`/business-units/${code}/disable`)
    return data
  },

  /** GET `/users/{id}/business-units` — concesiones (incluye revocadas e `is_effective`). */
  async getUserBusinessUnits(userId: number): Promise<UserBusinessUnit[]> {
    const { data } = await api.get<UserBusinessUnit[]>(`/users/${userId}/business-units`)
    return data
  },

  /** GET `/business-units/{code}/grant-candidates` — misma empresa, sin el actor (contrato). */
  async getGrantCandidates(code: string): Promise<GrantCandidate[]> {
    const { data } = await api.get<GrantCandidate[]>(`/business-units/${code}/grant-candidates`)
    return data
  },

  /** POST `/users/{id}/business-units` `{code}` — la empresa es la efectiva; nunca se envía. */
  async grantBusinessUnit(userId: number, code: string): Promise<UserBusinessUnit> {
    const { data } = await api.post<UserBusinessUnit>(`/users/${userId}/business-units`, { code })
    return data
  },

  /** DELETE `/users/{id}/business-units/{code}` — marca `revoked_at`; no borra. */
  async revokeBusinessUnit(userId: number, code: string): Promise<UserBusinessUnit> {
    const { data } = await api.delete<UserBusinessUnit>(`/users/${userId}/business-units/${code}`)
    return data
  },
}
