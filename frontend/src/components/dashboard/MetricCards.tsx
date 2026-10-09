'use client'

import React from 'react'
import {
  Zap,
  Target,
  FileText,
  Flame,
  Award,
  TrendingUp,
  Cpu,
} from 'lucide-react'

interface MetricCardsProps {
  latestScore?: number | null
  avgScore?: number | null
  totalSessions?: number
  totalAtsScans?: number
  skillProgress?: number
  streakDays?: number
  isLoading?: boolean
}

export default function MetricCards({
  latestScore = 92.4,
  avgScore = 88.6,
  totalSessions = 14,
  totalAtsScans = 28,
  skillProgress = 84.5,
  streakDays = 4,
  isLoading = false,
}: MetricCardsProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {[...Array(6)].map((_, i) => (
          <div
            key={i}
            className="h-28 rounded-2xl bg-white/[0.03] border border-white/[0.06] animate-pulse p-4"
          />
        ))}
      </div>
    )
  }

  const metrics = [
    {
      label: 'Latest Score',
      value: latestScore !== null && latestScore !== undefined ? `${latestScore}%` : 'N/A',
      trend: '+4.2% vs last loop',
      trendUp: true,
      icon: Target,
      iconColor: 'text-cyan-400 bg-cyan-500/15 border-cyan-500/30',
    },
    {
      label: 'Avg Performance',
      value: avgScore !== null && avgScore !== undefined ? `${avgScore}%` : 'N/A',
      trend: 'Top 15% Percentile',
      trendUp: true,
      icon: Award,
      iconColor: 'text-indigo-400 bg-indigo-500/15 border-indigo-500/30',
    },
    {
      label: 'Mock Interviews',
      value: totalSessions.toString(),
      trend: 'Completed Loops',
      trendUp: true,
      icon: Zap,
      iconColor: 'text-purple-400 bg-purple-500/15 border-purple-500/30',
    },
    {
      label: 'ATS Analyses',
      value: totalAtsScans.toString(),
      trend: 'PGVector Scans',
      trendUp: true,
      icon: FileText,
      iconColor: 'text-emerald-400 bg-emerald-500/15 border-emerald-500/30',
    },
    {
      label: 'Skill Mastery',
      value: `${skillProgress}%`,
      trend: '+12.4% this month',
      trendUp: true,
      icon: Cpu,
      iconColor: 'text-blue-400 bg-blue-500/15 border-blue-500/30',
    },
    {
      label: 'Practice Streak',
      value: `${streakDays} Days`,
      trend: 'Multiplier Active 🔥',
      trendUp: true,
      icon: Flame,
      iconColor: 'text-amber-400 bg-amber-500/15 border-amber-500/30',
    },
  ]

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {metrics.map((m) => {
        const Icon = m.icon
        return (
          <div
            key={m.label}
            className="group relative rounded-2xl p-4 bg-[#0d1024] border border-white/[0.06] hover:border-indigo-500/40 hover:shadow-[0_8px_30px_rgba(0,0,0,0.6)] transition-all duration-300 flex flex-col justify-between"
          >
            {/* Top Row: Label and Icon */}
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-medium text-slate-400 truncate">{m.label}</span>
              <div
                className={`w-7 h-7 rounded-lg border flex items-center justify-center shrink-0 ${m.iconColor}`}
              >
                <Icon className="w-3.5 h-3.5" />
              </div>
            </div>

            {/* Metric Value */}
            <div className="text-2xl font-black text-white font-mono tracking-tight my-1">
              {m.value}
            </div>

            {/* Bottom Trend / Context */}
            <div className="text-[10px] font-mono text-emerald-400 truncate mt-1 flex items-center gap-1">
              <span>{m.trend}</span>
            </div>
          </div>
        )
      })}
    </div>
  )
}
