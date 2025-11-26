import axios from 'axios'
import { API_BASE_URL } from '../constants/apiConstants'

class TeamService {
  constructor() {
    this.axios = axios.create({
      baseURL: `${API_BASE_URL}/teams`,
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
          localStorage.removeItem('auth_token')
          localStorage.removeItem('user_data')
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
    )
  }

  // Team Management
  async createTeam(teamData) {
    const response = await this.axios.post('/teams', teamData)
    return response.data
  }

  async getAllTeams() {
    const response = await this.axios.get('/teams')
    return response.data
  }

  async getTeam(teamId) {
    const response = await this.axios.get(`/teams/${teamId}`)
    return response.data
  }

  async updateTeam(teamId, updates) {
    const response = await this.axios.put(`/teams/${teamId}`, updates)
    return response.data
  }

  async deleteTeam(teamId) {
    const response = await this.axios.delete(`/teams/${teamId}`)
    return response.data
  }

  // Team Member Management
  async assignUserToTeam(teamId, assignment) {
    const response = await this.axios.post(`/teams/${teamId}/members`, assignment)
    return response.data
  }

  async getTeamMembers(teamId) {
    const response = await this.axios.get(`/teams/${teamId}/members`)
    return response.data
  }

  async removeUserFromTeam(teamId, userId) {
    const response = await this.axios.delete(`/teams/${teamId}/members/${userId}`)
    return response.data
  }

  async updateTeamLead(teamId, userId, isTeamLead) {
    const response = await this.axios.put(`/teams/${teamId}/members/${userId}/lead`, isTeamLead, {
      headers: { 'Content-Type': 'application/json' }
    })
    return response.data
  }

  async promoteToTeamLead(teamId, userId) {
    const response = await this.axios.put(`/teams/${teamId}/members/${userId}/lead`, true, {
      headers: { 'Content-Type': 'application/json' }
    })
    return response.data
  }

  // Permission Management
  async grantUserPermission(permission) {
    const response = await this.axios.post('/permissions/users', permission)
    return response.data
  }

  async grantTeamPermission(permission) {
    const response = await this.axios.post('/permissions/teams', permission)
    return response.data
  }

  async getUserPermissions(userId) {
    const response = await this.axios.get(`/permissions/users/${userId}`)
    return response.data
  }

  async getTeamPermissions(teamId) {
    const response = await this.axios.get(`/permissions/teams/${teamId}`)
    return response.data
  }

  async revokeUserPermission(permissionId) {
    const response = await this.axios.delete(`/permissions/users/${permissionId}`)
    return response.data
  }

  async revokeTeamPermission(permissionId) {
    const response = await this.axios.delete(`/permissions/teams/${permissionId}`)
    return response.data
  }

  // Agent Management (new)
  async getTeamAgents(teamId, priority = null) {
    const params = {}
    if (priority) params.priority = priority
    const response = await this.axios.get(`/teams/${teamId}/agents`, { params })
    return response.data
  }

  async assignTeamAgent(teamId, agentData) {
    const response = await this.axios.post(`/teams/${teamId}/agents`, agentData)
    return response.data
  }

  async removeTeamAgent(teamId, agentId) {
    const response = await this.axios.delete(`/teams/${teamId}/agents/${agentId}`)
    return response.data
  }

  // System Information
  async getSystemStats() {
    const response = await this.axios.get('/stats')
    return response.data
  }

  async getAvailableApplications() {
    const response = await this.axios.get('/applications')
    return response.data
  }

  async getPermissionTypes() {
    const response = await this.axios.get('/permissions/types')
    return response.data
  }

  // Helper methods for searching users (calls auth service)
  async searchUsers(query) {
    // This calls the auth service to search users
    const response = await axios.get(`${API_BASE_URL}/auth/admin/users`, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('auth_token')}`
      },
      params: { search: query }
    })
    return response.data
  }
}

export const teamService = new TeamService()
