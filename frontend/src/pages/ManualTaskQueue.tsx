import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { manualTasksApi } from '@/api/manual_tasks'
import { AlertCircle, CheckCircle, Clock, ExternalLink, Play, SkipForward } from 'lucide-react'
import clsx from 'clsx'
import toast from 'react-hot-toast'
import { useState } from 'react'

const STATUS_ICON: Record<string, React.ReactNode> = {
  pending: <Clock size={14} className="text-yellow-500" />,
  in_progress: <Play size={14} className="text-blue-500" />,
  completed: <CheckCircle size={14} className="text-green-500" />,
  skipped: <SkipForward size={14} className="text-gray-400" />,
}

export default function ManualTaskQueue() {
  const qc = useQueryClient()
  const [statusFilter, setStatusFilter] = useState<string>('pending')
  const [notes, setNotes] = useState<Record<string, string>>({})

  const { data, isLoading } = useQuery({
    queryKey: ['manual-tasks', statusFilter],
    queryFn: () => manualTasksApi.list({ status: statusFilter || undefined }),
  })

  const start = useMutation({
    mutationFn: manualTasksApi.start,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['manual-tasks'] }),
  })

  const resolve = useMutation({
    mutationFn: ({ id, completion_notes }: { id: string; completion_notes: string }) =>
      manualTasksApi.resolve(id, completion_notes),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['manual-tasks'] })
      toast.success('Task marked complete!')
    },
  })

  const skip = useMutation({
    mutationFn: manualTasksApi.skip,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['manual-tasks'] }),
  })

  const tasks = data?.items ?? []
  const pendingCount = data?.pending_count ?? 0

  return (
    <div className="p-8 max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Manual Task Queue</h1>
          <p className="text-sm text-gray-500 mt-1">
            Sites that blocked automated access — requires your manual action
          </p>
        </div>
        {pendingCount > 0 && (
          <div className="flex items-center gap-2 bg-yellow-50 border border-yellow-200 rounded-lg px-4 py-2">
            <AlertCircle size={15} className="text-yellow-500" />
            <span className="text-sm font-medium text-yellow-700">{pendingCount} pending</span>
          </div>
        )}
      </div>

      {/* Filter tabs */}
      <div className="flex gap-1 mb-6 bg-gray-100 rounded-lg p-1 w-fit">
        {['pending', 'in_progress', 'completed', 'skipped', ''].map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={clsx(
              'px-3 py-1.5 text-sm rounded-md transition-colors',
              statusFilter === s ? 'bg-white text-gray-900 shadow-sm font-medium' : 'text-gray-500 hover:text-gray-700'
            )}
          >
            {s === '' ? 'All' : s.replace('_', ' ')}
          </button>
        ))}
      </div>

      {isLoading && (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-24 bg-gray-100 rounded-xl animate-pulse" />
          ))}
        </div>
      )}

      {!isLoading && tasks.length === 0 && (
        <div className="text-center py-16 text-gray-400">
          <CheckCircle size={36} className="mx-auto mb-3 opacity-40" />
          <p className="text-sm">No tasks in this category</p>
        </div>
      )}

      <div className="space-y-4">
        {tasks.map((task) => (
          <div key={task.id} className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-start gap-3">
              <div className="mt-0.5">{STATUS_ICON[task.status]}</div>
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm font-semibold text-gray-900">{task.title}</p>
                    <p className="text-xs text-gray-500 mt-0.5">{task.task_type}</p>
                  </div>
                  {task.site_url && (
                    <a
                      href={task.site_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 text-xs text-blue-600 hover:underline flex-shrink-0"
                    >
                      <ExternalLink size={11} />
                      Open site
                    </a>
                  )}
                </div>

                {task.description && (
                  <p className="text-sm text-gray-600 mt-2">{task.description}</p>
                )}

                {task.instructions && (
                  <div className="mt-3 bg-blue-50 rounded-lg p-3">
                    <p className="text-xs font-medium text-blue-700 mb-1">Instructions</p>
                    <p className="text-xs text-blue-600">{task.instructions}</p>
                  </div>
                )}

                <div className="mt-4 flex items-center gap-3">
                  {task.status === 'pending' && (
                    <button
                      onClick={() => start.mutate(task.id)}
                      className="flex items-center gap-1.5 text-sm px-3 py-1.5 border border-gray-200 rounded-lg hover:bg-gray-50"
                    >
                      <Play size={12} />
                      Start
                    </button>
                  )}

                  {task.status === 'in_progress' && (
                    <>
                      <input
                        value={notes[task.id] ?? ''}
                        onChange={(e) => setNotes((n) => ({ ...n, [task.id]: e.target.value }))}
                        placeholder="Completion notes (optional)..."
                        className="flex-1 text-sm border border-gray-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-green-500"
                      />
                      <button
                        onClick={() => resolve.mutate({ id: task.id, completion_notes: notes[task.id] ?? '' })}
                        className="flex items-center gap-1.5 text-sm px-3 py-1.5 bg-green-600 text-white rounded-lg hover:bg-green-700"
                      >
                        <CheckCircle size={12} />
                        Done
                      </button>
                    </>
                  )}

                  {['pending', 'in_progress'].includes(task.status) && (
                    <button
                      onClick={() => skip.mutate(task.id)}
                      className="flex items-center gap-1.5 text-sm px-3 py-1.5 text-gray-400 hover:text-gray-600"
                    >
                      <SkipForward size={12} />
                      Skip
                    </button>
                  )}

                  {task.completed_at && (
                    <span className="text-xs text-gray-400">
                      Completed {new Date(task.completed_at).toLocaleDateString()}
                    </span>
                  )}
                </div>

                {task.completion_notes && (
                  <p className="mt-2 text-xs text-gray-500 italic">"{task.completion_notes}"</p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
