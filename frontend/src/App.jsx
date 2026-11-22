import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import AdminAudit from './pages/AdminAudit'
import AdminSources from './pages/AdminSources'
import AdminUsers from './pages/AdminUsers'
import Dashboard from './pages/Dashboard'
import Landing from './pages/Landing'
import LiveMap from './pages/LiveMap'
import Login from './pages/Login'
import PhasePage from './pages/PhasePage'
import Profile from './pages/Profile'
import Register from './pages/Register'
import VerifyEmail from './pages/VerifyEmail'

const phase = (title, n, text) => <PhasePage title={title} phase={n}>{text}</PhasePage>

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/verify-email" element={<VerifyEmail />} />

      <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/map" element={<LiveMap />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/planner" element={phase('Journey planner', 3, 'Compares fastest, cheapest, fewest-transfer and flood-aware trips once verified route data and a routing engine are connected.')} />
        <Route path="/transport" element={phase('Transport finder', 2, 'Needs verified route, stop and fare data. Until then SafeRoute will not show invented routes.')} />
        <Route path="/flood" element={phase('Flood monitoring', 4, 'Needs a verified official data source and community reporting. Access to PAGASA and FloodCaster data has not been confirmed.')} />
        <Route path="/reports" element={phase('Community reports', 4, 'Report floods and road problems with a map location and optional photo, with moderation and expiry.')} />
        <Route path="/assistant" element={phase('Travel assistant', 5, 'Answers only from routes, fares and conditions retrieved from SafeRoute data, with sources and timestamps.')} />
        <Route path="/trips" element={phase('Saved trips', 3, 'Saved journeys arrive with the journey planner.')} />
        <Route path="/notifications" element={phase('Notifications', 5, 'Alerts for saved trips, floods, closures and disruptions.')} />
        <Route path="/admin/users" element={<ProtectedRoute roles={['admin']}><AdminUsers /></ProtectedRoute>} />
        <Route path="/admin/sources" element={<ProtectedRoute roles={['admin', 'moderator']}><AdminSources /></ProtectedRoute>} />
        <Route path="/admin/audit" element={<ProtectedRoute roles={['admin']}><AdminAudit /></ProtectedRoute>} />
        <Route path="/admin/transport" element={<ProtectedRoute roles={['admin']}>{phase('Transport management', 2, 'Manual entry and imports for routes, stops and operators.')}</ProtectedRoute>} />
        <Route path="/admin/fares" element={<ProtectedRoute roles={['admin']}>{phase('Fare management', 2, 'Versioned fare matrices entered from official issuances.')}</ProtectedRoute>} />
        <Route path="/admin/moderation" element={<ProtectedRoute roles={['admin', 'moderator']}>{phase('Report moderation', 4, 'Verify, reject and expire community reports.')}</ProtectedRoute>} />
        <Route path="/admin/analytics" element={<ProtectedRoute roles={['admin']}>{phase('Analytics', 6, 'Usage and data-quality analytics.')}</ProtectedRoute>} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
