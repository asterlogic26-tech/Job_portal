import { apiClient } from './client'

export interface Job {
  id: string
  title: string
  company_name: string
  source: string
  source_url?: string
  location?: string
  remote_policy?: string
  seniority_level?: string
  employment_type?: string
  salary_min?: number
  salary_max?: number
  salary_currency: string
  skills_required?: Array<{ name: string; category?: string }>
  description_markdown?: string
  apply_url?: string
  posted_at?: string
  discovered_at: string
  status: string
  is_duplicate: boolean
  match_score?: number
  interview_probability?: number
}

export interface JobListResponse {
  jobs: Job[]
  total: number
  page: number
  page_size: number
}

export interface JobSearchParams {
  page?: number
  page_size?: number
  remote_policy?: string
  seniority_level?: string
  salary_min?: number
  salary_max?: number
  min_match_score?: number
  status?: string
  sort_by?: string
}

export const jobsApi = {
  list: (params: JobSearchParams = {}) =>
    apiClient.get('/jobs', { params }).then((r) => r.data),

  get: (id: string) =>
    apiClient.get(`/jobs/${id}`).then((r) => r.data),

  hide: (id: string) =>
    apiClient.post(`/jobs/${id}/hide`).then((r) => r.data),

  unhide: (id: string) =>
    apiClient.post(`/jobs/${id}/unhide`).then((r) => r.data),

  save: (id: string) =>
    apiClient.post(`/jobs/${id}/save`).then((r) => r.data),

  unsave: (id: string) =>
    apiClient.delete(`/jobs/${id}/save`).then((r) => r.data),

  triggerDiscovery: () =>
    apiClient.post('/jobs/trigger-discovery').then((r) => r.data),

  triggerMatch: (id: string) =>
    apiClient.post(`/jobs/${id}/trigger-match`).then((r) => r.data),
}
