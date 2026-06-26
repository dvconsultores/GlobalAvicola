import { create } from 'zustand'
import api from '../services/api'

export interface CompanyOption {
  id: number
  name: string
  is_active?: boolean
}

interface CompanyState {
  activeCompanyId: number | null
  activeCompanyName: string | null
  companies: CompanyOption[]
  isSwitching: boolean

  /** Initialize active company from user data (called after login/fetchMe) */
  initFromUser: (id: number | null | undefined, name: string | null | undefined) => void

  /** Load full companies list (super_admin only) */
  fetchCompanies: () => Promise<void>

  /** Switch active company — calls /switch-company, updates auth tokens, reloads user */
  switchCompany: (id: number, name: string) => Promise<void>
}

export const useCompanyStore = create<CompanyState>((set, get) => ({
  activeCompanyId: null,
  activeCompanyName: null,
  companies: [],
  isSwitching: false,

  initFromUser: (id, name) => {
    set({ activeCompanyId: id ?? null, activeCompanyName: name ?? null })
  },

  fetchCompanies: async () => {
    try {
      const { data } = await api.get('/masters/companies', { params: { limit: 200 } })
      const list: CompanyOption[] = (data.items ?? data).filter((c: CompanyOption) => c.is_active !== false)
      set({ companies: list })
    } catch {
      // non-critical — leave companies as []
    }
  },

  switchCompany: async (id: number, name: string) => {
    if (get().isSwitching) return
    set({ isSwitching: true })
    try {
      const { data } = await api.post('/switch-company', { company_id: id })
      // Dynamically import to avoid circular dependency
      const { useAuthStore } = await import('./auth.store')
      useAuthStore.getState().setTokens(data.access_token, data.refresh_token)
      await useAuthStore.getState().fetchMe()
      set({ activeCompanyId: id, activeCompanyName: name, isSwitching: false })
    } catch (err) {
      set({ isSwitching: false })
      throw err
    }
  },
}))
