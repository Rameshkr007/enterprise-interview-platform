'use client'

import React from 'react'
import Link from 'next/link'
import {
  FileText,
  Bot,
  Code2,
  Building2,
  Coins,
  Sparkles,
  Briefcase,
  Flame,
  BarChart3,
  ArrowRight,
  TrendingUp,
  ShieldCheck,
  CheckCircle2,
} from 'lucide-react'

interface FeatureModule {
  id: string
  title: string
  category: string
  description: string
  href: string
  icon: React.ElementType
  iconColor: string
  accentBorder: string
  badge?: string
  isRecommended?: boolean
  stats?: string
}

const FEATURE_MODULES: FeatureModule[] = [
  {
    id: 'ats-analyzer',
    title: 'ATS Resume Analyzer',
    category: 'Semantic Intelligence',
    description: 'Score match percentage, find critical missing keywords, and benchmark against target job descriptions using PGVector.',
    href: '/ats',
    icon: FileText,
    iconColor: 'text-cyan-400',
    accentBorder: 'hover:border-cyan-500/50',
    badge: 'Vector Embeddings',
    isRecommended: true,
    stats: '94.2% ATS Pass Rate',
  },
  {
    id: 'mock-interview',
    title: 'Adaptive Mock Interview',
    category: 'Voice & Behavioral',
    description: 'Engage with an intelligent AI interviewer that adapts question difficulty, analyzes tone, and gives instant speech feedback.',
    href: '/interview',
    icon: Bot,
    iconColor: 'text-violet-400',
    accentBorder: 'hover:border-violet-500/50',
    badge: 'LangGraph Engine',
    stats: 'Live Audio & Transcription',
  },
  {
    id: 'coding-round',
    title: 'Technical Coding Sandbox',
    category: 'Algorithms & DS',
    description: 'Solve real-time coding challenges with Monaco IDE, live code execution, edge-case unit tests, and algorithmic complexity hints.',
    href: '/coding',
    icon: Code2,
    iconColor: 'text-emerald-400',
    accentBorder: 'hover:border-emerald-500/50',
    badge: 'Judge0 Sandbox',
    stats: 'Python, TS, Go, C++',
  },
  {
    id: 'company-mode',
    title: 'Company Simulation Mode',
    category: 'FAANG & Tier-1',
    description: 'Interview under exact rubric expectations used by Google (L5/L6), Meta, Amazon (Leadership Principles), and OpenAI.',
    href: '/company-interview',
    icon: Building2,
    iconColor: 'text-amber-400',
    accentBorder: 'hover:border-amber-500/50',
    badge: '12+ Company Rubrics',
    stats: 'FAANG Calibrated',
  },
  {
    id: 'salary-negotiation',
    title: 'Salary Negotiation Coach',
    category: 'Offer Optimization',
    description: 'Roleplay compensation negotiations against realistic recruiter counter-offers to maximize base, equity, and sign-on bonus.',
    href: '/salary-negotiation',
    icon: Coins,
    iconColor: 'text-emerald-400',
    accentBorder: 'hover:border-emerald-500/50',
    badge: 'Levels.fyi Benchmarks',
    stats: '+$28k Avg Increase',
  },
  {
    id: 'career-intelligence',
    title: 'AI Career Intelligence',
    category: 'Strategic Planning',
    description: 'Synthesize market hiring demand, compensation percentiles, and personalized gap analysis into an actionable promotion plan.',
    href: '/career-intelligence',
    icon: Sparkles,
    iconColor: 'text-blue-400',
    accentBorder: 'hover:border-blue-500/50',
    badge: 'Deep RAG Engine',
    stats: 'Target: Staff Eng',
  },
  {
    id: 'job-tracker',
    title: 'Application Kanban Tracker',
    category: 'Pipeline Management',
    description: 'Organize target applications across Wishlist, Applied, Technical, and Offer stages with automated follow-up reminders.',
    href: '/job-tracker',
    icon: Briefcase,
    iconColor: 'text-indigo-400',
    accentBorder: 'hover:border-indigo-500/50',
    badge: 'Kanban Flow',
    stats: '14 Active Roles',
  },
  {
    id: 'daily-challenge',
    title: 'Daily System Design Challenge',
    category: 'Architecture Sprint',
    description: 'Sharpen your system scaling intuition every morning with high-concurrency micro-challenges and earn streak multipliers.',
    href: '/daily-challenge',
    icon: Flame,
    iconColor: 'text-orange-400',
    accentBorder: 'hover:border-orange-500/50',
    badge: '+150 XP Today',
    stats: 'Day 14 Streak',
  },
  {
    id: 'analytics-ranking',
    title: 'Cohort Analytics & Percentile',
    category: 'Benchmark & Insights',
    description: 'Inspect your technical readiness percentile, category strength radars, speech confidence score, and pacing analytics.',
    href: '/analytics',
    icon: BarChart3,
    iconColor: 'text-purple-400',
    accentBorder: 'hover:border-purple-500/50',
    badge: 'Top 8.4% Cohort',
    stats: '88.4 / 100 Index',
  },
]

export default function FeatureCards() {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <span>Career Acceleration Modules</span>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              9 Active Engines
            </span>
          </h2>
          <p className="text-sm text-slate-400">
            Select a specialized simulation module calibrated for staff-tier engineering interviews.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {FEATURE_MODULES.map((module) => {
          const Icon = module.icon
          return (
            <Link
              key={module.id}
              href={module.href}
              className={`group relative rounded-2xl border p-6 transition-all duration-300 flex flex-col justify-between overflow-hidden bg-gradient-to-b from-slate-900/80 to-slate-950/90 backdrop-blur-xl ${
                module.isRecommended
                  ? 'border-cyan-500/50 shadow-lg shadow-cyan-950/40 ring-1 ring-cyan-500/30'
                  : 'border-slate-800/80 hover:border-slate-700 shadow-md shadow-black/40'
              } ${module.accentBorder} hover:-translate-y-1 hover:shadow-xl`}
            >
              {/* Subtle top glow bar for recommended */}
              {module.isRecommended && (
                <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-cyan-500 via-blue-500 to-violet-500" />
              )}

              {/* Ambient radial glow on hover */}
              <div className="absolute -top-12 -right-12 w-32 h-32 bg-cyan-500/5 rounded-full blur-2xl group-hover:bg-cyan-500/15 transition-all pointer-events-none" />

              <div>
                <div className="flex items-start justify-between mb-4">
                  <div className="p-3 rounded-xl bg-slate-800/60 border border-slate-700/60 group-hover:bg-slate-800 group-hover:border-slate-600 transition-colors">
                    <Icon className={`w-6 h-6 ${module.iconColor}`} />
                  </div>
                  <div className="flex items-center gap-1.5">
                    {module.isRecommended && (
                      <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                        Recommended Next
                      </span>
                    )}
                    {module.badge && !module.isRecommended && (
                      <span className="text-[10px] font-semibold tracking-wide px-2 py-0.5 rounded-full bg-slate-800/80 text-slate-300 border border-slate-700/60">
                        {module.badge}
                      </span>
                    )}
                  </div>
                </div>

                <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-1">
                  {module.category}
                </div>
                <h3 className="text-lg font-bold text-white group-hover:text-cyan-300 transition-colors mb-2">
                  {module.title}
                </h3>
                <p className="text-xs text-slate-300 line-clamp-3 leading-relaxed mb-4">
                  {module.description}
                </p>
              </div>

              <div className="pt-4 border-t border-slate-800/60 flex items-center justify-between">
                <span className="text-[11px] font-medium text-slate-400 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  {module.stats}
                </span>
                <span className="text-xs font-semibold text-cyan-400 flex items-center gap-1 group-hover:translate-x-1 transition-transform">
                  Launch <ArrowRight className="w-3.5 h-3.5" />
                </span>
              </div>
            </Link>
          )
        })}
      </div>
    </div>
  )
}
