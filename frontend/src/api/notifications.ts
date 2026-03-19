import { apiClient } from './client'

export interface Notification {
  id: string
  type: string
  title: string
  body?: string
  channel: string
  is_read: boolean
  read_at?: string
  action_url?: string
  priority: string
  created_at: string
}

export interface NotificationListResponse {
  notifications: Notification[]
  unread_count: number
  total: number
}

export const notificationsApi = {
  list: (params: { unread_only?: boolean; page?: number; page_size?: number } = {}) =>
    apiClient.get('/notifications', { params }).then((r) => r.data),

  markRead: (id: string) =>
    apiClient.post(`/notifications/${id}/read`).then((r) => r.data),

  markAllRead: () =>
    apiClient.post('/notifications/read-all').then((r) => r.data),

  clearRead: () =>
    apiClient.delete('/notifications/clear-read').then((r) => r.data),
}
