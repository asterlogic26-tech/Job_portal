import { apiClient } from './client'

export interface LoginRequest {
  email: string
  password: string
}

export interface Token {
  access_token: string
  token_type: string
}

export const authApi = {
  login: async (data: LoginRequest): Promise<Token> => {
    const res = await apiClient.post<Token>('/auth/login', data)
    return res.data
  },
  me: async () => {
    const res = await apiClient.get('/auth/me')
    return res.data
  },
}
