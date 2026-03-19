import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { companiesApi } from '@/api/companies'
import { Building2, Eye, EyeOff, TrendingUp, Search, RefreshCw } from 'lucide-react'
import clsx from 'clsx'
import toast from 'react-hot-toast'

function HiringBadge({ score }: { score: number }) {
  const pct = Math.round(score * 100)
  const color = pct >= 70 ? 'bg-green-100 text-green-700' : pct >= 40 ? 'bg-yellow-100 text-yellow-700' : 'bg-gray-100 text-gray-500'
  return <span className={clsx('text-xs px-2 py-0.5 rounded font-medium', color)}>{pct}% hiring</span>
}

export default function CompanyRadar() {
  const qc = useQueryClient()
  const [watchedOnly, setWatchedOnly] = useState(false)
  const [q, setQ] = useState('')
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['companies', { watchedOnly, q }],
    queryFn: () => companiesApi.list({ watched_only: watchedOnly, q: q || undefined }),
  })

  const toggleWatch = useMutation({
    mutationFn: ({ id, watched }: { id: string; watched: boolean }) =>
      watched ? companiesApi.unwatch(id) : companiesApi.watch(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['companies'] }),
  })

  const triggerRadar = useMutation({
    mutationFn: (id: string) => companiesApi.triggerRadar(id),
    onSuccess: () => toast.success('Radar scan triggered'),
  })

  const companies = data?.items ?? []
  const selected = companies.find((c) => c.id === selectedId)

  return (
    <div className="flex h-full">
      {/* Left list */}
      <div className="w-80 flex-shrink-0 flex flex-col border-r border-gray-200 bg-white">
        <div className="p-4 border-b space-y-3">
          <h1 className="text-lg font-bold text-gray-900">Company Radar</h1>
          <div className="relative">
            <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search companies..."
              className="w-full pl-8 pr-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
            <input
              type="checkbox"
              checked={watchedOnly}
              onChange={(e) => setWatchedOnly(e.target.checked)}
              className="rounded"
            />
            Watchlist only
          </label>
        </div>

        <div className="flex-1 overflow-y-auto divide-y">
          {isLoading && Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="p-4 animate-pulse">
              <div className="h-4 bg-gray-100 rounded w-2/3 mb-2" />
              <div className="h-3 bg-gray-100 rounded w-1/2" />
            </div>
          ))}

          {!isLoading && companies.map((company) => (
            <div
              key={company.id}
              onClick={() => setSelectedId(company.id)}
              className={clsx(
                'p-4 cursor-pointer hover:bg-gray-50 transition-colors',
                selectedId === company.id && 'bg-blue-50 border-l-2 border-blue-500'
              )}
            >
              <div className="flex items-center justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-gray-900 truncate">{company.name}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{company.industry || 'Tech'}</p>
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); toggleWatch.mutate({ id: company.id, watched: company.is_watched }) }}
                  className="text-gray-400 hover:text-blue-500"
                >
                  {company.is_watched ? <Eye size={14} className="text-blue-500" /> : <EyeOff size={14} />}
                </button>
              </div>
              <div className="mt-1.5">
                <HiringBadge score={company.hiring_score} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Detail */}
      <div className="flex-1 overflow-y-auto bg-gray-50 p-8">
        {selected ? (
          <div className="max-w-2xl space-y-6">
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-xl font-bold text-gray-900">{selected.name}</h2>
                  <p className="text-sm text-gray-500 mt-1">{selected.industry} · {selected.size_range} employees</p>
                  {selected.website && (
                    <a href={selected.website} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-600 hover:underline mt-1 block">
                      {selected.website}
                    </a>
                  )}
                </div>
                <div className="flex flex-col gap-2 items-end">
                  <button
                    onClick={() => toggleWatch.mutate({ id: selected.id, watched: selected.is_watched })}
                    className={clsx(
                      'flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg border transition-colors',
                      selected.is_watched
                        ? 'bg-blue-50 border-blue-200 text-blue-600'
                        : 'border-gray-200 text-gray-600 hover:bg-gray-50'
                    )}
                  >
                    <Eye size={13} />
                    {selected.is_watched ? 'Watching' : 'Watch'}
                  </button>
                  <button
                    onClick={() => triggerRadar.mutate(selected.id)}
                    className="flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50"
                  >
                    <RefreshCw size={13} />
                    Scan
                  </button>
                </div>
              </div>

              {selected.description && (
                <p className="text-sm text-gray-600 mt-4">{selected.description}</p>
              )}

              <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-500">Stage</p>
                  <p className="font-medium text-gray-800">{selected.stage || '—'}</p>
                </div>
                <div>
                  <p className="text-gray-500">Headquarters</p>
                  <p className="font-medium text-gray-800">{selected.headquarters || '—'}</p>
                </div>
                <div>
                  <p className="text-gray-500">Total Funding</p>
                  <p className="font-medium text-gray-800">
                    {selected.total_funding_usd ? `$${(selected.total_funding_usd / 1e6).toFixed(1)}M` : '—'}
                  </p>
                </div>
                <div>
                  <p className="text-gray-500">Last Round</p>
                  <p className="font-medium text-gray-800">{selected.last_funding_round || '—'}</p>
                </div>
                <div>
                  <p className="text-gray-500">Hiring Score</p>
                  <p className="font-medium text-gray-800">{Math.round(selected.hiring_score * 100)}%</p>
                </div>
                <div>
                  <p className="text-gray-500">Job Velocity</p>
                  <p className="font-medium text-gray-800">{selected.job_velocity.toFixed(1)} jobs/wk</p>
                </div>
              </div>
            </div>

            {selected.signals?.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <h3 className="text-sm font-semibold text-gray-800 mb-4">Recent Signals</h3>
                <div className="space-y-3">
                  {selected.signals.map((s) => (
                    <div key={s.id} className="flex gap-3">
                      <div className="w-2 h-2 rounded-full bg-blue-400 mt-1.5 flex-shrink-0" />
                      <div>
                        <p className="text-sm font-medium text-gray-800">{s.title}</p>
                        <p className="text-xs text-gray-500 mt-0.5">{s.summary}</p>
                        <p className="text-[10px] text-gray-400 mt-1">
                          {s.signal_type} · {s.signal_date ? new Date(s.signal_date).toLocaleDateString() : ''}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-400">
            <div className="text-center">
              <Building2 size={36} className="mx-auto mb-3 opacity-40" />
              <p className="text-sm">Select a company to view signals</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
