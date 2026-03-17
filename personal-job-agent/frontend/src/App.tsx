import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/layout/Layout'
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

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="jobs" element={<JobFeed />} />
          <Route path="pipeline" element={<Pipeline />} />
          <Route path="resumes" element={<ResumeStudio />} />
          <Route path="content" element={<ContentStudio />} />
          <Route path="companies" element={<CompanyRadar />} />
          <Route path="tasks" element={<ManualTaskQueue />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="profile" element={<ProfileHealth />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
