import { Bell, RefreshCw } from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notificationsApi } from '@/api/notifications'
import { jobsApi } from '@/api/jobs'
import { useState } from 'react'
import toast from 'react-hot-toast'

export function TopBar() {
  const qc = useQueryClient()
  const [showNotifs, setShowNotifs] = useState(false)

  const { data: notifData } = useQuery({
    queryKey: ['notifications', 'unread'],
    queryFn: () => notificationsApi.list({ unread_only: true, page_size: 5 }),
    refetchInterval: 30_000,
  })

  const markAllRead = useMutation({
    mutationFn: notificationsApi.markAllRead,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
  })

  const triggerDiscovery = useMutation({
    mutationFn: jobsApi.triggerDiscovery,
    onSuccess: () => toast.success('Job discovery triggered!'),
    onError: () => toast.error('Failed to trigger discovery'),
  })

  const unreadCount = notifData?.unread_count ?? 0

  return (
    <header className="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-6">
      <div className="text-sm text-gray-500">Personal Job Agent</div>

      <div className="flex items-center gap-3">
        {/* Trigger discovery */}
        <button
          onClick={() => triggerDiscovery.mutate()}
          disabled={triggerDiscovery.isPending}
          className="flex items-center gap-1.5 text-sm text-gray-600 hover:text-blue-600 px-3 py-1.5 rounded-md hover:bg-blue-50 transition-colors"
        >
          <RefreshCw size={14} className={triggerDiscovery.isPending ? 'animate-spin' : ''} />
          Scan Jobs
        </button>

        {/* Notifications */}
        <div className="relative">
          <button
            onClick={() => setShowNotifs(!showNotifs)}
            className="relative p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md"
          >
            <Bell size={18} />
            {unreadCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center">
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
          </button>

          {showNotifs && (
            <div className="absolute right-0 top-10 w-80 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
              <div className="flex items-center justify-between px-4 py-3 border-b">
                <span className="font-medium text-sm">Notifications</span>
                {unreadCount > 0 && (
                  <button
                    onClick={() => markAllRead.mutate()}
                    className="text-xs text-blue-600 hover:underline"
                  >
                    Mark all read
                  </button>
                )}
              </div>

              <div className="max-h-72 overflow-y-auto divide-y">
                {notifData?.items?.length === 0 ? (
                  <p className="text-sm text-gray-400 px-4 py-6 text-center">No new notifications</p>
                ) : (
                  notifData?.items?.map((n) => (
                    <div
                      key={n.id}
                      className={`px-4 py-3 ${n.is_read ? 'bg-white' : 'bg-blue-50'}`}
                    >
                      <p className="text-sm font-medium text-gray-800">{n.title}</p>
                      <p className="text-xs text-gray-500 mt-0.5">{n.body}</p>
                    </div>
                  ))
                )}
              </div>

              <div className="px-4 py-2 border-t">
                <a
                  href="/notifications"
                  className="text-xs text-blue-600 hover:underline"
                  onClick={() => setShowNotifs(false)}
                >
                  View all notifications →
                </a>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
