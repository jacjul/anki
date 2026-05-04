import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../state/AuthProvider'

export function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="center-screen">
        <p className="pulse">Restoring your study session...</p>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/auth" replace />
  }

  return <Outlet />
}
