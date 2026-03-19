import { apiClient } from './client'

export interface Application {
  id: string
  job_id: string
  status: string
  applied_at?: string
  confirmation_number?: string
  application_method?: string
  follow_up_date?: string
  recruiter_name?: string
  notes?: string
  timeline?: Array<{ status: string; timestamp: string; notes?: string }>
  created_at: string
  job_title?: string
  company_name?: string
  match_score?: number
}

export const applicationsApi = {
  list: (params: { status?: string } = {}) =>
    apiClient.get('/applications', { params }).then((r) => r.data),

  create: (data: { job_id: string; status?: string; notes?: string }) =>
    apiClient.post('/applications', data).then((r) => r.data),

  get: (id: string) =>
    apiClient.get(`/applications/${id}`).then((r) => r.data),

  update: (id: string, data: Record<string, any>) =>
    apiClient.patch(`/applications/${id}`, data).then((r) => r.data),

  updateStatus: (id: string, status: string) =>
    apiClient.patch(`/applications/${id}/status`, { status }).then((r) => r.data),

  delete: (id: string) =>
    apiClient.delete(`/applications/${id}`).then((r) => r.data),
}
