import { createContext, useContext, useState, useEffect } from 'react'
import { authService } from '../services/auth'
import { UserRole } from '../constants/apiConstants'

const AuthContext = createContext(undefined)

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    initializeAuth()
  }, [])

  const initializeAuth = async () => {
    try {
      // Check if we have a token
      const token = authService.getToken()
      if (token) {
        // Get user data from localStorage
        const cachedUser = authService.getCurrentUserData()
        if (cachedUser) {
          setUser(cachedUser)
        }
      }
    } catch (error) {
      console.error('Auth initialization error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const login = async (credentials) => {
    try {
      const authData = await authService.login(credentials)
      setUser(authData.user)
    } catch (error) {
      throw error
    }
  }

  const register = async (userData) => {
    try {
      await authService.register(userData)
    } catch (error) {
      throw error
    }
  }

  const logout = () => {
    authService.logout()
    setUser(null)
  }

  const refreshUser = async () => {
    try {
      const userData = await authService.getCurrentUser()
      setUser(userData)
    } catch (error) {

      logout()
    }
  }

  const value = {
    user,
    isLoading,
    isAuthenticated: !!user,
    isAdmin: user?.role === UserRole.ADMIN,
    isTeamLead: user?.role === UserRole.TEAM_LEAD || user?.role === UserRole.ADMIN,
    login,
    register,
    logout,
    refreshUser,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
