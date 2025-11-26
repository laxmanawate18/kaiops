import {
  createContext, useContext, useState, useEffect, useCallback
} from 'react'
import { feedbackService } from '../services/feedback'
import { useAuth } from './AuthContext'

const FeedbackContext = createContext(undefined)

export const FeedbackProvider = ({ children }) => {
  const { isAdmin, isTeamLead, isAuthenticated } = useAuth()
  const [myFeedback, setMyFeedback] = useState([])
  const [pending, setPending] = useState([])
  const [feedbackStats, setFeedbackStats] = useState(null)
  const [datasets, setDatasets] = useState([])
  const [datasetStats, setDatasetStats] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  
  // Check if user has permission to access feedback features
  const hasPermission = isAdmin || isTeamLead

  const reloadMy = useCallback(() => {
    if (!hasPermission) return Promise.resolve()
    
    return feedbackService.getMyFeedback()
      .then(data => {
        setMyFeedback(data)
        setError(null)
      })
      .catch(err => {
        // Silently handle 403 errors (no permission)
        if (err.response?.status !== 403) {

          setError(err.message)
        }
      })
  }, [hasPermission])

  const reloadPending = useCallback(() => {
    if (!hasPermission) return Promise.resolve()
    
    return feedbackService.getPending()
      .then(data => {
        setPending(data)
        setError(null)
      })
      .catch(err => {
        // Silently handle 403 errors (no permission)
        if (err.response?.status !== 403) {

          setError(err.message)
        }
      })
  }, [hasPermission])

  const reloadStats = useCallback(() => {
    if (!hasPermission) return Promise.resolve()
    
    return feedbackService.stats()
      .then(data => {
        setFeedbackStats(data)
        setError(null)
      })
      .catch(err => {
        // Silently handle 403 errors (no permission)
        if (err.response?.status !== 403) {

          setError(err.message)
        }
      })
  }, [hasPermission])

  const reloadDatasets = useCallback(() => {
    if (!hasPermission) return Promise.resolve()
    
    return feedbackService.getDatasets()
      .then(data => {
        setDatasets(data)
        setError(null)
      })
      .catch(err => {
        // Silently handle 403 errors (no permission)
        if (err.response?.status !== 403) {

          setError(err.message)
        }
      })
  }, [hasPermission])

  useEffect(() => {
    // Only load feedback data if user is authenticated and has permission
    if (!isAuthenticated || !hasPermission) {
      setIsLoading(false)
      return
    }

    const loadData = async () => {
      setIsLoading(true)
      try {
        await Promise.all([
          reloadMy(),
          reloadStats(),
          reloadPending(),
          reloadDatasets(),
          feedbackService.datasetStats()
            .then(setDatasetStats)
            .catch(err => {
              // Silently handle 403 errors
              if (err.response?.status !== 403) {

              }
            })
        ])
      } catch (err) {
        // Only log non-403 errors
        if (err.response?.status !== 403) {

          setError(err.message)
        }
      } finally {
        setIsLoading(false)
      }
    }
    loadData()
  }, [isAuthenticated, hasPermission, reloadMy, reloadStats, reloadPending, reloadDatasets])

  const sendFeedback = async (data) => {
    try {
      setError(null)
      const fb = await feedbackService.sendFeedback(data)
      await reloadMy()
      return fb
    } catch (err) {

      setError(err.message)
      throw err
    }
  }

  const reviewFeedback = async (id, review) => {
    try {
      setError(null)
      const fb = await feedbackService.review(id, review)
      await Promise.all([
        reloadStats(),
        reloadPending(),
        reloadDatasets()
      ])
      return fb
    } catch (err) {

      setError(err.message)
      throw err
    }
  }

  return (
    <FeedbackContext.Provider value={{
      sendFeedback, 
      myFeedback, 
      pending,
      reviewFeedback, 
      feedbackStats, 
      datasets,
      datasetStats, 
      reloadStats, 
      reloadPending,
      reloadMy,
      reloadDatasets,
      isLoading,
      error
    }}>
      {children}
    </FeedbackContext.Provider>
  )
}

export const useFeedback = () => {
  const ctx = useContext(FeedbackContext)
  if (!ctx) throw new Error('useFeedback must be used within FeedbackProvider')
  return ctx
}
