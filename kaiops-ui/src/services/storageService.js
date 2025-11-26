// Local storage service for session management
// This provides a consistent API for managing chat sessions and messages
// Now with optional backend persistence for chat history across devices and sessions

import { chatService } from './chatService'

// Helper to get user-specific storage key
const getUserStorageKey = (key) => {
  try {
    const userData = localStorage.getItem('user_data')
    if (userData) {
      const user = JSON.parse(userData)
      if (user && user.id) {
        return `${key}-user-${user.id}`
      }
    }
  } catch (error) {
    // Silently handle errors
  }
  // CRITICAL: Do NOT fallback to non-user-specific key for security
  // If no user is logged in, return null to prevent data leakage
  return null
}

export const storageService = {
  // Session management
  getSessions: () => {
    try {
      const storageKey = getUserStorageKey('kaiops-sessions')
      if (!storageKey) {
        // Removed console log
        return []
      }
      const sessions = localStorage.getItem(storageKey)
      return sessions ? JSON.parse(sessions) : []
    } catch (error) {
      // Removed console log
      return []
    }
  },

  createSession: async (sessionName) => {
    try {
      const storageKey = getUserStorageKey('kaiops-sessions')
      if (!storageKey) {
        // Removed console log
        return null
      }
      const sessions = storageService.getSessions()
      const timestamp = new Date().toLocaleString('en-US', { 
        month: 'short', 
        day: 'numeric', 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true 
      })
      
      // Try to create session in backend first (for persistence)
      let backendSession = null
      try {
        backendSession = await chatService.createSession(sessionName || `New Chat ${timestamp}`)
      } catch (error) {
        // Backend creation failed, continue with local-only session
      }
      
      // Create session (use backend ID if available, otherwise generate local ID)
      const newSession = {
        id: backendSession?.id || ('session-' + Math.random().toString(36).slice(2)),
        name: sessionName || `New Chat ${timestamp}`,
        createdAt: backendSession?.created_at || new Date().toISOString(),
        lastModified: backendSession?.last_modified || new Date().toISOString(),
        messages: [],
        synced: !!backendSession // Track if session is synced with backend
      }
      sessions.unshift(newSession)
      localStorage.setItem(storageKey, JSON.stringify(sessions))
      return newSession
    } catch (error) {
      // Removed console log
      return null
    }
  },

  deleteSession: async (sessionId) => {
    try {
      const storageKey = getUserStorageKey('kaiops-sessions')
      if (!storageKey) {
        // Removed console log
        return false
      }
      const sessions = storageService.getSessions()
      const sessionToDelete = sessions.find(s => s.id === sessionId)
      
      // Delete from backend if session was synced
      if (sessionToDelete?.synced) {
        try {
          await chatService.deleteSession(sessionId)
        } catch (error) {
          // Silently fail - local deletion will proceed
        }
      }
      
      const filteredSessions = sessions.filter(session => session.id !== sessionId)
      localStorage.setItem(storageKey, JSON.stringify(filteredSessions))
      return true
    } catch (error) {
      // Removed console log
      return false
    }
  },

  clearAllSessions: () => {
    try {
      const storageKey = getUserStorageKey('kaiops-sessions')
      if (!storageKey) {
        // Removed console log
        return false
      }
      localStorage.removeItem(storageKey)
      return true
    } catch (error) {
      // Removed console log
      return false
    }
  },

  // Message management
  getMessages: (sessionId) => {
    try {
      const sessions = storageService.getSessions()
      const session = sessions.find(s => s.id === sessionId)
      return session ? session.messages || [] : []
    } catch (error) {
      // Removed console log
      return []
    }
  },

  addMessage: async (sessionId, message) => {
    try {
      const storageKey = getUserStorageKey('kaiops-sessions')
      if (!storageKey) {
        // Removed console log
        return null
      }
      
      const sessions = storageService.getSessions()
      const sessionIndex = sessions.findIndex(s => s.id === sessionId)

      if (sessionIndex === -1) {
        // Removed console log
        return false
      }

      const newMessage = {
        id: Date.now() + Math.random(),
        text: message.text,
        sender: message.sender,
        timestamp: new Date().toISOString(),
        ...(message.imageUrl && { imageUrl: message.imageUrl }),
        ...(message.userMessage && { userMessage: message.userMessage }),
        ...(message.feedback && { feedback: message.feedback })
      }

      sessions[sessionIndex].messages.push(newMessage)
      sessions[sessionIndex].lastModified = new Date().toISOString()

      // Update session name if it's the first user message
      if (message.sender === 'user' && sessions[sessionIndex].messages.length === 1) {
        const truncatedText = message.text.trim().substring(0, 20)
        sessions[sessionIndex].name = truncatedText + (message.text.trim().length > 20 ? '...' : '')
      }

      localStorage.setItem(storageKey, JSON.stringify(sessions))
      
      // Try to sync message to backend (if session is synced)
      if (sessions[sessionIndex].synced) {
        try {
          await chatService.addMessage(sessionId, {
            text: message.text,
            sender: message.sender,
            metadata: message.metadata
          })
        } catch (error) {
          // Backend sync failed, but message is saved locally
        }
      }
      
      return newMessage
    } catch (error) {
      // Removed console log
      return null
    }
  },

  updateMessage: (sessionId, messageId, updates) => {
    try {
      const storageKey = getUserStorageKey('kaiops-sessions')
      if (!storageKey) {
        // Removed console log
        return false
      }
      
      const sessions = storageService.getSessions()
      const sessionIndex = sessions.findIndex(s => s.id === sessionId)

      if (sessionIndex === -1) {
        // Removed console log
        return false
      }

      const messageIndex = sessions[sessionIndex].messages.findIndex(m => m.id === messageId)
      
      if (messageIndex === -1) {
        // Removed console log
        return false
      }

      sessions[sessionIndex].messages[messageIndex] = {
        ...sessions[sessionIndex].messages[messageIndex],
        ...updates
      }
      sessions[sessionIndex].lastModified = new Date().toISOString()

      localStorage.setItem(storageKey, JSON.stringify(sessions))
      return true
    } catch (error) {
      // Removed console log
      return false
    }
  },

  clearMessages: (sessionId) => {
    try {
      const storageKey = getUserStorageKey('kaiops-sessions')
      if (!storageKey) {
        // Removed console log
        return false
      }
      
      const sessions = storageService.getSessions()
      const sessionIndex = sessions.findIndex(s => s.id === sessionId)

      if (sessionIndex === -1) {
        // Removed console log
        return false
      }

      sessions[sessionIndex].messages = []
      sessions[sessionIndex].lastModified = new Date().toISOString()
      localStorage.setItem(storageKey, JSON.stringify(sessions))
      return true
    } catch (error) {
      // Removed console log
      return false
    }
  },

  // Session utilities
  updateSessionName: async (sessionId, newName) => {
    try {
      const storageKey = getUserStorageKey('kaiops-sessions')
      if (!storageKey) {
        // Removed console log
        return false
      }
      
      const sessions = storageService.getSessions()
      const sessionIndex = sessions.findIndex(s => s.id === sessionId)

      if (sessionIndex === -1) {
        // Removed console log
        return false
      }

      // Update locally first
      sessions[sessionIndex].name = newName
      sessions[sessionIndex].lastModified = new Date().toISOString()
      localStorage.setItem(storageKey, JSON.stringify(sessions))

      // Sync with backend if session was created from backend
      if (sessions[sessionIndex].synced) {
        try {
          await chatService.updateSession(sessionId, { name: newName })
        } catch (error) {
          // Silently fail - local update succeeded
        }
      }

      return true
    } catch (error) {
      // Removed console log
      return false
    }
  },

  getSession: (sessionId) => {
    try {
      const sessions = storageService.getSessions()
      return sessions.find(s => s.id === sessionId) || null
    } catch (error) {
      // Removed console log
      return null
    }
  },

  // Security: Get current user ID for isolation verification
  getCurrentUserId: () => {
    try {
      const userData = localStorage.getItem('user_data')
      if (userData) {
        const user = JSON.parse(userData)
        return user?.id || null
      }
    } catch (error) {
      // Removed console log
    }
    return null
  },

  // Clean up user-specific data (only called when user manually clears all chats)
  clearUserData: () => {
    try {
      const userId = storageService.getCurrentUserId()
      if (userId) {
        // Remove user-specific sessions from localStorage
        const storageKey = `kaiops-sessions-user-${userId}`
        localStorage.removeItem(storageKey)
        
        // Also remove all ADK session mappings for this user
        const keysToRemove = []
        for (let i = 0; i < localStorage.length; i++) {
          const key = localStorage.key(i)
          if (key && key.startsWith(`adk-session-${userId}-`)) {
            keysToRemove.push(key)
          }
        }
        keysToRemove.forEach(key => localStorage.removeItem(key))
        
        // Removed console log
      }
    } catch (error) {
      // Removed console log
    }
  },

  // ==================== Backend Sync Methods ====================
  
  /**
   * Sync sessions with backend on login
   * Loads sessions from backend if available, merges with local
   */
  syncWithBackend: async () => {
    try {
      const backendSessions = await chatService.getSessions()
      
      if (backendSessions && backendSessions.length > 0) {
        // Merge backend sessions with local storage
        const localSessions = storageService.getSessions()
        const storageKey = getUserStorageKey('kaiops-sessions')
        
        if (!storageKey) {
          return false
        }
        
        // Create a map of existing local sessions by ID
        const localSessionMap = new Map(localSessions.map(s => [s.id, s]))
        
        // Merge: backend sessions take precedence for conflicts
        const mergedSessions = backendSessions.map(backendSession => {
          const localSession = localSessionMap.get(backendSession.id)
          if (localSession) {
            // Merge: keep local messages but update metadata from backend
            return {
              ...backendSession,
              messages: localSession.messages || [],
              synced: true // Sessions from backend are synced
            }
          }
          return {
            ...backendSession,
            messages: [], // Backend doesn't store individual messages yet
            synced: true // Sessions from backend are synced
          }
        })
        
        // Add any local-only sessions that aren't on backend
        localSessions.forEach(localSession => {
          if (!backendSessions.find(bs => bs.id === localSession.id)) {
            mergedSessions.push(localSession)
          }
        })
        
        // Sort by last modified
        mergedSessions.sort((a, b) => 
          new Date(b.last_modified || b.lastModified) - new Date(a.last_modified || a.lastModified)
        )
        
        // Save merged sessions
        localStorage.setItem(storageKey, JSON.stringify(mergedSessions))
        return true
      } else {
        return false
      }
    } catch (error) {
      // Silently fail - backend sync is optional
      return false
    }
  },
  
  /**
   * Push local session to backend
   */
  pushSessionToBackend: async (sessionId) => {
    try {
      const session = storageService.getSession(sessionId)
      if (!session) {
        return false
      }
      
      // Try to create session on backend
      await chatService.createSession(session.name)
      return true
    } catch (error) {
      return false
    }
  }
}
