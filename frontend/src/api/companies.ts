import { apiClient } from './client'

export interface Company {
  id: string
  name: string
  domain?: string
  industry?: string
  size_range?: string
  funding_stage?: string
  last_funding_date?: string
  last_funding_amount?: number
  headcount_estimate?: number
  headcount_growth_6m?: number
  job_posting_count_30d: number
  hiring_score: number
  is_watched: boolean
  description?: string
  created_at: string
}

export const companiesApi = {
  list: (params: { watched_only?: boolean; q?: string; page?: number; page_size?: number } = {}) =>
    apiClient.get('/companies', { params }).then((r) => r.data),

  get: (id: string) =>
    apiClient.get(`/companies/${id}`).then((r) => r.data),

  watch: (id: string) =>
    apiClient.post(`/companies/${id}/watch`).then((r) => r.data),

  unwatch: (id: string) =>
    apiClient.delete(`/companies/${id}/watch`).then((r) => r.data),

  toggleWatch: (id: string) =>
    apiClient.post(`/companies/${id}/watch`).then((r) => r.data),

  getSignals: (id: string) =>
    apiClient.get(`/companies/${id}/signals`).then((r) => r.data),

  triggerRadar: (id: string) =>
    apiClient.post(`/companies/${id}/trigger-radar`).then((r) => r.data),
}
