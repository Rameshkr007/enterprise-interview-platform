'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/store/auth'
import SpatialCard from '@/components/ui/SpatialCard'

export default function DashboardPage() {
  const { user, fetchMe, logout } = useAuthStore()
  const router = useRouter()
  const [activeTab, setActiveTab] = useState<'all' | 'interviews' | 'technical' | 'career'>('all')

  useEffect(() => {
    fetchMe().then(() => {
      if (!useAuthStore.getState().user) {
        router.push('/login')
      }
    })
  }, [fetchMe, router])

  if (!user) {
    return (
      <div className="min-h-screen bg-[#07080c] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-xl border border-cyan-500/40 border-t-cyan-400 animate-spin" />
          <p className="font-mono text-xs text-slate-400 tracking-wider">INITIALIZING AI COMMAND CENTER...</p>
        </div>
      </div>
    )
  }

  const firstName = user.full_name?.split(' ')[0] || 'Engineer'

  const allModules = [
    {
      category: 'career',
      href: '/ats',
      title: 'Semantic ATS Analyzer',
      description: 'Run 1536d PGVector cosine similarity against job descriptions to extract missing competencies.',
      icon: '📊',
      badge: 'PGVector Core',
      accentColor: '#00f0ff',
      ctaText: 'Launch ATS Scan',
      stat: '94% Match Potential',
      statLabel: 'Semantic Depth',
    },
    {
      category: 'interviews',
      href: '/interview/new',
      title: 'Adaptive Mock Interview',
      description: 'LangGraph multi-turn interview with real-time biometric telemetry, speech analysis, and dynamic follow-ups.',
      icon: '🎙️',
      badge: 'Stateful Engine',
      accentColor: '#8b5cf6',
      ctaText: 'Start Live Loop',
      stat: '10 Questions',
      statLabel: 'Target Session',
    },
    {
      category: 'technical',
      href: '/coding',
      title: 'AI Coding Interview',
      description: 'Full-featured collaborative code editor with automated complexity calculation and instant test suite execution.',
      icon: '💻',
      badge: 'Algorithmic',
      accentColor: '#38bdf8',
      ctaText: 'Open Code Studio',
      stat: 'O(N) Complexity',
      statLabel: 'Validation Rubric',
    },
    {
      category: 'technical',
      href: '/system-design',
      title: 'System Design Interview',
      description: 'Defend high-scale distributed architectures: load balancers, caching tiers, event brokers, and database partitions.',
      icon: '📐',
      badge: 'Distributed Systems',
      accentColor: '#10b981',
      ctaText: 'Architect System',
      stat: '100K QPS Target',
      statLabel: 'Scale Factor',
    },
    {
      category: 'interviews',
      href: '/company-mode',
      title: 'Company Mode Calibration',
      description: 'Calibrated simulations for Google committee grading, Amazon Leadership Principles, and Meta architectural loops.',
      icon: '🏢',
      badge: 'Tier-1 FAANG',
      accentColor: '#f59e0b',
      ctaText: 'Select Company',
      stat: '16 LPs Covered',
      statLabel: 'Evaluation Rubric',
    },
    {
      category: 'career',
      href: '/negotiation',
      title: 'Salary Negotiation Simulator',
      description: 'Interactive counter-offer sparring partner against aggressive recruiter compensation tactics.',
      icon: '💰',
      badge: 'Offer Sparring',
      accentColor: '#ec4899',
      ctaText: 'Counter Recruiter',
      stat: '+18% Avg Delta',
      statLabel: 'Comp Lift',
    },
    {
      category: 'career',
      href: '/resume-builder',
      title: 'AI Career Intelligence',
      description: 'Transform passive responsibilities into metric-backed STAR achievements and generate tailored executive narratives.',
      icon: '✨',
      badge: 'Synthesis AI',
      accentColor: '#06b6d4',
      ctaText: 'Enhance Resume',
      stat: 'STAR Format',
      statLabel: 'Impact Structuring',
    },
    {
      category: 'career',
      href: '/job-tracker',
      title: 'Job Pipeline Kanban',
      description: 'Unified application CRM to track interview stages, recruiter touchpoints, and scheduled interview rounds.',
      icon: '💼',
      badge: 'Pipeline CRM',
      accentColor: '#f97316',
      ctaText: 'View Pipeline',
      stat: 'Active Tracking',
      statLabel: 'Workflow Board',
    },
    {
      category: 'technical',
      href: '/daily-challenge',
      title: 'Daily Technical Challenge',
      description: 'Spaced repetition technical drills to maintain peak interview fluency with streak multipliers.',
      icon: '🔥',
      badge: 'Spaced Repetition',
      accentColor: '#ef4444',
      ctaText: 'Solve Problem',
      stat: 'Day 4 Streak',
      statLabel: 'Fluency Protocol',
    },
    {
      category: 'technical',
      href: '/analytics',
      title: 'Analytics & Ranking',
      description: 'Historical telemetry telemetry dashboard: acoustic pitch stability, silence pause ratios, and percentile ranking.',
      icon: '📈',
      badge: 'Diagnostic Telemetry',
      accentColor: '#a855f7',
      ctaText: 'View Diagnostics',
      stat: 'Top 15%',
      statLabel: 'Global Percentile',
    },
  ]

  const filteredModules = allModules.filter(
    (m) => activeTab === 'all' || m.category === activeTab
  )

  return (
    <div className="min-h-screen bg-[#07080c] text-slate-100 flex flex-col selection:bg-cyan-500/30 selection:text-cyan-200">
      {/* ── Top Navigation Bar ───────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 border-b border-white/5 bg-[#07080c]/85 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 h-18 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/" className="flex items-center gap-2 group">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-400 via-indigo-500 to-violet-600 flex items-center justify-center shadow-[0_0_15px_rgba(0,240,255,0.3)] transition-transform group-hover:scale-105">
                <span className="text-black font-black text-xs">AI</span>
              </div>
              <div>
                <span className="font-extrabold text-base tracking-tight text-white block">InterviewAI</span>
                <span className="text-[10px] font-mono text-cyan-400 block -mt-1">COMMAND CENTER</span>
              </div>
            </Link>
          </div>

          <div className="hidden lg:flex items-center gap-6 text-xs font-mono text-slate-400">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              RENDER CORE: HEALTHY
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-cyan-400" />
              PGVECTOR: READY
            </span>
          </div>

          <div className="flex items-center gap-4">
            <div className="text-right hidden sm:block">
              <div className="text-xs font-bold text-white">{user.full_name}</div>
              <div className="text-[11px] font-mono text-cyan-400 capitalize">{user.role || 'Candidate'}</div>
            </div>

            <button
              id="logout-btn"
              onClick={() => {
                logout()
                router.push('/login')
              }}
              className="text-xs font-semibold px-3.5 py-2 rounded-lg border border-white/10 bg-white/[0.03] text-slate-300 hover:text-white hover:bg-white/[0.08] hover:border-red-500/40 transition-colors"
            >
              Sign Out
            </button>
          </div>
        </div>
      </header>

      {/* ── Main Command Dashboard Body ─────────────────────────────────── */}
      <main className="max-w-7xl mx-auto px-6 py-10 flex-1 w-full animate-fade-in space-y-10">
        {/* Welcome & Mission Control Panel */}
        <div className="relative rounded-3xl border border-white/10 bg-gradient-to-r from-[#0c0e18] via-[#0f1220] to-[#0c0e18] p-8 md:p-10 overflow-hidden shadow-[0_10px_40px_rgba(0,0,0,0.5)]">
          {/* Subtle Ambient Glow */}
          <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

          <div className="relative z-10 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-8">
            <div className="space-y-3 max-w-2xl">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-[11px] font-mono font-medium bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">
                ACTIVE RECRUITMENT CALIBRATION
              </div>
              <h1 className="text-3xl md:text-4xl font-black text-white tracking-tight">
                Welcome back, <span className="gradient-text">{firstName}</span>.
              </h1>
              <p className="text-sm md:text-base text-slate-400 leading-relaxed">
                Target Role: <span className="text-slate-200 font-medium">Senior Full-Stack Engineer / Distributed Systems</span>.
                Your current readiness telemetry stands in the 85th percentile.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3 w-full lg:w-auto">
              <Link
                href="/interview/new"
                className="btn-cyan text-xs md:text-sm py-3 px-6 shadow-[0_0_20px_rgba(0,240,255,0.25)] flex items-center gap-2"
              >
                <span>Launch Mock Interview</span>
                <span>→</span>
              </Link>
              <Link
                href="/ats"
                className="btn-ghost text-xs md:text-sm py-3 px-6"
              >
                Analyze New Resume
              </Link>
            </div>
          </div>

          {/* Telemetry Metric Bar */}
          <div className="relative z-10 grid grid-cols-2 sm:grid-cols-4 gap-4 mt-8 pt-8 border-t border-white/10">
            <div className="p-4 rounded-xl bg-black/40 border border-white/5">
              <div className="text-xs font-mono text-slate-400 mb-1">Overall Readiness</div>
              <div className="text-2xl font-black text-cyan-400 font-mono">88%</div>
              <div className="text-[10px] text-emerald-400 font-mono mt-1">+4.2% this week</div>
            </div>
            <div className="p-4 rounded-xl bg-black/40 border border-white/5">
              <div className="text-xs font-mono text-slate-400 mb-1">Completed Loops</div>
              <div className="text-2xl font-black text-violet-400 font-mono">6 Rounds</div>
              <div className="text-[10px] text-slate-400 font-mono mt-1">Multi-Turn Sessions</div>
            </div>
            <div className="p-4 rounded-xl bg-black/40 border border-white/5">
              <div className="text-xs font-mono text-slate-400 mb-1">ATS Analyses</div>
              <div className="text-2xl font-black text-emerald-400 font-mono">12 Scans</div>
              <div className="text-[10px] text-slate-400 font-mono mt-1">PGVector Matched</div>
            </div>
            <div className="p-4 rounded-xl bg-black/40 border border-white/5">
              <div className="text-xs font-mono text-slate-400 mb-1">Practice Streak</div>
              <div className="text-2xl font-black text-amber-400 font-mono">4 Days 🔥</div>
              <div className="text-[10px] text-amber-300 font-mono mt-1">Daily Challenge Active</div>
            </div>
          </div>
        </div>

        {/* ── Capability Filter Tabs ───────────────────────────────────────── */}
        <div className="flex items-center justify-between flex-wrap gap-4 border-b border-white/5 pb-4">
          <div>
            <h2 className="text-xl font-bold text-white">Career Intelligence Launchpad</h2>
            <p className="text-xs text-slate-400 font-mono">Select a simulation module to initiate practice</p>
          </div>

          <div className="flex items-center gap-1.5 p-1 rounded-xl bg-white/[0.03] border border-white/10 text-xs font-mono">
            {(['all', 'interviews', 'technical', 'career'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-3.5 py-1.5 rounded-lg transition-colors capitalize ${
                  activeTab === tab
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>

        {/* ── 10-Module Spatial Card Grid ─────────────────────────────────── */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredModules.map((mod) => (
            <SpatialCard
              key={mod.title}
              href={mod.href}
              title={mod.title}
              description={mod.description}
              icon={mod.icon}
              badge={mod.badge}
              accentColor={mod.accentColor}
              ctaText={mod.ctaText}
              stat={mod.stat}
              statLabel={mod.statLabel}
            />
          ))}
        </div>

        {/* ── Diagnostic Skill Progress Strip ─────────────────────────────── */}
        <div className="rounded-2xl border border-white/10 bg-[#0c0e18]/80 p-7">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-base font-bold text-white">Competency Readiness Vectors</h3>
              <p className="text-xs text-slate-400 font-mono">Real-time skill rubric synthesis across recent attempts</p>
            </div>
            <Link href="/analytics" className="text-xs font-mono text-cyan-400 hover:underline">
              Full Breakdown →
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            {[
              { skill: 'Distributed Systems', score: 85, color: '#10b981' },
              { skill: 'LangGraph & AI Logic', score: 92, color: '#00f0ff' },
              { skill: 'Algorithmic Purity', score: 78, color: '#38bdf8' },
              { skill: 'STAR Behavioral Flow', score: 88, color: '#f59e0b' },
              { skill: 'Acoustic Confidence', score: 82, color: '#a855f7' },
            ].map((s) => (
              <div key={s.skill} className="p-4 rounded-xl bg-black/30 border border-white/5 space-y-2">
                <div className="flex items-center justify-between text-xs font-medium">
                  <span className="text-slate-300">{s.skill}</span>
                  <span className="font-mono font-bold" style={{ color: s.color }}>
                    {s.score}%
                  </span>
                </div>
                <div className="w-full h-1.5 rounded-full bg-white/10 overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{ width: `${s.score}%`, backgroundColor: s.color }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  )
}
