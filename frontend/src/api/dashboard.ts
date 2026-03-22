import { apiClient } from './client'

export interface DashboardStats {
  total_jobs_discovered: number
  new_jobs_today: number
  high_match_jobs: number
  total_applications: number
  active_applications: number
  pending_manual_tasks: number
  unread_notifications: number
  watched_companies: number
}

export interface DashboardSummary {
  stats: DashboardStats
  top_jobs: any[]
  recent_applications: any[]
  hot_companies: any[]
  pending_tasks: any[]
  recent_notifications: any[]
}

export const dashboardApi = {
  getSummary: () =>
    apiClient.get<DashboardSummary>('/dashboard/summary').then((r) => r.data),
}
