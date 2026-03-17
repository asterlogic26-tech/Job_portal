import { apiClient } from './client'

export interface ContentDraft {
  id: string
  type: string
  job_id?: string
  target_person?: string
  target_company?: string
  subject_line?: string
  content_body?: string
  tone?: string
  status: string
  created_at: string
}

export const contentApi = {
  list: (params: { content_type?: string; status?: string; page?: number; page_size?: number } = {}) =>
    apiClient.get('/content', { params }).then((r) => r.data),

  generate: (data: {
    content_type: string
    job_id?: string
    company_id?: string
    application_id?: string
    extra_context?: Record<string, any>
  }) => apiClient.post('/content/generate', data).then((r) => r.data),

  get: (id: string) =>
    apiClient.get(`/content/${id}`).then((r) => r.data),

  update: (id: string, data: { body?: string; title?: string; subject?: string; status?: string }) =>
    apiClient.patch(`/content/${id}`, data).then((r) => r.data),

  approve: (id: string) =>
    apiClient.post(`/content/${id}/approve`).then((r) => r.data),

  delete: (id: string) =>
    apiClient.delete(`/content/${id}`).then((r) => r.data),
}
