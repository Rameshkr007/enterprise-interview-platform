'use client'

import React from 'react'
import Link from 'next/link'
import HolographicBrain from '@/components/3d/HolographicBrain'
import { Zap, FileText, ArrowRight, Sparkles } from 'lucide-react'

interface WelcomeHeaderProps {
  userName: string
  targetRole?: string
  readinessScore?: number
  latestSessionId?: string | null
}

export default function WelcomeHeader({
  userName,
  targetRole = 'Senior Full-Stack Engineer / Distributed Systems',
  readinessScore = 88.4,
  latestSessionId,
}: WelcomeHeaderProps) {
  const firstName = userName?.split(' ')[0] || 'Engineer'

  return (
    <div className="relative rounded-3xl bg-gradient-to-r from-[#0c0e24] via-[#121535] to-[#0f122b] border border-indigo-500/25 p-7 sm:p-9 overflow-hidden shadow-[0_10px_40px_rgba(0,0,0,0.5)]">
      {/* Background Volumetric Lighting */}
      <div className="absolute top-0 right-1/4 w-96 h-96 bg-purple-600/15 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 left-10 w-72 h-72 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="relative z-10 flex flex-col lg:flex-row items-center justify-between gap-8">
        {/* Left Column: Greeting, Role & Action Prompts */}
        <div className="space-y-4 max-w-xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-[11px] font-mono font-medium bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 backdrop-blur-md">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
            LANGGRAPH 0.2 &bull; 1536D VECTOR CALIBRATION
          </div>

          <h1 className="text-3xl sm:text-4xl font-black text-white tracking-tight leading-snug">
            Welcome back, <span className="bg-gradient-to-r from-cyan-400 via-indigo-300 to-purple-400 bg-clip-text text-transparent">{firstName}</span>.
          </h1>

          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed font-normal">
            Target Role: <span className="text-white font-semibold">{targetRole}</span>.
            Your current readiness telemetry stands at <span className="text-cyan-400 font-bold font-mono">{readinessScore}%</span> (Tier-1 calibrated).
          </p>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center gap-3 pt-1">
            <Link
              href={latestSessionId ? `/interview/${latestSessionId}` : '/interview/new'}
              className="inline-flex items-center gap-2 py-3 px-6 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-xs sm:text-sm font-bold text-white shadow-[0_0_25px_rgba(99,102,241,0.4)] hover:brightness-110 transition-all cursor-pointer"
            >
              <Zap className="w-4 h-4 fill-white" />
              <span>{latestSessionId ? 'Resume Active Interview' : 'Launch AI Interview'}</span>
              <ArrowRight className="w-4 h-4" />
            </Link>

            <Link
              href="/ats"
              className="inline-flex items-center gap-2 py-3 px-5 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.1] text-xs sm:text-sm font-semibold text-slate-200 hover:text-white transition-all cursor-pointer"
            >
              <FileText className="w-4 h-4 text-cyan-400" />
              <span>Analyze My Resume</span>
            </Link>
          </div>

          {/* Recommended Next Action Chip */}
          <div className="pt-2">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-black/40 border border-white/[0.08] text-[11px] font-mono text-slate-300">
              <Sparkles className="w-3.5 h-3.5 text-amber-400 shrink-0" />
              <span>Recommended Next Action:</span>
              <span className="text-amber-300 font-semibold">Complete Distributed Consensus Loop in System Design</span>
            </div>
          </div>
        </div>

        {/* Right Column: 3D Holographic Neural Core */}
        <div className="relative w-full lg:w-72 h-56 shrink-0 flex items-center justify-center">
          <HolographicBrain />
        </div>
      </div>
    </div>
  )
}
