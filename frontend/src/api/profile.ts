import apiClient from './client'

export interface UserProfile {
  id: string
  full_name: string
  current_title: string
  target_titles: string[]
  skills: Array<{ name: string; level?: string; years?: number }>
  experience_years: number
  location: string
  remote_preference: string
  target_salary_min?: number
  target_salary_max?: number
  linkedin_url: string
  github_url: string
  resume_url?: string
  bio: string
  preferences: Record<string, any>
  health_score: number
  created_at: string
  updated_at: string
}

export const profileApi = {
  get: () =>
    apiClient.get<UserProfile>('/profile').then((r) => r.data),

  update: (data: Partial<UserProfile> | Record<string, any>) =>
    apiClient.patch<UserProfile>('/profile', data).then((r) => r.data),

  getHealth: () =>
    apiClient.get('/profile/health').then((r) => r.data),

  uploadResume: (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return apiClient.post('/profile/upload-resume', fd).then((r) => r.data)
  },

  refreshEmbedding: () =>
    apiClient.post('/profile/refresh-embedding').then((r) => r.data),
}
