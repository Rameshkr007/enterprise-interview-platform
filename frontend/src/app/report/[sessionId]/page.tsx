'use client'
import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { reportApi } from '@/lib/api'
import type { SessionReport } from '@/lib/types'

function StatCard({ label, value, unit = '' }: { label: string; value: number | string; unit?: string }) {
  return (
    <div className="glass-card p-6">
      <p className="text-slate-400 text-sm mb-2">{label}</p>
      <p className="text-2xl font-bold text-white">
        {typeof value === 'number' ? value.toFixed(1) : value}
        {unit && <span className="text-sm text-slate-400 ml-1">{unit}</span>}
      </p>
    </div>
  )
}

export default function ReportPage() {
  const params = useParams()
  const sessionId = params?.sessionId as string
  const router = useRouter()
  const [report, setReport] = useState<SessionReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      try {
        let r: SessionReport
        try {
          r = await reportApi.getBySession(sessionId)
        } catch {
          r = await reportApi.generate(sessionId)
        }
        setReport(r)
      } catch (err: unknown) {
        setError('Failed to load report')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [sessionId])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 rounded-full border-4 border-t-brand-500 border-brand-500/20 animate-spin mx-auto mb-4" />
          <p className="text-slate-400">Generating your performance report...</p>
        </div>
      </div>
    )
  }

  if (error || !report) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 mb-4">{error}</p>
          <button onClick={() => router.push('/dashboard')} className="btn-ghost">Dashboard</button>
        </div>
      </div>
    )
  }

  const audio = report.overall_audio_metrics
  const finalScore = Math.round(report.final_score)
  const scoreColor = finalScore >= 80 ? '#10b981' : finalScore >= 60 ? '#f59e0b' : '#ef4444'

  return (
    <div className="min-h-screen max-w-5xl mx-auto px-6 py-12 animate-fade-in">
      <button onClick={() => router.push('/dashboard')} className="btn-ghost mb-8">&larr; Dashboard</button>

      <div className="flex items-center justify-between mb-12">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Interview Performance Report</h1>
          <p className="text-slate-400 text-sm">Session {sessionId.slice(0, 8)}...</p>
        </div>
        <div className="text-center">
          <div className="text-5xl font-bold" style={{ color: scoreColor }}>{finalScore}</div>
          <div className="text-slate-400 text-sm mt-1">Overall Score</div>
        </div>
      </div>

      {/* Audio Metrics */}
      <section className="mb-10">
        <h2 className="text-lg font-bold text-white mb-4">Audio & Delivery Analytics</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
          <StatCard label="Confidence Score" value={(audio.confidence_score * 100)} unit="/100" />
          <StatCard label="Speech Rate" value={audio.avg_speech_rate_wpm} unit="wpm" />
          <StatCard label="Filler Word Rate" value={(audio.avg_filler_rate * 60)} unit="/min" />
          <StatCard label="Silence Ratio" value={(audio.avg_silence_ratio * 100)} unit="%" />
          <StatCard label="Pitch Variance" value={(audio.avg_pitch_variance_score * 100)} unit="/100" />
        </div>
      </section>

      {/* Category Scores */}
      <section className="mb-10">
        <h2 className="text-lg font-bold text-white mb-4">Performance by Category</h2>
        <div className="glass-card p-6 space-y-4">
          {Object.entries(report.category_scores).map(([cat, score]) => (
            <div key={cat}>
              <div className="flex justify-between mb-2">
                <span className="text-slate-300 text-sm capitalize">{cat.replace('_', ' ')}</span>
                <span className="text-white font-medium text-sm">{((score as number) * 100).toFixed(1)}</span>
              </div>
              <div className="progress-bar">
                <div className="progress-bar-fill" style={{ width: `${((score as number) * 100).toFixed(0)}%` }} />
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Strengths & Improvements */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-10">
        <div className="glass-card p-6">
          <h2 className="text-lg font-bold text-green-400 mb-4">Strengths</h2>
          <ul className="space-y-2">
            {report.strengths.map((s, i) => (
              <li key={i} className="flex items-start gap-2 text-slate-300 text-sm">
                <span className="text-green-400 mt-0.5">&#x2713;</span>{s}
              </li>
            ))}
            {report.strengths.length === 0 && <li className="text-slate-500 text-sm">No data yet</li>}
          </ul>
        </div>
        <div className="glass-card p-6">
          <h2 className="text-lg font-bold text-amber-400 mb-4">Areas to Improve</h2>
          <ul className="space-y-2">
            {report.improvement_areas.map((s, i) => (
              <li key={i} className="flex items-start gap-2 text-slate-300 text-sm">
                <span className="text-amber-400 mt-0.5">&#x2192;</span>{s}
              </li>
            ))}
            {report.improvement_areas.length === 0 && <li className="text-slate-500 text-sm">No data yet</li>}
          </ul>
        </div>
      </div>

      {/* Difficulty Progression */}
      <section className="glass-card p-6">
        <h2 className="text-lg font-bold text-white mb-6">Difficulty Progression</h2>
        <div className="flex gap-2 flex-wrap">
          {report.difficulty_progression.map((t, i) => {
            const score = t.composite_score ?? 0
            const c = score >= 0.7 ? '#10b981' : score >= 0.4 ? '#f59e0b' : '#ef4444'
            return (
              <div key={i} className="flex flex-col items-center gap-1">
                <div
                  className="w-8 rounded-t"
                  style={{ height: `${Math.max(score * 60, 8)}px`, background: c }}
                />
                <span className="text-xs text-slate-500">Q{t.turn_index + 1}</span>
              </div>
            )
          })}
        </div>
      </section>
    </div>
  )
}
