import { Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { UserRole } from '../constants/apiConstants'

const ProtectedRoute = ({ 
  children, 
  adminOnly = false,
  teamLeadOrAdmin = false,
  requiredRole
}) => {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-black dark:bg-gray-100">
        <div className="text-center">
          <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-gray-700 border-t-green-500 dark:border-gray-300 dark:border-t-blue-600"></div>
          <p className="text-sm text-gray-400 dark:text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  // Check specific role requirement
  if (requiredRole && user.role !== requiredRole) {
    return <Navigate to="/" replace />
  }

  // Check admin only access
  if (adminOnly && user.role !== UserRole.ADMIN) {
    return <Navigate to="/" replace />
  }

  // Check team lead or admin access
  if (teamLeadOrAdmin && user.role !== UserRole.ADMIN && user.role !== UserRole.TEAM_LEAD) {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}

export default ProtectedRoute
