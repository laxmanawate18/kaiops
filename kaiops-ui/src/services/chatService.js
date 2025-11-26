/**
 * Chat Service
 * 
 * API service for managing chat sessions with backend persistence.
 * Integrates with backend chat API for persistent session storage.
 */

import axios from 'axios'
import { API_BASE_URL } from '../constants/apiConstants'

class ChatService {
  constructor() {
    this.api = axios.create({
      baseURL: `${API_BASE_URL}/chat`,
      headers: {
        'Content-Type': 'application/json'
      }
    })

    // Add auth token interceptor
    this.api.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )
  }

  /**
   * Create a new chat session on backend
   * Returns the session object from CreateSessionResponse
   */
  async createSession(name) {
    try {
      const response = await this.api.post('/sessions', {
        name: name || undefined
      })
      // response.data = { session: ChatSession, message: string }
      return response.data.session
    } catch (error) {
      // Silently fail - backend sync is optional
      return null
    }
  }

  /**
   * Get all user's chat sessions from backend
   */
  async getSessions(includeInactive = true) {
    try {
      const response = await this.api.get('/sessions', {
        params: { include_inactive: includeInactive }
      })
      return response.data.sessions
    } catch (error) {
      // Silently fail - backend sync is optional
      return null
    }
  }

  /**
   * Get a specific session by ID
   */
  async getSession(sessionId) {
    try {
      const response = await this.api.get(`/sessions/${sessionId}`)
      return response.data
    } catch (error) {
      return null
    }
  }

  /**
   * Update session details (name, active status)
   */
  async updateSession(sessionId, updates) {
    try {
      const response = await this.api.patch(`/sessions/${sessionId}`, updates)
      return response.data
    } catch (error) {
      return null
    }
  }

  /**
   * Delete a session from backend
   */
  async deleteSession(sessionId) {
    try {
      const response = await this.api.delete(`/sessions/${sessionId}`)
      return response.data
    } catch (error) {
      return null
    }
  }

  /**
   * Get messages for a specific session
   */
  async getMessages(sessionId, limit = 100) {
    try {
      const response = await this.api.get(`/sessions/${sessionId}/messages`, {
        params: { limit }
      })
      return response.data.messages
    } catch (error) {
      return null
    }
  }

  /**
   * Add a message to a session on backend
   */
  async addMessage(sessionId, message) {
    try {
      const response = await this.api.post(`/sessions/${sessionId}/messages`, {
        text: message.text,
        sender: message.sender,
        metadata: message.metadata
      })
      return response.data
    } catch (error) {
      return null
    }
  }

  /**
   * Delete all sessions for current user
   */
  async deleteAllSessions() {
    try {
      const response = await this.api.delete('/sessions')
      return response.data
    } catch (error) {
      return null
    }
  }

  /**
   * Sync local sessions with backend
   * Useful after login to ensure consistency
   */
  async syncSessions() {
    try {
      const backendSessions = await this.getSessions()
      return backendSessions
    } catch (error) {
      return null
    }
  }
}

export const chatService = new ChatService()
export default chatService
