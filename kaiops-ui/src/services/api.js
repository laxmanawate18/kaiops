import axios from 'axios'
import { API_BASE_URL } from '../constants/apiConstants'

class ApiService {
  constructor() {
    this.axios = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Add request interceptor to include auth token
    this.axios.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
          console.log('Token added to request:', config.url)
        } else {
          console.warn('No token found in localStorage for:', config.url)
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    // Add response interceptor to handle auth errors
    this.axios.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          console.warn('401 Unauthorized - logging out')
          localStorage.removeItem('auth_token')
          localStorage.removeItem('user_data')
          // Only redirect if we're not already on login page
          if (window.location.pathname !== '/login') {
            window.location.href = '/login'
          }
        }
        return Promise.reject(error)
      }
    )
  }

  async healthCheck() {
    const response = await this.axios.get('/health')
    return response.data
  }

  async sendMessage(request) {
    const response = await this.axios.post('/chat', request)
    return response.data
  }

  async getUserSessions(userId) {
    const response = await this.axios.get(`/sessions/${userId}`)
    return response.data
  }

  async deleteSession(userId, sessionId) {
    const response = await this.axios.delete(`/sessions/${userId}/${sessionId}`)
    return response.data
  }

  async getStats() {
    const response = await this.axios.get('/stats')
    return response.data
  }

  async getChatStats() {
    const response = await this.axios.get('/chat/stats')
    return response.data
  }
}

export const apiService = new ApiService()
