import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

function Sidebar({ chatSessions = [], currentChatSessionId, onSelectChatSession, onCreateNewChat, onDeleteChat, onRenameChat }) {
  const [searchTerm, setSearchTerm] = useState('')
  const [editingSessionId, setEditingSessionId] = useState(null)
  const [editingName, setEditingName] = useState('')

  // Filter chat sessions based on search term (case-insensitive)
  const filteredChatSessions = (chatSessions || []).filter(session =>
    session && session.name && session.name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const handleRenameStart = (session, e) => {
    e.stopPropagation()
    setEditingSessionId(session.id)
    setEditingName(session.name)
  }

  const handleRenameSubmit = (sessionId) => {
    if (editingName.trim() && editingName !== chatSessions.find(s => s.id === sessionId)?.name) {
      onRenameChat(sessionId, editingName.trim())
    }
    setEditingSessionId(null)
    setEditingName('')
  }

  const handleRenameCancel = () => {
    setEditingSessionId(null)
    setEditingName('')
  }

  return (
    <div className="w-72 glass-panel flex flex-col border-r border-white/10 z-20 text-gray-200">
      {/* KaiOPS Branding Header */}
      <div className="px-4 pt-8 pb-4">
        <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-black/50 p-4 shadow-[0_25px_60px_rgba(2,10,30,0.65)]">
          <div className="absolute inset-0 bg-gradient-to-r from-kaiops-secondary/30 via-transparent to-kaiops-primary/20 blur-3xl opacity-60"></div>
          <div className="relative flex items-center gap-3">
            <div className="relative">
              <div className="absolute inset-0 rounded-2xl bg-kaiops-primary/40 blur-xl"></div>
              <div className="relative h-14 w-14 rounded-2xl border border-kaiops-primary/40 bg-black/80 flex items-center justify-center shadow-[0_0_25px_rgba(0,240,255,0.35)]">
                <svg viewBox="0 0 24 24" className="w-7 h-7 text-white" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 2L3 6.5V17.5L12 22L21 17.5V6.5L12 2ZM18.8 8.1V15.9L12 19.2L5.2 15.9V8.1L12 4.8L18.8 8.1Z" fill="currentColor" opacity="0.9" />
                  <path d="M12 9L8 11L12 13L16 11L12 9Z" fill="currentColor" />
                </svg>
              </div>
            </div>
            <div>
              <p className="text-base font-bold uppercase tracking-[0.5em] text-kaiops-primary/90">KaiOPS</p>
              <p className="text-xs font-semibold text-white drop-shadow-[0_0_15px_rgba(0,240,255,0.45)] mt-1 tracking-wide">Intelligent SRE Assistant</p>
            </div>
          </div>
          <div className="mt-4 flex items-center gap-2 text-xs text-gray-400">
            <span className="relative flex h-2.5 w-2.5">
              <span className="absolute inline-flex h-full w-full rounded-full bg-kaiops-primary opacity-40 animate-ping"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-kaiops-primary"></span>
            </span>
            Systems nominal
          </div>
        </div>
      </div>

      {/* Search Input */}
      <div className="relative mb-6 px-4">
        <input
          type="text"
          placeholder="Search sessions..."
          className="w-full p-2 pl-9 rounded-lg bg-black/40 text-gray-200 border border-white/10 focus:outline-none focus:border-kaiops-primary focus:ring-1 focus:ring-kaiops-primary/50 transition-all duration-200 text-sm placeholder-gray-500"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          aria-label="Search chat sessions"
        />
        <svg className="absolute left-6 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
        </svg>
      </div>

      {/* Chats Section */}
      <div className="flex-1 overflow-y-auto custom-scrollbar px-2">
        <h3 className="text-xs uppercase text-kaiops-primary/80 mb-3 px-2 tracking-[0.45em] font-semibold">
          Active Sessions
        </h3>
        {filteredChatSessions.length === 0 ? (
          <div className="text-center py-8 px-4">
            <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-white/5 flex items-center justify-center">
              <svg className="w-6 h-6 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
              </svg>
            </div>
            <p className="text-sm text-gray-400 mb-1">No active sessions</p>
            <p className="text-xs text-gray-500">Start a new operation below</p>
          </div>
        ) : (
          <ul className="space-y-1">
            <AnimatePresence mode="popLayout">
            {filteredChatSessions.map((session) => (
            <motion.li
              layout
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              whileHover={{ x: 4, backgroundColor: 'rgba(255, 255, 255, 0.03)' }}
              transition={{ type: "spring", stiffness: 500, damping: 30 }}
              key={session.id || `session-${idx}`}
              className={`flex items-center justify-between p-3 rounded-lg text-sm group border border-transparent relative overflow-hidden ${
                currentChatSessionId === session.id
                  ? 'bg-kaiops-primary/10 text-kaiops-primary border-kaiops-primary/20 shadow-[0_0_15px_rgba(0,240,255,0.15)]'
                  : 'text-gray-400'
              }`}
              aria-label={`Chat session: ${session.name}`}
            >
              {currentChatSessionId === session.id && (
                <motion.div
                  layoutId="activeSessionGlow"
                  className="absolute inset-0 bg-kaiops-primary/5"
                  initial={false}
                  transition={{ type: "spring", stiffness: 500, damping: 30 }}
                />
              )}
              
              {editingSessionId === session.id ? (
                <div className="flex items-center flex-1 min-w-0 gap-1 z-10">
                  <input
                    type="text"
                    value={editingName}
                    onChange={(e) => setEditingName(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        handleRenameSubmit(session.id)
                      } else if (e.key === 'Escape') {
                        handleRenameCancel()
                      }
                    }}
                    onBlur={() => handleRenameSubmit(session.id)}
                    className="flex-1 bg-black/50 text-gray-100 border border-white/10 px-2 py-1 rounded text-sm focus:outline-none focus:ring-1 focus:ring-kaiops-primary"
                    autoFocus
                  />
                </div>
              ) : (
                <>
                  <div 
                    className="flex items-center truncate flex-1 min-w-0 cursor-pointer z-10"
                    onClick={() => onSelectChatSession(session.id)}
                  >
                    <svg className={`w-4 h-4 mr-2 flex-shrink-0 transition-colors ${currentChatSessionId === session.id ? 'text-kaiops-primary' : 'text-gray-500 group-hover:text-gray-300'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                    </svg>
                    <span className="truncate font-medium">{session.name}</span>
                  </div>
                  <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity z-10">
                    <button
                      onClick={(e) => handleRenameStart(session, e)}
                      className="p-1 rounded hover:bg-blue-500/10 transition-all flex-shrink-0"
                      aria-label={`Rename chat: ${session.name}`}
                      title="Rename chat"
                    >
                      <svg className="w-4 h-4 text-blue-400 hover:text-blue-200" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                      </svg>
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        if (window.confirm(`Delete chat "${session.name}"?`)) {
                          onDeleteChat(session.id)
                        }
                      }}
                      className="p-1 rounded hover:bg-red-500/10 transition-all flex-shrink-0"
                      aria-label={`Delete chat: ${session.name}`}
                      title="Delete chat"
                    >
                      <svg className="w-4 h-4 text-red-400 hover:text-red-200" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                      </svg>
                    </button>
                  </div>
                </>
              )}
            </motion.li>
          ))}
            </AnimatePresence>
          </ul>
        )}
      </div>

      {/* New Chat Button at the bottom */}
      <div className="mt-auto pt-4 border-t border-white/10">
        <button
          onClick={() => onCreateNewChat("New Chat")}
          className="w-full flex items-center justify-center p-3 rounded-lg bg-gradient-to-r from-kaiops-secondary to-kaiops-primary text-white font-semibold text-base shadow-lg hover:shadow-kaiops-primary/40 transition-transform hover:scale-[1.01]"
          aria-label="Create new chat"
        >
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
          </svg>
          New chat
        </button>
      </div>
    </div>
  )
}

export default Sidebar
