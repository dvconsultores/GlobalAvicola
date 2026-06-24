import api from './api'

export interface KpiData {
  mortality?: number
  feed_conversion?: number
  egg_production?: number
  hatchery_yield?: number
  animal_welfare?: number
  vaccination_efficiency?: number
  transfer_efficiency?: number
  afcr?: number
  production_index?: number
  [key: string]: unknown
}

export interface LotReport {
  lot: Record<string, unknown>
  opening_balance?: Record<string, unknown>
  event_summary?: Record<string, unknown>
  [key: string]: unknown
}

export const reportsService = {
  getKpis: (lotId: number) =>
    api.get<KpiData>('/reports/kpis', { params: { lot_id: lotId } }),

  getMortalityKpi: (lotId: number) =>
    api.get('/reports/kpis/mortality', { params: { lot_id: lotId } }),

  getFeedConversionKpi: (lotId: number) =>
    api.get('/reports/kpis/feed-conversion', { params: { lot_id: lotId } }),

  getEggProductionKpi: (lotId: number) =>
    api.get('/reports/kpis/egg-production', { params: { lot_id: lotId } }),

  getHatcheryKpi: (lotId: number) =>
    api.get('/reports/kpis/hatchery', { params: { lot_id: lotId } }),

  getLotReport: (lotId: number) =>
    api.get<LotReport>(`/reports/lot/${lotId}`),

  getSapComparison: () =>
    api.get('/reports/sap-comparison'),
}
