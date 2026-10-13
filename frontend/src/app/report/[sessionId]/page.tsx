'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { reportApi, interviewApi } from '@/lib/api'
import type { RecordingPlaybackResponse } from '@/lib/api'
import type { SessionReport, TurnResponse } from '@/lib/types'
import {
  ChevronLeft,
  Video,
  Trash2,
  Download,
  Share2,
  CheckCircle2,
  AlertTriangle,
  Sparkles,
  ShieldCheck,
  Play,
  FileText,
  Layers,
  Cpu,
  GraduationCap,
  Activity,
  Award,
} from 'lucide-react'

function StatCard({ label, value, unit = '' }: { label: string; value: number | string; unit?: string }) {
  return (
    <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 shadow-md">
      <p className="text-slate-400 text-xs font-mono mb-1">{label}</p>
      <p className="text-2xl font-black text-white font-mono">
        {typeof value === 'number' ? value.toFixed(1) : value}
        {unit && <span className="text-xs text-slate-400 ml-1 font-sans">{unit}</span>}
      </p>
    </div>
  )
}

export default function ReportPage() {
  const params = useParams()
  const sessionId = params?.sessionId as string
  const router = useRouter()

  const [report, setReport] = useState<SessionReport | null>(null)
  const [turns, setTurns] = useState<TurnResponse[]>([])
  const [recording, setRecording] = useState<RecordingPlaybackResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isDeletingRecording, setIsDeletingRecording] = useState(false)
  const [deleteNotice, setDeleteNotice] = useState<string | null>(null)

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

        // Fetch interview turns
        try {
          const t = await interviewApi.getTurns(sessionId)
          setTurns(t)
        } catch {}

        // Fetch recording metadata
        try {
          const rec = await interviewApi.getRecording(sessionId)
          setRecording(rec)
        } catch {}
      } catch (err: unknown) {
        setError('Failed to generate or load report.')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [sessionId])

  const handleDeleteRecording = async () => {
    if (!window.confirm('Are you sure you want to permanently delete this session recording from private storage?')) {
      return
    }
    setIsDeletingRecording(true)
    try {
      await interviewApi.deleteRecording(sessionId)
      setRecording(null)
      setDeleteNotice('Recording permanently deleted from S3 storage.')
      setTimeout(() => setDeleteNotice(null), 5000)
    } catch {
      alert('Failed to delete recording.')
    } finally {
      setIsDeletingRecording(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#070814] text-slate-100">
        <div className="text-center space-y-4">
          <div className="w-12 h-12 rounded-full border-4 border-cyan-500 border-t-transparent animate-spin mx-auto" />
          <p className="text-sm font-mono text-slate-400">Synthesizing Bar Raiser Evidence &amp; Evaluation Scorecards...</p>
        </div>
      </div>
    )
  }

  if (error || !report) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#070814] text-slate-100">
        <div className="text-center space-y-4 p-8 rounded-3xl bg-slate-900 border border-slate-800">
          <p className="text-red-400 text-sm">{error}</p>
          <button
            onClick={() => router.push('/dashboard')}
            className="px-6 py-2 rounded-xl bg-cyan-500 text-slate-950 font-bold text-xs"
          >
            Return to Dashboard
          </button>
        </div>
      </div>
    )
  }

  const audio = report.overall_audio_metrics || {}
  const finalScore = Math.round(report.final_score)
  const scoreColor =
    finalScore >= 80 ? 'text-emerald-400' : finalScore >= 60 ? 'text-amber-400' : 'text-rose-400'

  return (
    <div className="min-h-screen bg-[#070814] text-slate-100 selection:bg-cyan-500/30 selection:text-cyan-200 py-10 px-4 sm:px-6 lg:px-8">
      {/* Background Volumetric Glows */}
      <div className="fixed top-0 left-1/3 w-[500px] h-[500px] bg-cyan-600/10 rounded-full blur-[140px] pointer-events-none" />
      <div className="fixed bottom-0 right-1/4 w-[450px] h-[450px] bg-indigo-600/10 rounded-full blur-[140px] pointer-events-none" />

      <div className="max-w-5xl mx-auto space-y-10 relative z-10 animate-fade-in">
        {/* Navigation Bar */}
        <div className="flex items-center justify-between pb-4 border-b border-white/[0.08]">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-white/[0.04] border border-white/[0.08] hover:border-white/[0.15] text-xs font-semibold text-slate-300 hover:text-white transition-all group"
          >
            <ChevronLeft className="w-4 h-4 text-slate-400 group-hover:-translate-x-0.5 transition-transform" />
            <span>Dashboard</span>
          </Link>

          <div className="flex items-center gap-3">
            <button
              onClick={() => window.print()}
              className="px-3.5 py-1.5 rounded-xl bg-white/[0.04] border border-white/[0.08] hover:border-white/[0.2] text-xs font-mono text-slate-300 hover:text-white flex items-center gap-1.5 cursor-pointer transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export PDF</span>
            </button>
          </div>
        </div>

        {/* Delete notification toast */}
        {deleteNotice && (
          <div className="p-4 rounded-2xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-sm flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{deleteNotice}</span>
          </div>
        )}

        {/* Header Hero */}
        <div className="p-8 rounded-3xl bg-gradient-to-br from-indigo-950/60 via-slate-900/80 to-slate-950/90 border border-white/10 shadow-2xl flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono font-bold bg-cyan-500/15 border border-cyan-500/30 text-cyan-300">
              <Award className="w-3.5 h-3.5 text-cyan-400" />
              <span>BAR RAISER INTERVIEW EVALUATION</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
              Performance Debrief &amp; Audit Report
            </h1>
            <p className="text-xs font-mono text-slate-400">
              Session ID: {sessionId} • Verified by LangGraph Multi-Agent Engine
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/80 border border-white/10 text-center min-w-[160px] shadow-xl">
            <div className={`text-5xl font-black font-mono ${scoreColor}`}>{finalScore}</div>
            <div className="text-xs text-slate-400 font-mono mt-1 uppercase font-bold">Overall Score</div>
            <div className="text-[10px] text-cyan-400 font-mono mt-0.5">
              {finalScore >= 80 ? 'Strong Hire' : finalScore >= 60 ? 'Hire' : 'Needs Practice'}
            </div>
          </div>
        </div>

        {/* Video / Audio Recording Playback Player Section */}
        {recording && recording.has_recording && recording.playback_url && (
          <section className="p-6 sm:p-8 rounded-3xl bg-slate-900/60 border border-cyan-500/30 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5 text-sm font-bold text-white font-mono">
                <Video className="w-4 h-4 text-cyan-400" />
                <span>Session Video Recording Playback</span>
              </div>

              <button
                type="button"
                onClick={handleDeleteRecording}
                disabled={isDeletingRecording}
                className="px-3 py-1.5 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-300 hover:bg-rose-500/25 text-xs font-mono flex items-center gap-1.5 cursor-pointer transition-all"
              >
                <Trash2 className="w-3.5 h-3.5 text-rose-400" />
                <span>{isDeletingRecording ? 'Deleting...' : 'Delete Recording'}</span>
              </button>
            </div>

            <div className="relative rounded-2xl overflow-hidden bg-black border border-slate-800 aspect-video max-h-[420px] mx-auto flex items-center justify-center">
              <video
                src={recording.playback_url}
                controls
                className="w-full h-full object-contain"
              >
                Your browser does not support video playback.
              </video>
            </div>

            <div className="text-[11px] text-slate-400 font-mono flex items-center justify-between pt-1">
              <span>Duration: ~{Math.round(recording.total_duration_s)}s</span>
              <span>Encrypted Object Storage • Short-lived Pre-signed URL</span>
            </div>
          </section>
        )}

        {/* Audio & Delivery Analytics */}
        <section className="space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 font-mono flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyan-400" />
            <span>Acoustic Delivery &amp; Speech Biometrics</span>
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3.5">
            <StatCard label="Confidence Index" value={((audio.confidence_score || 0.75) * 100)} unit="/100" />
            <StatCard label="Speech Rate" value={audio.avg_speech_rate_wpm || 135} unit="wpm" />
            <StatCard label="Filler Word Rate" value={((audio.avg_filler_rate || 0.02) * 60)} unit="/min" />
            <StatCard label="Silence Ratio" value={((audio.avg_silence_ratio || 0.12) * 100)} unit="%" />
            <StatCard label="Pitch Stability" value={((audio.avg_pitch_variance_score || 0.65) * 100)} unit="/100" />
          </div>
        </section>

        {/* Competency & Category Mastery */}
        <section className="space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 font-mono flex items-center gap-2">
            <Layers className="w-4 h-4 text-purple-400" />
            <span>Competency Category Mastery</span>
          </h2>
          <div className="p-6 rounded-3xl bg-slate-900/60 border border-slate-800/80 space-y-4">
            {Object.entries(report.category_scores).map(([cat, score]) => {
              const numScore = Number(score) * (Number(score) <= 1.0 ? 100 : 1)
              return (
                <div key={cat} className="space-y-1.5">
                  <div className="flex justify-between text-xs font-mono">
                    <span className="text-slate-300 font-bold capitalize">{cat.replace('_', ' ')}</span>
                    <span className="text-cyan-300 font-bold">{numScore.toFixed(1)} / 100</span>
                  </div>
                  <div className="w-full h-2.5 rounded-full bg-slate-800 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-indigo-500 transition-all duration-500"
                      style={{ width: `${Math.min(numScore, 100)}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </section>

        {/* Strengths & Improvement Areas */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-6 rounded-3xl bg-slate-900/60 border border-emerald-500/30 space-y-4">
            <h3 className="text-sm font-bold uppercase tracking-wider text-emerald-400 font-mono flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              <span>Demonstrated Strengths</span>
            </h3>
            <ul className="space-y-2.5">
              {report.strengths.map((s, i) => (
                <li key={i} className="flex items-start gap-2.5 text-xs text-slate-200">
                  <span className="text-emerald-400 font-bold mt-0.5">✓</span>
                  <span>{s}</span>
                </li>
              ))}
              {report.strengths.length === 0 && (
                <li className="text-xs text-slate-400">Clear structured communication foundations.</li>
              )}
            </ul>
          </div>

          <div className="p-6 rounded-3xl bg-slate-900/60 border border-amber-500/30 space-y-4">
            <h3 className="text-sm font-bold uppercase tracking-wider text-amber-400 font-mono flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" />
              <span>Targeted Improvement Areas</span>
            </h3>
            <ul className="space-y-2.5">
              {report.improvement_areas.map((s, i) => (
                <li key={i} className="flex items-start gap-2.5 text-xs text-slate-200">
                  <span className="text-amber-400 font-bold mt-0.5">→</span>
                  <span>{s}</span>
                </li>
              ))}
              {report.improvement_areas.length === 0 && (
                <li className="text-xs text-slate-400">Deepen edge case validation under concurrency constraints.</li>
              )}
            </ul>
          </div>
        </div>

        {/* Turn-by-Turn Evidence & Model Answer Review */}
        {turns.length > 0 && (
          <section className="space-y-4">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 font-mono flex items-center gap-2">
              <FileText className="w-4 h-4 text-cyan-400" />
              <span>Turn-by-Turn Questions, Transcripts &amp; Evaluation</span>
            </h2>

            <div className="space-y-4">
              {turns.map((t, idx) => (
                <div
                  key={t.id || idx}
                  className="p-6 rounded-3xl bg-slate-900/60 border border-slate-800/80 space-y-3.5"
                >
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="px-2.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 font-bold">
                      Turn #{t.turn_index + 1} • {t.question_category}
                    </span>
                    <span className="text-slate-400 capitalize">Difficulty: {t.question_difficulty}</span>
                  </div>

                  <div className="space-y-1">
                    <div className="text-[11px] font-mono text-slate-400 uppercase">Question:</div>
                    <div className="text-sm font-bold text-white leading-relaxed">{t.question_text}</div>
                  </div>

                  {t.raw_transcript && (
                    <div className="space-y-1 p-3.5 rounded-2xl bg-slate-950/80 border border-slate-800">
                      <div className="text-[10px] font-mono text-cyan-400 uppercase">Your Spoken / Typed Response:</div>
                      <div className="text-xs text-slate-300 font-mono leading-relaxed whitespace-pre-wrap">
                        {t.raw_transcript}
                      </div>
                    </div>
                  )}

                  {t.eval_feedback && (
                    <div className="space-y-1 p-3.5 rounded-2xl bg-indigo-500/10 border border-indigo-500/20">
                      <div className="text-[10px] font-mono text-indigo-300 uppercase">Bar Raiser Feedback &amp; Rubric:</div>
                      <div className="text-xs text-slate-200 leading-relaxed">
                        {t.eval_feedback}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  )
}
