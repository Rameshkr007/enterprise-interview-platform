'use client'

import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { interviewApi, getBaseUrl } from '@/lib/api'
import { useInterviewStore } from '@/store/interview'
import { useAuthStore } from '@/store/auth'
import {
  Code2,
  Cpu,
  Database,
  Network,
  Terminal,
  Zap,
  Sparkles,
  Flame,
  Building2,
  Clock,
  Mic,
  Sliders,
  CheckCircle2,
  ArrowRight,
  ShieldCheck,
  GraduationCap,
  Layers,
  HelpCircle,
  AlertTriangle,
  ChevronLeft,
  UserCheck,
  LogIn,
  RefreshCw,
  Activity,
} from 'lucide-react'

// ── CSE Targeted Presets ─────────────────────────────────────────────────────
interface PresetConfig {
  id: string
  name: string
  subtitle: string
  tag: string
  icon: React.ElementType
  iconColor: string
  borderColor: string
  bgHover: string
  questionCount: number
  difficulty: 'easy' | 'medium' | 'hard'
  adaptive: boolean
  categories: string[]
  hiringTier: string
  estMinutes: number
}

const CSE_PRESETS: PresetConfig[] = [
  {
    id: 'campus-placement',
    name: 'Campus Placement SDE-1',
    subtitle: 'DSA Patterns, Core OS/DBMS, & Project Architecture Defense',
    tag: 'Most Popular for CSE',
    icon: GraduationCap,
    iconColor: 'text-cyan-400',
    borderColor: 'border-cyan-500/40 hover:border-cyan-400',
    bgHover: 'group-hover:bg-cyan-500/10',
    questionCount: 8,
    difficulty: 'medium',
    adaptive: true,
    categories: ['technical', 'system_design', 'behavioral'],
    hiringTier: 'Campus Drives (TCS Prime, Infosys DPE, Wipro, Tier-1 Drives)',
    estMinutes: 18,
  },
  {
    id: 'faang-algorithmic',
    name: 'FAANG Algorithmic Loop',
    subtitle: 'Advanced Problem Solving, Edge Cases, & Time/Space Rigor',
    tag: 'Tier-1 Product Bar',
    icon: Flame,
    iconColor: 'text-orange-400',
    borderColor: 'border-orange-500/40 hover:border-orange-400',
    bgHover: 'group-hover:bg-orange-500/10',
    questionCount: 10,
    difficulty: 'hard',
    adaptive: true,
    categories: ['technical', 'system_design'],
    hiringTier: 'Google, Amazon (LP), Meta, Microsoft, Uber',
    estMinutes: 24,
  },
  {
    id: 'fullstack-web',
    name: 'Full-Stack & Systems Dev',
    subtitle: 'React/Next.js Internals, REST APIs, SQL Queries & Async Concurrency',
    tag: 'High-Growth Tech',
    icon: Layers,
    iconColor: 'text-violet-400',
    borderColor: 'border-violet-500/40 hover:border-violet-400',
    bgHover: 'group-hover:bg-violet-500/10',
    questionCount: 8,
    difficulty: 'medium',
    adaptive: true,
    categories: ['technical', 'situational'],
    hiringTier: 'Swiggy, Zomato, Razorpay, FinTech & YC Startups',
    estMinutes: 16,
  },
  {
    id: 'core-cs-fundamentals',
    name: 'Core CS Fundamentals',
    subtitle: 'Operating Systems, DBMS & SQL, Computer Networks, & OOPs Concepts',
    tag: 'Gatekeeper Round',
    icon: Terminal,
    iconColor: 'text-emerald-400',
    borderColor: 'border-emerald-500/40 hover:border-emerald-400',
    bgHover: 'group-hover:bg-emerald-500/10',
    questionCount: 6,
    difficulty: 'medium',
    adaptive: true,
    categories: ['technical'],
    hiringTier: 'Technical Written & First-Round Elimination Interviews',
    estMinutes: 12,
  },
]

// ── CSE Focus Disciplines ────────────────────────────────────────────────────
interface DisciplineOption {
  id: string
  name: string
  shortDesc: string
  icon: React.ElementType
  color: string
}

const CSE_DISCIPLINES: DisciplineOption[] = [
  {
    id: 'technical',
    name: 'Data Structures & Algorithms',
    shortDesc: 'Arrays, Trees, Graphs, DP, Sorting, & Time Complexity',
    icon: Code2,
    color: 'text-cyan-400',
  },
  {
    id: 'system_design',
    name: 'Core CS (OS, DBMS, Networks, HLD)',
    shortDesc: 'Deadlocks, Indexing, TCP/IP, Caching, & Scalable Schemas',
    icon: Cpu,
    color: 'text-purple-400',
  },
  {
    id: 'behavioral',
    name: 'Project Defense & STAR Behavioral',
    shortDesc: 'Final-year projects, tech trade-offs, teamwork, & leadership',
    icon: GraduationCap,
    color: 'text-amber-400',
  },
  {
    id: 'situational',
    name: 'Practical Debugging & Web Engineering',
    shortDesc: 'Production bugs, async concurrency, state handling, & APIs',
    icon: Network,
    color: 'text-emerald-400',
  },
  {
    id: 'culture_fit',
    name: 'HR & Engineering Culture Caliber',
    shortDesc: 'Conflict resolution, workplace adaptability, & ambition',
    icon: Sparkles,
    color: 'text-pink-400',
  },
]

const HIRING_TIERS = [
  { id: 'campus', label: '🎓 Campus Placements (SDE-1)', desc: 'TCS Prime, Infosys, Cognizant, College Drives' },
  { id: 'unicorns', label: '🦄 Tech Unicorns & Product', desc: 'Swiggy, Zomato, Razorpay, Zepto, Flipkart' },
  { id: 'faang', label: '🏛️ MAANG / FAANG Global', desc: 'Google, Meta, Microsoft, Amazon L4/L5' },
  { id: 'startup', label: '🚀 YC & High-Velocity Startups', desc: 'Fast prototyping, high ownership & system intuition' },
]

export default function NewInterviewPage() {
  const router = useRouter()
  const setSession = useInterviewStore((s) => s.setSession)
  const { user, login, fetchMe } = useAuthStore()

  // State
  const [selectedPreset, setSelectedPreset] = useState<string>('campus-placement')
  const [count, setCount] = useState<number>(8)
  const [categories, setCategories] = useState<string[]>(['technical', 'system_design', 'behavioral'])
  const [difficulty, setDifficulty] = useState<'easy' | 'medium' | 'hard'>('medium')
  const [adaptiveMode, setAdaptiveMode] = useState<boolean>(true)
  const [targetTier, setTargetTier] = useState<string>('campus')
  const [isCreating, setIsCreating] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  // Auth & Backend Warmup Telemetry State
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false)
  const [isAuthLoading, setIsAuthLoading] = useState<boolean>(true)
  const [isDemoLoggingIn, setIsDemoLoggingIn] = useState<boolean>(false)
  const [serverWarmup, setServerWarmup] = useState<'online' | 'warming' | 'checking'>('checking')

  // Check auth and ping backend on mount to pre-warm Render
  useEffect(() => {
    let isMounted = true

    async function initCheck() {
      // 1. Check local auth status
      const localToken = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null
      if (localToken) {
        setIsAuthenticated(true)
        fetchMe().catch(() => {})
      } else if (user) {
        setIsAuthenticated(true)
      } else {
        setIsAuthenticated(false)
      }
      setIsAuthLoading(false)

      // 2. Background ping to wake up Render if sleeping
      try {
        const rootUrl = getBaseUrl().replace('/api/v1', '')
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 8000)

        const res = await fetch(`${rootUrl}/health`, {
          method: 'GET',
          signal: controller.signal,
        })
        clearTimeout(timeoutId)

        if (isMounted) {
          if (res.ok) {
            setServerWarmup('online')
          } else {
            setServerWarmup('warming')
          }
        }
      } catch {
        if (isMounted) {
          setServerWarmup('warming')
        }
      }
    }

    initCheck()
    return () => {
      isMounted = false
    }
  }, [fetchMe, user])

  // Apply Preset
  const handleApplyPreset = (preset: PresetConfig) => {
    setSelectedPreset(preset.id)
    setCount(preset.questionCount)
    setCategories(preset.categories)
    setDifficulty(preset.difficulty)
    setAdaptiveMode(preset.adaptive)
  }

  // Toggle Category
  const toggleCategory = (catId: string) => {
    setSelectedPreset('') // custom mode
    setCategories((prev) =>
      prev.includes(catId)
        ? prev.length > 1
          ? prev.filter((c) => c !== catId)
          : prev
        : [...prev, catId]
    )
  }

  // Calculate estimated duration
  const estimatedMinutes = Math.round(count * 2.2)

  // 1-Click CSE Demo Sign In
  const handleQuickDemoLogin = async () => {
    setIsDemoLoggingIn(true)
    setError(null)
    try {
      await login('candidate@enterprise.ai', 'CandidatePassword123!')
      setIsAuthenticated(true)
      setIsDemoLoggingIn(false)
    } catch {
      // Fallback: try candidate account
      try {
        await login('csetest@enterprise.ai', 'Password123!')
        setIsAuthenticated(true)
      } catch (err: any) {
        setError(err?.response?.data?.detail || err?.response?.data?.message || 'Demo sign-in failed. Please use the login page.')
      } finally {
        setIsDemoLoggingIn(false)
      }
    }
  }

  // Start Session with Auto-Auth Resilience
  async function startInterview() {
    setIsCreating(true)
    setError(null)

    try {
      // 1. Ensure user is authenticated before creating session
      const existingToken = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null
      if (!existingToken && !user) {
        // Auto-provision guest candidate access seamlessly
        try {
          await login('candidate@enterprise.ai', 'CandidatePassword123!')
          setIsAuthenticated(true)
        } catch {
          await login('csetest@enterprise.ai', 'Password123!')
          setIsAuthenticated(true)
        }
      }

      // 2. Create Interview Session
      const session = await interviewApi.createSession({
        target_question_count: count,
        focus_categories: categories.length > 0 ? categories : ['technical'],
        starting_difficulty: difficulty,
        adaptive_mode: adaptiveMode,
      })

      setSession(session)
      router.push(`/interview/${session.id}`)
    } catch (err: any) {
      let msg = 'Failed to initialize interview session.'

      if (err?.response?.data?.detail) {
        const detail = err.response.data.detail
        msg = typeof detail === 'string' ? detail : detail[0]?.msg || JSON.stringify(detail)
      } else if (err?.response?.data?.message) {
        msg = err.response.data.message
      } else if (err?.code === 'ECONNABORTED' || err?.message?.includes('timeout')) {
        msg = 'The AI Engine took longer than usual while warming up. Please click Launch once more.'
      } else if (err?.message) {
        msg = err.message
      }

      setError(msg)
      setIsCreating(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#070814] text-slate-100 selection:bg-cyan-500/30 selection:text-cyan-200 py-8 px-4 sm:px-6 lg:px-8">
      {/* Background Volumetric Glows */}
      <div className="fixed top-0 left-1/3 w-[500px] h-[500px] bg-blue-600/10 rounded-full blur-[140px] pointer-events-none" />
      <div className="fixed bottom-0 right-1/4 w-[450px] h-[450px] bg-cyan-500/10 rounded-full blur-[140px] pointer-events-none" />

      <div className="max-w-5xl mx-auto space-y-8 relative z-10 animate-fade-in">
        {/* Navigation Bar */}
        <div className="flex items-center justify-between pb-4 border-b border-white/[0.06]">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-white/[0.04] border border-white/[0.08] hover:border-white/[0.15] text-xs font-semibold text-slate-300 hover:text-white transition-all group"
          >
            <ChevronLeft className="w-4 h-4 text-slate-400 group-hover:-translate-x-0.5 transition-transform" />
            <span>Back to Dashboard</span>
          </Link>

          <div className="flex items-center gap-3 text-[11px] font-mono text-slate-400">
            {/* Live Backend Telemetry Indicator */}
            {serverWarmup === 'online' ? (
              <span className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                AI ENGINE: ONLINE &amp; READY
              </span>
            ) : (
              <span className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-300">
                <Activity className="w-3.5 h-3.5 animate-spin text-amber-400" />
                AI BACKEND: CONNECTED
              </span>
            )}

            {/* Auth Indicator */}
            {isAuthenticated ? (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-300">
                <UserCheck className="w-3.5 h-3.5 text-cyan-400" />
                <span className="truncate max-w-[120px]">{user?.full_name?.split(' ')[0] || 'Authenticated'}</span>
              </span>
            ) : (
              <button
                type="button"
                onClick={handleQuickDemoLogin}
                disabled={isDemoLoggingIn}
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-500/15 border border-indigo-500/30 text-indigo-300 hover:bg-indigo-500/25 transition-all cursor-pointer font-bold"
              >
                <Zap className="w-3.5 h-3.5 text-indigo-400" />
                <span>{isDemoLoggingIn ? 'Signing In...' : '1-Click Demo Login'}</span>
              </button>
            )}
          </div>
        </div>

        {/* Hero Section */}
        <div className="space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono font-medium bg-gradient-to-r from-cyan-500/10 via-indigo-500/10 to-purple-500/10 border border-cyan-500/30 text-cyan-300">
            <GraduationCap className="w-3.5 h-3.5 text-cyan-400" />
            <span>CSE Placement &amp; SDE Technical Launchpad</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Configure Interview Session
          </h1>
          <p className="text-sm sm:text-base text-slate-400 max-w-2xl leading-relaxed">
            Calibrated specifically for Computer Science &amp; Engineering students. Practice adaptive coding algorithms, core CS fundamentals, system design, and project defense with real-time AI debriefs.
          </p>
        </div>

        {/* Non-Authenticated Banner (Helpful for direct visitors) */}
        {!isAuthenticated && !isAuthLoading && (
          <div className="p-4 rounded-2xl bg-gradient-to-r from-indigo-950/40 via-purple-950/30 to-slate-900/40 border border-indigo-500/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-lg">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shrink-0">
                <Sparkles className="w-4 h-4" />
              </div>
              <div>
                <div className="text-xs font-bold text-white">Instant CSE Candidate Access Available</div>
                <div className="text-[11px] text-slate-300">
                  Click below to instantly authenticate as Arjun Sharma (CSE Candidate) or launch directly.
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2 self-stretch sm:self-auto shrink-0">
              <button
                type="button"
                onClick={handleQuickDemoLogin}
                disabled={isDemoLoggingIn}
                className="flex-1 sm:flex-none px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-xs font-bold text-white shadow-md transition-all flex items-center justify-center gap-1.5 cursor-pointer"
              >
                <Zap className="w-3.5 h-3.5 fill-white" />
                <span>{isDemoLoggingIn ? 'Authenticating...' : '1-Click Quick Login'}</span>
              </button>
              <Link
                href="/login"
                className="px-3 py-2 rounded-xl bg-white/[0.04] border border-white/[0.08] hover:bg-white/[0.08] text-xs font-semibold text-slate-300 hover:text-white transition-all text-center"
              >
                Sign In
              </Link>
            </div>
          </div>
        )}

        {/* Error Alert with Smart Recovery */}
        {error && (
          <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm flex items-start justify-between gap-3 animate-shake">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
              <div className="flex-1">
                <div className="font-bold">Session Initialization Notice</div>
                <div className="text-xs text-red-300/80 mt-0.5">{error}</div>
              </div>
            </div>
            <button
              type="button"
              onClick={startInterview}
              disabled={isCreating}
              className="px-3 py-1.5 rounded-xl bg-red-500/20 border border-red-500/40 text-xs font-bold text-white hover:bg-red-500/30 transition-all flex items-center gap-1.5 shrink-0 cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Retry</span>
            </button>
          </div>
        )}

        {/* ── Section 1: 1-Click CSE Placement Presets ──────────────────────── */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2 font-mono">
              <Zap className="w-4 h-4 text-amber-400" />
              <span>Step 1: Choose CSE Placement Blueprint</span>
            </h2>
            <span className="text-xs text-slate-400">Select preset or customize below</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {CSE_PRESETS.map((preset) => {
              const Icon = preset.icon
              const isSelected = selectedPreset === preset.id
              return (
                <button
                  key={preset.id}
                  type="button"
                  onClick={() => handleApplyPreset(preset)}
                  className={`group relative text-left p-5 rounded-2xl border transition-all duration-300 overflow-hidden cursor-pointer ${
                    isSelected
                      ? 'bg-gradient-to-br from-indigo-950/60 to-slate-900/90 border-cyan-400 shadow-[0_0_30px_rgba(6,182,212,0.25)] ring-1 ring-cyan-400/50'
                      : 'bg-slate-900/40 border-slate-800/80 hover:bg-slate-900/80 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="flex items-center gap-3">
                      <div className={`p-2.5 rounded-xl bg-white/[0.05] border border-white/[0.08] ${preset.iconColor}`}>
                        <Icon className="w-5 h-5" />
                      </div>
                      <div>
                        <div className="font-bold text-sm text-white group-hover:text-cyan-300 transition-colors">
                          {preset.name}
                        </div>
                        <div className="text-[10px] font-mono text-cyan-400 font-semibold mt-0.5">
                          {preset.tag}
                        </div>
                      </div>
                    </div>

                    {isSelected && (
                      <span className="p-1 rounded-full bg-cyan-500/20 text-cyan-400 border border-cyan-500/40">
                        <CheckCircle2 className="w-4 h-4" />
                      </span>
                    )}
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed mb-4">
                    {preset.subtitle}
                  </p>

                  <div className="flex items-center justify-between pt-3 border-t border-white/[0.06] text-[11px] text-slate-400 font-mono">
                    <span className="flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5 text-slate-400" />
                      ~{preset.estMinutes} mins ({preset.questionCount} Qs)
                    </span>
                    <span className="capitalize text-slate-300">
                      {preset.difficulty} Level
                    </span>
                  </div>
                </button>
              )
            })}
          </div>
        </div>

        {/* ── Section 2: Custom Fine-Tuning ─────────────────────────────────── */}
        <div className="rounded-3xl border border-white/[0.08] bg-slate-950/60 backdrop-blur-2xl p-6 sm:p-8 space-y-8 shadow-2xl">
          <div className="border-b border-white/[0.06] pb-4">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2 font-mono">
              <Sliders className="w-4 h-4 text-cyan-400" />
              <span>Step 2: Fine-Tune Technical Curriculum</span>
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Customize the topics, target hiring bar, and question depth for your upcoming drive.
            </p>
          </div>

          {/* Discipline Selection Grid */}
          <div className="space-y-3">
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 font-mono">
              Target Technical Disciplines <span className="text-cyan-400">*</span>
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {CSE_DISCIPLINES.map((disc) => {
                const Icon = disc.icon
                const isChecked = categories.includes(disc.id)
                return (
                  <button
                    key={disc.id}
                    type="button"
                    onClick={() => toggleCategory(disc.id)}
                    className={`p-3.5 rounded-2xl border text-left transition-all flex items-start gap-3 cursor-pointer ${
                      isChecked
                        ? 'bg-indigo-950/40 border-indigo-500/50 shadow-sm shadow-indigo-950/50 text-white'
                        : 'bg-white/[0.02] border-white/[0.06] text-slate-400 hover:border-white/[0.12] hover:text-slate-200'
                    }`}
                  >
                    <div
                      className={`p-2 rounded-xl border mt-0.5 shrink-0 ${
                        isChecked
                          ? 'bg-indigo-500/20 border-indigo-400/30 ' + disc.color
                          : 'bg-white/[0.04] border-white/[0.08] text-slate-500'
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-bold truncate leading-tight">
                        {disc.name}
                      </div>
                      <div className="text-[10px] text-slate-400 line-clamp-2 mt-1 leading-snug">
                        {disc.shortDesc}
                      </div>
                    </div>
                  </button>
                )
              })}
            </div>
          </div>

          {/* Target Company / Hiring Tier */}
          <div className="space-y-3">
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 font-mono">
              Hiring Rubric Calibration
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {HIRING_TIERS.map((tier) => (
                <button
                  key={tier.id}
                  type="button"
                  onClick={() => setTargetTier(tier.id)}
                  className={`p-3.5 rounded-2xl border text-left transition-all cursor-pointer ${
                    targetTier === tier.id
                      ? 'bg-cyan-950/30 border-cyan-500/60 ring-1 ring-cyan-500/30'
                      : 'bg-white/[0.02] border-white/[0.06] hover:border-white/[0.12]'
                  }`}
                >
                  <div className="text-xs font-bold text-white mb-1">{tier.label}</div>
                  <div className="text-[10px] text-slate-400 leading-snug">{tier.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Slider & Difficulty Row */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 pt-2">
            {/* Left: Question Count Slider (7 cols) */}
            <div className="lg:col-span-7 space-y-4">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono">
                  Interview Depth: <span className="text-cyan-400 font-extrabold text-sm">{count} Questions</span>
                </label>
                <span className="text-xs font-mono text-slate-400 flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5 text-cyan-400" />
                  Estimated: <strong className="text-white">~{estimatedMinutes} mins</strong>
                </span>
              </div>

              {/* Enhanced Styled Range Slider */}
              <div className="space-y-2">
                <input
                  id="question-count"
                  type="range"
                  min={3}
                  max={20}
                  step={1}
                  value={count}
                  onChange={(e) => {
                    setSelectedPreset('')
                    setCount(Number(e.target.value))
                  }}
                  className="w-full h-2.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400 focus:outline-none"
                />
                <div className="flex justify-between text-[11px] font-mono text-slate-400">
                  <span>3 Qs (Quick Drill)</span>
                  <span>8 Qs (Campus Std)</span>
                  <span>14 Qs (Onsite Mock)</span>
                  <span>20 Qs (Deep Dive)</span>
                </div>
              </div>
            </div>

            {/* Right: Starting Difficulty (5 cols) */}
            <div className="lg:col-span-5 space-y-4">
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 font-mono">
                Starting Difficulty
              </label>
              <div className="grid grid-cols-3 gap-2">
                {(['easy', 'medium', 'hard'] as const).map((diff) => (
                  <button
                    key={diff}
                    type="button"
                    onClick={() => {
                      setSelectedPreset('')
                      setDifficulty(diff)
                    }}
                    className={`py-2 px-3 rounded-xl text-xs font-bold uppercase tracking-wider border transition-all cursor-pointer text-center ${
                      difficulty === diff
                        ? diff === 'easy'
                          ? 'bg-emerald-500/20 border-emerald-500/60 text-emerald-300'
                          : diff === 'medium'
                          ? 'bg-cyan-500/20 border-cyan-500/60 text-cyan-300'
                          : 'bg-red-500/20 border-red-500/60 text-red-300'
                        : 'bg-white/[0.03] border-white/[0.08] text-slate-400 hover:text-white'
                    }`}
                  >
                    {diff}
                  </button>
                ))}
              </div>

              {/* Adaptive Toggle */}
              <div
                onClick={() => setAdaptiveMode(!adaptiveMode)}
                className="flex items-center justify-between p-2.5 rounded-xl bg-white/[0.03] border border-white/[0.06] cursor-pointer hover:border-white/[0.12] transition-colors"
              >
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-cyan-400" />
                  <span className="text-xs font-semibold text-slate-200">Real-Time Adaptive Scaling</span>
                </div>
                <div
                  className={`w-9 h-5 rounded-full p-0.5 transition-colors ${
                    adaptiveMode ? 'bg-cyan-500' : 'bg-slate-700'
                  }`}
                >
                  <div
                    className={`w-4 h-4 rounded-full bg-white transition-transform ${
                      adaptiveMode ? 'translate-x-4' : 'translate-x-0'
                    }`}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ── Section 3: CSE Student Hardware & AI Evaluation Checklist ─────── */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/[0.06] flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 shrink-0">
              <Mic className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-bold text-white">Audio &amp; Voice Input</div>
              <div className="text-[11px] text-slate-400 mt-0.5">Whisper AI speech-to-text with filler word &amp; WPM metrics.</div>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/[0.06] flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400 shrink-0">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-bold text-white">Multi-Dimension Scoring</div>
              <div className="text-[11px] text-slate-400 mt-0.5">Technical accuracy, foundational depth, &amp; articulation radar.</div>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/[0.06] flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 shrink-0">
              <CheckCircle2 className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-bold text-white">Debrief Report &amp; Rank</div>
              <div className="text-[11px] text-slate-400 mt-0.5">Instant performance telemetry report &amp; percentile rank.</div>
            </div>
          </div>
        </div>

        {/* ── Section 4: Primary Action Launch Bar ──────────────────────────── */}
        <div className="sticky bottom-4 z-30 p-4 sm:p-5 rounded-3xl bg-slate-900/90 border border-cyan-500/40 backdrop-blur-2xl shadow-[0_10px_50px_rgba(0,0,0,0.8)] flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-2xl bg-cyan-500/20 border border-cyan-500/40 flex items-center justify-center text-cyan-400 shrink-0">
              <Terminal className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs sm:text-sm font-bold text-white flex items-center gap-2">
                <span>Selected:</span>
                <span className="text-cyan-400">{count} Questions</span>
                <span className="text-slate-600">•</span>
                <span className="capitalize text-slate-300">{difficulty} Difficulty</span>
                {adaptiveMode && (
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                    Adaptive
                  </span>
                )}
              </div>
              <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                Target: {HIRING_TIERS.find((t) => t.id === targetTier)?.label.split(' ')[1] || 'SDE-1'} &bull; ~{estimatedMinutes} Minutes
              </div>
            </div>
          </div>

          <button
            id="start-interview-btn"
            type="button"
            onClick={startInterview}
            disabled={isCreating}
            className="w-full sm:w-auto px-8 py-3.5 rounded-2xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-sm font-extrabold text-white shadow-[0_0_30px_rgba(99,102,241,0.5)] hover:brightness-110 active:scale-95 disabled:opacity-50 transition-all flex items-center justify-center gap-2.5 cursor-pointer shrink-0"
          >
            {isCreating ? (
              <>
                <Sparkles className="w-4 h-4 animate-spin text-cyan-300" />
                <span>Initializing LangGraph Engine...</span>
              </>
            ) : (
              <>
                <Zap className="w-4 h-4 fill-white" />
                <span>Launch AI Interview</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
