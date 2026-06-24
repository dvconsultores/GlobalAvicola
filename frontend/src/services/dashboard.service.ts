import api from './api'

export interface MobileDashboardData {
  today_events: number
  pending_corrections: number
  approved_today: number
  active_lots: number
  [key: string]: unknown
}

export interface AdminDashboardData {
  total_events: number
  pending_review: number
  pending_approval: number
  last_7_days: number
  by_status?: Record<string, number>
  top_event_types?: { event_type: string; count: number }[]
  weekly_mortality_trend?: { date: string; mortality: number }[]
  [key: string]: unknown
}

export const dashboardService = {
  getMobile: () =>
    api.get<MobileDashboardData>('/dashboard/mobile'),

  getAdmin: () =>
    api.get<AdminDashboardData>('/dashboard/admin'),
}
