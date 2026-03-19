import { apiClient } from './client'

export interface ManualTask {
  id: string
  source_service: string
  category: string
  priority: string
  title: string
  description?: string
  context_data?: Record<string, any>
  action_url?: string
  status: string
  due_at?: string
  created_at: string
}

export const manualTasksApi = {
  list: (params: { status?: string } = {}) =>
    apiClient.get('/manual-tasks', { params }).then((r) => r.data),

  get: (id: string) =>
    apiClient.get(`/manual-tasks/${id}`).then((r) => r.data),

  start: (id: string) =>
    apiClient.post(`/manual-tasks/${id}/start`).then((r) => r.data),

  resolve: (id: string, completion_notes = '') =>
    apiClient.post(`/manual-tasks/${id}/resolve`, { completion_notes }).then((r) => r.data),

  skip: (id: string) =>
    apiClient.post(`/manual-tasks/${id}/skip`).then((r) => r.data),
}
