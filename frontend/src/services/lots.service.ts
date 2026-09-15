import api from './api'

export interface LotResponse {
  id: number
  lot_code: string
  bird_type: 'grandparent' | 'breeder' | 'broiler' | 'hatchery'
  status: 'active' | 'closed' | 'cancelled'
  company_id: number
  farm_id?: number
  house_id?: number
  start_date: string
  end_date?: string
  genetic_line_id?: number
  breed_id?: number
  current_phase?: string
}

export interface KpiResponse {
  mortality?: number
  feed_conversion?: number
  egg_production?: number
  hatchery_yield?: number
  [key: string]: unknown
}

export interface PhaseResponse {
  id: number
  lot_id: number
  phase_code: string
  start_date: string
  end_date?: string
  start_population_male: number
  start_population_female: number
  is_active: boolean
}

export const lotsService = {
  list: (params?: { farm_id?: number; status?: string; search?: string; limit?: number }) =>
    api.get<LotResponse[]>('/lots', { params }),

  get: (id: number) =>
    api.get<LotResponse>(`/lots/${id}`),

  create: (data: Partial<LotResponse> & { start_date: string }) =>
    api.post<LotResponse>('/lots', data),

  update: (id: number, data: Partial<LotResponse>) =>
    api.put<LotResponse>(`/lots/${id}`, data),

  close: (id: number) =>
    api.post(`/lots/${id}/close`),

  activateManual: (data: Record<string, unknown>) =>
    api.post('/lots/activate-manual', data),

  getPhases: (id: number) =>
    api.get<PhaseResponse[]>(`/lots/${id}/phases`),

  addPhase: (id: number, data: Partial<PhaseResponse>) =>
    api.post<PhaseResponse>(`/lots/${id}/phases`, data),

  getOpeningBalance: (id: number) =>
    api.get(`/lots/${id}/opening-balance`),

  getTraceability: (id: number) =>
    api.get(`/lots/${id}/traceability`),
}
