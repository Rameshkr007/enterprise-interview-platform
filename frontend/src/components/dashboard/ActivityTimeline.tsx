'use client'

import React, { useEffect, useState } from 'react'
import Link from 'next/link'
import {
  Calendar,
  Clock,
  Award,
  ChevronRight,
  ArrowRight,
  FileBarChart2,
  PlayCircle,
  CheckCircle,
  AlertCircle,
  History,
  Filter,
} from 'lucide-react'
import { interviewApi } from '@/lib/api'
import type { InterviewSession } from '@/lib/types'

export default function ActivityTimeline() {
  const [sessions, setSessions] = useState<InterviewSession[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'completed' | 'active'>('all')

  useEffect(() => {
    interviewApi
      .getSessions()
      .then((data) => {
        if (Array.isArray(data)) {
          setSessions(data)
        }
      })
      .catch(() => {
        // Fallback demo session for onboarding display if none yet
        setSessions([])
      })
      .finally(() => {
        setIsLoading(false)
      })
  }, [])

  const filteredSessions = sessions.filter((s) => {
    if (filter === 'completed') return s.status === 'completed'
    if (filter === 'active') return s.status === 'active' || s.status === 'pending'
    return true
  })

  return (
    <div className="rounded-2xl border border-slate-800/80 bg-gradient-to-b from-slate-900/90 to-slate-950/90 p-6 backdrop-blur-xl shadow-lg shadow-black/40">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-4 border-b border-slate-800/80">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
            <History className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <span>Interview Activity Timeline</span>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-800 text-slate-300">
                {sessions.length} Sessions
              </span>
            </h3>
            <p className="text-xs text-slate-400">
              Audit log of completed mock interviews, performance scores, and diagnostic debriefs.
            </p>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-slate-950/80 border border-slate-800 self-start sm:self-center">
          <button
            onClick={() => setFilter('all')}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-colors ${
              filter === 'all' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30' : 'text-slate-400 hover:text-white'
            }`}
          >
            All
          </button>
          <button
            onClick={() => setFilter('completed')}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-colors ${
              filter === 'completed' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30' : 'text-slate-400 hover:text-white'
            }`}
          >
            Completed
          </button>
          <button
            onClick={() => setFilter('active')}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-colors ${
              filter === 'active' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30' : 'text-slate-400 hover:text-white'
            }`}
          >
            In-Progress
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-3 py-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 rounded-xl bg-slate-800/40 animate-pulse border border-slate-800/60" />
          ))}
        </div>
      ) : filteredSessions.length > 0 ? (
        <div className="space-y-3">
          {filteredSessions.map((session) => {
            const isCompleted = session.status === 'completed'
            const score = session.aggregate_score != null ? Math.round(session.aggregate_score) : null
            const formattedDate = new Date(session.created_at).toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
              year: 'numeric',
            })

            return (
              <div
                key={session.id}
                className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl bg-slate-950/50 border border-slate-800/80 hover:border-slate-700 transition-all hover:bg-slate-950/80"
              >
                <div className="flex items-start sm:items-center gap-3.5">
                  <div
                    className={`p-2.5 rounded-xl border mt-0.5 sm:mt-0 ${
                      isCompleted
                        ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                        : 'bg-cyan-500/10 border-cyan-500/20 text-cyan-400'
                    }`}
                  >
                    {isCompleted ? <CheckCircle className="w-5 h-5" /> : <PlayCircle className="w-5 h-5" />}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-bold text-white capitalize break-words">
                        {session.current_topic || 'Staff System Architecture & Behavioral'}
                      </span>
                      <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                        {session.current_difficulty}
                      </span>
                      <span
                        className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                          isCompleted
                            ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                            : 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                        }`}
                      >
                        {session.status}
                      </span>
                    </div>

                    <div className="flex items-center gap-4 text-xs text-slate-400 mt-1">
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3.5 h-3.5" />
                        {formattedDate}
                      </span>
                      <span>
                        Question {session.current_question_index} of {session.target_question_count}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-4 self-end sm:self-center">
                  {score !== null ? (
                    <div className="text-right">
                      <div className="text-sm font-extrabold text-cyan-400">{score} / 100</div>
                      <div className="text-[10px] text-slate-500 uppercase tracking-wider">Score</div>
                    </div>
                  ) : (
                    <div className="text-right">
                      <div className="text-xs text-slate-400">In Progress</div>
                    </div>
                  )}

                  {isCompleted ? (
                    <Link
                      href={`/reports/${session.id}`}
                      className="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 hover:bg-cyan-500/20 transition-all flex items-center gap-1.5"
                    >
                      <FileBarChart2 className="w-3.5 h-3.5" />
                      Report
                    </Link>
                  ) : (
                    <Link
                      href={`/interview?sessionId=${session.id}`}
                      className="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 hover:bg-emerald-500/20 transition-all flex items-center gap-1.5"
                    >
                      <PlayCircle className="w-3.5 h-3.5" />
                      Resume
                    </Link>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        /* Empty State */
        <div className="text-center py-12 px-4 rounded-xl border border-dashed border-slate-800 bg-slate-950/30">
          <div className="w-12 h-12 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 flex items-center justify-center mx-auto mb-3">
            <History className="w-6 h-6" />
          </div>
          <h4 className="text-base font-bold text-white mb-1">No interview history recorded yet</h4>
          <p className="text-xs text-slate-400 max-w-sm mx-auto mb-5 leading-relaxed">
            Run your first adaptive AI interview simulation to generate live performance analytics, speech metrics, and debrief reports.
          </p>
          <Link
            href="/interview"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold text-slate-950 bg-gradient-to-r from-cyan-400 to-blue-500 hover:opacity-95 shadow-lg shadow-cyan-500/20"
          >
            <PlayCircle className="w-4 h-4" />
            Launch First Simulation
          </Link>
        </div>
      )}
    </div>
  )
}
