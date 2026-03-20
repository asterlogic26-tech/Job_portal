import { useQuery } from '@tanstack/react-query'
import { dashboardApi } from '@/api/dashboard'
import {
  Briefcase, TrendingUp, Users, CheckSquare,
  Bell, FileText, Building2, Star,
} from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import clsx from 'clsx'

const STATUS_COLORS: Record<string, string> = {
  saved: '#94a3b8',
  applying: '#60a5fa',
  applied: '#3b82f6',
  phone_screen: '#a78bfa',
  technical_interview: '#8b5cf6',
  onsite_interview: '#7c3aed',
  offer: '#10b981',
  accepted: '#059669',
  rejected: '#ef4444',
  withdrawn: '#f59e0b',
  ghosted: '#9ca3af',
}

function StatCard({
  label,
  value,
  icon: Icon,
  color = 'blue',
}: {
  label: string
  value: number | string
  icon: React.ComponentType<{ size?: number; className?: string }>
  color?: string
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 flex items-center gap-4">
      <div className={clsx('p-3 rounded-lg', {
        'bg-blue-50 text-blue-600': color === 'blue',
        'bg-green-50 text-green-600': color === 'green',
        'bg-purple-50 text-purple-600': color === 'purple',
        'bg-amber-50 text-amber-600': color === 'amber',
        'bg-red-50 text-red-600': color === 'red',
      })}>
        <Icon size={20} />
      </div>
      <div>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
        <p className="text-sm text-gray-500">{label}</p>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['dashboard'],
    queryFn: dashboardApi.getSummary,
    refetchInterval: 60_000,
    retry: 2,
  })

  if (isLoading) {
    return (
      <div className="p-8 grid grid-cols-4 gap-4 animate-pulse">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="h-24 bg-gray-100 rounded-xl" />
        ))}
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div className="p-8 flex flex-col items-center justify-center gap-3 text-gray-500">
        <p className="text-lg font-medium">Could not load dashboard data</p>
        <p className="text-sm">The backend may still be starting up. Retrying automatically…</p>
      </div>
    )
  }

  const d = data

  return (
    <div className="p-8 space-y-8">
      <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>

      {/* Stats grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Jobs Discovered" value={d.total_jobs_discovered} icon={Briefcase} color="blue" />
        <StatCard label="New Today" value={d.new_jobs_today} icon={TrendingUp} color="green" />
        <StatCard label="High Matches" value={d.high_match_jobs} icon={Star} color="purple" />
        <StatCard label="Saved Jobs" value={d.saved_jobs} icon={FileText} color="amber" />
        <StatCard label="Applications" value={d.total_applications} icon={CheckSquare} color="blue" />
        <StatCard label="Active Apps" value={d.active_applications} icon={TrendingUp} color="green" />
        <StatCard label="Interviews" value={d.interviews_scheduled} icon={Users} color="purple" />
        <StatCard label="Pending Tasks" value={d.pending_manual_tasks} icon={Bell} color="red" />
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Application pipeline chart */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-base font-semibold text-gray-800 mb-4">Application Pipeline</h2>
          {d.applications_by_status.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-8">No applications yet</p>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={d.applications_by_status} layout="vertical">
                <XAxis type="number" tick={{ fontSize: 12 }} />
                <YAxis
                  type="category"
                  dataKey="status"
                  tick={{ fontSize: 11 }}
                  width={120}
                />
                <Tooltip />
                <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                  {d.applications_by_status.map((entry) => (
                    <Cell
                      key={entry.status}
                      fill={STATUS_COLORS[entry.status] ?? '#60a5fa'}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Quick stats */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
          <h2 className="text-base font-semibold text-gray-800">At a Glance</h2>

          {[
            { label: 'Profile Health', value: `${d.profile_health_score}/100`, bar: d.profile_health_score, color: 'bg-green-500' },
            { label: 'Companies Watched', value: d.watched_companies, bar: null, color: '' },
            { label: 'Companies Actively Hiring', value: d.companies_hiring, bar: null, color: '' },
            { label: 'Unread Notifications', value: d.unread_notifications, bar: null, color: '' },
            { label: 'Pending Content Drafts', value: d.pending_content_drafts, bar: null, color: '' },
          ].map((item) => (
            <div key={item.label}>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">{item.label}</span>
                <span className="font-semibold text-gray-900">{item.value}</span>
              </div>
              {item.bar !== null && (
                <div className="mt-1.5 h-1.5 bg-gray-100 rounded-full">
                  <div
                    className={`h-1.5 rounded-full ${item.color}`}
                    style={{ width: `${Math.min(100, item.bar)}%` }}
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
