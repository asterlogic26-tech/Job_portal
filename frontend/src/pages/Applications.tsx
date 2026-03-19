import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Briefcase, Bot, AlertCircle, CheckCircle2, Clock,
  ExternalLink, ChevronDown, ChevronUp, RefreshCw,
  Trophy, MessageSquare, X, Filter,
} from 'lucide-react'
import clsx from 'clsx'
import toast from 'react-hot-toast'
import axios from 'axios'

// ── Types ──────────────────────────────────────────────────────────────────────

interface TimelineEvent {
  event: string
  timestamp: string
  detail: string
}

interface Application {
  id: string
  job_id: string
  job_title: string | null
  company_name: string | null
  job_url: string | null
  status: string
  is_auto_applied: boolean
  apply_method: string | null
  blocked_reason: string | null
  direct_apply_url: string
  match_score: number | null
  applied_at: string | null
  last_activity_at: string
  cover_letter_id: string | null
  timeline: TimelineEvent[]
  notes: string
}

interface Stats {
  total: number
  auto_applied: number
  blocked: number
  applied: number
  interview: number
  offer: number
}

// ── API ────────────────────────────────────────────────────────────────────────

const api = {
  list: (params?: Record<string, string | boolean>) =>
    axios.get<Application[]>('/api/v1/applications', { params }).then(r => r.data),
  stats: () =>
    axios.get<Stats>('/api/v1/applications/stats').then(r => r.data),
  updateStatus: (id: string, status: string, note = '') =>
    axios.patch<Application>(`/api/v1/applications/${id}/status`, { status, note }).then(r => r.data),
  markApplied: (id: string) =>
    axios.post<Application>(`/api/v1/applications/${id}/mark-applied`).then(r => r.data),
  triggerAutoApply: (jobId: string) =>
    axios.post(`/api/v1/applications/job/${jobId}/auto-apply`).then(r => r.data),
  delete: (id: string) =>
    axios.delete(`/api/v1/applications/${id}`).then(r => r.data),
}

// ── Status config ──────────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  saved:               { label: 'Saved',          color: 'text-gray-600',  bg: 'bg-gray-100' },
  applying:            { label: 'Preparing',       color: 'text-blue-600',  bg: 'bg-blue-50'  },
  auto_applying:       { label: 'Auto-Applying…',  color: 'text-violet-600',bg: 'bg-violet-50'},
  auto_applied:        { label: 'Auto-Applied',    color: 'text-green-700', bg: 'bg-green-100'},
  blocked:             { label: 'Action Needed',   color: 'text-red-700',   bg: 'bg-red-100'  },
  applied:             { label: 'Applied',         color: 'text-blue-700',  bg: 'bg-blue-100' },
  phone_screen:        { label: 'Phone Screen',    color: 'text-purple-700',bg: 'bg-purple-100'},
  technical_interview: { label: 'Tech Interview',  color: 'text-indigo-700',bg: 'bg-indigo-100'},
  onsite_interview:    { label: 'Onsite',          color: 'text-indigo-800',bg: 'bg-indigo-200'},
  offer:               { label: 'Offer 🎉',        color: 'text-emerald-700',bg: 'bg-emerald-100'},
  accepted:            { label: 'Accepted ✓',      color: 'text-emerald-800',bg: 'bg-emerald-200'},
  rejected:            { label: 'Rejected',        color: 'text-gray-500',  bg: 'bg-gray-100' },
  withdrawn:           { label: 'Withdrawn',       color: 'text-gray-400',  bg: 'bg-gray-50'  },
  ghosted:             { label: 'Ghosted',         color: 'text-gray-400',  bg: 'bg-gray-50'  },
}

const FILTER_TABS = [
  { key: '',              label: 'All' },
  { key: 'blocked',       label: 'Needs Action' },
  { key: 'auto_applied',  label: 'Auto-Applied' },
  { key: 'applied',       label: 'Applied' },
  { key: 'phone_screen',  label: 'Interview' },
  { key: 'offer',         label: 'Offer' },
]

const NEXT_STATUSES: Record<string, string[]> = {
  applied:       ['phone_screen', 'rejected', 'withdrawn'],
  auto_applied:  ['phone_screen', 'rejected', 'withdrawn'],
  phone_screen:  ['technical_interview', 'rejected', 'withdrawn'],
  technical_interview: ['onsite_interview', 'rejected', 'withdrawn'],
  onsite_interview: ['offer', 'rejected', 'withdrawn'],
  offer:         ['accepted', 'rejected', 'withdrawn'],
}

// ── Helpers ────────────────────────────────────────────────────────────────────

function fmtDate(iso: string | null) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function ScoreBadge({ score }: { score: number | null }) {
  if (score == null) return null
  const color = score >= 75 ? 'bg-green-100 text-green-800' : score >= 50 ? 'bg-yellow-100 text-yellow-800' : 'bg-gray-100 text-gray-600'
  return <span className={clsx('text-xs font-semibold px-2 py-0.5 rounded-full', color)}>{score.toFixed(0)}%</span>
}

function StatusBadge({ status }: { status: string }) {
  const cfg = STATUS_CONFIG[status] ?? { label: status, color: 'text-gray-600', bg: 'bg-gray-100' }
  return <span className={clsx('text-xs font-medium px-2 py-0.5 rounded-full', cfg.bg, cfg.color)}>{cfg.label}</span>
}

function MethodBadge({ method, isAuto }: { method: string | null; isAuto: boolean }) {
  if (!isAuto && !method) return null
  if (method === 'playwright' || isAuto)
    return <span className="inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full bg-violet-100 text-violet-700"><Bot size={10} />AI Applied</span>
  if (method === 'manual')
    return <span className="inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">Manual</span>
  return null
}

// ── Stats row ──────────────────────────────────────────────────────────────────

function StatsRow({ stats }: { stats: Stats }) {
  const items = [
    { label: 'Total',       value: stats.total,        color: 'text-gray-700' },
    { label: 'Auto-Applied',value: stats.auto_applied, color: 'text-violet-700' },
    { label: 'Needs Action',value: stats.blocked,      color: 'text-red-600'  },
    { label: 'Applied',     value: stats.applied,      color: 'text-blue-700' },
    { label: 'Interviews',  value: stats.interview,    color: 'text-purple-700' },
    { label: 'Offers',      value: stats.offer,        color: 'text-emerald-700' },
  ]
  return (
    <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
      {items.map(item => (
        <div key={item.label} className="bg-white rounded-xl border border-gray-200 p-4 text-center">
          <p className={clsx('text-2xl font-bold', item.color)}>{item.value}</p>
          <p className="text-xs text-gray-500 mt-0.5">{item.label}</p>
        </div>
      ))}
    </div>
  )
}

// ── Timeline ───────────────────────────────────────────────────────────────────

function Timeline({ events }: { events: TimelineEvent[] }) {
  if (!events || events.length === 0)
    return <p className="text-sm text-gray-400 py-2">No timeline events yet.</p>
  return (
    <ol className="relative border-l border-gray-200 ml-2 space-y-3 py-2">
      {[...events].reverse().map((ev, i) => (
        <li key={i} className="ml-4">
          <span className="absolute -left-1.5 w-3 h-3 rounded-full bg-blue-500 border-2 border-white" />
          <p className="text-xs text-gray-500">{new Date(ev.timestamp).toLocaleString()}</p>
          <p className="text-sm font-medium text-gray-700 capitalize">{ev.event.replace(/_/g, ' ')}</p>
          <p className="text-xs text-gray-500">{ev.detail}</p>
        </li>
      ))}
    </ol>
  )
}

// ── Application card ──────────────────────────────────────────────────────────

function AppCard({ app, onStatusChange, onMarkApplied, onDelete }: {
  app: Application
  onStatusChange: (id: string, status: string) => void
  onMarkApplied: (id: string) => void
  onDelete: (id: string) => void
}) {
  const [expanded, setExpanded] = useState(false)
  const isBlocked = app.status === 'blocked'
  const nextStatuses = NEXT_STATUSES[app.status] ?? []

  return (
    <div className={clsx(
      'bg-white rounded-xl border shadow-sm transition-shadow hover:shadow-md',
      isBlocked ? 'border-red-300 ring-1 ring-red-200' : 'border-gray-200',
    )}>
      {/* Card header */}
      <div className="p-4">
        <div className="flex items-start justify-between gap-3">
          {/* Company initials */}
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-violet-500 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
            {(app.company_name ?? '?')[0].toUpperCase()}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="font-semibold text-gray-900 truncate">{app.job_title ?? 'Unknown Role'}</h3>
              {isBlocked && <AlertCircle size={14} className="text-red-500 flex-shrink-0" />}
            </div>
            <p className="text-sm text-gray-500">{app.company_name ?? '—'}</p>
          </div>

          <div className="flex items-center gap-1.5 flex-shrink-0">
            <ScoreBadge score={app.match_score} />
            <button
              onClick={() => onDelete(app.id)}
              className="text-gray-300 hover:text-red-400 transition-colors"
              title="Remove"
            >
              <X size={14} />
            </button>
          </div>
        </div>

        {/* Status row */}
        <div className="flex items-center gap-2 mt-3 flex-wrap">
          <StatusBadge status={app.status} />
          <MethodBadge method={app.apply_method} isAuto={app.is_auto_applied} />
          <span className="text-xs text-gray-400 ml-auto">{fmtDate(app.applied_at ?? app.last_activity_at)}</span>
        </div>

        {/* Blocked alert */}
        {isBlocked && (
          <div className="mt-3 p-3 bg-red-50 rounded-lg border border-red-200">
            <p className="text-xs font-semibold text-red-700 mb-1">
              Auto-apply was blocked — manual action required
            </p>
            <p className="text-xs text-red-500 mb-2">Reason: {app.blocked_reason ?? 'unknown'}</p>
            <div className="flex gap-2">
              {app.direct_apply_url && (
                <a
                  href={app.direct_apply_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-xs font-medium text-white bg-red-600 hover:bg-red-700 px-3 py-1.5 rounded-md transition-colors"
                >
                  <ExternalLink size={11} /> Apply Now
                </a>
              )}
              <button
                onClick={() => onMarkApplied(app.id)}
                className="inline-flex items-center gap-1 text-xs font-medium text-red-700 border border-red-300 hover:bg-red-100 px-3 py-1.5 rounded-md transition-colors"
              >
                <CheckCircle2 size={11} /> I Applied
              </button>
            </div>
          </div>
        )}

        {/* Quick status progress buttons */}
        {nextStatuses.length > 0 && (
          <div className="flex gap-1.5 mt-3 flex-wrap">
            {nextStatuses.map(s => (
              <button
                key={s}
                onClick={() => onStatusChange(app.id, s)}
                className="text-xs px-2.5 py-1 rounded-md border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
              >
                → {STATUS_CONFIG[s]?.label ?? s}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Expand timeline */}
      <button
        onClick={() => setExpanded(e => !e)}
        className="w-full flex items-center justify-between px-4 py-2 text-xs text-gray-400 hover:bg-gray-50 border-t border-gray-100 transition-colors"
      >
        <span>Timeline ({app.timeline?.length ?? 0} events)</span>
        {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
      </button>

      {expanded && (
        <div className="px-4 pb-4 border-t border-gray-100">
          <Timeline events={app.timeline ?? []} />
          {app.job_url && (
            <a
              href={app.job_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs text-blue-600 hover:underline mt-2"
            >
              <ExternalLink size={10} /> View Job Posting
            </a>
          )}
        </div>
      )}
    </div>
  )
}

// ── Main page ──────────────────────────────────────────────────────────────────

export default function Applications() {
  const qc = useQueryClient()
  const [activeTab, setActiveTab] = useState('')

  const { data: stats } = useQuery({
    queryKey: ['applications', 'stats'],
    queryFn: api.stats,
    refetchInterval: 30_000,
  })

  const { data: apps = [], isLoading, refetch } = useQuery({
    queryKey: ['applications', 'list', activeTab],
    queryFn: () => api.list(activeTab ? { status: activeTab } : {}),
    refetchInterval: 30_000,
  })

  const updateStatus = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      api.updateStatus(id, status),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['applications'] })
      toast.success('Status updated')
    },
    onError: () => toast.error('Failed to update status'),
  })

  const markApplied = useMutation({
    mutationFn: (id: string) => api.markApplied(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['applications'] })
      toast.success('Marked as applied!')
    },
  })

  const deleteApp = useMutation({
    mutationFn: (id: string) => api.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['applications'] })
      toast.success('Removed')
    },
  })

  // Separate blocked items to always show at top
  const blocked = apps.filter(a => a.status === 'blocked')
  const rest = apps.filter(a => a.status !== 'blocked')

  return (
    <div className="p-6 md:p-8 space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Application Tracker</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Full pipeline — auto-applied, blocked, and manually tracked
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-blue-600 px-3 py-1.5 rounded-md hover:bg-blue-50 transition-colors"
        >
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {/* Stats */}
      {stats && <StatsRow stats={stats} />}

      {/* Filter tabs */}
      <div className="flex gap-1 border-b border-gray-200 overflow-x-auto pb-0">
        {FILTER_TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={clsx(
              'text-sm font-medium px-4 py-2 border-b-2 -mb-px transition-colors whitespace-nowrap',
              activeTab === tab.key
                ? 'border-blue-600 text-blue-700'
                : 'border-transparent text-gray-500 hover:text-gray-700',
            )}
          >
            {tab.label}
            {tab.key === 'blocked' && blocked.length > 0 && activeTab !== 'blocked' && (
              <span className="ml-1.5 bg-red-500 text-white text-xs rounded-full px-1.5 py-0.5">
                {blocked.length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Application list */}
      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-32 bg-gray-100 rounded-xl animate-pulse" />
          ))}
        </div>
      ) : apps.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <Briefcase size={40} className="mx-auto mb-3 opacity-30" />
          <p className="font-medium">No applications yet</p>
          <p className="text-sm mt-1">Jobs with 75%+ match will be auto-applied automatically</p>
        </div>
      ) : (
        <div className="space-y-3">
          {/* Blocked items first */}
          {activeTab === '' && blocked.map(app => (
            <AppCard
              key={app.id}
              app={app}
              onStatusChange={(id, status) => updateStatus.mutate({ id, status })}
              onMarkApplied={id => markApplied.mutate(id)}
              onDelete={id => deleteApp.mutate(id)}
            />
          ))}
          {/* Rest */}
          {rest.map(app => (
            <AppCard
              key={app.id}
              app={app}
              onStatusChange={(id, status) => updateStatus.mutate({ id, status })}
              onMarkApplied={id => markApplied.mutate(id)}
              onDelete={id => deleteApp.mutate(id)}
            />
          ))}
        </div>
      )}
    </div>
  )
}
