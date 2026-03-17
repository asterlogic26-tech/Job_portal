import { useQuery } from '@tanstack/react-query'
import { dashboardApi } from '@/api/dashboard'
import { applicationsApi } from '@/api/applications'
import { jobsApi } from '@/api/jobs'
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis,
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend,
} from 'recharts'

const PIE_COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#6b7280', '#ec4899', '#14b8a6']

export default function Analytics() {
  const { data: summary } = useQuery({
    queryKey: ['dashboard'],
    queryFn: dashboardApi.getSummary,
  })

  const { data: appsData } = useQuery({
    queryKey: ['applications'],
    queryFn: () => applicationsApi.list(),
  })

  const { data: jobsData } = useQuery({
    queryKey: ['jobs', { page_size: 100 }],
    queryFn: () => jobsApi.list({ page_size: 100 }),
  })

  const appsByStatus = summary?.applications_by_status ?? []
  const apps = appsData ?? []

  // Source distribution
  const sourceMap: Record<string, number> = {}
  jobsData?.items?.forEach((j) => {
    sourceMap[j.source] = (sourceMap[j.source] ?? 0) + 1
  })
  const sourceData = Object.entries(sourceMap).map(([name, value]) => ({ name, value }))

  // Match score distribution
  const scoreRanges = [
    { label: '<40%', count: 0 },
    { label: '40–59%', count: 0 },
    { label: '60–74%', count: 0 },
    { label: '75%+', count: 0 },
  ]
  jobsData?.items?.forEach((j) => {
    const s = j.match?.total_score ?? 0
    if (s < 0.4) scoreRanges[0].count++
    else if (s < 0.6) scoreRanges[1].count++
    else if (s < 0.75) scoreRanges[2].count++
    else scoreRanges[3].count++
  })

  return (
    <div className="p-8 space-y-8">
      <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>

      <div className="grid grid-cols-2 gap-6">
        {/* Application pipeline */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Application Pipeline</h2>
          {appsByStatus.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-8">No applications yet</p>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie
                  data={appsByStatus}
                  dataKey="count"
                  nameKey="status"
                  cx="50%"
                  cy="50%"
                  outerRadius={90}
                  label={({ status, count }) => `${status}: ${count}`}
                  labelLine={false}
                >
                  {appsByStatus.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Match score distribution */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Job Match Distribution</h2>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={scoreRanges}>
              <XAxis dataKey="label" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Source distribution */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Jobs by Source</h2>
          {sourceData.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-8">No jobs discovered yet</p>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={sourceData} layout="vertical">
                <XAxis type="number" tick={{ fontSize: 12 }} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 12 }} width={100} />
                <Tooltip />
                <Bar dataKey="value" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Summary table */}
        {summary && (
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-sm font-semibold text-gray-700 mb-4">Key Metrics</h2>
            <table className="w-full text-sm">
              <tbody className="divide-y divide-gray-100">
                {[
                  ['Total Jobs Discovered', summary.total_jobs_discovered],
                  ['New Jobs Today', summary.new_jobs_today],
                  ['High Match (75%+)', summary.high_match_jobs],
                  ['Saved Jobs', summary.saved_jobs],
                  ['Total Applications', summary.total_applications],
                  ['Active Applications', summary.active_applications],
                  ['Interviews Scheduled', summary.interviews_scheduled],
                  ['Watched Companies', summary.watched_companies],
                  ['Profile Health', `${summary.profile_health_score}/100`],
                ].map(([label, val]) => (
                  <tr key={label as string}>
                    <td className="py-2 text-gray-500">{label}</td>
                    <td className="py-2 text-right font-semibold text-gray-900">{val}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
