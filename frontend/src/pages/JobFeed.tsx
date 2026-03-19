import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { jobsApi } from '@/api/jobs'
import { applicationsApi } from '@/api/applications'
import {
  Search, MapPin, Clock, DollarSign,
  Bookmark, BookmarkCheck, EyeOff, ExternalLink,
  ChevronDown, Filter,
} from 'lucide-react'
import clsx from 'clsx'
import toast from 'react-hot-toast'

const REMOTE_BADGE: Record<string, string> = {
  remote: 'bg-green-100 text-green-700',
  hybrid: 'bg-yellow-100 text-yellow-700',
  onsite: 'bg-red-100 text-red-700',
  flexible: 'bg-blue-100 text-blue-700',
}

function ScoreBar({ score }: { score: number }) {
  const pct = Math.round(score * 100)
  const color =
    pct >= 75 ? 'bg-green-500' :
    pct >= 60 ? 'bg-blue-500' :
    pct >= 40 ? 'bg-yellow-500' : 'bg-gray-300'
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-24 bg-gray-100 rounded-full">
        <div className={`h-1.5 rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-medium text-gray-600">{pct}%</span>
    </div>
  )
}

export default function JobFeed() {
  const qc = useQueryClient()
  const [q, setQ] = useState('')
  const [remoteOnly, setRemoteOnly] = useState(false)
  const [savedOnly, setSavedOnly] = useState(false)
  const [page, setPage] = useState(1)
  const [selectedJob, setSelectedJob] = useState<string | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['jobs', { q, remoteOnly, savedOnly, page }],
    queryFn: () => jobsApi.list({ q: q || undefined, remote_only: remoteOnly, saved_only: savedOnly, page }),
  })

  const toggleSave = useMutation({
    mutationFn: ({ id, saved }: { id: string; saved: boolean }) =>
      saved ? jobsApi.unsave(id) : jobsApi.save(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['jobs'] }),
  })

  const hideJob = useMutation({
    mutationFn: jobsApi.hide,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['jobs'] })
      toast.success('Job hidden')
    },
  })

  const quickApply = useMutation({
    mutationFn: (jobId: string) =>
      applicationsApi.create({ job_id: jobId, status: 'applied' }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['jobs'] })
      toast.success('Application created!')
    },
  })

  const jobs = data?.items ?? []
  const total = data?.total ?? 0

  return (
    <div className="flex h-full">
      {/* Left: job list */}
      <div className="w-96 flex-shrink-0 flex flex-col border-r border-gray-200 bg-white">
        {/* Search */}
        <div className="p-4 border-b space-y-3">
          <div className="relative">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              value={q}
              onChange={(e) => { setQ(e.target.value); setPage(1) }}
              placeholder="Search jobs, companies..."
              className="w-full pl-8 pr-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="flex gap-3 text-sm">
            <label className="flex items-center gap-1.5 text-gray-600 cursor-pointer">
              <input
                type="checkbox"
                checked={remoteOnly}
                onChange={(e) => { setRemoteOnly(e.target.checked); setPage(1) }}
                className="rounded"
              />
              Remote only
            </label>
            <label className="flex items-center gap-1.5 text-gray-600 cursor-pointer">
              <input
                type="checkbox"
                checked={savedOnly}
                onChange={(e) => { setSavedOnly(e.target.checked); setPage(1) }}
                className="rounded"
              />
              Saved
            </label>
          </div>
        </div>

        {/* Count */}
        <div className="px-4 py-2 text-xs text-gray-400 border-b">
          {total} jobs found
        </div>

        {/* List */}
        <div className="flex-1 overflow-y-auto divide-y">
          {isLoading && (
            Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="p-4 animate-pulse">
                <div className="h-4 bg-gray-100 rounded w-3/4 mb-2" />
                <div className="h-3 bg-gray-100 rounded w-1/2" />
              </div>
            ))
          )}

          {!isLoading && jobs.map((job) => (
            <div
              key={job.id}
              onClick={() => setSelectedJob(job.id)}
              className={clsx(
                'p-4 cursor-pointer hover:bg-gray-50 transition-colors',
                selectedJob === job.id && 'bg-blue-50 border-l-2 border-blue-500'
              )}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-gray-900 truncate">{job.title}</p>
                  <p className="text-xs text-gray-600 mt-0.5">{job.company_name}</p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    toggleSave.mutate({ id: job.id, saved: job.is_saved })
                  }}
                  className="text-gray-400 hover:text-blue-500 flex-shrink-0 mt-0.5"
                >
                  {job.is_saved ? <BookmarkCheck size={15} className="text-blue-500" /> : <Bookmark size={15} />}
                </button>
              </div>

              <div className="mt-2 flex items-center gap-2 flex-wrap">
                <span className={clsx('text-[10px] px-1.5 py-0.5 rounded font-medium', REMOTE_BADGE[job.remote_policy] ?? 'bg-gray-100 text-gray-600')}>
                  {job.remote_policy}
                </span>
                {job.match && <ScoreBar score={job.match.total_score} />}
              </div>

              <div className="mt-1.5 flex items-center gap-3 text-[11px] text-gray-400">
                {job.location && <span className="flex items-center gap-0.5"><MapPin size={10} />{job.location}</span>}
                {job.posted_at && <span className="flex items-center gap-0.5"><Clock size={10} />{job.posted_at}</span>}
              </div>
            </div>
          ))}
        </div>

        {/* Pagination */}
        {total > 20 && (
          <div className="p-3 border-t flex items-center justify-between text-sm">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1 rounded border text-gray-600 disabled:opacity-40"
            >
              Prev
            </button>
            <span className="text-gray-500">Page {page}</span>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={jobs.length < 20}
              className="px-3 py-1 rounded border text-gray-600 disabled:opacity-40"
            >
              Next
            </button>
          </div>
        )}
      </div>

      {/* Right: job detail */}
      <div className="flex-1 overflow-y-auto bg-gray-50">
        {selectedJob ? (
          <JobDetail
            jobId={selectedJob}
            onHide={() => { hideJob.mutate(selectedJob); setSelectedJob(null) }}
            onApply={() => quickApply.mutate(selectedJob)}
          />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-400">
            <div className="text-center">
              <Search size={32} className="mx-auto mb-3 opacity-40" />
              <p className="text-sm">Select a job to view details</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function JobDetail({
  jobId,
  onHide,
  onApply,
}: {
  jobId: string
  onHide: () => void
  onApply: () => void
}) {
  const { data: job, isLoading } = useQuery({
    queryKey: ['job', jobId],
    queryFn: () => jobsApi.get(jobId),
  })

  if (isLoading) return <div className="p-8 animate-pulse space-y-4">
    {Array.from({ length: 5 }).map((_, i) => <div key={i} className="h-4 bg-gray-100 rounded" />)}
  </div>

  if (!job) return <div className="p-8 text-gray-400">Job not found</div>

  const match = job.match

  return (
    <div className="max-w-3xl mx-auto p-8 space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-gray-900">{job.title}</h1>
            <p className="text-base text-gray-600 mt-1">{job.company_name}</p>
            <div className="flex items-center gap-3 mt-2 text-sm text-gray-500">
              {job.location && <span className="flex items-center gap-1"><MapPin size={13} />{job.location}</span>}
              {job.remote_policy !== 'unknown' && (
                <span className={clsx('text-xs px-2 py-0.5 rounded font-medium', REMOTE_BADGE[job.remote_policy] ?? 'bg-gray-100')}>
                  {job.remote_policy}
                </span>
              )}
              {job.seniority_level !== 'unknown' && (
                <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">{job.seniority_level}</span>
              )}
            </div>
            {(job.salary_min || job.salary_max) && (
              <p className="mt-2 text-sm font-medium text-green-600 flex items-center gap-1">
                <DollarSign size={13} />
                {job.salary_min?.toLocaleString()}
                {job.salary_max && ` – ${job.salary_max?.toLocaleString()}`}
                {' '}{job.salary_currency}
              </p>
            )}
          </div>
          <div className="flex flex-col gap-2">
            <a
              href={job.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-sm px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <ExternalLink size={13} />
              View Job
            </a>
            <button
              onClick={onApply}
              className="text-sm px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Track Application
            </button>
            <button
              onClick={onHide}
              className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-gray-600 px-4 py-1.5"
            >
              <EyeOff size={12} />
              Hide
            </button>
          </div>
        </div>
      </div>

      {/* Match details */}
      {match && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-sm font-semibold text-gray-800 mb-4">Match Analysis</h2>
          <div className="grid grid-cols-2 gap-4">
            {[
              { label: 'Overall Match', value: match.total_score },
              { label: 'Skill Match', value: match.skill_score },
              { label: 'Seniority Fit', value: match.seniority_score },
              { label: 'Salary Alignment', value: match.salary_score },
              { label: 'Company Growth', value: match.company_growth_score },
              { label: 'Recency', value: match.recency_score },
            ].map(({ label, value }) => (
              <div key={label}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-gray-500">{label}</span>
                  <span className="font-medium">{Math.round(value * 100)}%</span>
                </div>
                <div className="h-1.5 bg-gray-100 rounded-full">
                  <div
                    className={clsx('h-1.5 rounded-full', value >= 0.75 ? 'bg-green-500' : value >= 0.5 ? 'bg-blue-500' : 'bg-gray-300')}
                    style={{ width: `${Math.round(value * 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 grid grid-cols-2 gap-4">
            {match.matching_skills.length > 0 && (
              <div>
                <p className="text-xs font-medium text-green-600 mb-1">Matching Skills</p>
                <div className="flex flex-wrap gap-1">
                  {match.matching_skills.map((s) => (
                    <span key={s} className="text-xs bg-green-50 text-green-700 px-2 py-0.5 rounded">{s}</span>
                  ))}
                </div>
              </div>
            )}
            {match.missing_skills.length > 0 && (
              <div>
                <p className="text-xs font-medium text-red-500 mb-1">Missing Skills</p>
                <div className="flex flex-wrap gap-1">
                  {match.missing_skills.map((s) => (
                    <span key={s} className="text-xs bg-red-50 text-red-600 px-2 py-0.5 rounded">{s}</span>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="mt-3 pt-3 border-t text-sm">
            <span className="text-gray-500">Interview probability: </span>
            <span className="font-semibold text-gray-800">{Math.round(match.interview_probability * 100)}%</span>
          </div>
        </div>
      )}

      {/* Skills */}
      {job.required_skills?.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-sm font-semibold text-gray-800 mb-3">Required Skills</h2>
          <div className="flex flex-wrap gap-1.5">
            {job.required_skills.map((s: any) => (
              <span key={typeof s === 'string' ? s : s.name} className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                {typeof s === 'string' ? s : s.name}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
