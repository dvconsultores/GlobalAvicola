import api from './api'

export interface LoginRequest {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface UserResponse {
  id: number
  username: string
  first_name: string
  last_name: string
  email: string
  phone?: string
  role_id: number
  company_id: number
  view_type: 'web' | 'mobile'
  is_active: boolean
  last_login?: string
}

export interface RoleResponse {
  id: number
  name: string
  description?: string
  is_active: boolean
}

export const authService = {
  login: (data: LoginRequest) =>
    api.post<TokenResponse>('/login', data),

  refresh: (refreshToken: string) =>
    api.post<TokenResponse>('/refresh', { refresh_token: refreshToken }),

  getMe: () =>
    api.get<UserResponse>('/me'),

  listUsers: (params?: { search?: string }) =>
    api.get<UserResponse[]>('/users', { params }),

  createUser: (data: Partial<UserResponse> & { password: string }) =>
    api.post<UserResponse>('/users', data),

  updateUser: (id: number, data: Partial<UserResponse> & { password?: string }) =>
    api.put<UserResponse>(`/users/${id}`, data),

  deactivateUser: (id: number) =>
    api.delete(`/users/${id}`),

  listRoles: () =>
    api.get<RoleResponse[]>('/roles'),

  createRole: (data: { name: string; description?: string }) =>
    api.post<RoleResponse>('/roles', data),

  updateRole: (id: number, data: Partial<RoleResponse>) =>
    api.put<RoleResponse>(`/roles/${id}`, data),
}
