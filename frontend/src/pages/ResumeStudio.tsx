import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { jobsApi } from '@/api/jobs'
import { profileApi } from '@/api/profile'
import apiClient from '@/api/client'
import { FileText, Sparkles, Upload, CheckCircle } from 'lucide-react'
import clsx from 'clsx'
import toast from 'react-hot-toast'

export default function ResumeStudio() {
  const [jobId, setJobId] = useState('')
  const [result, setResult] = useState<{
    ats_score: number
    keyword_gaps: string[]
    suggested_summary: string
    tailoring_tips: string[]
  } | null>(null)

  const { data: profile } = useQuery({ queryKey: ['profile'], queryFn: profileApi.get })
  const { data: jobs } = useQuery({
    queryKey: ['jobs', { page_size: 100 }],
    queryFn: () => jobsApi.list({ page_size: 100 }),
  })

  const customize = useMutation({
    mutationFn: async () => {
      const resp = await apiClient.post('/resume/customize', { job_id: jobId })
      return resp.data
    },
    onSuccess: (data) => setResult(data),
    onError: () => toast.error('Resume customization failed'),
  })

  const uploadResume = useMutation({
    mutationFn: async (file: File) => {
      const fd = new FormData()
      fd.append('file', file)
      const resp = await apiClient.post('/profile/upload-resume', fd)
      return resp.data
    },
    onSuccess: () => toast.success('Resume uploaded!'),
    onError: () => toast.error('Upload failed'),
  })

  return (
    <div className="p-8 max-w-3xl space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Resume Studio</h1>
      <p className="text-sm text-gray-500">Tailor your resume to a specific job and measure ATS compatibility.</p>

      {/* Resume upload */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-base font-semibold text-gray-800 mb-3">Your Resume</h2>
        {profile?.resume_url ? (
          <div className="flex items-center gap-3">
            <FileText size={18} className="text-blue-500" />
            <a href={profile.resume_url} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-600 hover:underline">
              View current resume
            </a>
          </div>
        ) : (
          <p className="text-sm text-gray-400">No resume uploaded yet</p>
        )}

        <label className="mt-4 flex items-center gap-2 cursor-pointer w-fit">
          <input
            type="file"
            accept=".pdf,.docx"
            className="sr-only"
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file) uploadResume.mutate(file)
            }}
          />
          <div className="flex items-center gap-2 text-sm px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
            <Upload size={14} />
            {uploadResume.isPending ? 'Uploading…' : 'Upload Resume (PDF/DOCX)'}
          </div>
        </label>
      </div>

      {/* Customize */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-base font-semibold text-gray-800 mb-4">Tailor to a Job</h2>

        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-700">Select Job</label>
            <select
              value={jobId}
              onChange={(e) => setJobId(e.target.value)}
              className="mt-1 w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Choose a job…</option>
              {jobs?.items?.map((job) => (
                <option key={job.id} value={job.id}>
                  {job.title} — {job.company_name}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={() => customize.mutate()}
            disabled={!jobId || customize.isPending}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            <Sparkles size={14} />
            {customize.isPending ? 'Analyzing…' : 'Analyze & Customize'}
          </button>
        </div>
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-4">
          {/* ATS score */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-base font-semibold text-gray-800 mb-4">ATS Compatibility</h2>
            <div className="flex items-center gap-4">
              <div className={clsx('text-3xl font-bold', result.ats_score >= 0.75 ? 'text-green-600' : result.ats_score >= 0.5 ? 'text-yellow-500' : 'text-red-500')}>
                {Math.round(result.ats_score * 100)}%
              </div>
              <div className="flex-1">
                <div className="h-2.5 bg-gray-100 rounded-full">
                  <div
                    className={clsx('h-2.5 rounded-full', result.ats_score >= 0.75 ? 'bg-green-500' : result.ats_score >= 0.5 ? 'bg-yellow-500' : 'bg-red-400')}
                    style={{ width: `${Math.round(result.ats_score * 100)}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Suggested summary */}
          {result.suggested_summary && (
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="text-base font-semibold text-gray-800 mb-3">Suggested Summary</h2>
              <p className="text-sm text-gray-700 leading-relaxed">{result.suggested_summary}</p>
            </div>
          )}

          {/* Keyword gaps */}
          {result.keyword_gaps.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="text-base font-semibold text-gray-800 mb-3">Missing Keywords</h2>
              <p className="text-xs text-gray-500 mb-3">Add these to your resume where relevant</p>
              <div className="flex flex-wrap gap-2">
                {result.keyword_gaps.map((kw) => (
                  <span key={kw} className="text-xs bg-red-50 text-red-600 border border-red-200 px-2 py-1 rounded">{kw}</span>
                ))}
              </div>
            </div>
          )}

          {/* Tips */}
          {result.tailoring_tips.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="text-base font-semibold text-gray-800 mb-3">Tailoring Tips</h2>
              <ul className="space-y-2">
                {result.tailoring_tips.map((tip, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                    <CheckCircle size={13} className="text-blue-400 mt-0.5 flex-shrink-0" />
                    {tip}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
