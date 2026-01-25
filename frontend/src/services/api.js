import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api

// Helper functions for common API operations
export const uploadFile = async (endpoint, file, additionalData = {}) => {
  const formData = new FormData()
  formData.append('image', file)

  Object.entries(additionalData).forEach(([key, value]) => {
    formData.append(key, value)
  })

  return api.post(endpoint, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const getUploadUrl = (path) => {
  const baseUrl = import.meta.env.VITE_API_URL || '/api'
  return `${baseUrl}/models/uploads/${path}`
}
