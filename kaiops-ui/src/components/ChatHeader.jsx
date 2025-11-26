import PropTypes from 'prop-types'
import { useState } from 'react'
import ConfirmDialog from './ConfirmDialog'

function ChatHeader({ currentChatSessionName, onClearChat, onRenameChatSession, currentChatSessionId, onClearAllSessions }) {
  const [showClearAllConfirm, setShowClearAllConfirm] = useState(false)

  const handleClearAllClick = () => {
    setShowClearAllConfirm(true)
  }

  const handleConfirmClearAll = async () => {
    setShowClearAllConfirm(false)
    if (onClearAllSessions) {
      await onClearAllSessions()
    }
  }

  return (
    <div className="flex items-center justify-between px-6 py-4 border-b border-white/5 bg-black/30 backdrop-blur-2xl">
      <div className="flex items-center gap-4">
        <div className="relative h-12 w-12 rounded-2xl bg-gradient-to-br from-kaiops-primary/50 to-kaiops-secondary/60 flex items-center justify-center shadow-[0_0_25px_rgba(0,240,255,0.5)]">
          <div className="absolute inset-0 rounded-2xl border border-white/10"></div>
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className="text-white drop-shadow-[0_0_8px_rgba(0,0,0,0.6)]">
            <path d="M12 2L2 7V17L12 22L22 17V7L12 2ZM12 4.3L19.5 8.2V15.8L12 19.7L4.5 15.8V8.2L12 4.3ZM12 10.5L17 13L12 15.5L7 13L12 10.5Z" fill="currentColor" />
          </svg>
        </div>
        <div>
          <div className="flex items-center gap-3 mb-1 flex-wrap">
            <span className="px-2 py-0.5 rounded-full bg-white/10 text-[10px] uppercase tracking-[0.35em] text-kaiops-primary/90">KaiOPS</span>
            <span className="text-[10px] uppercase tracking-[0.3em] font-semibold text-emerald-300/90 drop-shadow-[0_0_8px_rgba(16,185,129,0.3)]">Incidents End Here</span>
          </div>
          <h2 className="text-lg font-semibold text-white">
            {currentChatSessionName || 'New Chat'}
          </h2>
          <p className="text-[11px] text-gray-400">KaiOPS • Intelligent SRE Assistant</p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <button
          onClick={onClearChat}
          className="px-3 py-2 rounded-xl bg-white/10 text-gray-200 hover:bg-white/20 transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
          disabled={!currentChatSessionId}
          aria-label="Clear current chat"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
          </svg>
          <span className="hidden sm:inline">Clear</span>
        </button>
        <button
          onClick={handleClearAllClick}
          className="px-3 py-2 rounded-xl bg-red-600/20 text-red-300 hover:bg-red-600/30 transition-all flex items-center gap-2"
          aria-label="Clear all sessions"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4v2m0 5v.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
          <span className="hidden sm:inline">Clear All</span>
        </button>
      </div>
      <ConfirmDialog
        isOpen={showClearAllConfirm}
        title="Clear All Sessions"
        message="Are you sure you want to delete all sessions? This action cannot be undone."
        confirmText="Delete All"
        cancelText="Cancel"
        onConfirm={handleConfirmClearAll}
        onClose={() => setShowClearAllConfirm(false)}
        type="danger"
      />
    </div>
  )
}

export default ChatHeader

ChatHeader.propTypes = {
  currentChatSessionName: PropTypes.string,
  onClearChat: PropTypes.func.isRequired,
  onRenameChatSession: PropTypes.func,
  currentChatSessionId: PropTypes.string,
  onClearAllSessions: PropTypes.func
}
