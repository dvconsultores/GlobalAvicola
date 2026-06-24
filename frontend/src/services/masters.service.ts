import api from './api'

export interface MasterEntity {
  id: number
  name: string
  is_active: boolean
  [key: string]: unknown
}

export const mastersService = {
  list: <T = MasterEntity>(entity: string, params?: { skip?: number; limit?: number; search?: string }) =>
    api.get<T[]>(`/masters/${entity}`, { params }),

  get: <T = MasterEntity>(entity: string, id: number) =>
    api.get<T>(`/masters/${entity}/${id}`),

  create: <T = MasterEntity>(entity: string, data: Record<string, unknown>) =>
    api.post<T>(`/masters/${entity}`, data),

  update: <T = MasterEntity>(entity: string, id: number, data: Record<string, unknown>) =>
    api.put<T>(`/masters/${entity}/${id}`, data),

  deactivate: (entity: string, id: number) =>
    api.delete(`/masters/${entity}/${id}`),

  // Convenience methods for specific entities
  listFarms: (params?: { skip?: number; limit?: number }) =>
    api.get<MasterEntity[]>('/masters/farms', { params }),

  listHouses: (params?: { skip?: number; limit?: number }) =>
    api.get<MasterEntity[]>('/masters/houses', { params }),

  listHatcheries: (params?: { skip?: number; limit?: number }) =>
    api.get<MasterEntity[]>('/masters/hatcheries', { params }),

  listGeneticLines: (params?: { skip?: number; limit?: number }) =>
    api.get<MasterEntity[]>('/masters/genetic-lines', { params }),

  listBreeds: (params?: { skip?: number; limit?: number }) =>
    api.get<MasterEntity[]>('/masters/breeds', { params }),

  listFeedTypes: (params?: { skip?: number; limit?: number }) =>
    api.get<MasterEntity[]>('/masters/feed-types', { params }),

  listCorrectionTypes: () =>
    api.get<MasterEntity[]>('/masters/correction-types'),

  getHousesByFarm: (farmId: number) =>
    api.get<MasterEntity[]>(`/masters/farms/${farmId}/houses`),

  getIncubatorsByHatchery: (hatcheryId: number) =>
    api.get<MasterEntity[]>(`/masters/hatcheries/${hatcheryId}/incubators`),
}
