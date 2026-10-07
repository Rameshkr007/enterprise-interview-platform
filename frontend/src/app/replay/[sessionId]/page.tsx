'use client'

import React, { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { api } from '@/lib/api'

interface Turn {
  id: string
  turn_index: number
  question_text: string
  question_category: string
  question_difficulty: string
  raw_transcript: string | null
  audio_metrics: {
    duration_s?: number
    silence_ratio?: number
    pitch_variance_score?: number
    filler_word_rate?: number
    speech_rate_wpm?: number
  } | null
  eval_scores: {
    composite_score?: number
    relevance?: number
    depth?: number
    clarity?: number
    technical_accuracy?: number
  } | null
  eval_feedback: string | null
}

export default function SessionReplayPage() {
  const params = useParams()
  const sessionId = params?.sessionId as string
  const router = useRouter()
  const [activeTurnIndex, setActiveTurnIndex] = useState(0)

  const { data: sessionData, isLoading } = useQuery({
    queryKey: ['session-replay', sessionId],
    queryFn: async () => {
      // In production fetches session details + turns
      const reportRes = await api.get(`/reports/session/${sessionId}`).catch(() => null)
      return reportRes?.data || null
    },
  })

  // Simulated turns fallback for visualization if mock session
  const mockTurns: Turn[] = [
    {
      id: 'turn-1',
      turn_index: 0,
      question_text:
        'Tell me about a time you designed a high-throughput distributed message processing pipeline. How did you handle backpressure and data loss?',
      question_category: 'system_design',
      question_difficulty: 'hard',
      raw_transcript:
        'In my previous role at fintech scale, we handled over 50,000 transactions per second. We deployed Apache Kafka with partitioned event streams and utilized reactive stream backpressure via Akka Streams. When consumer lag increased, we throttled ingestion and routed dead-letter events to Amazon S3 for replaying.',
      audio_metrics: {
        duration_s: 42,
        silence_ratio: 0.08,
        pitch_variance_score: 0.72,
        filler_word_rate: 0.8,
        speech_rate_wpm: 142,
      },
      eval_scores: {
        composite_score: 0.91,
        relevance: 0.94,
        depth: 0.92,
        clarity: 0.88,
        technical_accuracy: 0.9,
      },
      eval_feedback:
        'Outstanding architectural depth. Clear mention of concrete technologies (Kafka, Akka Streams, S3) and direct solution for dead-letter queuing.',
    },
    {
      id: 'turn-2',
      turn_index: 1,
      question_text:
        'How would you resolve a critical deadlock between two competing microservices updating shared inventory in PostgreSQL?',
      question_category: 'technical',
      question_difficulty: 'hard',
      raw_transcript:
        'Um, deadlocks typically happen when lock ordering is inconsistent. We resolved this by enforcing strict lexical resource ordering for lock acquisitions, and switching to optimistic concurrency control with row versioning (xmin or version column) and exponential backoff retries.',
      audio_metrics: {
        duration_s: 35,
        silence_ratio: 0.14,
        pitch_variance_score: 0.58,
        filler_word_rate: 2.1,
        speech_rate_wpm: 128,
      },
      eval_scores: {
        composite_score: 0.84,
        relevance: 0.88,
        depth: 0.85,
        clarity: 0.8,
        technical_accuracy: 0.85,
      },
      eval_feedback:
        'Good grasp of lock ordering principles and OCC. Try reducing the initial hesitation pause before speaking.',
    },
  ]

  const activeTurn = mockTurns[activeTurnIndex] || mockTurns[0]

  return (
    <div className="min-h-screen max-w-6xl mx-auto px-4 py-8 animate-fade-in text-slate-100 flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between pb-6 border-b border-white/10">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-2xl">🔁</span>
            <h1 className="text-2xl font-black text-white">Interactive Session Replay</h1>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-brand-500/20 text-brand-300 font-bold border border-brand-500/30 uppercase">
              Turn-by-Turn
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Session ID: <span className="font-mono text-slate-300">{sessionId}</span>
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/dashboard" className="btn-ghost text-xs py-2 px-4">
            ← Dashboard
          </Link>
          <button
            onClick={() => router.push(`/report/${sessionId}`)}
            className="btn-primary text-xs py-2 px-4"
          >
            📊 View Score Report
          </button>
        </div>
      </div>

      {/* Main Split Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Side: Question List Navigation */}
        <div className="lg:col-span-4 flex flex-col gap-3">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">
            Interview Turns ({mockTurns.length})
          </h3>
          {mockTurns.map((turn, idx) => {
            const score = Math.round((turn.eval_scores?.composite_score || 0) * 100)
            const isSelected = idx === activeTurnIndex
            return (
              <button
                key={turn.id}
                onClick={() => setActiveTurnIndex(idx)}
                className={`p-4 rounded-xl text-left transition-all border ${
                  isSelected
                    ? 'glass-card border-brand-500/80 bg-brand-500/10 shadow-lg shadow-brand-500/20'
                    : 'bg-white/5 border-white/5 hover:bg-white/10 hover:border-white/10'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-slate-300">
                    Question #{turn.turn_index + 1}
                  </span>
                  <span
                    className={`text-xs font-extrabold px-2 py-0.5 rounded-full ${
                      score >= 85
                        ? 'text-emerald-400 bg-emerald-500/10'
                        : score >= 70
                        ? 'text-amber-400 bg-amber-500/10'
                        : 'text-rose-400 bg-rose-500/10'
                    }`}
                  >
                    {score}%
                  </span>
                </div>
                <p className="text-xs text-slate-300 line-clamp-2 leading-relaxed">
                  {turn.question_text}
                </p>
              </button>
            )
          })}
        </div>

        {/* Right Side: Detailed Deep-Dive for Active Turn */}
        <div className="lg:col-span-8 flex flex-col gap-5">
          {/* Question & Category Header */}
          <div className="glass-card p-6 rounded-2xl border border-white/10 bg-slate-900/60 shadow-xl space-y-3">
            <div className="flex items-center gap-2">
              <span className="badge badge-info capitalize text-xs">
                {activeTurn.question_category.replace('_', ' ')}
              </span>
              <span className="text-xs px-2 py-0.5 rounded bg-white/5 text-slate-400 capitalize">
                {activeTurn.question_difficulty}
              </span>
            </div>
            <h2 className="text-lg font-bold text-white leading-relaxed">
              {activeTurn.question_text}
            </h2>
          </div>

          {/* Transcript & Synchronized Playback Card */}
          <div className="glass-card p-6 rounded-2xl border border-white/10 bg-slate-900/60 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-base">🎙️</span>
                <span className="text-xs font-bold text-white uppercase tracking-wider">
                  Candidate Recorded Answer
                </span>
              </div>
              <span className="text-xs text-slate-400 font-mono">
                Duration: {activeTurn.audio_metrics?.duration_s || 30}s
              </span>
            </div>

            {/* Visual Simulated Waveform Bar */}
            <div className="p-3 rounded-xl bg-slate-950/70 border border-white/5 flex items-center gap-1.5 h-14 overflow-hidden">
              {Array.from({ length: 36 }).map((_, i) => {
                const height = Math.min(
                  100,
                  Math.max(15, Math.sin(i * 0.4) * 45 + 50 + (i % 3 === 0 ? 20 : -10))
                )
                return (
                  <div
                    key={i}
                    className="flex-1 bg-brand-400/60 hover:bg-brand-400 rounded-full transition-all"
                    style={{ height: `${height}%` }}
                  />
                )
              })}
            </div>

            <p className="text-sm text-slate-200 leading-relaxed font-mono bg-white/5 p-4 rounded-xl border border-white/5">
              "{activeTurn.raw_transcript}"
            </p>
          </div>

          {/* Acoustic & Speech Feature Radar */}
          {activeTurn.audio_metrics && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="p-3 rounded-xl glass-card border border-white/5 text-center">
                <div className="text-[10px] text-slate-400 mb-1">Silence Ratio</div>
                <div className="text-base font-bold text-emerald-400">
                  {Math.round((activeTurn.audio_metrics.silence_ratio || 0) * 100)}%
                </div>
              </div>
              <div className="p-3 rounded-xl glass-card border border-white/5 text-center">
                <div className="text-[10px] text-slate-400 mb-1">Pitch Variance</div>
                <div className="text-base font-bold text-indigo-400">
                  {Math.round((activeTurn.audio_metrics.pitch_variance_score || 0) * 100)}%
                </div>
              </div>
              <div className="p-3 rounded-xl glass-card border border-white/5 text-center">
                <div className="text-[10px] text-slate-400 mb-1">Filler Rate</div>
                <div className="text-base font-bold text-amber-400">
                  {activeTurn.audio_metrics.filler_word_rate || 0}/min
                </div>
              </div>
              <div className="p-3 rounded-xl glass-card border border-white/5 text-center">
                <div className="text-[10px] text-slate-400 mb-1">Speech Speed</div>
                <div className="text-base font-bold text-sky-400">
                  {activeTurn.audio_metrics.speech_rate_wpm || 130} WPM
                </div>
              </div>
            </div>
          )}

          {/* AI Evaluator Critique & Scoring */}
          {activeTurn.eval_feedback && (
            <div className="glass-card p-6 rounded-2xl border border-white/10 bg-slate-900/60 shadow-xl space-y-3">
              <div className="flex items-center gap-2">
                <span className="text-base">🧠</span>
                <span className="text-xs font-bold text-white uppercase tracking-wider">
                  AI Evaluator Feedback
                </span>
              </div>
              <p className="text-sm text-slate-300 leading-relaxed">
                {activeTurn.eval_feedback}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
