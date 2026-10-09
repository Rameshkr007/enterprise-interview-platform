'use client'

import React from 'react'
import Link from 'next/link'
import {
  Compass,
  ArrowRight,
  CheckCircle2,
  Circle,
  PlayCircle,
  Award,
  Milestone,
} from 'lucide-react'

interface MilestoneItem {
  title: string
  status: 'completed' | 'in-progress' | 'upcoming'
  duration: string
  topics: string
}

const ROADMAP_STEPS: MilestoneItem[] = [
  {
    title: 'Phase 1: High-Throughput System Design',
    status: 'completed',
    duration: 'Week 1-2',
    topics: 'Backpressure, gRPC connection pooling, Kafka partitioning',
  },
  {
    title: 'Phase 2: Distributed Consensus & Storage Engines',
    status: 'in-progress',
    duration: 'Current (Week 3)',
    topics: 'Raft consensus invariants, LSM trees vs B-Trees, split-brain recovery',
  },
  {
    title: 'Phase 3: Executive Behavioral & Leadership (STAR)',
    status: 'upcoming',
    duration: 'Week 4',
    topics: 'Cross-functional conflict, architectural trade-offs, driving org impact',
  },
]

export default function LearningRoadmapWidget() {
  return (
    <div className="rounded-2xl border border-slate-800/80 bg-gradient-to-b from-slate-900/90 to-slate-950/90 p-6 backdrop-blur-xl shadow-lg shadow-black/40">
      <div className="flex items-center justify-between mb-5 pb-3 border-b border-slate-800/80">
        <div className="flex items-center gap-2.5">
          <div className="p-2.5 rounded-xl bg-violet-500/10 border border-violet-500/20 text-violet-400">
            <Compass className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[11px] font-bold uppercase tracking-wider text-violet-400">
              Personalized Career Pathway
            </div>
            <h3 className="text-base font-bold text-white">Target: Staff Systems Architect (L6)</h3>
          </div>
        </div>
        <Link
          href="/learning"
          className="text-xs font-semibold text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
        >
          View Full Graph <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      <div className="space-y-3.5 mb-5">
        {ROADMAP_STEPS.map((step, idx) => (
          <div
            key={idx}
            className={`p-3.5 rounded-xl border transition-colors flex items-start justify-between gap-3 ${
              step.status === 'in-progress'
                ? 'bg-violet-950/20 border-violet-500/40 ring-1 ring-violet-500/20'
                : step.status === 'completed'
                ? 'bg-slate-950/40 border-slate-800/60'
                : 'bg-slate-950/20 border-slate-900 opacity-60'
            }`}
          >
            <div className="flex items-start gap-3">
              <div className="mt-0.5">
                {step.status === 'completed' && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
                {step.status === 'in-progress' && <PlayCircle className="w-4 h-4 text-violet-400 animate-pulse" />}
                {step.status === 'upcoming' && <Circle className="w-4 h-4 text-slate-600" />}
              </div>
              <div>
                <div className="text-xs font-bold text-white flex items-center gap-2">
                  <span>{step.title}</span>
                  <span className="text-[10px] font-semibold text-slate-400">({step.duration})</span>
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">{step.topics}</div>
              </div>
            </div>

            {step.status === 'in-progress' && (
              <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full bg-violet-500/20 text-violet-300 border border-violet-500/30 whitespace-nowrap">
                Active Track
              </span>
            )}
          </div>
        ))}
      </div>

      <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between">
        <div className="text-xs text-slate-400">
          Curriculum progress: <span className="font-bold text-white">68% Complete</span>
        </div>
        <Link
          href="/learning"
          className="px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-violet-500/10 text-violet-300 border border-violet-500/20 hover:bg-violet-500/20 transition-all flex items-center gap-1.5"
        >
          Resume Learning <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  )
}
