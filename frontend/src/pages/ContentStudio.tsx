import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { contentApi } from '@/api/content'
import { CheckCircle, Plus, Trash2, Edit3, Sparkles } from 'lucide-react'
import clsx from 'clsx'
import toast from 'react-hot-toast'

const CONTENT_TYPES = [
  { value: 'cover_letter', label: 'Cover Letter' },
  { value: 'linkedin_post', label: 'LinkedIn Post' },
  { value: 'outreach_email', label: 'Outreach Email' },
  { value: 'follow_up_email', label: 'Follow-up Email' },
  { value: 'thank_you_note', label: 'Thank You Note' },
  { value: 'connection_request', label: 'Connection Request' },
]

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-yellow-100 text-yellow-700',
  approved: 'bg-green-100 text-green-700',
  sent: 'bg-blue-100 text-blue-700',
  archived: 'bg-gray-100 text-gray-500',
}

export default function ContentStudio() {
  const qc = useQueryClient()
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [showGenerate, setShowGenerate] = useState(false)
  const [genType, setGenType] = useState('linkedin_post')
  const [genTopic, setGenTopic] = useState('')
  const [editing, setEditing] = useState(false)
  const [editBody, setEditBody] = useState('')
  const [filterType, setFilterType] = useState<string>('')

  const { data, isLoading } = useQuery({
    queryKey: ['content', { filterType }],
    queryFn: () => contentApi.list({ content_type: filterType || undefined }),
  })

  const generate = useMutation({
    mutationFn: ({ type, topic }: { type: string; topic: string }) =>
      contentApi.generate({ content_type: type, extra_context: topic || undefined }),
    onSuccess: (newItem) => {
      qc.invalidateQueries({ queryKey: ['content'] })
      setSelectedId(newItem.id)
      setShowGenerate(false)
      setGenTopic('')
      toast.success('Content draft generated!')
    },
    onError: () => toast.error('Generation failed'),
  })

  const approve = useMutation({
    mutationFn: contentApi.approve,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['content'] })
      toast.success('Content approved!')
    },
  })

  const update = useMutation({
    mutationFn: ({ id, body }: { id: string; body: string }) =>
      contentApi.update(id, { body }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['content'] })
      setEditing(false)
      toast.success('Saved')
    },
  })

  const remove = useMutation({
    mutationFn: contentApi.delete,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['content'] })
      setSelectedId(null)
      toast.success('Deleted')
    },
  })

  const items = data?.items ?? []
  const selected = items.find((c) => c.id === selectedId)

  return (
    <div className="flex h-full">
      {/* Sidebar */}
      <div className="w-72 flex-shrink-0 border-r border-gray-200 bg-white flex flex-col">
        <div className="p-4 border-b space-y-3">
          <div className="flex items-center justify-between">
            <h1 className="text-lg font-bold text-gray-900">Content Studio</h1>
            <button
              onClick={() => setShowGenerate(true)}
              className="p-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <Plus size={14} />
            </button>
          </div>
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="w-full text-sm border border-gray-200 rounded-lg px-3 py-1.5 focus:outline-none"
          >
            <option value="">All types</option>
            {CONTENT_TYPES.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </div>

        <div className="flex-1 overflow-y-auto divide-y">
          {isLoading && Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="p-4 animate-pulse">
              <div className="h-4 bg-gray-100 rounded w-3/4 mb-2" />
              <div className="h-3 bg-gray-100 rounded w-1/2" />
            </div>
          ))}

          {!isLoading && items.map((item) => (
            <div
              key={item.id}
              onClick={() => { setSelectedId(item.id); setEditing(false) }}
              className={clsx(
                'p-4 cursor-pointer hover:bg-gray-50',
                selectedId === item.id && 'bg-blue-50 border-l-2 border-blue-500'
              )}
            >
              <p className="text-sm font-medium text-gray-900 truncate">{item.title || item.content_type}</p>
              <div className="flex items-center gap-2 mt-1">
                <span className={clsx('text-[10px] px-1.5 py-0.5 rounded', STATUS_COLORS[item.status])}>
                  {item.status}
                </span>
                <span className="text-[10px] text-gray-400">
                  {CONTENT_TYPES.find((t) => t.value === item.content_type)?.label ?? item.content_type}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Main area */}
      <div className="flex-1 overflow-y-auto bg-gray-50">
        {showGenerate && (
          <div className="max-w-lg mx-auto mt-16 bg-white rounded-xl border border-gray-200 p-8">
            <h2 className="text-lg font-bold text-gray-900 mb-6">Generate New Content</h2>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-700">Content Type</label>
                <select
                  value={genType}
                  onChange={(e) => setGenType(e.target.value)}
                  className="mt-1 w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {CONTENT_TYPES.map((t) => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700">Topic / Instructions</label>
                <textarea
                  value={genTopic}
                  onChange={(e) => setGenTopic(e.target.value)}
                  placeholder="e.g. Write a post about the latest AI news this week, specifically about new LLM releases..."
                  rows={4}
                  className="mt-1 w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                />
              </div>
              <div className="flex gap-3">
                <button
                  onClick={() => generate.mutate({ type: genType, topic: genTopic })}
                  disabled={generate.isPending}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  <Sparkles size={14} />
                  {generate.isPending ? 'Generating…' : 'Generate'}
                </button>
                <button
                  onClick={() => setShowGenerate(false)}
                  className="px-4 py-2 text-sm border border-gray-200 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {selected && !showGenerate && (
          <div className="max-w-3xl mx-auto p-8 space-y-6">
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="text-lg font-bold text-gray-900">{selected.title || selected.content_type}</h2>
                  {selected.subject && (
                    <p className="text-sm text-gray-500 mt-0.5">Subject: {selected.subject}</p>
                  )}
                  <div className="flex items-center gap-2 mt-2">
                    <span className={clsx('text-xs px-2 py-0.5 rounded font-medium', STATUS_COLORS[selected.status])}>
                      {selected.status}
                    </span>
                    <span className="text-xs text-gray-400">{selected.model_used}</span>
                  </div>
                </div>
                <div className="flex gap-2">
                  {selected.status === 'draft' && (
                    <button
                      onClick={() => approve.mutate(selected.id)}
                      className="flex items-center gap-1.5 text-sm px-3 py-1.5 bg-green-600 text-white rounded-lg hover:bg-green-700"
                    >
                      <CheckCircle size={13} />
                      Approve
                    </button>
                  )}
                  <button
                    onClick={() => { setEditing(true); setEditBody(selected.body) }}
                    className="flex items-center gap-1.5 text-sm px-3 py-1.5 border border-gray-200 rounded-lg hover:bg-gray-50"
                  >
                    <Edit3 size={13} />
                    Edit
                  </button>
                  <button
                    onClick={() => remove.mutate(selected.id)}
                    className="text-gray-400 hover:text-red-500 p-1.5"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 p-6">
              {editing ? (
                <div className="space-y-3">
                  <textarea
                    value={editBody}
                    onChange={(e) => setEditBody(e.target.value)}
                    className="w-full h-80 text-sm border border-gray-200 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none font-mono"
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={() => update.mutate({ id: selected.id, body: editBody })}
                      className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700"
                    >
                      Save
                    </button>
                    <button
                      onClick={() => setEditing(false)}
                      className="px-4 py-2 text-sm border border-gray-200 rounded-lg hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <pre className="text-sm text-gray-800 whitespace-pre-wrap font-sans leading-relaxed">
                  {selected.body}
                </pre>
              )}
            </div>
          </div>
        )}

        {!selected && !showGenerate && (
          <div className="flex items-center justify-center h-full text-gray-400">
            <div className="text-center">
              <Edit3 size={36} className="mx-auto mb-3 opacity-40" />
              <p className="text-sm">Select a draft or generate new content</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
