import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notificationsApi } from '@/api/notifications'
import { Bell, CheckCheck, Trash2 } from 'lucide-react'
import clsx from 'clsx'
import toast from 'react-hot-toast'
import { useState } from 'react'

const PRIORITY_COLOR: Record<string, string> = {
  high: 'bg-red-500',
  normal: 'bg-blue-400',
  low: 'bg-gray-300',
}

export default function Notifications() {
  const qc = useQueryClient()
  const [unreadOnly, setUnreadOnly] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['notifications', { unreadOnly }],
    queryFn: () => notificationsApi.list({ unread_only: unreadOnly }),
  })

  const markRead = useMutation({
    mutationFn: notificationsApi.markRead,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
  })

  const markAllRead = useMutation({
    mutationFn: notificationsApi.markAllRead,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['notifications'] })
      toast.success('All marked as read')
    },
  })

  const clearRead = useMutation({
    mutationFn: notificationsApi.clearRead,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['notifications'] })
      toast.success('Read notifications cleared')
    },
  })

  const items = data?.items ?? []
  const unreadCount = data?.unread_count ?? 0

  return (
    <div className="p-8 max-w-3xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Notifications</h1>
          {unreadCount > 0 && (
            <p className="text-sm text-gray-500 mt-0.5">{unreadCount} unread</p>
          )}
        </div>
        <div className="flex gap-2">
          <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
            <input
              type="checkbox"
              checked={unreadOnly}
              onChange={(e) => setUnreadOnly(e.target.checked)}
              className="rounded"
            />
            Unread only
          </label>
          {unreadCount > 0 && (
            <button
              onClick={() => markAllRead.mutate()}
              className="flex items-center gap-1.5 text-sm px-3 py-1.5 border border-gray-200 rounded-lg hover:bg-gray-50"
            >
              <CheckCheck size={13} />
              Mark all read
            </button>
          )}
          <button
            onClick={() => clearRead.mutate()}
            className="flex items-center gap-1.5 text-sm px-3 py-1.5 border border-gray-200 rounded-lg hover:bg-gray-50 text-gray-500"
          >
            <Trash2 size={13} />
            Clear read
          </button>
        </div>
      </div>

      {isLoading && (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-16 bg-gray-100 rounded-xl animate-pulse" />
          ))}
        </div>
      )}

      {!isLoading && items.length === 0 && (
        <div className="text-center py-16 text-gray-400">
          <Bell size={36} className="mx-auto mb-3 opacity-40" />
          <p className="text-sm">No notifications</p>
        </div>
      )}

      <div className="space-y-2">
        {items.map((n) => (
          <div
            key={n.id}
            className={clsx(
              'bg-white rounded-xl border border-gray-200 p-4 flex items-start gap-3',
              !n.is_read && 'border-blue-100 bg-blue-50/30'
            )}
          >
            <div className={clsx('w-2 h-2 rounded-full mt-1.5 flex-shrink-0', PRIORITY_COLOR[n.priority] ?? 'bg-gray-300')} />
            <div className="flex-1 min-w-0">
              <p className={clsx('text-sm', n.is_read ? 'text-gray-700' : 'text-gray-900 font-medium')}>
                {n.title}
              </p>
              {n.body && <p className="text-xs text-gray-500 mt-0.5">{n.body}</p>}
              <p className="text-[10px] text-gray-400 mt-1">
                {new Date(n.created_at).toLocaleString()}
              </p>
            </div>
            {!n.is_read && (
              <button
                onClick={() => markRead.mutate(n.id)}
                className="text-xs text-blue-500 hover:underline flex-shrink-0"
              >
                Mark read
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
