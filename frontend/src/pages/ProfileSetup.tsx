import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { profileApi } from '@/api/profile'
import { CheckCircle, Plus, X, Save, RefreshCw, Upload, AlertCircle } from 'lucide-react'
import toast from 'react-hot-toast'

const SKILL_LEVELS = ['beginner', 'intermediate', 'expert']
const REMOTE_OPTIONS = ['remote', 'hybrid', 'onsite', 'any']
const INDIA_CITIES = ['Mumbai', 'Bangalore', 'Pune', 'Hyderabad', 'Chennai', 'Delhi', 'Gurgaon', 'Noida', 'Kolkata', 'Ahmedabad']

interface Skill { name: string; level: string; years: number }

function TagInput({ label, values, onChange, placeholder }: {
  label: string; values: string[]; onChange: (v: string[]) => void; placeholder: string
}) {
  const [input, setInput] = useState('')
  const add = () => {
    const v = input.trim()
    if (v && !values.includes(v)) onChange([...values, v])
    setInput('')
  }
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1.5">{label}</label>
      <div className="flex flex-wrap gap-2 mb-2">
        {values.map((v) => (
          <span key={v} className="flex items-center gap-1 bg-blue-50 text-blue-700 text-xs px-2.5 py-1 rounded-full">
            {v}
            <button type="button" onClick={() => onChange(values.filter((x) => x !== v))}><X size={11} /></button>
          </span>
        ))}
      </div>
      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), add())}
          placeholder={placeholder}
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button type="button" onClick={add} className="px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm">
          <Plus size={14} />
        </button>
      </div>
    </div>
  )
}

function SkillsEditor({ skills, onChange }: { skills: Skill[]; onChange: (s: Skill[]) => void }) {
  const [name, setName] = useState('')
  const [level, setLevel] = useState('intermediate')
  const [years, setYears] = useState(1)

  const add = () => {
    if (!name.trim()) return
    if (!skills.find((s) => s.name.toLowerCase() === name.toLowerCase())) {
      onChange([...skills, { name: name.trim(), level, years }])
    }
    setName('')
  }

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">Skills</label>
      <div className="flex flex-wrap gap-2 mb-3">
        {skills.map((s) => (
          <div key={s.name} className="flex items-center gap-1.5 bg-gray-50 border border-gray-200 rounded-lg px-3 py-1.5 text-sm">
            <span className="font-medium text-gray-800">{s.name}</span>
            <span className={`text-xs px-1.5 py-0.5 rounded ${s.level === 'expert' ? 'bg-green-100 text-green-700' : s.level === 'intermediate' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-500'}`}>
              {s.level}
            </span>
            <span className="text-xs text-gray-400">{s.years}y</span>
            <button type="button" onClick={() => onChange(skills.filter((x) => x.name !== s.name))} className="text-gray-400 hover:text-red-500">
              <X size={11} />
            </button>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-4 gap-2">
        <input value={name} onChange={(e) => setName(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), add())}
          placeholder="Skill name" className="col-span-2 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        <select value={level} onChange={(e) => setLevel(e.target.value)} className="border border-gray-300 rounded-lg px-2 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
          {SKILL_LEVELS.map((l) => <option key={l}>{l}</option>)}
        </select>
        <div className="flex gap-1">
          <input type="number" min={0} max={30} value={years} onChange={(e) => setYears(Number(e.target.value))}
            className="w-16 border border-gray-300 rounded-lg px-2 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          <button type="button" onClick={add} className="flex-1 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm flex items-center justify-center">
            <Plus size={14} />
          </button>
        </div>
      </div>
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-5">
      <h2 className="text-base font-semibold text-gray-800 border-b pb-3">{title}</h2>
      {children}
    </div>
  )
}

function Field({ label, required, children }: { label: string; required?: boolean; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1.5">
        {label} {required && <span className="text-red-500">*</span>}
      </label>
      {children}
    </div>
  )
}

const inputCls = "w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition"

export default function ProfileSetup() {
  const qc = useQueryClient()
  const { data: profile, isLoading } = useQuery({ queryKey: ['profile'], queryFn: profileApi.get })

  const [form, setForm] = useState({
    full_name: '', current_title: '', experience_years: 0, location: '',
    linkedin_url: '', github_url: '', bio: '',
    target_salary_min: '', target_salary_max: '',
    remote_preference: 'any',
    target_titles: [] as string[],
    skills: [] as Skill[],
    preferences: {} as Record<string, any>,
  })

  useEffect(() => {
    if (profile) {
      setForm({
        full_name: profile.full_name || '',
        current_title: profile.current_title || '',
        experience_years: profile.experience_years || 0,
        location: profile.location || '',
        linkedin_url: profile.linkedin_url || '',
        github_url: profile.github_url || '',
        bio: profile.bio || '',
        target_salary_min: profile.target_salary_min?.toString() || '',
        target_salary_max: profile.target_salary_max?.toString() || '',
        remote_preference: profile.remote_preference || 'any',
        target_titles: profile.target_titles || [],
        skills: (profile.skills as Skill[]) || [],
        preferences: {
          phone: '',
          naukri_url: '',
          preferred_locations: [],
          max_monthly_applies: 100,
          prefer_india_first: true,
          ...profile.preferences,
        },
      })
    }
  }, [profile])

  const set = (key: string, val: any) => setForm((f) => ({ ...f, [key]: val }))
  const setPref = (key: string, val: any) => setForm((f) => ({ ...f, preferences: { ...f.preferences, [key]: val } }))

  const save = useMutation({
    mutationFn: () => profileApi.update({
      ...form,
      target_salary_min: form.target_salary_min ? Number(form.target_salary_min) : undefined,
      target_salary_max: form.target_salary_max ? Number(form.target_salary_max) : undefined,
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['profile'] })
      toast.success('Profile saved!')
    },
    onError: () => toast.error('Failed to save profile'),
  })

  const refreshEmb = useMutation({
    mutationFn: profileApi.refreshEmbedding,
    onSuccess: () => toast.success('Embedding refreshed — job matching updated!'),
  })

  const uploadResume = useMutation({
    mutationFn: (file: File) => profileApi.uploadResume(file),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['profile'] }); toast.success('Resume uploaded!') },
    onError: () => toast.error('Upload failed'),
  })

  if (isLoading) return (
    <div className="p-8 animate-pulse space-y-4">
      {Array.from({ length: 4 }).map((_, i) => <div key={i} className="h-32 bg-gray-100 rounded-xl" />)}
    </div>
  )

  const isComplete = form.full_name && form.current_title && form.skills.length > 0 && form.linkedin_url

  return (
    <div className="p-6 max-w-3xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Profile Setup</h1>
          <p className="text-sm text-gray-500 mt-0.5">Fill in your details — the AI uses this to find and apply to matching jobs daily.</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => refreshEmb.mutate()} disabled={refreshEmb.isPending}
            className="flex items-center gap-1.5 text-sm px-3 py-2 border border-gray-200 rounded-lg hover:bg-gray-50">
            <RefreshCw size={13} className={refreshEmb.isPending ? 'animate-spin' : ''} /> Sync AI
          </button>
          <button onClick={() => save.mutate()} disabled={save.isPending}
            className="flex items-center gap-1.5 text-sm px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
            <Save size={13} /> {save.isPending ? 'Saving…' : 'Save Profile'}
          </button>
        </div>
      </div>

      {!isComplete && (
        <div className="flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-800">
          <AlertCircle size={16} className="mt-0.5 flex-shrink-0" />
          Complete your profile to activate daily job scanning and auto-apply.
        </div>
      )}

      {/* Personal Info */}
      <Section title="Personal Information">
        <div className="grid grid-cols-2 gap-4">
          <Field label="Full Name" required>
            <input className={inputCls} value={form.full_name} onChange={(e) => set('full_name', e.target.value)} placeholder="Shubham Dongre" />
          </Field>
          <Field label="Phone Number">
            <input className={inputCls} value={form.preferences.phone || ''} onChange={(e) => setPref('phone', e.target.value)} placeholder="+91 9876543210" />
          </Field>
          <Field label="Current Title" required>
            <input className={inputCls} value={form.current_title} onChange={(e) => set('current_title', e.target.value)} placeholder="Software Engineer" />
          </Field>
          <Field label="Years of Experience" required>
            <input type="number" min={0} max={40} className={inputCls} value={form.experience_years} onChange={(e) => set('experience_years', Number(e.target.value))} />
          </Field>
          <Field label="Current Location">
            <input className={inputCls} value={form.location} onChange={(e) => set('location', e.target.value)} placeholder="Mumbai, India" />
          </Field>
          <Field label="Remote Preference">
            <select className={inputCls} value={form.remote_preference} onChange={(e) => set('remote_preference', e.target.value)}>
              {REMOTE_OPTIONS.map((o) => <option key={o} value={o}>{o.charAt(0).toUpperCase() + o.slice(1)}</option>)}
            </select>
          </Field>
        </div>
        <Field label="Bio / Summary">
          <textarea className={inputCls} rows={4} value={form.bio} onChange={(e) => set('bio', e.target.value)}
            placeholder="Write a short professional summary that the AI will use when crafting outreach messages..." />
        </Field>
      </Section>

      {/* Social / Profile URLs */}
      <Section title="Profile Links">
        <div className="grid grid-cols-1 gap-4">
          <Field label="LinkedIn URL" required>
            <input className={inputCls} value={form.linkedin_url} onChange={(e) => set('linkedin_url', e.target.value)} placeholder="https://linkedin.com/in/your-profile" />
          </Field>
          <Field label="Naukri Profile URL">
            <input className={inputCls} value={form.preferences.naukri_url || ''} onChange={(e) => setPref('naukri_url', e.target.value)} placeholder="https://naukri.com/profile/your-name" />
          </Field>
          <Field label="GitHub URL">
            <input className={inputCls} value={form.github_url} onChange={(e) => set('github_url', e.target.value)} placeholder="https://github.com/username" />
          </Field>
        </div>
      </Section>

      {/* Skills */}
      <Section title="Skills">
        <SkillsEditor skills={form.skills} onChange={(s) => set('skills', s)} />
      </Section>

      {/* Job Preferences */}
      <Section title="Job Search Preferences">
        <TagInput label="Target Job Titles" values={form.target_titles} onChange={(v) => set('target_titles', v)}
          placeholder="e.g. Backend Engineer" />

        <TagInput
          label="Preferred Locations (India cities first, then others)"
          values={form.preferences.preferred_locations || []}
          onChange={(v) => setPref('preferred_locations', v)}
          placeholder="e.g. Mumbai" />

        <div className="flex flex-wrap gap-2">
          {INDIA_CITIES.filter((c) => !form.preferences.preferred_locations?.includes(c)).map((c) => (
            <button key={c} type="button" onClick={() => setPref('preferred_locations', [...(form.preferences.preferred_locations || []), c])}
              className="text-xs px-2.5 py-1 border border-dashed border-gray-300 rounded-full text-gray-500 hover:border-blue-400 hover:text-blue-600">
              + {c}
            </button>
          ))}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Field label="Min Salary (₹/year)">
            <input type="number" className={inputCls} value={form.target_salary_min} onChange={(e) => set('target_salary_min', e.target.value)} placeholder="800000" />
          </Field>
          <Field label="Max Salary (₹/year)">
            <input type="number" className={inputCls} value={form.target_salary_max} onChange={(e) => set('target_salary_max', e.target.value)} placeholder="1500000" />
          </Field>
        </div>
      </Section>

      {/* Auto-Apply Settings */}
      <Section title="Auto-Apply Settings">
        <div className="grid grid-cols-2 gap-4">
          <Field label="Max Applications / Month">
            <input type="number" min={1} max={200} className={inputCls}
              value={form.preferences.max_monthly_applies ?? 100}
              onChange={(e) => setPref('max_monthly_applies', Number(e.target.value))} />
          </Field>
          <Field label="Daily Apply Limit">
            <input type="number" min={1} max={20} className={inputCls}
              value={form.preferences.max_daily_applies ?? 5}
              onChange={(e) => setPref('max_daily_applies', Number(e.target.value))} />
          </Field>
        </div>

        <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
          <input type="checkbox" id="india-first" className="w-4 h-4 text-blue-600 rounded"
            checked={form.preferences.prefer_india_first ?? true}
            onChange={(e) => setPref('prefer_india_first', e.target.checked)} />
          <label htmlFor="india-first" className="text-sm text-gray-700">
            <span className="font-medium">Apply to India jobs first</span>
            <span className="text-gray-500"> — prioritize Indian companies and locations before international ones</span>
          </label>
        </div>

        <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
          <input type="checkbox" id="auto-apply" className="w-4 h-4 text-blue-600 rounded"
            checked={form.preferences.auto_apply_enabled ?? false}
            onChange={(e) => setPref('auto_apply_enabled', e.target.checked)} />
          <label htmlFor="auto-apply" className="text-sm text-gray-700">
            <span className="font-medium">Enable daily auto-apply</span>
            <span className="text-gray-500"> — AI will automatically apply to matching jobs each day</span>
          </label>
        </div>
      </Section>

      {/* Resume Upload */}
      <Section title="Resume">
        <div className="flex items-center gap-4">
          {profile?.resume_url ? (
            <div className="flex items-center gap-2 text-sm text-green-700 bg-green-50 border border-green-200 rounded-lg px-4 py-2.5">
              <CheckCircle size={14} /> Resume uploaded
            </div>
          ) : (
            <p className="text-sm text-gray-500">No resume uploaded yet.</p>
          )}
          <label className="flex items-center gap-2 cursor-pointer text-sm px-4 py-2.5 border border-gray-300 rounded-lg hover:bg-gray-50">
            <Upload size={14} />
            {uploadResume.isPending ? 'Uploading…' : profile?.resume_url ? 'Replace Resume' : 'Upload Resume (PDF/DOCX)'}
            <input type="file" accept=".pdf,.docx" className="hidden"
              onChange={(e) => { const f = e.target.files?.[0]; if (f) uploadResume.mutate(f) }} />
          </label>
        </div>
      </Section>

      {/* Save */}
      <div className="flex justify-end pb-8">
        <button onClick={() => save.mutate()} disabled={save.isPending}
          className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium">
          <Save size={15} /> {save.isPending ? 'Saving…' : 'Save & Activate'}
        </button>
      </div>
    </div>
  )
}
