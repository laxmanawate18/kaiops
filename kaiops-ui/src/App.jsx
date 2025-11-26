import { useState, useCallback, useEffect, useRef, useMemo } from 'react'
import { Routes, Route, Link, useLocation, Navigate } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { useAuth } from './contexts/AuthContext'
import { useADKStream } from './hooks/useADKStream'
import { storageService } from './services/storageService'
import ChatHeader from './components/ChatHeader'
import Sidebar from './components/Sidebar'
import MessageBubble from './components/MessageBubble'
import TypingIndicator from './components/TypingIndicator'
import QuickActions from './components/QuickActions'
import ConfirmDialog from './components/ConfirmDialog'
import ChatInput from './components/ChatInput'
import ThreeBackground from './components/ThreeBackground'
import Login from './components/Login'
import Register from './components/Register'
import Dashboard from './components/Dashboard'
import UserManagement from './components/UserManagement'
import FeedbackReview from './components/FeedbackReview'
import Profile from './components/Profile'
import ProtectedRoute from './components/ProtectedRoute'
import { ApplicationList, ApplicationForm, ApplicationDetails } from './pages/Applications'

const PageTransition = ({ children }) => (
  <motion.div
    initial={{ opacity: 0, y: 10, scale: 0.99 }}
    animate={{ opacity: 1, y: 0, scale: 1 }}
    exit={{ opacity: 0, y: -10, scale: 0.99 }}
    transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
    className="h-full w-full"
  >
    {children}
  </motion.div>
)

function ChatInterface() {
  const { user } = useAuth()
  const location = useLocation()
  const [chatSessions, setChatSessions] = useState([])
  const [currentChatSessionId, setCurrentChatSessionId] = useState(null)
  const [showQuickActionsSection, setShowQuickActionsSection] = useState(true)
  const [displayMessages, setDisplayMessages] = useState([])
  const lastHandledMessageRef = useRef(null)
  const messagesEndRef = useRef(null)

  const {
    messages: adkMessages,
    isLoading,
    sendMessage: adkSendMessage,
    clearSession: adkClearSession,
    createNewSession: adkCreateNewSession
  } = useADKStream(currentChatSessionId)

  // Reset ref when navigation occurs without initial message (e.g., manual navigation)
  useEffect(() => {
    if (!location.state?.initialMessage) {
      lastHandledMessageRef.current = null
    }
  }, [location.pathname, location.state?.initialMessage])

  // Load user-specific sessions on mount and when user changes
  useEffect(() => {
    const loadSessions = async () => {
      // First try to sync with backend (persisted sessions)
      if (user?.id) {
        await storageService.syncWithBackend()
      }
      
      // Load sessions (either synced from backend or local)
      const sessions = storageService.getSessions()
      setChatSessions(sessions)
      if (sessions.length > 0) {
        setCurrentChatSessionId(sessions[0].id)
      } else {
        // No sessions, show empty state
        setCurrentChatSessionId(null)
        setShowQuickActionsSection(true)
      }
    }
    
    loadSessions()
  }, [user?.id]) // Reload sessions when user changes

  useEffect(() => {
    if (currentChatSessionId) {
      const messages = storageService.getMessages(currentChatSessionId)
      setDisplayMessages(messages)
      setShowQuickActionsSection(messages.length === 0)
    } else {
      setDisplayMessages([])
      setShowQuickActionsSection(true)
    }
  }, [currentChatSessionId])

  useEffect(() => {
    const syncMessages = async () => {
      if (adkMessages.length > 0 && currentChatSessionId) {
        const storedMessages = storageService.getMessages(currentChatSessionId)
        const newMessages = adkMessages.slice(storedMessages.length)

        for (const msg of newMessages) {
          // Find the last user message to associate with this AI response
          let lastUserMessage = 'User query'
          for (let i = storedMessages.length - 1; i >= 0; i--) {
            if (storedMessages[i].sender === 'user') {
              lastUserMessage = storedMessages[i].text
              break
            }
          }

          await storageService.addMessage(currentChatSessionId, {
            text: msg.text || msg.content,
            sender: msg.sender,
            timestamp: msg.timestamp,
            // Associate AI response with the previous user message
            ...(msg.sender === 'agent' && { userMessage: lastUserMessage })
          })
        }

        if (newMessages.length > 0) {
          setDisplayMessages(storageService.getMessages(currentChatSessionId))
          const updatedSessions = storageService.getSessions()
          setChatSessions(updatedSessions)
        }
      }
    }

    syncMessages()
  }, [adkMessages, currentChatSessionId])

  useEffect(() => {
    scrollToBottom()
  }, [displayMessages, isLoading])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  const createNewChatSession = useCallback(async (name) => {
    const newSession = await storageService.createSession(name)
    if (newSession) {
      setChatSessions(storageService.getSessions())
      setCurrentChatSessionId(newSession.id)
      setShowQuickActionsSection(true)
      await adkCreateNewSession()
      return newSession
    }
    return null
  }, [adkCreateNewSession])

  const handleSelectChatSession = useCallback((sessionId) => {
    setCurrentChatSessionId(sessionId)
  }, [])

  const handleSendMessage = useCallback(async (text, sessionId = null) => {
    let targetSessionId = sessionId || currentChatSessionId
    
    // If no session exists, create one first
    if (!targetSessionId) {
      const newSession = await createNewChatSession()
      if (newSession) {
        targetSessionId = newSession.id
      } else {

        return
      }
    }

    // Store the user message
    await storageService.addMessage(targetSessionId, {
      text,
      sender: 'user',
      timestamp: new Date().toISOString()
    })

    setDisplayMessages(storageService.getMessages(targetSessionId))
    setChatSessions(storageService.getSessions())
    setShowQuickActionsSection(false)

    try {
      await adkSendMessage(text)
      // The AI response will be added by the adkMessages useEffect
      // We'll update it there with the userMessage context
    } catch (error) {

      await storageService.addMessage(targetSessionId, {
        text: `Error: Failed to send message to ADK. ${error.message}`,
        sender: 'agent',
        timestamp: new Date().toISOString(),
        userMessage: text
      })
      setDisplayMessages(storageService.getMessages(targetSessionId))
    }
  }, [currentChatSessionId, adkSendMessage, createNewChatSession])

  const handleClearChat = useCallback(async () => {
    if (!currentChatSessionId) return
    storageService.clearMessages(currentChatSessionId)
    await adkClearSession()
    setDisplayMessages([])
    setShowQuickActionsSection(true)
    setChatSessions(storageService.getSessions())
  }, [currentChatSessionId, adkClearSession])

  const handleClearAllSessions = useCallback(async () => {
    try {
      const { chatService } = await import('./services/chatService')
      await chatService.deleteAllSessions()
      storageService.clearAllSessions()
      setChatSessions([])
      setCurrentChatSessionId(null)
      setDisplayMessages([])
      setShowQuickActionsSection(true)
    } catch (error) {
      console.error('Failed to clear all sessions:', error)
    }
  }, [])

  const handleRenameChatSession = useCallback(async (sessionId, newName) => {
    if (!sessionId || !newName) return
    await storageService.updateSessionName(sessionId, newName)
    setChatSessions(storageService.getSessions())
  }, [])

  const handleDeleteChat = useCallback(async (sessionId) => {
    await storageService.deleteSession(sessionId)
    const updatedSessions = storageService.getSessions()
    setChatSessions(updatedSessions)
    
    // If deleting the current session, switch to another session or show empty state
    if (sessionId === currentChatSessionId) {
      if (updatedSessions.length > 0) {
        const newSessionId = updatedSessions[0].id
        setCurrentChatSessionId(newSessionId)
        setDisplayMessages(storageService.getMessages(newSessionId))
        setShowQuickActionsSection(storageService.getMessages(newSessionId).length === 0)
      } else {
        // All chats deleted, show empty state - don't auto-create
        setCurrentChatSessionId(null)
        setDisplayMessages([])
        setShowQuickActionsSection(true)
      }
    }
  }, [currentChatSessionId])

  const handleUpdateMessage = useCallback((messageId, updatedMessage) => {
    if (!currentChatSessionId) return
    
    storageService.updateMessage(currentChatSessionId, messageId, updatedMessage)
    setDisplayMessages(storageService.getMessages(currentChatSessionId))
  }, [currentChatSessionId])

  const currentChatSessionName = useMemo(() => {
    const session = chatSessions.find(s => s.id === currentChatSessionId)
    return session ? session.name : "New Chat"
  }, [chatSessions, currentChatSessionId])

  // Handle initial message from navigation state (e.g., from Dashboard Quick Actions)
  useEffect(() => {
    const initialMessage = location.state?.initialMessage
    
    // Only process if we have a message AND we haven't processed this exact message yet
    if (initialMessage && lastHandledMessageRef.current !== initialMessage) {
      lastHandledMessageRef.current = initialMessage
      
      // Clear the state immediately to prevent re-sending
      window.history.replaceState({}, document.title)
      
      // Send message immediately using current or new session
      const sendInitialMessage = async () => {
        let targetSessionId = currentChatSessionId
        
        // Create new session only if none exists
        if (!targetSessionId) {
          const newSession = await createNewChatSession('New Chat')
          targetSessionId = newSession?.id
        }
        
        // Send message if we have a valid session
        if (targetSessionId) {
          // Small delay to ensure session is ready
          setTimeout(() => {
            handleSendMessage(initialMessage, targetSessionId)
          }, 200)
        }
      }
      
      sendInitialMessage()
    }
  }, [location.state?.initialMessage])

  return (
    <div className="flex w-full h-full rounded-2xl glass-panel shadow-2xl overflow-hidden">
      <Sidebar
        chatSessions={chatSessions}
        currentChatSessionId={currentChatSessionId}
        onSelectChatSession={handleSelectChatSession}
        onCreateNewChat={createNewChatSession}
        onDeleteChat={handleDeleteChat}
        onRenameChat={handleRenameChatSession}
      />

      <div className="flex-1 flex flex-col bg-transparent min-w-0">
        <ChatHeader
          currentChatSessionName={currentChatSessionName}
          onClearChat={handleClearChat}
          onRenameChatSession={handleRenameChatSession}
          currentChatSessionId={currentChatSessionId}
          onClearAllSessions={handleClearAllSessions}
        />

        <div className="flex-1 p-6 overflow-y-auto custom-scrollbar min-h-0">
          {showQuickActionsSection ? (
            <div className="flex flex-col items-center justify-center h-full w-full">
              <QuickActions onSendMessage={handleSendMessage} />
            </div>
          ) : (
            <div className="flex flex-col space-y-2">
              {displayMessages.map((msg, index) => (
                <MessageBubble 
                  key={msg.id || index} 
                  message={msg} 
                  onUpdateMessage={handleUpdateMessage}
                />
              ))}
              {isLoading && (
                <div className="flex justify-start mt-2">
                  <TypingIndicator />
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        <ChatInput
          onSendMessage={handleSendMessage}
          isDisabled={isLoading}
          currentChatSessionId={currentChatSessionId}
          onCreateNewChat={createNewChatSession}
        />
      </div>
    </div>
  )
}

function App() {
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false)
  const location = useLocation()
  const { isAuthenticated, isLoading, user, logout, isTeamLead, isAdmin } = useAuth()

  const handleLogout = useCallback(() => {
    logout()
    setShowLogoutConfirm(false)
  }, [logout])

  useEffect(() => {
    document.documentElement.classList.add('dark')
    return () => {
      document.documentElement.classList.remove('dark')
    }
  }, [])

  const isAuthPage = location.pathname === '/login' || location.pathname === '/register'

  if (isLoading && !isAuthPage) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#020610] text-gray-300">
        <div className="glass-panel p-8 text-center">
          <p className="text-[11px] uppercase tracking-[0.5em] text-kaiops-primary/80 mb-3">KaiOPS</p>
          <div className="mx-auto mb-4 h-12 w-12 rounded-full border border-white/10 flex items-center justify-center">
            <div className="h-6 w-6 border-b-2 border-kaiops-primary rounded-full animate-spin"></div>
          </div>
          <p className="text-sm text-gray-400">Initializing console…</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-screen w-screen overflow-hidden bg-black flex flex-col font-inter text-gray-100 relative">
      <div className="bg-noise" />
      <ThreeBackground theme="dark" />
      {/* Brand tagline watermark */}
      <div className="fixed top-4 right-6 z-50 text-[9px] tracking-widest font-bold text-kaiops-primary/30 pointer-events-none opacity-60 uppercase">
        Incidents End Here
      </div>

      {isAuthenticated && !isAuthPage && (
        <header className="z-20 w-full px-6 py-4 flex-none">
          <nav className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-6 py-4 shadow-[0_25px_80px_rgba(1,10,50,0.55)] backdrop-blur-2xl max-w-[1920px] mx-auto w-full">
            <div className="flex items-center gap-3 text-sm">
              <div className="px-3 py-1 rounded-full bg-gradient-to-r from-kaiops-primary/30 to-kaiops-secondary/30 text-kaiops-primary font-semibold tracking-[0.2em] uppercase text-[11px]">KaiOPS</div>
              <span className="text-emerald-300 font-bold tracking-widest text-[11px] animate-typing drop-shadow-[0_0_10px_rgba(16,185,129,0.4)]">Incidents End Here</span>
            </div>
            <div className="flex gap-2 text-xs font-medium">
              <Link to="/" className="px-3 py-2 rounded-lg text-gray-300 hover:text-white hover:bg-white/10 transition-all duration-200 hover:scale-105">Chat</Link>
              <Link to="/dashboard" className="px-3 py-2 rounded-lg text-gray-300 hover:text-white hover:bg-white/10 transition-all duration-200 hover:scale-105">Dashboard</Link>
              {user?.role === 'admin' && (
                <Link to="/users" className="px-3 py-2 rounded-lg text-gray-300 hover:text-white hover:bg-white/10 transition-all duration-200 hover:scale-105">Users</Link>
              )}
              {isTeamLead && (
                <Link to="/feedback" className="px-3 py-2 rounded-lg text-gray-300 hover:text-white hover:bg-white/10 transition-all duration-200 hover:scale-105">Feedback</Link>
              )}
              {isTeamLead && (
                <Link to="/applications" className="px-3 py-2 rounded-lg text-gray-300 hover:text-white hover:bg-white/10 transition-all duration-200 hover:scale-105">Applications</Link>
              )}
            </div>
            <div className="flex items-center gap-3 text-sm">
              <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-black/40 border border-white/5 shadow-lg">
                <div className="relative">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-kaiops-primary/60 opacity-60"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-kaiops-primary"></span>
                </div>
                <span className="text-gray-300">Online</span>
              </div>
              <Link
                to="/profile"
                className="flex items-center gap-2 px-3 py-2 rounded-xl bg-black/40 border border-white/5 text-gray-200 hover:text-white transition-all duration-200 hover:border-kaiops-primary/50"
                title="Profile"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                </svg>
                <span className="hidden sm:inline">{user?.username || 'User'}</span>
              </Link>
              <button
                onClick={() => setShowLogoutConfirm(true)}
                className="px-3 py-2 rounded-xl bg-gradient-to-r from-red-500 to-red-600 text-white font-semibold shadow-lg shadow-red-900/40 hover:scale-[1.05] active:scale-95 transition-all duration-200"
              >
                Logout
              </button>
            </div>
          </nav>
        </header>
      )}

      <main className="relative z-10 flex-1 w-full max-w-[1920px] mx-auto px-6 pb-6 overflow-hidden flex flex-col">
        <AnimatePresence mode="wait">
          <Routes location={location} key={location.pathname}>
            <Route path="/login" element={<PageTransition><Login /></PageTransition>} />
            <Route path="/register" element={<PageTransition><Register /></PageTransition>} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <PageTransition>
                    <ChatInterface />
                  </PageTransition>
                </ProtectedRoute>
              }
            />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <PageTransition>
                    <div className="w-full h-full rounded-2xl glass-panel p-6 overflow-hidden">
                      <Dashboard />
                    </div>
                  </PageTransition>
                </ProtectedRoute>
              }
            />
            <Route
              path="/users"
              element={
                <ProtectedRoute adminOnly>
                  <PageTransition>
                    <div className="w-full h-full rounded-2xl glass-panel p-6 overflow-hidden">
                      <UserManagement />
                    </div>
                  </PageTransition>
                </ProtectedRoute>
              }
            />
            <Route
              path="/feedback"
              element={
                <ProtectedRoute teamLeadOrAdmin>
                  <PageTransition>
                    <div className="w-full h-full rounded-2xl glass-panel p-6 overflow-hidden">
                      <FeedbackReview />
                    </div>
                  </PageTransition>
                </ProtectedRoute>
              }
            />
            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <PageTransition>
                    <div className="w-full h-full rounded-2xl glass-panel p-6 overflow-hidden">
                      <Profile />
                    </div>
                  </PageTransition>
                </ProtectedRoute>
              }
            />
            <Route
              path="/applications"
              element={
                <ProtectedRoute teamLeadOrAdmin>
                  <PageTransition>
                    <div className="w-full h-full rounded-2xl glass-panel p-6 overflow-hidden">
                      <ApplicationList />
                    </div>
                  </PageTransition>
                </ProtectedRoute>
              }
            />
            <Route
              path="/applications/new"
              element={
                <ProtectedRoute teamLeadOrAdmin>
                  <PageTransition>
                    <div className="w-full h-full rounded-2xl glass-panel p-6 overflow-hidden">
                      <ApplicationForm />
                    </div>
                  </PageTransition>
                </ProtectedRoute>
              }
            />
            <Route
              path="/applications/:id"
              element={
                <ProtectedRoute teamLeadOrAdmin>
                  <PageTransition>
                    <div className="w-full h-full rounded-2xl glass-panel p-6 overflow-hidden">
                      <ApplicationDetails />
                    </div>
                  </PageTransition>
                </ProtectedRoute>
              }
            />
            <Route
              path="/applications/:id/edit"
              element={
                <ProtectedRoute teamLeadOrAdmin>
                  <PageTransition>
                    <div className="w-full h-full rounded-2xl glass-panel p-6 overflow-hidden">
                      <ApplicationForm />
                    </div>
                  </PageTransition>
                </ProtectedRoute>
              }
            />
            {/* Catch-all route - redirect to home */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AnimatePresence>
      </main>

      {/* Logout Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showLogoutConfirm}
        onClose={() => setShowLogoutConfirm(false)}
        onConfirm={handleLogout}
        title="Confirm Logout"
        message={
          <div>
            <p className="mb-2">
              Are you sure you want to logout?
            </p>
            <p className="text-sm text-gray-400">
              You will need to log in again to access the application.
            </p>
          </div>
        }
        confirmText="Logout"
        cancelText="Cancel"
        type="warning"
      />
    </div>
  )
}

export default App

