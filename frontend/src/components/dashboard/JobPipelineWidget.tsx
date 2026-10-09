'use client'

import React from 'react'
import Link from 'next/link'
import {
  Briefcase,
  ArrowRight,
  ChevronRight,
  Clock,
  CheckCircle2,
  AlertCircle,
  Building,
} from 'lucide-react'

interface PipelineStage {
  stage: string
  count: number
  color: string
  bgColor: string
  textColor: string
}

const PIPELINE_STAGES: PipelineStage[] = [
  { stage: 'Wishlist', count: 6, color: 'border-slate-700', bgColor: 'bg-slate-800/40', textColor: 'text-slate-300' },
  { stage: 'Applied', count: 8, color: 'border-blue-500/40', bgColor: 'bg-blue-500/10', textColor: 'text-blue-400' },
  { stage: 'Technical', count: 4, color: 'border-cyan-500/40', bgColor: 'bg-cyan-500/10', textColor: 'text-cyan-400' },
  { stage: 'Final Round', count: 2, color: 'border-violet-500/40', bgColor: 'bg-violet-500/10', textColor: 'text-violet-400' },
  { stage: 'Offer Stage', count: 1, color: 'border-emerald-500/40', bgColor: 'bg-emerald-500/10', textColor: 'text-emerald-400' },
]

interface UrgentAction {
  company: string
  role: string
  event: string
  date: string
}

const UPCOMING_ACTIONS: UrgentAction[] = [
  { company: 'Stripe', role: 'Staff Systems Architect', event: 'Architecture Deep-Dive Loop', date: 'Tomorrow, 2:00 PM' },
  { company: 'Datadog', role: 'Principal Infrastructure Eng', event: 'Distributed Consensus Round', date: 'Oct 14, 11:30 AM' },
]

export default function JobPipelineWidget() {
  return (
    <div className="rounded-2xl border border-slate-800/80 bg-gradient-to-b from-slate-900/90 to-slate-950/90 p-6 backdrop-blur-xl shadow-lg shadow-black/40">
      <div className="flex items-center justify-between mb-5 pb-3 border-b border-slate-800/80">
        <div className="flex items-center gap-2.5">
          <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <Briefcase className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Active Opportunity Pipeline</h3>
            <p className="text-xs text-slate-400">Real-time status across 21 tracked roles</p>
          </div>
        </div>
        <Link
          href="/job-tracker"
          className="text-xs font-semibold text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
        >
          Manage Board <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {/* Stage Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-6">
        {PIPELINE_STAGES.map((s, idx) => (
          <div
            key={idx}
            className={`p-3.5 rounded-xl border ${s.color} ${s.bgColor} flex flex-col items-center text-center justify-center`}
          >
            <div className={`text-2xl font-black ${s.textColor}`}>{s.count}</div>
            <div className="text-[11px] font-semibold text-slate-300 mt-1">{s.stage}</div>
          </div>
        ))}
      </div>

      {/* Next Up / Urgent Events */}
      <div className="space-y-2.5">
        <h4 className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5 mb-2">
          <Clock className="w-3.5 h-3.5 text-cyan-400" />
          Upcoming Loops & Deadlines
        </h4>
        {UPCOMING_ACTIONS.map((item, idx) => (
          <div
            key={idx}
            className="flex items-center justify-between p-3 rounded-xl bg-slate-950/60 border border-slate-800/70 text-xs"
          >
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-white text-xs">
                {item.company[0]}
              </div>
              <div>
                <div className="font-bold text-white flex items-center gap-2">
                  <span>{item.company}</span>
                  <span className="text-slate-500">•</span>
                  <span className="text-slate-300 font-medium">{item.role}</span>
                </div>
                <div className="text-[11px] text-cyan-400 font-medium">{item.event}</div>
              </div>
            </div>
            <span className="text-[11px] font-semibold text-amber-300 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20 whitespace-nowrap">
              {item.date}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
