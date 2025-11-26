import { useEffect, useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useFeedback } from '../contexts/FeedbackContext'
import { useAuth } from '../contexts/AuthContext'
import { FeedbackCategory, DatasetType } from '../constants/apiConstants'

function FeedbackReview() {
  const { pending, reviewFeedback, feedbackStats, reloadPending, reloadStats } = useFeedback()
  const { isAdmin, isTeamLead } = useAuth()
  
  // UI State
  const [selectedId, setSelectedId] = useState(null)
  const [filterType, setFilterType] = useState('all') // all, positive, negative
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [notification, setNotification] = useState(null)

  // Review Form State
  const [reviewData, setReviewData] = useState({
    comment: '',
    tags: [],
    dataset: '',
    status: 'approved'
  })

  useEffect(() => {
    reloadPending()
    reloadStats()
  }, [])

  // Derived State
  const selectedFeedback = useMemo(() => 
    pending.find(f => f.id === selectedId), 
  [pending, selectedId])

  const filteredFeedback = useMemo(() => {
    return pending.filter(item => {
      if (filterType === 'positive') return item.feedback_type === 'thumbs_up'
      if (filterType === 'negative') return item.feedback_type === 'thumbs_down'
      return true
    })
  }, [pending, filterType])

  // Handlers
  const handleSelect = (id) => {
    setSelectedId(id)
    // Reset form when selecting new item
    const feedback = pending.find(f => f.id === id)
    setReviewData({
      comment: '',
      tags: feedback?.tags || [],
      dataset: '',
      status: 'approved'
    })
  }

  const handleSubmitReview = async (status) => {
    if (!selectedId) return
    
    setIsSubmitting(true)
    try {
      await reviewFeedback(selectedId, {
        status: status,
        reviewer_comment: reviewData.comment,
        new_tags: reviewData.tags,
        add_to_dataset: reviewData.dataset || undefined
      })
      
      showNotification(`Feedback ${status} successfully`, 'success')
      setSelectedId(null)
    } catch (error) {
      showNotification('Failed to submit review', 'error')
    } finally {
      setIsSubmitting(false)
    }
  }

  const showNotification = (text, type) => {
    setNotification({ text, type })
    setTimeout(() => setNotification(null), 3000)
  }

  const toggleTag = (tag) => {
    setReviewData(prev => ({
      ...prev,
      tags: prev.tags.includes(tag) 
        ? prev.tags.filter(t => t !== tag)
        : [...prev.tags, tag]
    }))
  }

  // Access Control
  if (!isAdmin && !isTeamLead) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="glass-panel border-red-500/30 bg-red-500/10 p-8 text-center">
          <h2 className="text-2xl font-bold text-red-400">Access Denied</h2>
          <p className="text-slate-400">Restricted to Administrators and Team Leads.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full w-full overflow-hidden flex flex-col gap-6 pr-2">
      {/* Header & Stats */}
      <div className="flex-none">
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel relative overflow-hidden rounded-3xl border border-white/10 px-8 py-8 mb-6"
        >
          <div className="absolute inset-0 opacity-30">
            <div className="absolute top-0 right-0 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl" />
            <div className="absolute bottom-0 left-0 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />
          </div>

          <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <div>
              <p className="text-xs font-semibold tracking-[0.4em] text-purple-400 mb-2">QUALITY ASSURANCE</p>
              <h1 className="text-4xl font-black tracking-tight text-white mb-2">Feedback Review</h1>
              <p className="text-slate-400">Review user interactions to improve AI model performance.</p>
            </div>

            <div className="flex gap-4">
              <StatCard 
                label="Pending" 
                value={pending.length} 
                icon="⏳" 
                color="text-amber-400" 
                bg="bg-amber-500/10" 
                border="border-amber-500/20"
              />
              <StatCard 
                label="Approved" 
                value={feedbackStats?.approved || 0} 
                icon="✅" 
                color="text-emerald-400" 
                bg="bg-emerald-500/10" 
                border="border-emerald-500/20"
              />
              <StatCard 
                label="Rating" 
                value={feedbackStats?.avg_rating?.toFixed(1) || '-'} 
                icon="⭐" 
                color="text-purple-400" 
                bg="bg-purple-500/10" 
                border="border-purple-500/20"
              />
            </div>
          </div>
        </motion.div>
      </div>

      {/* Main Content - Split View */}
      <div className="flex-1 min-h-0 flex gap-6">
        {/* Left Panel: List */}
        <div className="w-1/3 flex flex-col gap-4 min-w-[320px]">
          {/* Filters */}
          <div className="flex gap-2 p-1 glass-panel rounded-xl border border-white/10 bg-white/5">
            {['all', 'positive', 'negative'].map(type => (
              <button
                key={type}
                onClick={() => setFilterType(type)}
                className={`flex-1 py-2 px-3 rounded-lg text-xs font-bold uppercase tracking-wider transition ${
                  filterType === type 
                    ? 'bg-white/10 text-white shadow-lg' 
                    : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                {type}
              </button>
            ))}
          </div>

          {/* Scrollable List */}
          <div className="flex-1 overflow-y-auto custom-scrollbar space-y-3 pr-2">
            <AnimatePresence mode="popLayout">
              {filteredFeedback.map((item, idx) => (
                <motion.div
                  key={item.id || `feedback-${idx}`}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  transition={{ delay: idx * 0.05 }}
                  onClick={() => handleSelect(item.id)}
                  className={`cursor-pointer rounded-xl border p-4 transition-all hover:scale-[1.02] ${
                    selectedId === item.id
                      ? 'glass-panel border-purple-500/50 bg-purple-500/10 shadow-lg shadow-purple-500/10'
                      : 'glass-card border-white/5 hover:border-white/20 hover:bg-white/5'
                  }`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <span className={`text-xs font-bold px-2 py-1 rounded-md ${
                      item.feedback_type === 'thumbs_up' 
                        ? 'bg-emerald-500/20 text-emerald-300' 
                        : 'bg-rose-500/20 text-rose-300'
                    }`}>
                      {item.feedback_type === 'thumbs_up' ? '👍 Positive' : '👎 Negative'}
                    </span>
                    <span className="text-xs text-slate-500">
                      {new Date(item.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <p className="text-sm text-white font-medium line-clamp-2 mb-2">
                    "{item.user_message}"
                  </p>
                  <div className="flex items-center gap-2 text-xs text-slate-400">
                    <div className="w-5 h-5 rounded-full bg-white/10 flex items-center justify-center">👤</div>
                    {item.username}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
            
            {filteredFeedback.length === 0 && (
              <div className="text-center py-12 text-slate-500">
                <p className="text-4xl mb-2">📭</p>
                <p>No pending feedback</p>
              </div>
            )}
          </div>
        </div>

        {/* Right Panel: Detail View */}
        <div className="flex-1 glass-panel rounded-3xl border border-white/10 overflow-hidden flex flex-col relative">
          {selectedFeedback ? (
            <>
              {/* Scrollable Content */}
              <div className="flex-1 overflow-y-auto custom-scrollbar p-8">
                {/* Conversation Context */}
                <div className="space-y-6 mb-8">
                  <div className="flex gap-4">
                    <div className="w-10 h-10 rounded-full bg-slate-700 flex-shrink-0 flex items-center justify-center text-lg">👤</div>
                    <div className="flex-1">
                      <p className="text-xs font-bold text-slate-400 mb-1">USER MESSAGE</p>
                      <div className="bg-slate-800/50 rounded-2xl rounded-tl-none p-4 text-slate-200 border border-white/5">
                        {selectedFeedback.user_message}
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-4">
                    <div className="w-10 h-10 rounded-full bg-purple-600/20 border border-purple-500/30 flex-shrink-0 flex items-center justify-center text-lg">🤖</div>
                    <div className="flex-1">
                      <p className="text-xs font-bold text-purple-400 mb-1">AI RESPONSE</p>
                      <div className="bg-purple-500/10 rounded-2xl rounded-tl-none p-4 text-white border border-purple-500/20">
                        {selectedFeedback.ai_response}
                      </div>
                    </div>
                  </div>
                </div>

                {/* User Feedback Details */}
                <div className="glass-card rounded-xl border border-white/10 p-6 mb-8">
                  <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                    <span>📝</span> User Feedback
                  </h3>
                  
                  {selectedFeedback.comment && (
                    <div className="mb-4">
                      <p className="text-xs text-slate-500 mb-1">COMMENT</p>
                      <p className="text-slate-300 italic">"{selectedFeedback.comment}"</p>
                    </div>
                  )}

                  {selectedFeedback.suggested_response && (
                    <div className="mb-4">
                      <p className="text-xs text-slate-500 mb-1">SUGGESTED IMPROVEMENT</p>
                      <p className="text-emerald-300 bg-emerald-500/10 p-3 rounded-lg border border-emerald-500/20">
                        {selectedFeedback.suggested_response}
                      </p>
                    </div>
                  )}

                  <div className="flex flex-wrap gap-2">
                    {selectedFeedback.tags.map(tag => (
                      <span key={tag} className="text-xs px-2 py-1 rounded bg-white/10 text-slate-300 border border-white/5">
                        #{tag}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Review Controls */}
                <div className="space-y-6">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <span>⚖️</span> Review Decision
                  </h3>

                  {/* Tags Selection */}
                  <div>
                    <label className="text-xs font-semibold text-slate-400 mb-2 block">CATEGORIZE ISSUE</label>
                    <div className="flex flex-wrap gap-2">
                      {Object.values(FeedbackCategory).map(tag => (
                        <button
                          key={tag}
                          onClick={() => toggleTag(tag)}
                          className={`text-xs px-3 py-1.5 rounded-lg border transition ${
                            reviewData.tags.includes(tag)
                              ? 'bg-purple-500 text-white border-purple-400'
                              : 'bg-white/5 text-slate-400 border-white/10 hover:border-white/30'
                          }`}
                        >
                          {tag}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Dataset Action */}
                  <div>
                    <label className="text-xs font-semibold text-slate-400 mb-2 block">ADD TO DATASET</label>
                    <div className="grid grid-cols-3 gap-3">
                      {[
                        { value: '', label: 'None' },
                        { value: DatasetType.TRAINING, label: 'Training' },
                        { value: DatasetType.EVALUATION, label: 'Evaluation' }
                      ].map(opt => (
                        <button
                          key={opt.value}
                          onClick={() => setReviewData(prev => ({ ...prev, dataset: opt.value }))}
                          className={`py-2 px-3 rounded-lg text-xs font-bold border transition ${
                            reviewData.dataset === opt.value
                              ? 'bg-blue-500/20 text-blue-300 border-blue-500/50'
                              : 'bg-white/5 text-slate-400 border-white/10 hover:bg-white/10'
                          }`}
                        >
                          {opt.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Reviewer Comment */}
                  <div>
                    <label className="text-xs font-semibold text-slate-400 mb-2 block">INTERNAL NOTES</label>
                    <textarea
                      value={reviewData.comment}
                      onChange={e => setReviewData(prev => ({ ...prev, comment: e.target.value }))}
                      placeholder="Add notes for the engineering team..."
                      className="w-full bg-black/20 border border-white/10 rounded-xl p-3 text-sm text-white focus:border-purple-500/50 focus:outline-none transition h-24 resize-none"
                    />
                  </div>
                </div>
              </div>

              {/* Sticky Action Bar */}
              <div className="p-6 border-t border-white/10 bg-black/20 backdrop-blur-md flex gap-4">
                <button
                  onClick={() => handleSubmitReview('approved')}
                  disabled={isSubmitting}
                  className="flex-1 bg-gradient-to-r from-emerald-500 to-green-600 text-white font-bold py-3 rounded-xl shadow-lg shadow-emerald-500/20 hover:shadow-emerald-500/30 transition transform hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? 'Processing...' : '✅ Approve & Close'}
                </button>
                <button
                  onClick={() => handleSubmitReview('denied')}
                  disabled={isSubmitting}
                  className="flex-1 bg-white/5 border border-white/10 text-slate-300 font-bold py-3 rounded-xl hover:bg-rose-500/10 hover:text-rose-300 hover:border-rose-500/30 transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  ❌ Reject
                </button>
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-slate-500">
              <div className="w-24 h-24 rounded-full bg-white/5 flex items-center justify-center mb-4 text-4xl">
                👈
              </div>
              <p className="text-lg font-medium">Select an item to review</p>
              <p className="text-sm opacity-60">Choose a feedback entry from the list</p>
            </div>
          )}
        </div>
      </div>

      {/* Notification Toast */}
      <AnimatePresence>
        {notification && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className={`fixed bottom-6 right-6 z-50 px-6 py-4 rounded-2xl shadow-2xl border backdrop-blur-xl flex items-center gap-3 ${
              notification.type === 'success' 
                ? 'bg-emerald-500/20 border-emerald-500/30 text-emerald-200' 
                : 'bg-rose-500/20 border-rose-500/30 text-rose-200'
            }`}
          >
            <span className="text-xl">{notification.type === 'success' ? '✨' : '⚠️'}</span>
            <span className="font-semibold">{notification.text}</span>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// Helper Component
const StatCard = ({ label, value, icon, color, bg, border }) => (
  <div className={`flex flex-col items-center justify-center px-6 py-3 rounded-2xl border ${bg} ${border} min-w-[120px]`}>
    <span className="text-2xl mb-1">{icon}</span>
    <span className={`text-2xl font-black ${color}`}>{value}</span>
    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">{label}</span>
  </div>
)

export default FeedbackReview
