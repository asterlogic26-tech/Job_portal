import axios from 'axios'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ? `${import.meta.env.VITE_API_URL}/api/v1` : '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

// Attach token from localStorage on every request
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  // Let browser set Content-Type for FormData so it includes the boundary
  if (config.data instanceof FormData) {
    delete config.headers['Content-Type']
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    const message = error.response?.data?.detail || error.message || 'An error occurred'
    return Promise.reject(new Error(message))
  }
)

export default apiClient
