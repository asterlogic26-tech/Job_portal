import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Search, Kanban, FileText, MessageSquare,
  Building2, ClipboardList, BarChart3, User, Settings, Bot, LogOut
} from 'lucide-react'
import clsx from 'clsx'

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/jobs', icon: Search, label: 'Job Feed' },
  { to: '/pipeline', icon: Kanban, label: 'Pipeline' },
  { to: '/resumes', icon: FileText, label: 'Resumes' },
  { to: '/content', icon: MessageSquare, label: 'Content Studio' },
  { to: '/companies', icon: Building2, label: 'Company Radar' },
  { to: '/tasks', icon: ClipboardList, label: 'Manual Tasks' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/profile', icon: User, label: 'Profile Health' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

export default function Sidebar() {
  const navigate = useNavigate()

  function logout() {
    localStorage.removeItem('access_token')
    navigate('/login', { replace: true })
  }

  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
      {/* Logo */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="font-bold text-gray-900 text-sm">AI Job Agent</div>
            <div className="text-xs text-gray-500">Personal Command Center</div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-0.5">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors',
                isActive
                  ? 'bg-blue-50 text-blue-700 font-medium'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              )
            }
          >
            <Icon className="w-4 h-4 flex-shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 space-y-2">
        <div className="text-xs text-gray-400 text-center">v1.0.0 — Single User Mode</div>
        <button
          onClick={logout}
          className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-500 hover:bg-red-50 rounded-lg transition-colors"
        >
          <LogOut size={14} />
          Sign out
        </button>
      </div>
    </aside>
  )
}
