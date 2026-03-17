import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { applicationsApi } from '@/api/applications'
import { DragDropContext, Droppable, Draggable, DropResult } from '@hello-pangea/dnd'
import clsx from 'clsx'
import toast from 'react-hot-toast'
import { ExternalLink, Plus, Trash2 } from 'lucide-react'

const COLUMNS = [
  { id: 'saved', label: 'Saved', color: 'border-gray-300 bg-gray-50' },
  { id: 'applied', label: 'Applied', color: 'border-blue-300 bg-blue-50' },
  { id: 'phone_screen', label: 'Phone Screen', color: 'border-purple-300 bg-purple-50' },
  { id: 'technical_interview', label: 'Technical', color: 'border-indigo-300 bg-indigo-50' },
  { id: 'onsite_interview', label: 'Onsite', color: 'border-violet-300 bg-violet-50' },
  { id: 'offer', label: 'Offer', color: 'border-green-300 bg-green-50' },
]

export default function Pipeline() {
  const qc = useQueryClient()

  const { data: apps = [], isLoading } = useQuery({
    queryKey: ['applications'],
    queryFn: () => applicationsApi.list(),
  })

  const updateStatus = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      applicationsApi.updateStatus(id, status),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['applications'] }),
    onError: () => toast.error('Failed to update status'),
  })

  const deleteApp = useMutation({
    mutationFn: applicationsApi.delete,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['applications'] })
      toast.success('Application removed')
    },
  })

  const onDragEnd = (result: DropResult) => {
    if (!result.destination) return
    const newStatus = result.destination.droppableId
    const appId = result.draggableId
    updateStatus.mutate({ id: appId, status: newStatus })
  }

  const grouped = COLUMNS.reduce((acc, col) => {
    acc[col.id] = apps.filter((a) => a.status === col.id)
    return acc
  }, {} as Record<string, typeof apps>)

  if (isLoading) {
    return (
      <div className="p-6 flex gap-4 animate-pulse">
        {COLUMNS.map((col) => (
          <div key={col.id} className="w-60 h-48 bg-gray-100 rounded-xl flex-shrink-0" />
        ))}
      </div>
    )
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Application Pipeline</h1>

      <DragDropContext onDragEnd={onDragEnd}>
        <div className="flex gap-4 overflow-x-auto pb-4">
          {COLUMNS.map((col) => {
            const colApps = grouped[col.id] ?? []
            return (
              <div key={col.id} className={clsx('flex-shrink-0 w-60 rounded-xl border-2 p-3', col.color)}>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold text-gray-700">{col.label}</h3>
                  <span className="text-xs bg-white text-gray-500 rounded-full px-2 py-0.5 border">
                    {colApps.length}
                  </span>
                </div>

                <Droppable droppableId={col.id}>
                  {(provided, snapshot) => (
                    <div
                      ref={provided.innerRef}
                      {...provided.droppableProps}
                      className={clsx(
                        'min-h-20 space-y-2 transition-colors rounded-lg',
                        snapshot.isDraggingOver && 'bg-white/60'
                      )}
                    >
                      {colApps.map((app, idx) => (
                        <Draggable key={app.id} draggableId={app.id} index={idx}>
                          {(provided, snapshot) => (
                            <div
                              ref={provided.innerRef}
                              {...provided.draggableProps}
                              {...provided.dragHandleProps}
                              className={clsx(
                                'bg-white rounded-lg border border-gray-200 p-3 shadow-sm',
                                snapshot.isDragging && 'shadow-md rotate-1'
                              )}
                            >
                              <p className="text-sm font-medium text-gray-900 leading-tight">
                                {app.job_title ?? 'Unknown Position'}
                              </p>
                              <p className="text-xs text-gray-500 mt-0.5">{app.company_name}</p>

                              {app.applied_at && (
                                <p className="text-[10px] text-gray-400 mt-1.5">
                                  Applied {new Date(app.applied_at).toLocaleDateString()}
                                </p>
                              )}

                              <div className="flex gap-1 mt-2">
                                {app.job_url && (
                                  <a
                                    href={app.job_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-gray-400 hover:text-blue-500"
                                    onClick={(e) => e.stopPropagation()}
                                  >
                                    <ExternalLink size={12} />
                                  </a>
                                )}
                                <button
                                  onClick={() => deleteApp.mutate(app.id)}
                                  className="text-gray-300 hover:text-red-400 ml-auto"
                                >
                                  <Trash2 size={12} />
                                </button>
                              </div>
                            </div>
                          )}
                        </Draggable>
                      ))}
                      {provided.placeholder}
                    </div>
                  )}
                </Droppable>
              </div>
            )
          })}
        </div>
      </DragDropContext>

      {/* Rejected / Ghosted */}
      <div className="mt-8">
        <h2 className="text-sm font-medium text-gray-500 mb-3">Closed</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {apps
            .filter((a) => ['rejected', 'withdrawn', 'ghosted', 'accepted'].includes(a.status))
            .map((app) => (
              <div key={app.id} className="bg-white rounded-lg border border-gray-200 p-3 opacity-70">
                <p className="text-sm font-medium text-gray-800">{app.job_title}</p>
                <p className="text-xs text-gray-500">{app.company_name}</p>
                <span className={clsx(
                  'mt-1.5 inline-block text-[10px] px-2 py-0.5 rounded font-medium',
                  app.status === 'accepted' ? 'bg-green-100 text-green-700' :
                  app.status === 'rejected' ? 'bg-red-100 text-red-600' :
                  'bg-gray-100 text-gray-500'
                )}>
                  {app.status}
                </span>
              </div>
            ))}
        </div>
      </div>
    </div>
  )
}
