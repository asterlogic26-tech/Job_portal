import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { profileApi } from '@/api/profile'
import { useState } from 'react'
import toast from 'react-hot-toast'
import { Save, Bell, RefreshCw } from 'lucide-react'

export default function Settings() {
  const qc = useQueryClient()

  const { data: profile } = useQuery({
    queryKey: ['profile'],
    queryFn: profileApi.get,
  })

  const [prefs, setPrefs] = useState<Record<string, any>>({})
  const [initialized, setInitialized] = useState(false)

  if (profile && !initialized) {
    setPrefs(profile.preferences ?? {})
    setInitialized(true)
  }

  const savePrefs = useMutation({
    mutationFn: () => profileApi.update({ preferences: prefs }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['profile'] })
      toast.success('Preferences saved!')
    },
  })

  const triggerDiscovery = async () => {
    try {
      const { jobsApi } = await import('@/api/jobs')
      await jobsApi.triggerDiscovery()
      toast.success('Discovery triggered!')
    } catch {
      toast.error('Failed')
    }
  }

  return (
    <div className="p-8 max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Settings</h1>

      {/* Notifications */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-base font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <Bell size={16} />
          Notification Preferences
        </h2>

        <div className="space-y-4">
          {[
            { key: 'notify_high_match', label: 'High match job alerts', desc: 'Notify when a job scores 75%+ match' },
            { key: 'notify_digest', label: 'Daily digest email', desc: 'Get a daily summary each morning at 8am' },
          ].map(({ key, label, desc }) => (
            <label key={key} className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={prefs[key] ?? false}
                onChange={(e) => setPrefs((p) => ({ ...p, [key]: e.target.checked }))}
                className="mt-0.5 rounded"
              />
              <div>
                <p className="text-sm font-medium text-gray-800">{label}</p>
                <p className="text-xs text-gray-500 mt-0.5">{desc}</p>
              </div>
            </label>
          ))}

          <div>
            <label className="text-sm font-medium text-gray-700">Minimum match score to display</label>
            <div className="flex items-center gap-3 mt-2">
              <input
                type="range"
                min={0}
                max={100}
                step={5}
                value={prefs.min_match_score ?? 50}
                onChange={(e) => setPrefs((p) => ({ ...p, min_match_score: parseInt(e.target.value) }))}
                className="flex-1"
              />
              <span className="text-sm font-semibold text-gray-700 w-10 text-right">
                {prefs.min_match_score ?? 50}%
              </span>
            </div>
          </div>
        </div>

        <button
          onClick={() => savePrefs.mutate()}
          disabled={savePrefs.isPending}
          className="mt-6 flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          <Save size={13} />
          Save Preferences
        </button>
      </div>

      {/* Job Discovery */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-base font-semibold text-gray-800 mb-2 flex items-center gap-2">
          <RefreshCw size={16} />
          Job Discovery
        </h2>
        <p className="text-sm text-gray-500 mb-4">
          Automatically runs every 4 hours. You can also trigger a manual scan.
        </p>
        <button
          onClick={triggerDiscovery}
          className="flex items-center gap-2 text-sm px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50"
        >
          <RefreshCw size={13} />
          Trigger Manual Scan Now
        </button>
      </div>

      {/* About */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-base font-semibold text-gray-800 mb-3">About</h2>
        <dl className="text-sm space-y-2">
          <div className="flex justify-between">
            <dt className="text-gray-500">Version</dt>
            <dd className="font-medium text-gray-800">0.1.0</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-500">Mode</dt>
            <dd className="font-medium text-gray-800">Single-user (local)</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-500">Anti-bypass</dt>
            <dd className="font-medium text-green-600">Enforced — never bypasses CAPTCHA</dd>
          </div>
        </dl>
      </div>
    </div>
  )
}
