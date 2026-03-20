import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/layout/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import Login from './pages/Login'
import Register from './pages/Register'
import JobFeed from './pages/JobFeed'
import Pipeline from './pages/Pipeline'
import ResumeStudio from './pages/ResumeStudio'
import ContentStudio from './pages/ContentStudio'
import CompanyRadar from './pages/CompanyRadar'
import ManualTaskQueue from './pages/ManualTaskQueue'
import Analytics from './pages/Analytics'
import ProfileHealth from './pages/ProfileHealth'
import Settings from './pages/Settings'
import Dashboard from './pages/Dashboard'
import Applications from './pages/Applications'
import ProfileSetup from './pages/ProfileSetup'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="jobs" element={<JobFeed />} />
          <Route path="pipeline" element={<Pipeline />} />
          <Route path="applications" element={<Applications />} />
          <Route path="resumes" element={<ResumeStudio />} />
          <Route path="content" element={<ContentStudio />} />
          <Route path="companies" element={<CompanyRadar />} />
          <Route path="tasks" element={<ManualTaskQueue />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="profile" element={<ProfileSetup />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
