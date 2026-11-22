import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Loading } from './StateViews'

export default function ProtectedRoute({ children, roles }) {
  const { user, loading } = useAuth()
  const loc = useLocation()
  if (loading) return <div className="grid h-full place-items-center"><Loading label="Checking your session" /></div>
  if (!user) return <Navigate to="/login" replace state={{ from: loc.pathname }} />
  if (roles && !roles.includes(user.role)) return <Navigate to="/dashboard" replace />
  return children
}
