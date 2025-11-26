import { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'

function ChatInput({ onSendMessage, isDisabled = false, currentChatSessionId, onCreateNewChat }) {
  const [message, setMessage] = useState('')
  const textareaRef = useRef(null)

  // Update message state and adjust textarea height on input change
  const handleInputChange = (e) => {
    setMessage(e.target.value)
    adjustTextareaHeight()
  }

  // Dynamically adjust the height of the textarea based on its content
  const adjustTextareaHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px'
    }
  }

  // Effect to adjust textarea height on initial render and when message changes
  useEffect(() => {
    adjustTextareaHeight()
  }, [message])

  // Handle sending a message
  const handleSendMessage = async () => {
    if (message.trim() && !isDisabled) {
      let sessionToAddTo = currentChatSessionId
      if (sessionToAddTo === null) {
        // If no chat session is active, create a new one
        const newSession = await onCreateNewChat("New Chat")
        sessionToAddTo = newSession?.id
      }

      // Send the message
      if (sessionToAddTo) {
        onSendMessage(message, sessionToAddTo)
        setMessage('')
      } else {

      }
    }
  }

  // Handle key down events for the textarea
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <div className="p-5 border-t border-white/5 bg-black/30 backdrop-blur-xl relative z-10">
      <div className="flex items-end space-x-3 max-w-4xl mx-auto">
        <div className="relative flex-1 group">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-kaiops-primary/20 to-kaiops-secondary/20 rounded-2xl blur opacity-0 group-focus-within:opacity-100 transition duration-500"></div>
            <textarea
              ref={textareaRef}
              className="relative w-full p-4 rounded-2xl bg-black/40 text-gray-100 placeholder-gray-500 border border-white/10 focus:outline-none focus:border-kaiops-primary/50 focus:ring-1 focus:ring-kaiops-primary/20 resize-none overflow-hidden custom-scrollbar disabled:opacity-50 disabled:cursor-not-allowed text-sm shadow-inner transition-all duration-300"
              rows="1"
              placeholder={isDisabled ? "Connecting to KaiOPS..." : "Type your prompt here..."}
              value={message}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              disabled={isDisabled}
              aria-label="Message input"
            />
        </div>

        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="p-4 rounded-2xl bg-gradient-to-r from-kaiops-secondary to-kaiops-primary text-white shadow-lg shadow-kaiops-primary/20 disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none"
          onClick={handleSendMessage}
          disabled={!message.trim() || isDisabled}
          aria-label="Send message"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path>
          </svg>
        </motion.button>
      </div>
    </div>
  )
}

export default ChatInput
