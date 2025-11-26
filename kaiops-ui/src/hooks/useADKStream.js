import { useState, useCallback, useRef, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'

export const useADKStream = (chatSessionId) => {
  const { user } = useAuth()
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [timelineEvents, setTimelineEvents] = useState([])

  const eventSourceRef = useRef(null)
  const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  const appName = import.meta.env.VITE_APP_NAME || 'sre_agent'
  const userId = user?.id || 'anonymous-user'
  
  // Get ADK session storage key for current chat session
  const getAdkSessionKey = useCallback(() => {
    if (!chatSessionId || !user?.id) return null
    return `adk-session-${user.id}-${chatSessionId}`
  }, [chatSessionId, user?.id])
  
  // Initialize or restore ADK session ID from storage
  const [adkSessionId] = useState(() => {
    const storageKey = getAdkSessionKey()
    if (storageKey) {
      const stored = localStorage.getItem(storageKey)
      if (stored) return stored
    }
    return 'session-' + Math.random().toString(36).slice(2)
  })
  
  const sessionIdRef = useRef(adkSessionId)
  const sessionCreatedRef = useRef(false)
  
  // Update ADK session ID when chat session changes
  useEffect(() => {
    const storageKey = getAdkSessionKey()
    if (storageKey) {
      const stored = localStorage.getItem(storageKey)
      if (stored && stored !== sessionIdRef.current) {
        // Restore existing ADK session for this chat
        sessionIdRef.current = stored
        sessionCreatedRef.current = false // Will verify/create on next message
      } else if (!stored) {
        // New chat session - generate and save new ADK session ID
        const newAdkSessionId = 'session-' + Math.random().toString(36).slice(2)
        sessionIdRef.current = newAdkSessionId
        sessionCreatedRef.current = false
        localStorage.setItem(storageKey, newAdkSessionId)
      }
    }
    
    // Clear messages when switching chat sessions
    setMessages([])
    setTimelineEvents([])
    setError(null)
  }, [chatSessionId, getAdkSessionKey])

  const addMessage = useCallback((message, sender = 'user') => {
    const newMessage = {
      id: Date.now() + Math.random(),
      text: message,
      sender,
      timestamp: new Date()
    }
    setMessages(prev => [...prev, newMessage])
    return newMessage
  }, [])

  const addTimelineEvent = useCallback((event) => {
    setTimelineEvents(prev => [...prev, event])
  }, [])

  const toContent = (text) => ({
    role: 'user',
    parts: [{ text }]
  })

  // Create session only if it doesn't exist
  const ensureSession = useCallback(async () => {
    if (sessionCreatedRef.current) return

    try {
      const response = await fetch(
        `${apiUrl}/apps/${appName}/users/${userId}/sessions/${sessionIdRef.current}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ state: {} })
        }
      )
      if (response.ok || response.status === 400) {
        sessionCreatedRef.current = true
      } else {
        throw new Error(`Session creation failed: ${response.status}`)
      }
    } catch (err) {
      if (err.message.includes('400')) {
        sessionCreatedRef.current = true
      } else {
        throw err
      }
    }
  }, [apiUrl, appName, userId])

  const sendMessage = useCallback(async (message) => {
    setError(null)
    setIsLoading(true)
    addMessage(message, 'user')

    try {
      await ensureSession()

      const response = await fetch(`${apiUrl}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          app_name: appName,
          user_id: userId,
          session_id: sessionIdRef.current,
          streaming: true,
          new_message: toContent(message)
        })
      })

      if (!response.ok) {
        const errorDetail = await response.json().catch(() => ({}))
        throw new Error(`API Error: ${response.status} - ${JSON.stringify(errorDetail)}`)
      }

      const result = await response.json()

      // Handle direct event array response
      if (Array.isArray(result)) {
        result.forEach(event => {
          addTimelineEvent(event)
          if (event.content?.parts) {
            event.content.parts.forEach(part => {
              if (part.text) addMessage(part.text, 'agent')
            })
          }
        })
        setIsLoading(false)
        return { type: 'handled_direct_response' }
      }

      // Handle streaming-based response
      const runId = result.run_id || result.invocationId || result.id
      if (runId) {
        startStreaming(runId)
        return { type: 'streaming_started', runId }
      }

      throw new Error('Response was not an event array and contained no run_id.')
    } catch (err) {

      setError(err.message)
      addMessage(`// ERROR: Unable to send message.\n${err.message}`, 'agent')
      setIsLoading(false)
      return { type: 'error', error: err.message }
    }
  }, [apiUrl, appName, userId, ensureSession, addMessage, addTimelineEvent])

  const startStreaming = useCallback((runId) => {
    if (!runId) return
    eventSourceRef.current?.close()

    const url = `${apiUrl}/stream/${runId}`
    const eventSource = new EventSource(url)
    eventSourceRef.current = eventSource

    eventSource.onmessage = (e) => {
      try {
        const eventData = JSON.parse(e.data)
        addTimelineEvent(eventData)
        if (eventData.content?.parts) {
          eventData.content.parts.forEach(p => p.text && addMessage(p.text, 'agent'))
        }
        if (eventData.is_final_response || eventData.event === 'on_agent_final_output') {
          eventSource.close()
          setIsLoading(false)
        }
      } catch (parseErr) {

      }
    }

    eventSource.onerror = (err) => {

      setError('Stream connection failed')
      eventSource.close()
      setIsLoading(false)
    }
  }, [apiUrl, addMessage, addTimelineEvent])

  const clearSession = useCallback(async () => {
    // Close any active streams
    eventSourceRef.current?.close()

    // Clear local state
    setMessages([])
    setTimelineEvents([])
    setError(null)
    setIsLoading(false)

    // Try to delete the session from the backend
    if (sessionCreatedRef.current) {
      try {
        await fetch(
          `${apiUrl}/apps/${appName}/users/${userId}/sessions/${sessionIdRef.current}`,
          {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' }
          }
        )
      } catch (err) {

      }
    }

    // Generate new session ID
    sessionIdRef.current = 'session-' + Math.random().toString(36).slice(2)
    sessionCreatedRef.current = false
    
    // Clear stored ADK session ID
    const storageKey = getAdkSessionKey()
    if (storageKey) {
      localStorage.removeItem(storageKey)
    }
  }, [apiUrl, appName, userId, getAdkSessionKey])

  const createNewSession = useCallback(async () => {
    await clearSession()
    return sessionIdRef.current
  }, [clearSession])

  useEffect(() => () => {
    eventSourceRef.current?.close()
  }, [])

  return {
    messages,
    isLoading,
    error,
    timelineEvents,
    sendMessage,
    clearSession,
    createNewSession,
    sessionId: sessionIdRef.current
  }
}
