import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { profileApi } from '@/api/profile'
import { CheckCircle, AlertTriangle, User, Award, RefreshCw } from 'lucide-react'
import clsx from 'clsx'
import toast from 'react-hot-toast'
import { useState } from 'react'

const GRADE_COLOR: Record<string, string> = {
  A: 'text-green-600 bg-green-50',
  B: 'text-blue-600 bg-blue-50',
  C: 'text-yellow-600 bg-yellow-50',
  D: 'text-red-600 bg-red-50',
  F: 'text-gray-600 bg-gray-100',
}

export default function ProfileHealth() {
  const qc = useQueryClient()
  const [editing, setEditing] = useState(false)

  const { data: profile, isLoading: profileLoading } = useQuery({
    queryKey: ['profile'],
    queryFn: profileApi.get,
  })

  const { data: health } = useQuery({
    queryKey: ['profile', 'health'],
    queryFn: profileApi.getHealth,
  })

  const updateProfile = useMutation({
    mutationFn: profileApi.update,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['profile'] })
      toast.success('Profile updated!')
      setEditing(false)
    },
  })

  const refreshEmbedding = useMutation({
    mutationFn: profileApi.refreshEmbedding,
    onSuccess: () => toast.success('Embedding refreshed!'),
  })

  const [form, setForm] = useState<Record<string, any>>({})

  const startEdit = () => {
    if (profile) {
      setForm({
        full_name: profile.full_name,
        current_title: profile.current_title,
        experience_years: profile.experience_years,
        location: profile.location,
        remote_preference: profile.remote_preference,
        target_salary_min: profile.target_salary_min ?? '',
        target_salary_max: profile.target_salary_max ?? '',
        linkedin_url: profile.linkedin_url,
        github_url: profile.github_url,
        bio: profile.bio,
      })
      setEditing(true)
    }
  }

  if (profileLoading) {
    return (
      <div className="p-8 animate-pulse space-y-4">
        <div className="h-8 bg-gray-100 rounded w-48" />
        <div className="h-32 bg-gray-100 rounded-xl" />
      </div>
    )
  }

  return (
    <div className="p-8 max-w-3xl space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Profile Health</h1>
        <div className="flex gap-2">
          <button
            onClick={() => refreshEmbedding.mutate()}
            disabled={refreshEmbedding.isPending}
            className="flex items-center gap-1.5 text-sm px-3 py-1.5 border border-gray-200 rounded-lg hover:bg-gray-50"
          >
            <RefreshCw size={13} className={refreshEmbedding.isPending ? 'animate-spin' : ''} />
            Refresh Embedding
          </button>
          <button
            onClick={startEdit}
            className="flex items-center gap-1.5 text-sm px-4 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <User size={13} />
            Edit Profile
          </button>
        </div>
      </div>

      {/* Health score */}
      {health && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center gap-6">
            <div className={clsx('w-20 h-20 rounded-full flex items-center justify-center text-3xl font-bold', GRADE_COLOR[health.grade])}>
              {health.grade}
            </div>
            <div className="flex-1">
              <div className="flex items-baseline gap-2 mb-2">
                <span className="text-3xl font-bold text-gray-900">{health.score}</span>
                <span className="text-gray-400">/100</span>
              </div>
              <div className="h-2 bg-gray-100 rounded-full">
                <div
                  className={clsx('h-2 rounded-full transition-all', health.score >= 80 ? 'bg-green-500' : health.score >= 60 ? 'bg-blue-500' : health.score >= 40 ? 'bg-yellow-500' : 'bg-red-400')}
                  style={{ width: `${health.score}%` }}
                />
              </div>
              <p className="text-sm text-gray-500 mt-2">
                {health.score >= 80 ? 'Excellent! Your profile is well optimized.' :
                 health.score >= 60 ? 'Good profile. A few improvements possible.' :
                 health.score >= 40 ? 'Average profile. Several sections need attention.' :
                 'Profile needs significant work to improve match accuracy.'}
              </p>
            </div>
          </div>

          {health.missing_fields.length > 0 && (
            <div className="mt-5 pt-4 border-t">
              <p className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-1.5">
                <AlertTriangle size={13} className="text-yellow-500" />
                Missing or incomplete sections
              </p>
              <div className="flex flex-wrap gap-2">
                {health.missing_fields.map((f) => (
                  <span key={f} className="text-xs bg-yellow-50 text-yellow-700 border border-yellow-200 px-2 py-0.5 rounded">{f}</span>
                ))}
              </div>
            </div>
          )}

          {health.suggestions.length > 0 && (
            <div className="mt-4 space-y-1.5">
              {health.suggestions.map((s, i) => (
                <div key={i} className="flex items-start gap-2 text-sm text-gray-600">
                  <CheckCircle size={13} className="text-blue-400 mt-0.5 flex-shrink-0" />
                  {s}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Profile data (view or edit) */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-base font-semibold text-gray-800 mb-4">Profile Details</h2>

        {editing ? (
          <div className="space-y-4">
            {[
              { key: 'full_name', label: 'Full Name', type: 'text' },
              { key: 'current_title', label: 'Current Title', type: 'text' },
              { key: 'experience_years', label: 'Years of Experience', type: 'number' },
              { key: 'location', label: 'Location', type: 'text' },
              { key: 'linkedin_url', label: 'LinkedIn URL', type: 'url' },
              { key: 'github_url', label: 'GitHub URL', type: 'url' },
              { key: 'target_salary_min', label: 'Min Salary ($)', type: 'number' },
              { key: 'target_salary_max', label: 'Max Salary ($)', type: 'number' },
            ].map(({ key, label, type }) => (
              <div key={key}>
                <label className="text-sm font-medium text-gray-700">{label}</label>
                <input
                  type={type}
                  value={form[key] ?? ''}
                  onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
                  className="mt-1 w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            ))}

            <div>
              <label className="text-sm font-medium text-gray-700">Bio</label>
              <textarea
                value={form.bio ?? ''}
                onChange={(e) => setForm((f) => ({ ...f, bio: e.target.value }))}
                rows={4}
                className="mt-1 w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              />
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => updateProfile.mutate(form)}
                disabled={updateProfile.isPending}
                className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {updateProfile.isPending ? 'Saving…' : 'Save Profile'}
              </button>
              <button
                onClick={() => setEditing(false)}
                className="px-4 py-2 text-sm border border-gray-200 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : profile && (
          <dl className="grid grid-cols-2 gap-x-8 gap-y-4 text-sm">
            {[
              { label: 'Full Name', value: profile.full_name },
              { label: 'Current Title', value: profile.current_title },
              { label: 'Experience', value: `${profile.experience_years} years` },
              { label: 'Location', value: profile.location },
              { label: 'Remote Preference', value: profile.remote_preference },
              { label: 'Target Salary', value: profile.target_salary_min ? `$${profile.target_salary_min.toLocaleString()} – $${profile.target_salary_max?.toLocaleString()}` : '—' },
              { label: 'LinkedIn', value: profile.linkedin_url || '—' },
              { label: 'GitHub', value: profile.github_url || '—' },
            ].map(({ label, value }) => (
              <div key={label}>
                <dt className="text-gray-500">{label}</dt>
                <dd className="font-medium text-gray-800 mt-0.5">{value}</dd>
              </div>
            ))}
          </dl>
        )}
      </div>

      {/* Skills */}
      {profile?.skills?.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-base font-semibold text-gray-800 mb-4">Skills</h2>
          <div className="flex flex-wrap gap-2">
            {profile.skills.map((s: any) => (
              <div key={s.name} className="flex items-center gap-1.5 bg-gray-50 border border-gray-200 rounded-lg px-3 py-1.5">
                <span className="text-sm font-medium text-gray-800">{s.name}</span>
                <span className={clsx('text-xs px-1 py-0.5 rounded', {
                  'bg-green-100 text-green-700': s.level === 'expert',
                  'bg-blue-100 text-blue-700': s.level === 'intermediate',
                  'bg-gray-100 text-gray-500': s.level === 'beginner',
                })}>
                  {s.level}
                </span>
                {s.years && <span className="text-xs text-gray-400">{s.years}y</span>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
