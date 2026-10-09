'use client'
import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { atsApi } from '@/lib/api'
import type { AtsAnalysisResult } from '@/lib/types'

function ScoreRing({ score, label }: { score: number; label: string }) {
  const pct = Math.min(score, 100)
  const color =
    pct >= 80 ? '#10b981' : pct >= 60 ? '#f59e0b' : '#ef4444'
  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative w-24 h-24">
        <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
          <circle cx="18" cy="18" r="15.9" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="3" />
          <circle
            cx="18" cy="18" r="15.9" fill="none"
            stroke={color} strokeWidth="3"
            strokeDasharray={`${(pct / 100) * 100} 100`}
            strokeLinecap="round"
            style={{ transition: 'stroke-dasharray 1s ease' }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-lg font-bold text-white">{Math.round(pct)}</span>
        </div>
      </div>
      <span className="text-xs text-slate-400 uppercase tracking-wide">{label}</span>
    </div>
  )
}

function TierBadge({ tier }: { tier: string }) {
  const map: Record<string, string> = {
    excellent: 'badge badge-success',
    good: 'badge badge-info',
    fair: 'badge badge-warning',
    poor: 'badge badge-danger',
  }
  return <span className={map[tier] ?? 'badge badge-info'}>{tier}</span>
}

export default function AtsPage() {
  const [file, setFile] = useState<File | null>(null)
  const [jdTitle, setJdTitle] = useState('')
  const [jdText, setJdText] = useState('')
  const [step, setStep] = useState<'upload' | 'analyzing' | 'result'>('upload')
  const [result, setResult] = useState<AtsAnalysisResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(true)
  const router = useRouter()

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token')
      setIsLoggedIn(!!token)
    }
  }, [])

  async function handleAnalyze() {
    if (!file || !jdText.trim()) return
    setError(null)

    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null
    if (!token) {
      setError('Please log in first to analyze your resume.')
      router.push('/login')
      return
    }

    setStep('analyzing')
    try {
      const { resume_id } = await atsApi.uploadResume(file)
      const { jd_id } = await atsApi.createJd({ title: jdTitle || 'Target Role', raw_text: jdText })
      const analysis = await atsApi.analyze(resume_id, jd_id)
      setResult(analysis)
      setStep('result')
    } catch (err: unknown) {
      const axiosErr = err as {
        response?: {
          status?: number
          data?: { detail?: string | Array<{ msg: string; message?: string }>; message?: string }
        }
        message?: string
      }
      if (axiosErr?.response?.status === 401) {
        setError('Your login session expired. Please log in again to continue.')
        router.push('/login')
        return
      }
      let errorMsg = 'Analysis failed. Please check your network and try again.'
      const detail = axiosErr?.response?.data?.detail
      if (typeof detail === 'string') {
        errorMsg = detail
      } else if (Array.isArray(detail) && detail[0]) {
        errorMsg = detail[0].msg || detail[0].message || 'Validation error'
      } else if (axiosErr?.response?.data?.message) {
        errorMsg = axiosErr.response.data.message
      } else if (axiosErr?.message) {
        errorMsg = axiosErr.message
      }
      setError(errorMsg)
      setStep('upload')
    }
  }

  if (step === 'analyzing') {
    return (
      <div className="min-h-screen flex items-center justify-center flex-col gap-6">
        <div className="relative w-20 h-20">
          <div className="absolute inset-0 rounded-full border-4 border-brand-500/20" />
          <div className="absolute inset-0 rounded-full border-4 border-t-brand-500 animate-spin" />
        </div>
        <div className="text-center">
          <p className="text-white font-semibold text-lg mb-1">Analyzing your resume...</p>
          <p className="text-slate-400 text-sm">Generating embeddings & computing semantic similarity</p>
        </div>
      </div>
    )
  }

  if (step === 'result' && result) {
    const sections = result.section_scores as Record<string, number>
    return (
      <div className="min-h-screen max-w-5xl mx-auto px-6 py-12 animate-fade-in">
        <button onClick={() => setStep('upload')} className="btn-ghost mb-8">
          &larr; New Analysis
        </button>

        <div className="glass-card p-8 mb-8">
          <div className="flex flex-wrap items-center justify-between gap-6 mb-8">
            <div>
              <h1 className="text-2xl font-bold text-white mb-2">ATS Analysis Report</h1>
              <div className="flex items-center gap-3">
                <TierBadge tier={result.match_tier} />
                <span className="text-slate-400 text-sm">Cosine similarity: {(result.cosine_similarity * 100).toFixed(1)}%</span>
              </div>
            </div>
            <ScoreRing score={result.overall_score} label="Overall Score" />
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(sections).map(([key, val]) => (
              <ScoreRing key={key} score={(val as number) * 100} label={key} />
            ))}
          </div>
        </div>

        {/* Skill Gaps */}
        <div className="glass-card p-8 mb-8">
          <h2 className="text-lg font-bold text-white mb-6">Skill Gaps Detected</h2>
          <div className="space-y-4">
            {result.skill_gaps.map((gap, i) => (
              <div key={i} className="p-4 rounded-xl bg-red-500/5 border border-red-500/20">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-white">{gap.skill_name}</span>
                  <span className={`badge ${gap.gap_type === 'missing' ? 'badge-danger' : 'badge-warning'}`}>
                    {gap.gap_type}
                  </span>
                </div>
                <div className="progress-bar mb-2">
                  <div className="progress-bar-fill" style={{ width: `${(gap.jd_importance * 100).toFixed(0)}%`, background: 'linear-gradient(90deg,#ef4444,#f97316)' }} />
                </div>
                <p className="text-slate-400 text-xs">JD Importance: {(gap.jd_importance * 100).toFixed(0)}%</p>
              </div>
            ))}
            {result.skill_gaps.length === 0 && <p className="text-slate-400 text-sm">No critical gaps detected.</p>}
          </div>
        </div>

        {/* Matched Skills */}
        <div className="glass-card p-8">
          <h2 className="text-lg font-bold text-white mb-6">Matched Skills</h2>
          <div className="flex flex-wrap gap-3">
            {result.matched_skills.map((skill, i) => (
              <div key={i} className="px-3 py-2 rounded-lg bg-green-500/10 border border-green-500/20 text-green-400 text-sm font-medium">
                {skill.skill_name}{' '}
                <span className="text-green-600">({(skill.confidence * 100).toFixed(0)}%)</span>
              </div>
            ))}
          </div>
        </div>

        <div className="flex justify-center mt-12">
          <button
            id="start-interview-from-ats"
            onClick={() => router.push('/interview/new')}
            className="btn-primary text-base px-10 py-4"
          >
            &#x1F3A4; Start Interview Based on This Analysis
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen max-w-3xl mx-auto px-6 py-16 animate-fade-in">
      <button onClick={() => router.push('/dashboard')} className="btn-ghost mb-8">
        &larr; Dashboard
      </button>

      <h1 className="text-3xl font-bold text-white mb-2">ATS Resume Analyzer</h1>
      <p className="text-slate-400 mb-10">
        Upload your resume and paste a job description. We compute semantic similarity using PGVector embeddings.
      </p>

      {!isLoggedIn && (
        <div className="p-4 mb-6 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-sm flex items-center justify-between">
          <span>You must be signed in to analyze resumes with PGVector.</span>
          <button
            onClick={() => router.push('/login')}
            className="px-4 py-1.5 rounded-lg bg-amber-500 text-slate-900 font-semibold text-xs hover:bg-amber-400 transition"
          >
            Sign In Now
          </button>
        </div>
      )}

      {error && (
        <div className="p-4 mb-6 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
          {error}
        </div>
      )}

      <div className="glass-card p-8 space-y-8">
        {/* Resume Upload */}
        <div>
          <label className="block text-sm font-semibold text-slate-300 mb-3">Resume (PDF / TXT)</label>
          <label
            id="resume-dropzone"
            className="block border-2 border-dashed border-white/10 rounded-xl p-10 text-center cursor-pointer hover:border-brand-500/50 hover:bg-brand-500/5 transition-all"
          >
            <div className="text-4xl mb-3">&#x1F4C4;</div>
            {file ? (
              <p className="text-green-400 font-medium">{file.name}</p>
            ) : (
              <p className="text-slate-400">
                Drag & drop or <span className="text-brand-400 underline">click to upload</span>
              </p>
            )}
            <input
              id="resume-file-input"
              type="file"
              accept=".pdf,.txt,.docx"
              className="hidden"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
          </label>
        </div>

        {/* JD Input */}
        <div>
          <label className="block text-sm font-semibold text-slate-300 mb-3">Job Title</label>
          <input
            id="jd-title"
            type="text"
            className="input-field mb-4"
            placeholder="e.g. Senior Software Engineer"
            value={jdTitle}
            onChange={(e) => setJdTitle(e.target.value)}
          />
          <label className="block text-sm font-semibold text-slate-300 mb-3">Job Description</label>
          <textarea
            id="jd-text"
            rows={8}
            className="input-field resize-none"
            placeholder="Paste the full job description here..."
            value={jdText}
            onChange={(e) => setJdText(e.target.value)}
          />
        </div>

        <button
          id="analyze-btn"
          onClick={handleAnalyze}
          disabled={!file || !jdText.trim()}
          className="btn-primary w-full py-4 text-base"
        >
          Analyze Resume Semantically
        </button>
      </div>
    </div>
  )
}
