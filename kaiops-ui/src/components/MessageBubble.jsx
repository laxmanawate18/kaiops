import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useFeedback } from '../contexts/FeedbackContext'
import { FeedbackCategory, FeedbackType } from '../constants/apiConstants'
import ApplicationsTable from './ApplicationsTable'

function MessageBubble({ message, onUpdateMessage }) {
  const isUser = message.sender === 'user'
  const { sendFeedback } = useFeedback()
  const [feedback, setFeedback] = useState(message.feedback || null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [showDetailedFeedback, setShowDetailedFeedback] = useState(false)
  const [showSuccessToast, setShowSuccessToast] = useState(false)
  const [detailedFeedbackData, setDetailedFeedbackData] = useState({
    rating: 3,
    tags: [],
    comment: '',
    suggestedResponse: ''
  })

  // Sync feedback state with message prop
  useEffect(() => {
    if (message.feedback && message.feedback !== feedback) {
      setFeedback(message.feedback)
    }
  }, [message.feedback])

  const handleFeedback = async (type) => {
    if (isSubmitting || isUser) return
    
    // Handle copy action
    if (type === FeedbackType.COPY) {
      try {
        const textToCopy = message.text || message.content || ''
        await navigator.clipboard.writeText(textToCopy)
        alert('Response copied to clipboard!')
        return
      } catch (error) {

        alert('Failed to copy to clipboard.')
        return
      }
    }

    // Handle thumbs up - submit immediately with positive defaults
    if (type === FeedbackType.THUMBS_UP) {
      setIsSubmitting(true)
      try {
        const conversationId = sessionStorage.getItem('current_session_id') || 'default-session'
        const messageId = message.id || `msg-${Date.now()}`
        const userMessage = message.userMessage || 'User query'
        const aiResponse = message.text || message.content || ''
        
        // Debug logging to help identify issues
        if (!message.userMessage) {

        }
        if (!aiResponse || aiResponse.startsWith('Error:') || aiResponse.includes('ERROR')) {

        }
        
        await sendFeedback({
          conversation_id: conversationId,
          message_id: String(messageId),
          user_message: userMessage,
          ai_response: aiResponse,
          feedback_type: type,
          rating: 5,
          tags: [FeedbackCategory.HELPFULNESS],
          comment: '',
        })
        setFeedback(type)
        
        // Update parent message state to persist feedback
        if (onUpdateMessage) {
          onUpdateMessage(message.id, { ...message, feedback: type })
        }
        
        // Show success toast
        setShowSuccessToast(true)
        setTimeout(() => setShowSuccessToast(false), 3000)
      } catch (error) {

        alert('Failed to submit feedback. Please try again.')
      } finally {
        setIsSubmitting(false)
      }
      return
    }

    // Handle thumbs down - show inline feedback form
    if (type === FeedbackType.THUMBS_DOWN) {
      setShowDetailedFeedback(true)
      setFeedback(type)
      return
    }
  }

  const handleDetailedFeedback = async () => {
    if (isSubmitting || isUser) return
    
    setIsSubmitting(true)
    try {
      const conversationId = sessionStorage.getItem('current_session_id') || 'default-session'
      const messageId = message.id || `msg-${Date.now()}`
      const userMessage = message.userMessage || 'User query'
      const aiResponse = message.text || message.content || ''
      
      // Debug logging to help identify issues
      if (!message.userMessage) {

      }
      if (!aiResponse || aiResponse.startsWith('Error:') || aiResponse.includes('ERROR')) {

      }
      
      // Always thumbs down for detailed feedback
      const feedbackType = FeedbackType.THUMBS_DOWN
      
      await sendFeedback({
        conversation_id: conversationId,
        message_id: String(messageId),
        user_message: userMessage,
        ai_response: aiResponse,
        feedback_type: feedbackType,
        rating: detailedFeedbackData.rating,
        tags: detailedFeedbackData.tags,
        comment: detailedFeedbackData.comment || undefined,
        suggested_response: detailedFeedbackData.suggestedResponse || undefined,
      })
      
      setFeedback(feedbackType)
      setShowDetailedFeedback(false)
      
      // Update parent message state to persist feedback
      if (onUpdateMessage) {
        onUpdateMessage(message.id, { ...message, feedback: feedbackType })
      }
      
      // Show success toast
      setShowSuccessToast(true)
      setTimeout(() => setShowSuccessToast(false), 3000)
      
      // Reset form
      setDetailedFeedbackData({
        rating: 3,
        tags: [],
        comment: '',
        suggestedResponse: ''
      })
    } catch (error) {

      alert('Failed to submit feedback. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const toggleTag = (tag) => {
    setDetailedFeedbackData(prev => ({
      ...prev,
      tags: prev.tags.includes(tag)
        ? prev.tags.filter(t => t !== tag)
        : [...prev.tags, tag]
    }))
  }

  const renderMessageContent = () => {
    const rawText = message.text || message.content || ''

    if (!isUser && rawText) {
      try {
        // Attempt to parse JSON, handling potential Markdown code blocks
        let textToParse = rawText.trim()
        
        // Strip markdown code blocks if present (e.g. ```json ... ```)
        if (textToParse.startsWith('```')) {
          textToParse = textToParse.replace(/^```(?:json)?\s*/, '').replace(/\s*```$/, '')
        }

        const parsed = typeof textToParse === 'string' ? JSON.parse(textToParse) : textToParse
        
        if (parsed && typeof parsed === 'object' && parsed.data_type === 'applications_table') {
          return <ApplicationsTable data={parsed} />
        }
      } catch (error) {
        // Not JSON or failed to parse, fall back to text render
      }
    }

    const textClasses = isUser
      ? 'text-sm leading-relaxed mb-2 text-gray-100 whitespace-pre-wrap'
      : 'text-sm leading-relaxed mb-2 text-gray-100/90 whitespace-pre-wrap font-mono'

    return (
      <p className={textClasses}>
        {String(rawText)}
      </p>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} group mb-4`}
    >
      <div
        className={`max-w-3xl p-5 rounded-2xl shadow-xl transition-all duration-300 ease-in-out relative text-sm border
          ${isUser
            ? 'bg-gradient-to-r from-kaiops-secondary/40 to-kaiops-primary/30 text-white border-transparent rounded-br-none'
            : 'bg-black/40 text-gray-100 border-white/10 rounded-bl-none'
          }
          backdrop-blur-xl
        `}
      >
        <p className="font-semibold mb-1 text-xs opacity-90 flex items-center">
          {isUser ? (
            <>
              <svg className="w-4 h-4 mr-1 text-blue-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
              </svg>
              You
            </>
          ) : (
            <>
              {/* Robot icon for KaiOPS Agent */}
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" className="w-4 h-4 mr-1 text-green-300" viewBox="0 0 16 16">
                <path d="M6 12.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 0 1h-3a.5.5 0 0 1-.5-.5ZM.5 8.5a.5.5 0 0 1 0-1h15a.5.5 0 0 1 0 1H.5ZM12 1.5V3h2V1.5a.5.5 0 0 0-.5-.5h-1a.5.5 0 0 0-.5.5ZM4 1.5V3H2V1.5a.5.5 0 0 1 .5-.5h1a.5.5 0 0 1 .5.5ZM12.5 10a.5.5 0 0 1 .5.5v1.5a.5.5 0 0 1-.5.5h-9a.5.5 0 0 1-.5-.5v-1.5a.5.5 0 0 1 .5-.5h9ZM16 8A8 8 0 1 0 0 8a8 8 0 0 0 16 0ZM1 8a7 7 0 1 1 14 0A7 7 0 0 1 1 8Z"/>
              </svg>
              KaiOPS Agent
            </>
          )}
        </p>

        {renderMessageContent()}

        {message.imageUrl && (
          <div className="my-3 rounded-lg overflow-hidden border border-white/10 shadow-md">
            <img src={message.imageUrl} alt="Message content" className="w-full h-auto object-cover" />
          </div>
        )}

        {/* Modern Feedback buttons for agent messages */}
        {!isUser && (
          <div className="mt-4 pt-3 border-t border-white/10">
            {/* Warning if trying to provide feedback on error message */}
            {(message.text?.includes('ERROR') || message.text?.includes('Error:') || message.text?.startsWith('Error')) && (
              <div className="mb-3 px-3 py-2 rounded-lg bg-yellow-500/10 border border-yellow-500/30 text-yellow-300 text-xs">
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  <span>Note: This appears to be an error message. Feedback may not be meaningful.</span>
                </div>
              </div>
            )}
            
            {/* Warning if user message context is missing */}
            {!message.userMessage && (
              <div className="mb-3 px-3 py-2 rounded-lg bg-orange-500/10 border border-orange-500/30 text-orange-300 text-xs">
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                  <span>Debug: Original user question not captured. Feedback will use placeholder.</span>
                </div>
              </div>
            )}
            
            <div className="flex items-center gap-2 flex-wrap">
              {/* Thumbs Up */}
              <button
                onClick={() => handleFeedback(FeedbackType.THUMBS_UP)}
                disabled={isSubmitting || (feedback !== null && feedback !== FeedbackType.THUMBS_DOWN)}
                className={`group relative inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium transition-all duration-200 ${
                  feedback === FeedbackType.THUMBS_UP
                    ? 'bg-gradient-to-r from-green-500/20 to-emerald-500/20 text-green-300 ring-1 ring-green-400/60'
                    : 'bg-white/5 text-gray-300 hover:bg-green-500/10 hover:text-green-300 hover:ring-1 hover:ring-green-400/40'
                } ${feedback !== null && feedback !== FeedbackType.THUMBS_UP ? 'opacity-40' : ''} disabled:cursor-not-allowed disabled:opacity-40`}
                title="Helpful response"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M2 10.5a1.5 1.5 0 113 0v6a1.5 1.5 0 01-3 0v-6zM6 10.333v5.43a2 2 0 001.106 1.79l.05.025A4 4 0 008.943 18h5.416a2 2 0 001.962-1.608l1.2-6A2 2 0 0015.56 8H12V4a2 2 0 00-2-2 1 1 0 00-1 1v.667a4 4 0 01-.8 2.4L6.8 7.933a4 4 0 00-.8 2.4z" />
                </svg>
                <span className="hidden sm:inline">Helpful</span>
              </button>

              {/* Thumbs Down */}
              <button
                onClick={() => handleFeedback(FeedbackType.THUMBS_DOWN)}
                disabled={isSubmitting || (feedback !== null && feedback !== FeedbackType.THUMBS_DOWN)}
                className={`group relative inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium transition-all duration-200 ${
                  feedback === FeedbackType.THUMBS_DOWN
                    ? 'bg-gradient-to-r from-red-500/20 to-rose-500/20 text-red-300 ring-1 ring-red-400/60'
                    : 'bg-white/5 text-gray-300 hover:bg-red-500/10 hover:text-red-300 hover:ring-1 hover:ring-red-400/40'
                } ${feedback !== null && feedback !== FeedbackType.THUMBS_DOWN ? 'opacity-40' : ''} disabled:cursor-not-allowed disabled:opacity-40`}
                title="Not helpful"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M18 9.5a1.5 1.5 0 11-3 0v-6a1.5 1.5 0 013 0v6zM14 9.667v-5.43a2 2 0 00-1.105-1.79l-.05-.025A4 4 0 0011.055 2H5.64a2 2 0 00-1.962 1.608l-1.2 6A2 2 0 004.44 12H8v4a2 2 0 002 2 1 1 0 001-1v-.667a4 4 0 01.8-2.4l1.4-1.866a4 4 0 00.8-2.4z" />
                </svg>
                <span className="hidden sm:inline">Not helpful</span>
              </button>

              {/* Copy */}
              <button
                onClick={() => handleFeedback(FeedbackType.COPY)}
                className="group relative inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium transition-all duration-200 bg-white/5 text-gray-300 hover:bg-blue-500/10 hover:text-blue-300 hover:ring-1 hover:ring-blue-400/40"
                title="Copy response"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                <span className="hidden sm:inline">Copy</span>
              </button>

              {/* Regenerate */}
              {message.onRegenerate && (
                <button
                  onClick={message.onRegenerate}
                  disabled={message.isRegenerating}
                  className="group relative inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium transition-all duration-200 bg-white/5 text-gray-300 hover:bg-purple-500/10 hover:text-purple-300 hover:ring-1 hover:ring-purple-400/40 disabled:opacity-40 disabled:cursor-not-allowed"
                  title="Regenerate response"
                >
                  <svg className={`w-4 h-4 ${message.isRegenerating ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  <span className="hidden sm:inline">Regenerate</span>
                </button>
              )}
              
              {/* Success Toast */}
              {showSuccessToast && (
                <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium bg-green-500/20 text-green-300 ring-1 ring-green-400/60 animate-fade-in">
                  <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  Thank you!
                </div>
              )}
              
              {message.isRegenerating && (
                <span className="text-xs text-blue-300 animate-pulse">
                  Regenerating...
                </span>
              )}
            </div>

            {/* Inline detailed feedback form for thumbs down */}
            {showDetailedFeedback && feedback === FeedbackType.THUMBS_DOWN && (
              <div className="mt-4 rounded-xl border border-white/10 bg-white/5 p-4">
                <h4 className="text-sm font-semibold text-white mb-3">Help us improve</h4>
                
                {/* Category Tags */}
                <div className="mb-3">
                  <label className="block text-xs font-medium text-gray-300 mb-2">
                    What went wrong? (select all that apply)
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {Object.values(FeedbackCategory).map((category) => (
                      <label
                        key={category}
                        className="flex items-center gap-1.5 cursor-pointer text-xs"
                      >
                        <input
                          type="checkbox"
                          checked={detailedFeedbackData.tags.includes(category)}
                          onChange={() => toggleTag(category)}
                          className="rounded border-white/20 bg-white/10 text-green-300 focus:ring-green-400/30"
                        />
                        <span className="text-gray-300">
                          {category.replace('_', ' ')}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Comment */}
                <div className="mb-3">
                  <label className="block text-xs font-medium text-gray-300 mb-2">
                    Additional comments
                  </label>
                  <textarea
                    value={detailedFeedbackData.comment}
                    onChange={(e) => setDetailedFeedbackData(prev => ({ ...prev, comment: e.target.value }))}
                    rows={3}
                    className="w-full rounded-lg border border-white/10 bg-black/40 p-3 text-sm text-gray-100 placeholder-gray-500 focus:border-red-500 focus:outline-none focus:ring-2 focus:ring-red-500/30"
                    placeholder="Tell us what would make this response better..."
                  />
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  <button
                    onClick={handleDetailedFeedback}
                    disabled={isSubmitting || detailedFeedbackData.tags.length === 0}
                    className="flex-1 rounded-lg bg-red-600/90 px-4 py-2 text-sm font-semibold text-white transition hover:bg-red-600 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {isSubmitting ? 'Submitting...' : 'Submit Feedback'}
                  </button>
                  <button
                    onClick={() => {
                      setShowDetailedFeedback(false)
                      setFeedback(null)
                      setDetailedFeedbackData({ rating: 3, tags: [], comment: '', suggestedResponse: '' })
                    }}
                    disabled={isSubmitting}
                    className="rounded-lg border border-white/10 bg-black/40 px-4 py-2 text-sm font-semibold text-gray-300 transition hover:bg-white/5 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

      </div>
    </motion.div>
  )
}

export default MessageBubble
