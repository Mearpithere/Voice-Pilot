import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/layout/Layout'
import useAuthStore from './store/authStore'
import Dashboard from './pages/Dashboard'
import CallLogs from './pages/CallLogs'
import Appointments from './pages/Appointments'
import ClinicSettings from './pages/ClinicSettings'
import WidgetEmbed from './pages/WidgetEmbed'
import Login from './pages/Login'

function ProtectedRoute({ children }) {
  const token = useAuthStore((s) => s.token)
  return token ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard"  element={<Dashboard />} />
          <Route path="calls"      element={<CallLogs />} />
          <Route path="appointments" element={<Appointments />} />
          <Route path="settings"   element={<ClinicSettings />} />
          <Route path="widget"     element={<WidgetEmbed />} />
        </Route>
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
