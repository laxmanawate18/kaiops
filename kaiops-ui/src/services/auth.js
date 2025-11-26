import axios from 'axios'
import { API_BASE_URL } from '../constants/apiConstants'

class AuthService {
  constructor() {
    this.axios = axios.create({
      baseURL: `${API_BASE_URL}/auth`,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Add request interceptor to include auth token
    this.axios.interceptors.request.use(
      (config) => {
        const token = this.getToken()
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
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
          this.logout()
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
    )
  }

  async login(credentials) {
    const response = await this.axios.post('/login', credentials)
    const authData = response.data
    
    // Store token and user data
    localStorage.setItem('auth_token', authData.access_token)
    localStorage.setItem('user_data', JSON.stringify(authData.user))
    
    console.log('Login successful - Token stored:', !!authData.access_token)
    console.log('User data stored:', authData.user)
    
    return authData
  }

  async register(userData) {
    const response = await this.axios.post('/register', userData)
    return response.data
  }

  async createUser(userData) {
    // Use register endpoint to create new user
    // Admin can then update role/status if needed
    const response = await this.axios.post('/register', userData)
    return response.data
  }

  async getCurrentUser() {
    const response = await this.axios.get('/me')
    // Update stored user data
    localStorage.setItem('user_data', JSON.stringify(response.data))
    return response.data
  }

  async changePassword(passwordData) {
    const response = await this.axios.post('/change-password', passwordData)
    return response.data
  }

  async getAllUsers() {
    const response = await this.axios.get('/admin/users')
    return response.data
  }

  async deleteUser(username) {
    const response = await this.axios.delete(`/admin/users/${username}`)
    return response.data
  }

  async updateUserRole(username, role) {
    const response = await this.axios.put(`/admin/users/${username}/role`, role, {
      headers: { 'Content-Type': 'application/json' }
    })
    return response.data
  }

  async updateUser(userId, data) {
    const response = await this.axios.put(`/admin/users/${userId}`, data)
    return response.data
  }

  async toggleUserActive(username, isActive) {
    const response = await this.axios.put(
      `/admin/users/${username}/toggle-active`,
      null,
      { params: { is_active: isActive } }
    )
    return response.data
  }

  logout() {
    // NOTE: Chat sessions are NOT cleared on logout - they persist in backend
    // Users can manually clear their chat history if desired
    
    // Only clear authentication tokens
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user_data')
  }

  getToken() {
    return localStorage.getItem('auth_token')
  }

  getCurrentUserData() {
    const userData = localStorage.getItem('user_data')
    return userData ? JSON.parse(userData) : null
  }

  isAuthenticated() {
    return !!this.getToken()
  }

  isAdmin() {
    const user = this.getCurrentUserData()
    return user?.role === 'admin'
  }

  isTeamLead() {
    const user = this.getCurrentUserData()
    return user?.role === 'team_lead' || user?.role === 'admin'
  }
}

export const authService = new AuthService()
