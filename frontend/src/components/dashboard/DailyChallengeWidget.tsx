'use client'

import React from 'react'
import Link from 'next/link'
import {
  Flame,
  Zap,
  Clock,
  ArrowRight,
  Code,
  ShieldAlert,
  Sparkles,
} from 'lucide-react'

export default function DailyChallengeWidget() {
  return (
    <div className="rounded-2xl border border-orange-500/30 bg-gradient-to-b from-slate-900/90 to-slate-950/90 p-6 backdrop-blur-xl shadow-lg shadow-orange-950/20 relative overflow-hidden">
      {/* Background ambient glow */}
      <div className="absolute -top-16 -right-16 w-36 h-36 bg-orange-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2.5 rounded-xl bg-orange-500/15 border border-orange-500/30 text-orange-400">
            <Flame className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <div className="text-[11px] font-bold uppercase tracking-wider text-orange-400">
              Daily Challenge #42
            </div>
            <h3 className="text-base font-bold text-white">Distributed Rate Limiter (Token Bucket)</h3>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-red-500/15 text-red-300 border border-red-500/30">
            Hard
          </span>
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-orange-500/15 text-orange-300 border border-orange-500/30 flex items-center gap-1">
            <Zap className="w-3 h-3" /> +150 XP
          </span>
        </div>
      </div>

      <p className="text-xs text-slate-300 mb-4 leading-relaxed">
        Design a cluster-wide token-bucket rate limiter handling 250,000 req/sec with sub-millisecond latency using Redis Lua scripts and local sliding-window approximations.
      </p>

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3 border-t border-slate-800/80">
        <div className="flex items-center gap-3 text-xs text-slate-400">
          <span className="flex items-center gap-1">
            <Clock className="w-3.5 h-3.5 text-slate-500" />
            Expires in 08h 42m
          </span>
          <span>•</span>
          <span className="text-orange-400 font-semibold">14-Day Streak Protected</span>
        </div>

        <Link
          href="/daily-challenge"
          className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-xl text-xs font-bold text-slate-950 bg-gradient-to-r from-orange-400 to-amber-500 hover:opacity-95 shadow-lg shadow-orange-500/20 transition-all"
        >
          <span>Solve Today's Challenge</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  )
}
